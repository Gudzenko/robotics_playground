"""Headless integration test for localization and planning without motion."""

import os
from pathlib import Path
import tempfile
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_testing.actions import ReadyToTest
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import OccupancyGrid, Path as NavigationPath
import pytest
import rclpy
from rclpy.action import ActionClient
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from tf2_ros import Buffer, TransformListener


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_path_planning_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Start path planning with a test-only map and no graphical clients."""
    package_share = get_package_share_directory('cargo_bot_navigation')
    launch_source = PythonLaunchDescriptionSource(
        f'{package_share}/launch/path_planning.launch.py',
    )
    fixture = Path(__file__).parent / 'fixtures' / 'planning_test.yaml'
    return LaunchDescription([
        IncludeLaunchDescription(
            launch_source,
            launch_arguments={
                'map': str(fixture),
                'headless': 'true',
                'use_rviz': 'false',
                'sensor_profile': 'ideal',
                'gz_partition': f'cargo_bot_planning_test_{os.getpid()}',
            }.items(),
        ),
        ReadyToTest(),
    ])


class TestPathPlanningGraph(unittest.TestCase):
    """Verify localization, planning and the absence of motion output."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('path_planning_contract_test')
        cls.map = None
        cls.costmap = None
        cls.path = None
        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        costmap_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        cls.subscriptions = [
            cls.node.create_subscription(
                OccupancyGrid, '/map', cls._map_callback, map_qos,
            ),
            cls.node.create_subscription(
                OccupancyGrid,
                '/global_costmap/costmap',
                cls._costmap_callback,
                costmap_qos,
            ),
            cls.node.create_subscription(
                NavigationPath,
                '/planned_path',
                cls._path_callback,
                map_qos,
            ),
        ]
        cls.goal_publisher = cls.node.create_publisher(
            PoseStamped, '/goal_pose', 10,
        )
        cls.planner_client = ActionClient(
            cls.node, ComputePathToPose, '/compute_path_to_pose',
        )
        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _map_callback(cls, message):
        cls.map = message

    @classmethod
    def _costmap_callback(cls, message):
        cls.costmap = message

    @classmethod
    def _path_callback(cls, message):
        cls.path = message

    def test_click_goal_calculates_path_without_cmd_vel(self):
        """A map goal should create a visible path but never command motion."""
        ready_deadline = time.monotonic() + 60.0
        transform_ready = False
        planner_ready = False
        while time.monotonic() < ready_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            planner_ready = self.planner_client.server_is_ready()
            transform_ready = self.tf_buffer.can_transform(
                'map', 'base_footprint', rclpy.time.Time(),
            )
            if (
                self.map is not None
                and self.costmap is not None
                and planner_ready
                and transform_ready
            ):
                break

        self.assertIsNotNone(self.map)
        self.assertEqual(self.map.header.frame_id, 'map')
        self.assertIsNotNone(self.costmap)
        self.assertTrue(planner_ready)
        self.assertTrue(transform_ready)

        goal = PoseStamped()
        goal.header.frame_id = 'map'
        goal.pose.position.x = 0.0
        goal.pose.position.y = 3.0
        goal.pose.orientation.z = 0.70710678
        goal.pose.orientation.w = 0.70710678
        goal.header.stamp = self.node.get_clock().now().to_msg()
        self.goal_publisher.publish(goal)
        path_deadline = time.monotonic() + 20.0
        while time.monotonic() < path_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.2)
            if self.path is not None and self.path.poses:
                break

        self.assertIsNotNone(self.path)
        self.assertGreater(len(self.path.poses), 1)
        self.assertEqual(self.path.header.frame_id, 'map')
        endpoint = self.path.poses[-1].pose.position
        self.assertAlmostEqual(endpoint.x, goal.pose.position.x, delta=0.5)
        self.assertAlmostEqual(endpoint.y, goal.pose.position.y, delta=0.5)
        endpoint_orientation = self.path.poses[-1].pose.orientation
        self.assertAlmostEqual(endpoint_orientation.z, goal.pose.orientation.z, delta=0.05)
        self.assertAlmostEqual(endpoint_orientation.w, goal.pose.orientation.w, delta=0.05)
        for pose in self.path.poses:
            position = pose.pose.position
            column = int(
                (position.x - self.map.info.origin.position.x)
                / self.map.info.resolution
            )
            row = int(
                (position.y - self.map.info.origin.position.y)
                / self.map.info.resolution
            )
            self.assertGreaterEqual(column, 0)
            self.assertLess(column, self.map.info.width)
            self.assertGreaterEqual(row, 0)
            self.assertLess(row, self.map.info.height)
            occupancy = self.map.data[row * self.map.info.width + column]
            self.assertGreaterEqual(occupancy, 0)
            self.assertLess(occupancy, 65)

        invalid_goal = PoseStamped()
        invalid_goal.header.frame_id = 'map'
        invalid_goal.header.stamp = self.node.get_clock().now().to_msg()
        invalid_goal.pose.position.x = 50.0
        invalid_goal.pose.position.y = 50.0
        invalid_goal.pose.orientation.w = 1.0
        self.goal_publisher.publish(invalid_goal)
        clear_deadline = time.monotonic() + 5.0
        while time.monotonic() < clear_deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.path is not None and not self.path.poses:
                break
        self.assertEqual(self.path.poses, [])
        self.assertEqual(self.node.get_publishers_info_by_topic('/cmd_vel'), [])
