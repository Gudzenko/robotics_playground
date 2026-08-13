"""Acceptance test for a corridor-to-room navigation turn."""

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
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
import pytest
import rclpy
from rclpy.action import ActionClient


AXLE_OFFSET = 0.16


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    indoor_map = package.parents[1] / 'saved_maps' / 'indoor_map.yaml'
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_navigation_turn_test_logs',
    )
    tested_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(package / 'launch' / 'static_navigation.launch.py'),
        ),
        launch_arguments={
            'map': str(indoor_map),
            'initial_pose_x': '-4.0',
            'initial_pose_y': '10.5',
            'initial_pose_yaw': '0.0',
            'headless': 'true',
            'use_rviz': 'false',
            'gz_partition': f'cargo_bot_navigation_turn_test_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestNavigationTurn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('navigation_turn_acceptance_test')
        cls.commands = []
        cls.odometry = None
        cls.node.create_subscription(Twist, '/cmd_vel', cls._command, 20)
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry, 20,
        )
        cls.navigator = ActionClient(cls.node, NavigateToPose, '/navigate_to_pose')
        cls.controller_state = cls.node.create_client(
            GetState, '/controller_server/get_state',
        )
        cls.navigator_state = cls.node.create_client(
            GetState, '/bt_navigator/get_state',
        )

    @classmethod
    def tearDownClass(cls):
        cls.navigator.destroy()
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _command(cls, message):
        cls.commands.append(message)

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

    def _lifecycle_active(self, client):
        future = client.call_async(GetState.Request())
        if not self._spin_until(future.done, 3.0):
            return False
        return future.result().current_state.id == 3

    def _axle_position(self):
        pose = self.odometry.pose.pose
        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        return (
            pose.position.x + AXLE_OFFSET * math.cos(yaw),
            pose.position.y + AXLE_OFFSET * math.sin(yaw),
        )

    def test_corridor_exit_turn_reaches_room_and_stops(self):
        ready = self._spin_until(
            lambda: (
                self.navigator.server_is_ready()
                and self.odometry is not None
                and self.controller_state.service_is_ready()
                and self.navigator_state.service_is_ready()
            ),
            70.0,
        )
        self.assertTrue(ready)
        self.assertTrue(
            self._spin_until(
                lambda: (
                    self._lifecycle_active(self.controller_state)
                    and self._lifecycle_active(self.navigator_state)
                ),
                30.0,
            ),
        )
        self._spin_until(lambda: False, 5.0)

        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = 4.0
        goal.pose.pose.position.y = 3.0
        goal.pose.pose.orientation.w = 1.0
        send = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(send.done, 5.0))
        handle = send.result()
        self.assertTrue(handle.accepted)
        result = handle.get_result_async()
        self.assertTrue(self._spin_until(result.done, 50.0))
        self.assertEqual(result.result().status, GoalStatus.STATUS_SUCCEEDED)
        self.assertTrue(self.commands)
        axle_x, axle_y = self._axle_position()
        self.assertLessEqual(math.hypot(axle_x - 4.0, axle_y - 3.0), 0.40)
        self.assertLessEqual(
            max(abs(command.linear.x) for command in self.commands), 2.01,
        )
        self.assertLessEqual(
            max(abs(command.angular.z) for command in self.commands), 1.01,
        )

        stopped = self._spin_until(
            lambda: (
                abs(self.commands[-1].linear.x) <= 0.02
                and abs(self.commands[-1].angular.z) <= 0.02
            ),
            3.0,
        )
        self.assertTrue(stopped)
