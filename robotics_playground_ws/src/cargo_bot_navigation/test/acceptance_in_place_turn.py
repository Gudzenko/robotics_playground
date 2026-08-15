"""Acceptance test for a differential-drive turn before forward travel."""

import math
import os
from pathlib import Path
import tempfile
import time
import unittest

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
import pytest
import rclpy
from rclpy.action import ActionClient


START_X = -4.0
START_Y = 10.5
GOAL_X = -7.0
AXLE_OFFSET = 0.16


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    indoor_map = package.parents[1] / 'saved_maps' / 'indoor_map.yaml'
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_in_place_turn_test_logs',
    )
    tested_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(package / 'launch' / 'static_navigation.launch.py'),
        ),
        launch_arguments={
            'map': str(indoor_map),
            'initial_pose_x': str(START_X),
            'initial_pose_y': str(START_Y),
            'initial_pose_yaw': '0.0',
            'headless': 'true',
            'use_rviz': 'false',
            'gz_partition': f'cargo_bot_in_place_turn_test_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestInPlaceTurn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('in_place_turn_acceptance_test')
        cls.odometry = None
        cls.commands = []
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry, 20,
        )
        cls.node.create_subscription(Twist, '/cmd_vel', cls.commands.append, 20)
        cls.navigator = ActionClient(cls.node, NavigateToPose, '/navigate_to_pose')

    @classmethod
    def tearDownClass(cls):
        cls.navigator.destroy()
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _odometry(cls, message):
        cls.odometry = message

    def _spin_until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
            if predicate():
                return True
        return False

    def _axle_pose(self):
        pose = self.odometry.pose.pose
        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        return (
            pose.position.x + AXLE_OFFSET * math.cos(yaw),
            pose.position.y + AXLE_OFFSET * math.sin(yaw),
            yaw,
        )

    @staticmethod
    def _angle_difference(first, second):
        return math.atan2(math.sin(first - second), math.cos(first - second))

    def test_robot_turns_around_before_driving_to_goal_behind_it(self):
        ready = self._spin_until(
            lambda: self.odometry is not None and self.navigator.server_is_ready(),
            80.0,
        )
        self.assertTrue(ready)
        self._spin_until(lambda: False, 3.0)
        start_x, start_y, start_yaw = self._axle_pose()

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = GOAL_X
        goal.pose.pose.position.y = START_Y
        goal.pose.pose.orientation.w = 1.0
        sent = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(sent.done, 5.0))
        handle = sent.result()
        self.assertTrue(handle.accepted)
        result = handle.get_result_async()

        turned_in_place = False
        deadline = time.monotonic() + 45.0
        while not result.done() and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
            axle_x, axle_y, yaw = self._axle_pose()
            displacement = math.hypot(axle_x - start_x, axle_y - start_y)
            turn = abs(self._angle_difference(yaw, start_yaw))
            if turn >= 2.6 and displacement <= 0.10:
                turned_in_place = True

        self.assertTrue(result.done())
        self.assertEqual(result.result().status, GoalStatus.STATUS_SUCCEEDED)
        self.assertTrue(turned_in_place)
        self.assertTrue(any(abs(item.angular.z) >= 0.5 for item in self.commands))
        final_x, final_y, _ = self._axle_pose()
        self.assertLessEqual(math.hypot(final_x - GOAL_X, final_y - START_Y), 0.40)
