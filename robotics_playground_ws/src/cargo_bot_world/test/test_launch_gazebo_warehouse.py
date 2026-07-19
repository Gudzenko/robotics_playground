"""Headless smoke test for the Gazebo warehouse simulation."""

import math
import os
from pathlib import Path
import tempfile
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_testing.actions import ReadyToTest
from nav_msgs.msg import Odometry
import pytest
import rclpy
from rclpy.qos import qos_profile_sensor_data, ReliabilityPolicy
from sensor_msgs.msg import Imu, JointState, LaserScan
from tf2_msgs.msg import TFMessage


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_gazebo_launch_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Launch the warehouse simulation without the Gazebo GUI."""
    package_share = get_package_share_directory('cargo_bot_world')
    warehouse_launch = PythonLaunchDescriptionSource(
        f'{package_share}/launch/gazebo_warehouse.launch.py',
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            warehouse_launch,
            launch_arguments={
                'headless': 'true',
                'gz_partition': f'cargo_bot_warehouse_ideal_test_{os.getpid()}',
            }.items(),
        ),
        ReadyToTest(),
    ])


class TestGazeboWarehouseLaunch(unittest.TestCase):
    """Check that Gazebo, robot spawning and topic bridging work together."""

    @classmethod
    def setUpClass(cls):
        """Create an inspection node and subscribe to the stable scan topic."""
        rclpy.init()
        cls.node = rclpy.create_node('gazebo_warehouse_launch_test')
        cls.scan = None
        cls.imu = None
        cls.wheel_joint_state = None
        cls.manipulator_joint_state = None
        cls.wheel_odometry = None
        cls.ground_truth_odometry = None
        cls.filtered_odometry = None
        cls.filtered_positions = []
        cls.odom_base_transform_received = False
        cls.scan_subscription = cls.node.create_subscription(
            LaserScan,
            '/scan',
            cls._scan_callback,
            qos_profile_sensor_data,
        )
        cls.joint_state_subscription = cls.node.create_subscription(
            JointState,
            '/joint_states',
            cls._joint_state_callback,
            qos_profile_sensor_data,
        )
        cls.imu_subscription = cls.node.create_subscription(
            Imu,
            '/imu/data_raw',
            cls._imu_callback,
            qos_profile_sensor_data,
        )
        cls.wheel_odometry_subscription = cls.node.create_subscription(
            Odometry,
            '/wheel/odometry',
            cls._wheel_odometry_callback,
            10,
        )
        cls.ground_truth_subscription = cls.node.create_subscription(
            Odometry,
            '/ground_truth/odometry',
            cls._ground_truth_callback,
            10,
        )
        cls.filtered_odometry_subscription = cls.node.create_subscription(
            Odometry,
            '/odometry/filtered',
            cls._filtered_odometry_callback,
            10,
        )
        cls.tf_subscription = cls.node.create_subscription(
            TFMessage,
            '/tf',
            cls._tf_callback,
            100,
        )
        cls.cmd_vel_publisher = cls.node.create_publisher(Twist, '/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        """Destroy the inspection node and stop its ROS context."""
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _scan_callback(cls, message):
        cls.scan = message

    @classmethod
    def _joint_state_callback(cls, message):
        wheel_joints = {'left_wheel_joint', 'right_wheel_joint'}
        if wheel_joints.issubset(message.name):
            cls.wheel_joint_state = message
        manipulator_joints = {
            'manipulator_mount_joint',
            'manipulator_lift_joint',
            'manipulator_arm_joint',
            'manipulator_left_finger_joint',
            'manipulator_right_finger_joint',
        }
        if manipulator_joints.issubset(message.name):
            cls.manipulator_joint_state = message

    @classmethod
    def _imu_callback(cls, message):
        cls.imu = message

    @classmethod
    def _wheel_odometry_callback(cls, message):
        cls.wheel_odometry = message

    @classmethod
    def _ground_truth_callback(cls, message):
        cls.ground_truth_odometry = message

    @classmethod
    def _filtered_odometry_callback(cls, message):
        cls.filtered_odometry = message
        cls.filtered_positions.append((
            message.pose.pose.position.x,
            message.pose.pose.position.y,
        ))

    @classmethod
    def _tf_callback(cls, message):
        cls.odom_base_transform_received = any(
            transform.header.frame_id == 'odom'
            and transform.child_frame_id == 'base_footprint'
            for transform in message.transforms
        ) or cls.odom_base_transform_received

    def test_ideal_imu_reports_rest_acceleration_and_positive_yaw_rate(self):
        """IMU should respond to forward acceleration and a left turn."""
        deadline = time.monotonic() + 20.0
        while self.imu is None and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertIsNotNone(self.imu, 'No Imu received on /imu/data_raw')
        self.assertEqual(self.imu.header.frame_id, 'imu_link')
        quaternion_norm = math.sqrt(
            self.imu.orientation.x ** 2
            + self.imu.orientation.y ** 2
            + self.imu.orientation.z ** 2
            + self.imu.orientation.w ** 2
        )
        self.assertAlmostEqual(quaternion_norm, 1.0, places=5)
        acceleration_norm = 0.0
        deadline = time.monotonic() + 5.0
        while abs(acceleration_norm - 9.8) > 0.2 and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            acceleration_norm = math.sqrt(
                self.imu.linear_acceleration.x ** 2
                + self.imu.linear_acceleration.y ** 2
                + self.imu.linear_acceleration.z ** 2
            )
        self.assertAlmostEqual(acceleration_norm, 9.8, delta=0.2)
        self.assertLess(abs(self.imu.angular_velocity.z), 0.1)
        self.assertEqual(
            list(self.imu.orientation_covariance),
            [0.000001, 0.0, 0.0, 0.0, 0.000001, 0.0, 0.0, 0.0, 0.000001],
        )

        drive_command = Twist()
        drive_command.linear.x = 1.0
        drive_command.angular.z = 0.5
        maximum_forward_acceleration = 0.0
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            self.cmd_vel_publisher.publish(drive_command)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            maximum_forward_acceleration = max(
                maximum_forward_acceleration,
                abs(self.imu.linear_acceleration.x),
            )
            if (
                maximum_forward_acceleration > 0.01
                and self.imu.angular_velocity.z > 0.1
            ):
                break

        stop_command = Twist()
        self.cmd_vel_publisher.publish(stop_command)
        self.assertGreater(maximum_forward_acceleration, 0.01)
        self.assertGreater(self.imu.angular_velocity.z, 0.1)

    def test_robot_spawn_and_bridges_start(self, proc_info, proc_output):
        """Gazebo should accept the robot and configure its core bridges."""
        proc_output.assertWaitFor(
            'Entity creation successful.',
            timeout=30.0,
        )
        proc_output.assertWaitFor(
            'Creating GZ->ROS Bridge: [/clock',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Creating GZ->ROS Bridge: [/odom',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Creating GZ->ROS Bridge: [/sim/scan',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Lidar relay started [ideal/gazebo]: /sim/scan -> /scan',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Creating GZ->ROS Bridge: [/sim/imu',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'IMU relay started [ideal/gazebo]: /sim/imu -> /imu/data_raw',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Wheel odometry started [ideal/gazebo]: '
            '/sim/joint_states -> /wheel/odometry',
            timeout=10.0,
        )
        proc_output.assertWaitFor(
            'Manipulator control node started',
            timeout=10.0,
        )
        nodes = set(self.node.get_node_names())
        self.assertIn('ekf_filter_node', nodes)
        proc_info.assertWaitForShutdown(
            process='create',
            timeout=10.0,
        )

    def test_stable_scan_has_expected_shape_and_ranges(self):
        """The ideal lidar should publish configured scans containing obstacles."""
        deadline = time.monotonic() + 20.0
        while self.scan is None and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertIsNotNone(self.scan, 'No LaserScan received on /scan')
        self.assertEqual(self.scan.header.frame_id, 'lidar_link')
        self.assertEqual(len(self.scan.ranges), 720)
        self.assertAlmostEqual(self.scan.range_min, 0.15)
        self.assertAlmostEqual(self.scan.range_max, 20.0)
        finite_ranges = [value for value in self.scan.ranges if math.isfinite(value)]
        self.assertTrue(finite_ranges, 'Scan contains no finite obstacle ranges')
        self.assertTrue(all(self.scan.range_min <= value <= self.scan.range_max
                            for value in finite_ranges))
        publishers = self.node.get_publishers_info_by_topic('/scan')
        self.assertTrue(publishers)
        self.assertEqual(
            publishers[0].qos_profile.reliability,
            ReliabilityPolicy.RELIABLE,
        )

    def test_wheel_joint_states_are_available_for_robot_tf(self):
        """Wheel and manipulator states should share the robot TF input."""
        deadline = time.monotonic() + 10.0
        while (
            (
                self.wheel_joint_state is None
                or self.manipulator_joint_state is None
            )
            and time.monotonic() < deadline
        ):
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertIsNotNone(
            self.wheel_joint_state,
            'No complete drive-wheel JointState received',
        )
        self.assertIsNotNone(
            self.manipulator_joint_state,
            'No complete manipulator JointState received',
        )

    def test_encoder_odometry_and_ground_truth_are_separate(self):
        """Wheel odometry should be derived from joints beside simulator truth."""
        drive_command = Twist()
        drive_command.linear.x = 0.5
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            self.cmd_vel_publisher.publish(drive_command)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if (
                self.wheel_odometry is not None
                and self.ground_truth_odometry is not None
                and self.filtered_odometry is not None
                and self.wheel_odometry.pose.pose.position.x > 0.05
            ):
                break

        self.cmd_vel_publisher.publish(Twist())
        self.assertIsNotNone(self.wheel_odometry)
        self.assertIsNotNone(self.ground_truth_odometry)
        self.assertIsNotNone(self.filtered_odometry)
        self.assertEqual(self.wheel_odometry.header.frame_id, 'odom')
        self.assertEqual(self.wheel_odometry.child_frame_id, 'base_footprint')
        self.assertGreater(self.wheel_odometry.pose.pose.position.x, 0.05)
        self.assertEqual(self.filtered_odometry.header.frame_id, 'odom')
        self.assertEqual(self.filtered_odometry.child_frame_id, 'base_footprint')

        truth_position = self.ground_truth_odometry.pose.pose.position
        wheel_position = self.wheel_odometry.pose.pose.position
        filtered_position = self.filtered_odometry.pose.pose.position
        wheel_error = math.hypot(
            wheel_position.x - truth_position.x,
            wheel_position.y - truth_position.y,
        )
        filtered_error = math.hypot(
            filtered_position.x - truth_position.x,
            filtered_position.y - truth_position.y,
        )
        print(
            'IDEAL_LOCALIZATION_METRICS '
            f'wheel_position_error={wheel_error:.6f} '
            f'filtered_position_error={filtered_error:.6f}',
        )
        self.assertLess(wheel_error, 0.25)
        self.assertLess(filtered_error, 0.25)
        self.assertTrue(all(
            math.isfinite(value)
            for position in self.filtered_positions
            for value in position
        ))

        wheel_publishers = self.node.get_publishers_info_by_topic('/wheel/odometry')
        truth_publishers = self.node.get_publishers_info_by_topic('/ground_truth/odometry')
        self.assertEqual({info.node_name for info in wheel_publishers}, {'wheel_odometry'})
        self.assertIn('ros_gz_bridge', {info.node_name for info in truth_publishers})

    def test_ekf_is_the_only_odom_to_base_tf_owner(self):
        """Gazebo bridge must not compete with the EKF for local odometry TF."""
        deadline = time.monotonic() + 10.0
        while not self.odom_base_transform_received and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertTrue(self.odom_base_transform_received)
        tf_publishers = self.node.get_publishers_info_by_topic('/tf')
        publisher_names = {info.node_name for info in tf_publishers}
        self.assertIn('ekf_filter_node', publisher_names)
        self.assertNotIn('ros_gz_bridge', publisher_names)
