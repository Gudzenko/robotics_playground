"""Acceptance test for static-map trajectory execution."""

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
from std_srvs.srv import Trigger


START_X = -4.0
START_Y = 10.5
AXLE_OFFSET = 0.16
STRAIGHT_GOAL = (4.0, 10.5)


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    workspace = package.parents[1]
    indoor_map = workspace / 'saved_maps' / 'indoor_map.yaml'
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_static_navigation_test_logs',
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
            'gz_partition': f'cargo_bot_static_navigation_test_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestStaticNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('static_navigation_acceptance_test')
        cls.odometry = None
        cls.commands = []
        cls.command_samples = []
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry_callback, 20,
        )
        cls.node.create_subscription(
            Twist, '/cmd_vel', cls._command_callback, 20,
        )
        cls.navigator = ActionClient(cls.node, NavigateToPose, '/navigate_to_pose')
        cls.cancel_client = cls.node.create_client(Trigger, '/cancel_navigation')
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
    def _odometry_callback(cls, message):
        cls.odometry = message

    @classmethod
    def _command_callback(cls, message):
        cls.commands.append(message)
        cls.command_samples.append((time.monotonic(), message))

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

    def _wait_for_stack(self):
        ready = self._spin_until(
            lambda: (
                self.odometry is not None
                and self.navigator.server_is_ready()
                and self.cancel_client.service_is_ready()
                and self.controller_state.service_is_ready()
                and self.navigator_state.service_is_ready()
            ),
            70.0,
        )
        self.assertTrue(ready)
        active_deadline = time.monotonic() + 30.0
        while time.monotonic() < active_deadline:
            if (
                self._lifecycle_active(self.controller_state)
                and self._lifecycle_active(self.navigator_state)
            ):
                return
            time.sleep(0.2)
        self.fail('Controller and BT Navigator did not become active')

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

    def _navigate(self, goal_xy, timeout):
        self.commands.clear()
        self.command_samples.clear()
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = goal_xy[0]
        goal.pose.pose.position.y = goal_xy[1]
        goal.pose.pose.orientation.w = 1.0
        send = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(send.done, 5.0))
        handle = send.result()
        self.assertTrue(handle.accepted)
        result = handle.get_result_async()
        errors = []
        side_changes = 0
        previous_side = 0
        deadline = time.monotonic() + timeout
        while not result.done() and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
            if goal_xy == STRAIGHT_GOAL and self.odometry is not None:
                error = abs(self._axle_position()[1] - START_Y)
                errors.append(error)
                side = 1 if self._axle_position()[1] > START_Y else -1
                if previous_side and side != previous_side:
                    side_changes += 1
                previous_side = side
        self.assertTrue(result.done(), f'Navigation to {goal_xy} timed out')
        self.assertEqual(result.result().status, GoalStatus.STATUS_SUCCEEDED)
        self.assertTrue(self.commands)
        return errors, side_changes

    def _assert_acceleration_limits(self):
        linear_accelerations = []
        angular_accelerations = []
        for previous, current in zip(
            self.command_samples, self.command_samples[1:],
        ):
            elapsed = current[0] - previous[0]
            if 0.02 <= elapsed <= 0.20:
                linear_accelerations.append(
                    (current[1].linear.x - previous[1].linear.x) / elapsed,
                )
                angular_accelerations.append(
                    (current[1].angular.z - previous[1].angular.z) / elapsed,
                )
        self.assertTrue(linear_accelerations)
        self.assertLessEqual(max(linear_accelerations), 2.1)
        self.assertGreaterEqual(min(linear_accelerations), -2.8)
        self.assertLessEqual(max(angular_accelerations), 2.9)
        self.assertGreaterEqual(min(angular_accelerations), -3.4)

    def _assert_stopped(self):
        self.commands.clear()
        stopped = self._spin_until(
            lambda: (
                bool(self.commands)
                and abs(self.commands[-1].linear.x) <= 0.02
                and abs(self.commands[-1].angular.z) <= 0.02
            ),
            3.0,
        )
        self.assertTrue(stopped)
        final = self.commands[-1]
        self.assertAlmostEqual(final.linear.x, 0.0, delta=0.02)
        self.assertAlmostEqual(final.angular.z, 0.0, delta=0.02)

    def test_representative_routes_and_cancellation(self):
        self._wait_for_stack()

        straight_errors, crossings = self._navigate(STRAIGHT_GOAL, 30.0)
        self.assertLessEqual(max(straight_errors), 0.10)
        self.assertLessEqual(sum(straight_errors) / len(straight_errors), 0.05)
        self.assertLessEqual(crossings, 1)
        axle_x, axle_y = self._axle_position()
        self.assertLessEqual(
            math.hypot(axle_x - STRAIGHT_GOAL[0], axle_y - STRAIGHT_GOAL[1]),
            0.40,
        )
        self.assertLessEqual(
            max(abs(command.linear.x) for command in self.commands), 2.01,
        )
        self.assertLessEqual(
            max(abs(command.angular.z) for command in self.commands), 1.01,
        )
        self._assert_acceleration_limits()
        self._assert_stopped()

        start_x, start_y = self._axle_position()
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = START_X
        goal.pose.pose.position.y = START_Y
        goal.pose.pose.orientation.w = 1.0
        send = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(send.done, 5.0))
        handle = send.result()
        self.assertTrue(handle.accepted)
        result = handle.get_result_async()
        moved = self._spin_until(
            lambda: math.hypot(
                self._axle_position()[0] - start_x,
                self._axle_position()[1] - start_y,
            ) > 0.40,
            15.0,
        )
        self.assertTrue(moved)
        cancel = self.cancel_client.call_async(Trigger.Request())
        self.assertTrue(self._spin_until(cancel.done, 8.0))
        self.assertTrue(cancel.result().success)
        self.assertTrue(self._spin_until(result.done, 8.0))
        self.assertEqual(result.result().status, GoalStatus.STATUS_CANCELED)
        self._assert_stopped()
