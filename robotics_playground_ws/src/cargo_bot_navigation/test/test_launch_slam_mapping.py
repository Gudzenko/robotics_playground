"""Headless integration test for the indoor SLAM mapping graph."""

import math
import os
from pathlib import Path
import statistics
import tempfile
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from cargo_bot_navigation.save_slam_map import SlamMapSaver
from geometry_msgs.msg import Twist
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_testing.actions import ReadyToTest
from nav_msgs.msg import OccupancyGrid, Odometry
import pytest
import rclpy
from rclpy.parameter import Parameter
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_slam_mapping_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Start the ideal indoor SLAM graph without graphical clients."""
    package_share = get_package_share_directory('cargo_bot_navigation')
    mapping_launch = PythonLaunchDescriptionSource(
        f'{package_share}/launch/slam_mapping.launch.py',
    )
    return LaunchDescription([
        IncludeLaunchDescription(
            mapping_launch,
            launch_arguments={
                'headless': 'true',
                'use_rviz': 'false',
                'sensor_profile': 'ideal',
                'gz_partition': f'cargo_bot_slam_test_{os.getpid()}',
            }.items(),
        ),
        ReadyToTest(),
    ])


class TestSlamMappingGraph(unittest.TestCase):
    """Verify the public data and TF chain required for later navigation."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('slam_mapping_contract_test')
        cls.map = None
        cls.scan = None
        cls.odometry = None
        cls.ground_truth = None
        cls.subscriptions = [
            cls.node.create_subscription(
                OccupancyGrid, '/map', cls._map_callback, 10,
            ),
            cls.node.create_subscription(
                LaserScan, '/scan', cls._scan_callback, 10,
            ),
            cls.node.create_subscription(
                Odometry, '/odometry/filtered', cls._odometry_callback, 10,
            ),
            cls.node.create_subscription(
                Odometry,
                '/ground_truth/odometry',
                cls._ground_truth_callback,
                10,
            ),
        ]
        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)
        cls.cmd_vel_publisher = cls.node.create_publisher(Twist, '/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _map_callback(cls, message):
        cls.map = message

    @classmethod
    def _scan_callback(cls, message):
        cls.scan = message

    @classmethod
    def _odometry_callback(cls, message):
        cls.odometry = message

    @classmethod
    def _ground_truth_callback(cls, message):
        cls.ground_truth = message

    def test_slam_topics_and_tf_chain(self):
        """SLAM should produce a non-empty map connected to the lidar frame."""
        deadline = time.monotonic() + 35.0
        transform_ready = False
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            transform_ready = self.tf_buffer.can_transform(
                'map', 'lidar_link', rclpy.time.Time(),
            )
            if (
                self.map is not None
                and self.scan is not None
                and self.odometry is not None
                and self.ground_truth is not None
                and transform_ready
            ):
                break

        self.assertIsNotNone(self.scan)
        self.assertEqual(self.scan.header.frame_id, 'lidar_link')
        self.assertIsNotNone(self.odometry)
        self.assertEqual(self.odometry.header.frame_id, 'odom')
        self.assertIsNotNone(self.ground_truth)
        self.assertIsNotNone(self.map)
        self.assertEqual(self.map.header.frame_id, 'map')
        self.assertGreater(self.map.info.width, 0)
        self.assertGreater(self.map.info.height, 0)
        self.assertTrue(transform_ready)

        initial_odometry_yaw = self._yaw(self.odometry.pose.pose.orientation)
        initial_truth_yaw = self._yaw(
            self.ground_truth.pose.pose.orientation,
        )

        tf_history_deadline = time.monotonic() + 1.0
        while time.monotonic() < tf_history_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        command = Twist()
        command.linear.x = 3.0
        movement_deadline = time.monotonic() + 0.5
        moving_clouds = []
        moving_map_clouds = []
        last_scan_stamp = None
        while time.monotonic() < movement_deadline:
            self.cmd_vel_publisher.publish(command)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.scan is not None:
                scan_stamp = (
                    self.scan.header.stamp.sec,
                    self.scan.header.stamp.nanosec,
                )
                if scan_stamp != last_scan_stamp:
                    moving_clouds.append(
                        self._scan_points_in_frame(self.scan, 'odom'),
                    )
                    moving_map_clouds.append(
                        self._scan_points_in_frame(self.scan, 'map'),
                    )
                    last_scan_stamp = scan_stamp
        self.cmd_vel_publisher.publish(Twist())

        moving_errors = [
            self._median_nearest_distance(first, second)
            for first, second in zip(moving_clouds, moving_clouds[1:])
        ]
        moving_alignment_error = statistics.median(moving_errors)
        moving_map_errors = [
            self._median_nearest_distance(first, second)
            for first, second in zip(moving_map_clouds, moving_map_clouds[1:])
        ]
        moving_map_alignment_error = statistics.median(moving_map_errors)

        settle_deadline = time.monotonic() + 1.0
        while time.monotonic() < settle_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        before_scan = self.scan
        before_points = self._scan_points_in_frame(before_scan, 'map')
        before_odom_points = self._scan_points_in_frame(before_scan, 'odom')

        turn = Twist()
        turn.angular.z = 1.0
        turn_deadline = time.monotonic() + 2.5
        turning_map_clouds = []
        last_turn_scan_stamp = None
        while time.monotonic() < turn_deadline:
            self.cmd_vel_publisher.publish(turn)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.scan is not None:
                scan_stamp = (
                    self.scan.header.stamp.sec,
                    self.scan.header.stamp.nanosec,
                )
                if scan_stamp != last_turn_scan_stamp:
                    turning_map_clouds.append(
                        self._scan_points_in_frame(self.scan, 'map'),
                    )
                    last_turn_scan_stamp = scan_stamp
        self.cmd_vel_publisher.publish(Twist())

        turning_map_errors = [
            self._median_nearest_distance(first, second)
            for first, second in zip(
                turning_map_clouds, turning_map_clouds[1:],
            )
        ]
        turning_map_alignment_error = statistics.median(
            turning_map_errors,
        )

        saver_ready_deadline = time.monotonic() + 3.0
        while time.monotonic() < saver_ready_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        after_points = self._scan_points_in_frame(self.scan, 'map')
        after_odom_points = self._scan_points_in_frame(self.scan, 'odom')
        alignment_error = self._median_nearest_distance(
            before_points, after_points,
        )
        odom_alignment_error = self._median_nearest_distance(
            before_odom_points, after_odom_points,
        )

        odometry_yaw = self._yaw(self.odometry.pose.pose.orientation)
        truth_yaw = self._yaw(self.ground_truth.pose.pose.orientation)
        odometry_turn = self._angle_difference(
            odometry_yaw, initial_odometry_yaw,
        )
        truth_turn = self._angle_difference(truth_yaw, initial_truth_yaw)
        print(
            'SLAM_TURN_METRICS '
            f'odometry_turn={odometry_turn:.6f} '
            f'ground_truth_turn={truth_turn:.6f} '
            f'scan_alignment_error={alignment_error:.6f} '
            f'odom_scan_alignment_error={odom_alignment_error:.6f} '
            f'moving_scan_alignment_error={moving_alignment_error:.6f} '
            f'moving_map_alignment_error={moving_map_alignment_error:.6f} '
            f'turning_map_alignment_error={turning_map_alignment_error:.6f}',
        )
        self.assertGreater(odometry_turn, 0.15)
        self.assertAlmostEqual(odometry_turn, truth_turn, delta=0.15)
        self.assertLess(moving_alignment_error, 0.15)
        self.assertLess(moving_map_alignment_error, 0.15)
        self.assertLess(turning_map_alignment_error, 0.15)
        map_origin_yaw = self._yaw(self.map.info.origin.orientation)
        self.assertAlmostEqual(map_origin_yaw, 0.0, delta=1.0e-6)

        map_to_odom = self.tf_buffer.lookup_transform(
            'map', 'odom', rclpy.time.Time(),
        )
        correction_yaw = self._yaw(map_to_odom.transform.rotation)
        self.assertLess(abs(correction_yaw), 0.35)

        with tempfile.TemporaryDirectory(prefix='cargo_bot_slam_map_') as directory:
            base_path = Path(directory) / 'integration_map'
            self._save_and_check_map(base_path)

    def _save_and_check_map(self, base_path):
        """Save both map formats and verify the generated artifact set."""
        saver = SlamMapSaver()
        saver.set_parameters([
            Parameter('map_name', value=base_path.name),
            Parameter(
                'map_output_dir', value=str(base_path.parent),
            ),
        ])
        try:
            self.assertEqual(saver.save(), base_path)
        finally:
            saver.destroy_node()

        self.assertTrue(base_path.with_suffix('.yaml').is_file())
        self.assertTrue(base_path.with_suffix('.pgm').is_file())
        self.assertTrue(base_path.with_suffix('.posegraph').is_file())
        self.assertTrue(base_path.with_suffix('.data').is_file())

    @staticmethod
    def _yaw(quaternion):
        """Return planar yaw from a geometry message quaternion."""
        return math.atan2(
            2.0 * (
                quaternion.w * quaternion.z
                + quaternion.x * quaternion.y
            ),
            1.0 - 2.0 * (
                quaternion.y * quaternion.y
                + quaternion.z * quaternion.z
            ),
        )

    @staticmethod
    def _angle_difference(current, initial):
        """Return the shortest signed planar angle difference."""
        return math.atan2(
            math.sin(current - initial),
            math.cos(current - initial),
        )

    def _scan_points_in_frame(self, scan, target_frame):
        """Transform a subsample of scan endpoints into the requested frame."""
        stamp = rclpy.time.Time.from_msg(scan.header.stamp)
        deadline = time.monotonic() + 2.0
        while not self.tf_buffer.can_transform(
            target_frame, scan.header.frame_id, stamp,
        ) and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
        transform = self.tf_buffer.lookup_transform(
            target_frame, scan.header.frame_id, stamp,
        ).transform
        yaw = self._yaw(transform.rotation)
        cosine = math.cos(yaw)
        sine = math.sin(yaw)
        points = []
        for index in range(0, len(scan.ranges), 2):
            distance = scan.ranges[index]
            if not math.isfinite(distance):
                continue
            angle = scan.angle_min + index * scan.angle_increment
            local_x = distance * math.cos(angle)
            local_y = distance * math.sin(angle)
            points.append((
                transform.translation.x + cosine * local_x - sine * local_y,
                transform.translation.y + sine * local_x + cosine * local_y,
            ))
        return points

    @staticmethod
    def _median_nearest_distance(first, second):
        """Return symmetric median nearest-neighbour distance for two scans."""
        def distances(source, target):
            return [
                min(math.hypot(x - tx, y - ty) for tx, ty in target)
                for x, y in source
            ]

        return statistics.median(distances(first, second) + distances(second, first))
