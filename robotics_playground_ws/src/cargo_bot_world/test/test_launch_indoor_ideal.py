"""Deterministic ideal-profile sensor test in the indoor rooms world."""

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
from sensor_msgs.msg import Imu, LaserScan


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_indoor_ideal_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Launch the indoor world headlessly with ideal Gazebo sensors."""
    package_share = get_package_share_directory('cargo_bot_world')
    indoor_launch = PythonLaunchDescriptionSource(
        f'{package_share}/launch/indoor_rooms.launch.py',
    )
    return LaunchDescription([
        IncludeLaunchDescription(
            indoor_launch,
            launch_arguments={
                'headless': 'true',
                'sensor_profile': 'ideal',
                'gz_partition': f'cargo_bot_indoor_ideal_test_{os.getpid()}',
            }.items(),
        ),
        ReadyToTest(),
    ])


class TestIndoorIdealSensors(unittest.TestCase):
    """Verify the navigation sensor contract in the future SLAM world."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('indoor_ideal_sensor_test')
        cls.scan = None
        cls.imu = None
        cls.wheel = None
        cls.filtered = None
        cls.subscriptions = [
            cls.node.create_subscription(LaserScan, '/scan', cls._scan_callback, 10),
            cls.node.create_subscription(Imu, '/imu/data_raw', cls._imu_callback, 10),
            cls.node.create_subscription(
                Odometry, '/wheel/odometry', cls._wheel_callback, 10,
            ),
            cls.node.create_subscription(
                Odometry, '/odometry/filtered', cls._filtered_callback, 10,
            ),
        ]
        cls.cmd_vel_publisher = cls.node.create_publisher(Twist, '/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _scan_callback(cls, message):
        cls.scan = message

    @classmethod
    def _imu_callback(cls, message):
        cls.imu = message

    @classmethod
    def _wheel_callback(cls, message):
        cls.wheel = message

    @classmethod
    def _filtered_callback(cls, message):
        cls.filtered = message

    def test_ideal_navigation_contract_and_motion(self):
        """Indoor ideal sensors and fused odometry should all respond."""
        command = Twist()
        command.linear.x = 0.4
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            self.cmd_vel_publisher.publish(command)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if (
                self.scan is not None
                and self.imu is not None
                and self.wheel is not None
                and self.filtered is not None
                and self.filtered.pose.pose.position.x > 0.3
            ):
                break
        self.cmd_vel_publisher.publish(Twist())

        self.assertIsNotNone(self.scan)
        self.assertIsNotNone(self.imu)
        self.assertIsNotNone(self.wheel)
        self.assertIsNotNone(self.filtered)
        self.assertEqual(self.scan.header.frame_id, 'lidar_link')
        self.assertEqual(len(self.scan.ranges), 720)
        self.assertTrue(any(math.isfinite(value) for value in self.scan.ranges))
        self.assertEqual(self.imu.header.frame_id, 'imu_link')
        self.assertEqual(self.wheel.child_frame_id, 'base_footprint')
        self.assertEqual(self.filtered.header.frame_id, 'odom')
        self.assertGreater(self.filtered.pose.pose.position.x, 0.3)
