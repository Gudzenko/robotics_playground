"""Acceptance test for detecting and avoiding a spawned obstacle."""

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
from nav_msgs.msg import OccupancyGrid, Odometry
import pytest
import rclpy
from rclpy.action import ActionClient
from rclpy.parameter import Parameter
from rclpy.parameter_client import AsyncParameterClient
from std_srvs.srv import Trigger


START_X = -4.0
CORRIDOR_Y = 10.5
GOAL_X = 4.0
OBSTACLE_X = 0.0
OBSTACLE_Y = 10.0
OBSTACLE_SIZE = 0.5
AXLE_OFFSET = 0.16


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    workspace = package.parents[1]
    indoor_map = workspace / 'saved_maps' / 'indoor_map.yaml'
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_obstacle_navigation_logs',
    )
    tested_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(package / 'launch' / 'obstacle_navigation.launch.py'),
        ),
        launch_arguments={
            'map': str(indoor_map),
            'initial_pose_x': str(START_X),
            'initial_pose_y': str(CORRIDOR_Y),
            'initial_pose_yaw': '0.0',
            'headless': 'true',
            'use_rviz': 'false',
            'obstacle_name': f'navigation_obstacle_{os.getpid()}',
            'obstacle_x': str(OBSTACLE_X),
            'obstacle_y': str(OBSTACLE_Y),
            'obstacle_size_x': str(OBSTACLE_SIZE),
            'obstacle_size_y': str(OBSTACLE_SIZE),
            'gz_partition': f'cargo_bot_obstacle_test_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestObstacleNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('obstacle_navigation_acceptance_test')
        cls.odometry = None
        cls.costmap = None
        cls.memory_map = None
        cls.commands = []
        cls.positions = []
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry_callback, 20,
        )
        cls.node.create_subscription(
            OccupancyGrid, '/global_costmap/costmap', cls._costmap_callback, 10,
        )
        cls.node.create_subscription(
            OccupancyGrid, '/persistent_obstacle_map',
            cls._memory_map_callback, 10,
        )
        cls.node.create_subscription(
            Twist, '/cmd_vel', cls._command_callback, 20,
        )
        cls.navigator = ActionClient(cls.node, NavigateToPose, '/navigate_to_pose')
        cls.spawn = cls.node.create_client(Trigger, '/spawn_navigation_obstacle')
        cls.remove = cls.node.create_client(Trigger, '/remove_navigation_obstacle')
        cls.monitor_state = cls.node.create_client(
            GetState, '/collision_monitor/get_state',
        )
        cls.obstacle_parameters = AsyncParameterClient(
            cls.node, '/obstacle_manager',
        )

    @classmethod
    def tearDownClass(cls):
        cls.navigator.destroy()
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _odometry_callback(cls, message):
        cls.odometry = message
        pose = message.pose.pose
        q = pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        cls.positions.append((
            pose.position.x + AXLE_OFFSET * math.cos(yaw),
            pose.position.y + AXLE_OFFSET * math.sin(yaw),
        ))

    @classmethod
    def _costmap_callback(cls, message):
        cls.costmap = message

    @classmethod
    def _memory_map_callback(cls, message):
        cls.memory_map = message

    @classmethod
    def _command_callback(cls, message):
        cls.commands.append(message)

    def _spin_until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.05)
            if predicate():
                return True
        return False

    def _wait_for_active(self, client, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = client.call_async(GetState.Request())
            if self._spin_until(state.done, 3.0):
                if state.result().current_state.id == 3:
                    return True
            self._spin_until(lambda: False, 0.5)
        return False

    def _maximum_grid_value_near(
        self, grid, world_x, world_y, radius_metres,
    ):
        if grid is None:
            return -1
        info = grid.info
        center_column = int(
            (world_x - info.origin.position.x) / info.resolution,
        )
        center_row = int(
            (world_y - info.origin.position.y) / info.resolution,
        )
        radius = math.ceil(radius_metres / info.resolution)
        costs = []
        for row in range(center_row - radius, center_row + radius + 1):
            for column in range(
                center_column - radius, center_column + radius + 1,
            ):
                if 0 <= column < info.width and 0 <= row < info.height:
                    costs.append(grid.data[row * info.width + column])
        return max(costs, default=-1)

    def _maximum_cost_near(self, world_x, world_y, radius_metres):
        return self._maximum_grid_value_near(
            self.costmap, world_x, world_y, radius_metres,
        )

    def _maximum_cost_near_obstacle(self):
        return self._maximum_cost_near(
            OBSTACLE_X, OBSTACLE_Y, OBSTACLE_SIZE / 2.0 + 0.15,
        )

    def _memory_diagnostic(self):
        if self.memory_map is None:
            return 'persistent map was never received'
        info = self.memory_map.info
        occupied = []
        for index, value in enumerate(self.memory_map.data):
            if value < 100:
                continue
            column = index % info.width
            row = index // info.width
            world_x = info.origin.position.x + column * info.resolution
            world_y = info.origin.position.y + row * info.resolution
            occupied.append((world_x, world_y))
        if not occupied:
            return 'persistent map contains no occupied cells'
        nearest = min(
            occupied,
            key=lambda point: math.hypot(
                point[0] - OBSTACLE_X, point[1] - OBSTACLE_Y,
            ),
        )
        distance = math.hypot(
            nearest[0] - OBSTACLE_X, nearest[1] - OBSTACLE_Y,
        )
        return (
            f'{len(occupied)} occupied cells; nearest to obstacle is '
            f'({nearest[0]:.2f}, {nearest[1]:.2f}), {distance:.2f} m away'
        )

    def test_spawn_replan_avoid_remove(self):
        ready = self._spin_until(
            lambda: (
                self.odometry is not None
                and self.costmap is not None
                and self.navigator.server_is_ready()
                and self.spawn.service_is_ready()
                and self.remove.service_is_ready()
                and self.monitor_state.service_is_ready()
            ),
            80.0,
        )
        self.assertTrue(ready, (
            f'odom={self.odometry is not None}, costmap={self.costmap is not None}, '
            f'navigator={self.navigator.server_is_ready()}, '
            f'spawn={self.spawn.service_is_ready()}, '
            f'remove={self.remove.service_is_ready()}, '
            f'monitor={self.monitor_state.service_is_ready()}'
        ))
        self.assertTrue(self._wait_for_active(self.monitor_state, 30.0))

        spawned = self.spawn.call_async(Trigger.Request())
        self.assertTrue(self._spin_until(spawned.done, 8.0))
        self.assertTrue(spawned.result().success)
        self.assertTrue(self._spin_until(
            lambda: self._maximum_cost_near_obstacle() >= 99, 30.0,
        ))
        remembered = self._spin_until(
            lambda: self._maximum_grid_value_near(
                self.memory_map, OBSTACLE_X, OBSTACLE_Y,
                OBSTACLE_SIZE / 2.0 + 0.15,
            ) >= 100,
            30.0,
        )
        self.assertTrue(remembered, self._memory_diagnostic())

        self.commands.clear()
        self.positions.clear()
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        goal.pose.pose.position.x = GOAL_X
        goal.pose.pose.position.y = CORRIDOR_Y
        goal.pose.pose.orientation.w = 1.0
        sent = self.navigator.send_goal_async(goal)
        self.assertTrue(self._spin_until(sent.done, 5.0))
        handle = sent.result()
        self.assertTrue(handle.accepted)
        result = handle.get_result_async()
        self.assertTrue(self._spin_until(result.done, 65.0))
        self.assertEqual(result.result().status, GoalStatus.STATUS_SUCCEEDED)
        self.assertTrue(any(command.linear.x > 0.2 for command in self.commands))
        self.assertTrue(self.positions)
        self.assertGreater(
            max(abs(y - CORRIDOR_Y) for _, y in self.positions), 0.20,
        )
        self.assertGreater(
            min(math.hypot(x - OBSTACLE_X, y - OBSTACLE_Y)
                for x, y in self.positions),
            0.45,
        )
        final_x, final_y = self.positions[-1]
        self.assertLessEqual(math.hypot(final_x - GOAL_X, final_y - CORRIDOR_Y), 0.45)
        self.assertGreaterEqual(self._maximum_grid_value_near(
            self.memory_map, OBSTACLE_X, OBSTACLE_Y,
            OBSTACLE_SIZE / 2.0 + 0.15,
        ), 100)
        self.assertTrue(self._spin_until(
            lambda: self._maximum_cost_near_obstacle() >= 99, 5.0,
        ))
        removed = self.remove.call_async(Trigger.Request())
        self.assertTrue(self._spin_until(removed.done, 8.0))
        self.assertTrue(removed.result().success)
        observation_goal = NavigateToPose.Goal()
        observation_goal.pose = PoseStamped()
        observation_goal.pose.header.frame_id = 'map'
        observation_goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        observation_goal.pose.pose.position.x = 1.5
        observation_goal.pose.pose.position.y = CORRIDOR_Y
        observation_goal.pose.pose.orientation.z = 1.0
        sent = self.navigator.send_goal_async(observation_goal)
        self.assertTrue(self._spin_until(sent.done, 5.0))
        observation_handle = sent.result()
        self.assertTrue(observation_handle.accepted)
        observation_result = observation_handle.get_result_async()
        self.assertTrue(self._spin_until(observation_result.done, 35.0))
        self.assertEqual(
            observation_result.result().status, GoalStatus.STATUS_SUCCEEDED,
        )
        self.assertTrue(self._spin_until(
            lambda: self._maximum_grid_value_near(
                self.memory_map, OBSTACLE_X, OBSTACLE_Y,
                OBSTACLE_SIZE / 2.0 + 0.15,
            ) < 100,
            12.0,
        ))
        self.assertTrue(self._spin_until(
            lambda: self._maximum_cost_near_obstacle() < 99, 12.0,
        ))

        parameters = self.obstacle_parameters.set_parameters([
            Parameter('x', value=0.0),
            Parameter('y', value=CORRIDOR_Y),
            Parameter('size_x', value=0.6),
            Parameter('size_y', value=30.0),
        ])
        self.assertTrue(self._spin_until(parameters.done, 5.0))
        self.assertTrue(all(
            item.successful for item in parameters.result().results
        ))
        blocked = self.spawn.call_async(Trigger.Request())
        self.assertTrue(self._spin_until(blocked.done, 8.0))
        self.assertTrue(blocked.result().success)
        self._spin_until(lambda: False, 2.0)

        return_goal = NavigateToPose.Goal()
        return_goal.pose = PoseStamped()
        return_goal.pose.header.frame_id = 'map'
        return_goal.pose.header.stamp = self.node.get_clock().now().to_msg()
        return_goal.pose.pose.position.x = -2.0
        return_goal.pose.pose.position.y = CORRIDOR_Y
        return_goal.pose.pose.orientation.w = 1.0
        sent = self.navigator.send_goal_async(return_goal)
        self.assertTrue(self._spin_until(sent.done, 5.0))
        blocked_handle = sent.result()
        self.assertTrue(blocked_handle.accepted)
        blocked_result = blocked_handle.get_result_async()
        self._spin_until(lambda: False, 48.0)
        self.assertFalse(blocked_result.done())
        blocked_x, blocked_y = self.positions[-1]
        self.assertGreater(
            math.hypot(blocked_x + 2.0, blocked_y - CORRIDOR_Y), 0.5,
        )
        canceled = blocked_handle.cancel_goal_async()
        self.assertTrue(self._spin_until(canceled.done, 5.0))
        self.assertTrue(self._spin_until(blocked_result.done, 5.0))
        self.assertEqual(
            blocked_result.result().status, GoalStatus.STATUS_CANCELED,
        )
        self.assertTrue(self._spin_until(
            lambda: (
                self.commands
                and abs(self.commands[-1].linear.x) < 1e-6
                and abs(self.commands[-1].angular.z) < 1e-6
            ),
            3.0,
        ))

        removed = self.remove.call_async(Trigger.Request())
        self.assertTrue(self._spin_until(removed.done, 8.0))
        self.assertTrue(removed.result().success)
        sent = self.navigator.send_goal_async(return_goal)
        self.assertTrue(self._spin_until(sent.done, 5.0))
        resumed_handle = sent.result()
        self.assertTrue(resumed_handle.accepted)
        resumed_result = resumed_handle.get_result_async()
        self.assertTrue(self._spin_until(resumed_result.done, 100.0))
        self.assertEqual(resumed_result.result().status, GoalStatus.STATUS_SUCCEEDED)
        self.assertTrue(self._spin_until(
            lambda: self._maximum_grid_value_near(
                self.memory_map, 0.0, CORRIDOR_Y, 0.3,
            ) < 100,
            10.0,
        ))
        self.assertTrue(self._spin_until(
            lambda: self._maximum_cost_near(0.0, CORRIDOR_Y, 0.3) < 99,
            10.0,
        ))
