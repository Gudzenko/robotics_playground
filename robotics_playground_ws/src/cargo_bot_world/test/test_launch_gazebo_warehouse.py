"""Headless smoke test for the Gazebo warehouse simulation."""

import os
from pathlib import Path
import tempfile
import unittest

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_testing.actions import ReadyToTest
import pytest


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
            launch_arguments={'headless': 'true'}.items(),
        ),
        ReadyToTest(),
    ])


class TestGazeboWarehouseLaunch(unittest.TestCase):
    """Check that Gazebo, robot spawning and topic bridging work together."""

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
            'Manipulator control node started',
            timeout=10.0,
        )
        proc_info.assertWaitForShutdown(
            process='create',
            timeout=10.0,
        )
