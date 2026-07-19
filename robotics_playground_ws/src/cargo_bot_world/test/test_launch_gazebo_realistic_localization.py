"""Seeded realistic-profile integration test for local odometry fusion."""

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


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_realistic_ekf_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Launch seeded realistic sensors in the headless warehouse."""
    package_share = get_package_share_directory('cargo_bot_world')
    warehouse_launch = PythonLaunchDescriptionSource(
        f'{package_share}/launch/gazebo_warehouse.launch.py',
    )
    return LaunchDescription([
        IncludeLaunchDescription(
            warehouse_launch,
            launch_arguments={
                'headless': 'true',
                'sensor_profile': 'realistic',
                'gz_partition': (
                    f'cargo_bot_warehouse_realistic_test_{os.getpid()}'
                ),
            }.items(),
        ),
        ReadyToTest(),
    ])


class TestRealisticLocalization(unittest.TestCase):
    """Compare seeded noisy wheel and filtered estimates with simulator truth."""

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('realistic_localization_test')
        cls.wheel = None
        cls.filtered = None
        cls.truth = None
        cls.filtered_positions = []
        cls.subscriptions = [
            cls.node.create_subscription(
                Odometry, '/wheel/odometry', cls._wheel_callback, 10,
            ),
            cls.node.create_subscription(
                Odometry, '/odometry/filtered', cls._filtered_callback, 10,
            ),
            cls.node.create_subscription(
                Odometry, '/ground_truth/odometry', cls._truth_callback, 10,
            ),
        ]
        cls.cmd_vel_publisher = cls.node.create_publisher(Twist, '/cmd_vel', 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _wheel_callback(cls, message):
        cls.wheel = message

    @classmethod
    def _filtered_callback(cls, message):
        cls.filtered = message
        cls.filtered_positions.append((
            message.pose.pose.position.x,
            message.pose.pose.position.y,
        ))

    @classmethod
    def _truth_callback(cls, message):
        cls.truth = message

    def test_seeded_realistic_filter_is_continuous_and_bounded(self):
        """Noisy EKF output should remain continuous and near simulator truth."""
        command = Twist()
        command.linear.x = 0.6
        command.angular.z = 0.25
        deadline = time.monotonic() + 12.0
        while time.monotonic() < deadline:
            self.cmd_vel_publisher.publish(command)
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if (
                self.wheel is not None
                and self.filtered is not None
                and self.truth is not None
                and self.truth.pose.pose.position.x > 0.8
            ):
                break
        self.cmd_vel_publisher.publish(Twist())

        self.assertIsNotNone(self.wheel)
        self.assertIsNotNone(self.filtered)
        self.assertIsNotNone(self.truth)
        wheel_error = self._position_error(self.wheel, self.truth)
        filtered_error = self._position_error(self.filtered, self.truth)
        print(
            'REALISTIC_LOCALIZATION_METRICS '
            f'wheel_position_error={wheel_error:.6f} '
            f'filtered_position_error={filtered_error:.6f}',
        )
        self.assertLess(wheel_error, 0.5)
        self.assertLess(filtered_error, 0.5)
        self.assertGreater(len(self.filtered_positions), 5)
        jumps = [
            math.hypot(current[0] - previous[0], current[1] - previous[1])
            for previous, current in zip(
                self.filtered_positions,
                self.filtered_positions[1:],
            )
        ]
        self.assertTrue(all(math.isfinite(jump) for jump in jumps))
        self.assertLess(max(jumps), 0.25)

    @staticmethod
    def _position_error(estimate, truth):
        return math.hypot(
            estimate.pose.pose.position.x - truth.pose.pose.position.x,
            estimate.pose.pose.position.y - truth.pose.pose.position.y,
        )
