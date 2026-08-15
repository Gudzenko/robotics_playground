"""Acceptance test for moving and simultaneous persistent obstacles."""

import math
import os
from pathlib import Path
import tempfile
import time
import unittest

from geometry_msgs.msg import Twist
import launch
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
from nav_msgs.msg import OccupancyGrid, Odometry
import pytest
import rclpy
from rclpy.parameter import Parameter
from rclpy.parameter_client import AsyncParameterClient
from std_srvs.srv import Trigger


PRIMARY = (0.0, 10.0)
SECONDARY = (0.0, 11.0)


@pytest.mark.launch_test
def generate_test_description():
    package = Path(__file__).parents[1]
    workspace = package.parents[1]
    os.environ['ROS_LOG_DIR'] = str(
        Path(tempfile.gettempdir()) / 'cargo_bot_obstacle_memory_logs',
    )
    tested_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(package / 'launch' / 'obstacle_navigation.launch.py'),
        ),
        launch_arguments={
            'map': str(workspace / 'saved_maps' / 'indoor_map.yaml'),
            'initial_pose_x': '-4.0',
            'initial_pose_y': '10.5',
            'initial_pose_yaw': '0.0',
            'headless': 'true',
            'use_rviz': 'false',
            'obstacle_name': f'navigation_obstacle_{os.getpid()}',
            'secondary_obstacle_name': (
                f'secondary_navigation_obstacle_{os.getpid()}'
            ),
            'obstacle_x': str(PRIMARY[0]),
            'obstacle_y': str(PRIMARY[1]),
            'obstacle_size_x': '0.4',
            'obstacle_size_y': '0.4',
            'secondary_obstacle_x': str(SECONDARY[0]),
            'secondary_obstacle_y': str(SECONDARY[1]),
            'secondary_obstacle_size_x': '0.4',
            'secondary_obstacle_size_y': '0.4',
            'moving_obstacle_target_x': str(SECONDARY[0]),
            'moving_obstacle_target_y': str(SECONDARY[1]),
            'moving_obstacle_duration': '2.0',
            'gz_partition': f'cargo_bot_obstacle_memory_{os.getpid()}',
        }.items(),
    )
    return launch.LaunchDescription([
        tested_launch,
        launch_testing.actions.ReadyToTest(),
    ])


class TestObstacleMemoryScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('obstacle_memory_scenarios_test')
        cls.memory = None
        cls.odometry = None
        cls.commands = []
        cls.node.create_subscription(
            OccupancyGrid, '/persistent_obstacle_map', cls._memory, 10,
        )
        cls.node.create_subscription(
            Odometry, '/ground_truth/odometry', cls._odometry, 10,
        )
        cls.node.create_subscription(Twist, '/cmd_vel', cls.commands.append, 10)
        cls.spawn = cls.node.create_client(
            Trigger, '/spawn_navigation_obstacle',
        )
        cls.remove = cls.node.create_client(
            Trigger, '/remove_navigation_obstacle',
        )
        cls.spawn_secondary = cls.node.create_client(
            Trigger, '/spawn_secondary_navigation_obstacle',
        )
        cls.remove_secondary = cls.node.create_client(
            Trigger, '/remove_secondary_navigation_obstacle',
        )
        cls.start_moving = cls.node.create_client(
            Trigger, '/start_moving_navigation_obstacle',
        )
        cls.parameters = AsyncParameterClient(cls.node, '/obstacle_manager')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _memory(cls, message):
        cls.memory = message

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

    def _occupied_near(self, point, radius=0.35):
        if self.memory is None:
            return False
        info = self.memory.info
        center_x = int((point[0] - info.origin.position.x) / info.resolution)
        center_y = int((point[1] - info.origin.position.y) / info.resolution)
        cells = math.ceil(radius / info.resolution)
        for row in range(center_y - cells, center_y + cells + 1):
            for column in range(center_x - cells, center_x + cells + 1):
                if 0 <= column < info.width and 0 <= row < info.height:
                    if self.memory.data[row * info.width + column] == 100:
                        return True
        return False

    def _call(self, client, timeout=8.0):
        result = None
        for _ in range(5):
            future = client.call_async(Trigger.Request())
            self.assertTrue(self._spin_until(future.done, timeout))
            result = future.result()
            if result.success:
                return
            self._spin_until(lambda: False, 1.0)
        self.fail(result.message)

    def test_moving_and_multiple_obstacles(self):
        ready = self._spin_until(
            lambda: (
                self.odometry is not None
                and self.spawn.service_is_ready()
                and self.remove.service_is_ready()
                and self.spawn_secondary.service_is_ready()
                and self.remove_secondary.service_is_ready()
                and self.start_moving.service_is_ready()
            ),
            80.0,
        )
        self.assertTrue(ready, (
            f'odom={self.odometry is not None}, '
            f'spawn={self.spawn.service_is_ready()}, '
            f'remove={self.remove.service_is_ready()}, '
            f'spawn_secondary={self.spawn_secondary.service_is_ready()}, '
            f'remove_secondary={self.remove_secondary.service_is_ready()}, '
            f'start_moving={self.start_moving.service_is_ready()}'
        ))

        self._call(self.spawn)
        self.assertTrue(self._spin_until(lambda: self._occupied_near(PRIMARY), 20.0))
        self._call(self.start_moving)
        self.assertTrue(
            self._spin_until(lambda: self._occupied_near(SECONDARY), 15.0),
        )
        self._call(self.remove)
        self.assertTrue(self._spin_until(
            lambda: not self._occupied_near(SECONDARY), 15.0,
        ))

        parameters = self.parameters.set_parameters([
            Parameter('x', value=PRIMARY[0]),
            Parameter('y', value=PRIMARY[1]),
        ])
        self.assertTrue(self._spin_until(parameters.done, 5.0))
        self.assertTrue(all(item.successful for item in parameters.result().results))
        self._call(self.spawn)
        self._call(self.spawn_secondary)
        self.assertTrue(self._spin_until(
            lambda: (
                self._occupied_near(PRIMARY)
                and self._occupied_near(SECONDARY)
            ),
            20.0,
        ))

        self._call(self.remove)
        self.assertTrue(self._spin_until(
            lambda: (
                not self._occupied_near(PRIMARY)
                and self._occupied_near(SECONDARY)
            ),
            15.0,
        ))
        self._call(self.remove_secondary)
        self.assertTrue(self._spin_until(
            lambda: not self._occupied_near(SECONDARY), 15.0,
        ))
        self.assertFalse(any(
            abs(command.linear.x) > 1e-6 or abs(command.angular.z) > 1e-6
            for command in self.commands
        ))
