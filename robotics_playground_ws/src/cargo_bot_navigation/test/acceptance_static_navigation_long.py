"""Acceptance test for long navigation and an unreachable goal."""

import math
import os
from pathlib import Path
import tempfile
import time
import unittest

from action_msgs.msg import GoalStatus
from cargo_bot_navigation.map_collision import footprint_overlaps_occupied
from geometry_msgs.msg import PoseStamped, Twist
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
import pytest
import rclpy
from rclpy.action import ActionClient
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


AXLE_OFFSET = 0.16
START = (0.0, 0.0)
START_YAW = 1.5708
LONG_GOAL = (-17.05, 2.85)
UNREACHABLE_GOAL = (1000.0, 1000.0)


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    indoor_map = package.parents[1] / 'saved_maps' / 'indoor_map.yaml'
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_navigation_long_test_logs',
    )
    tested_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(package / 'launch' / 'static_navigation.launch.py'),
        ),
        launch_arguments={
            'map': str(indoor_map),
            'initial_pose_x': str(START[0]),
            'initial_pose_y': str(START[1]),
            'initial_pose_yaw': str(START_YAW),
            'headless': 'true',
            'use_rviz': 'false',
            'gz_partition': f'cargo_bot_navigation_long_test_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestLongNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('long_navigation_acceptance_test')
        cls.odometry = None
        cls.map = None
        cls.collision_detected = False
        cls.commands = []
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry, 20,
        )
        cls.node.create_subscription(Twist, '/cmd_vel', cls._command, 20)
        map_qos = QoSProfile(depth=1)
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        cls.node.create_subscription(
            OccupancyGrid, '/map', cls._map, map_qos,
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
    def _odometry(cls, message):
        cls.odometry = message
        if cls.map is None:
            return
        pose = message.pose.pose
        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        axle_x = pose.position.x + AXLE_OFFSET * math.cos(yaw)
        axle_y = pose.position.y + AXLE_OFFSET * math.sin(yaw)
        cls.collision_detected |= footprint_overlaps_occupied(
            cls.map, axle_x, axle_y, yaw,
        )

    @classmethod
    def _map(cls, message):
        cls.map = message

    @classmethod
    def _command(cls, message):
        cls.commands.append(message)

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

    def _send_goal(self, position):
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = position[0]
        goal.pose.pose.position.y = position[1]
        goal.pose.pose.orientation.w = 1.0
        future = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(future.done, 5.0))
        handle = future.result()
        self.assertTrue(handle.accepted)
        return handle.get_result_async()

    def test_long_route_then_unreachable_goal(self):
        ready = self._spin_until(
            lambda: (
                self.odometry is not None
                and self.map is not None
                and self.navigator.server_is_ready()
                and self.controller_state.service_is_ready()
                and self.navigator_state.service_is_ready()
            ),
            70.0,
        )
        self.assertTrue(ready)
        self.assertTrue(self._spin_until(
            lambda: (
                self._lifecycle_active(self.controller_state)
                and self._lifecycle_active(self.navigator_state)
            ),
            30.0,
        ))
        self._spin_until(lambda: False, 5.0)

        self.commands.clear()
        result = self._send_goal(LONG_GOAL)
        self.assertTrue(self._spin_until(result.done, 130.0))
        self.assertEqual(result.result().status, GoalStatus.STATUS_SUCCEEDED)
        axle_x, axle_y = self._axle_position()
        self.assertLessEqual(
            math.hypot(axle_x - LONG_GOAL[0], axle_y - LONG_GOAL[1]), 0.40,
        )
        self.assertGreaterEqual(math.hypot(
            axle_x - START[0], axle_y - START[1],
        ), 12.0)
        self.assertLessEqual(
            max(abs(command.linear.x) for command in self.commands), 2.01,
        )
        self.assertFalse(self.collision_detected)

        stopped = self._spin_until(
            lambda: (
                bool(self.commands)
                and abs(self.commands[-1].linear.x) <= 0.02
                and abs(self.commands[-1].angular.z) <= 0.02
            ),
            3.0,
        )
        self.assertTrue(stopped)
        self._spin_until(lambda: False, 0.5)
        start_x, start_y = self._axle_position()
        self.commands.clear()
        rejected = self._send_goal(UNREACHABLE_GOAL)
        maximum_displacement = 0.0
        deadline = time.monotonic() + 45.0
        while not rejected.done() and time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
            axle_x, axle_y = self._axle_position()
            maximum_displacement = max(
                maximum_displacement,
                math.hypot(axle_x - start_x, axle_y - start_y),
            )
        self.assertTrue(rejected.done())
        self.assertEqual(rejected.result().status, GoalStatus.STATUS_ABORTED)
        self.assertLessEqual(maximum_displacement, 0.05)
        self.assertFalse(any(
            abs(command.linear.x) > 0.02 or abs(command.angular.z) > 0.02
            for command in self.commands
        ))
