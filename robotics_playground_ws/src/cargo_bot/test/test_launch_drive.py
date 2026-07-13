"""Headless smoke test for the RViz differential-drive stack."""

import os
from pathlib import Path
import tempfile
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
from launch_testing.actions import ReadyToTest
import pytest
import rclpy
from sensor_msgs.msg import JointState


os.environ.setdefault(
    'ROS_LOG_DIR',
    str(Path(tempfile.gettempdir()) / 'cargo_bot_launch_test_logs'),
)


@pytest.mark.launch_test
def generate_test_description():
    """Launch the drive stack with RViz disabled."""
    package_share = get_package_share_directory('cargo_bot')
    drive_launch = PythonLaunchDescriptionSource(
        f'{package_share}/launch/drive_in_rviz.launch.py',
    )

    return LaunchDescription([
        IncludeLaunchDescription(
            drive_launch,
            launch_arguments={'use_rviz': 'false'}.items(),
        ),
        ReadyToTest(),
    ])


class TestDriveLaunch(unittest.TestCase):
    """Check that the headless drive graph exposes its public interfaces."""

    @classmethod
    def setUpClass(cls):
        """Create one inspection node for the launch tests."""
        rclpy.init()
        cls.node = rclpy.create_node('drive_launch_test')
        cls.manipulator_joint_state_received = False
        cls.joint_state_subscription = cls.node.create_subscription(
            JointState,
            '/joint_states',
            cls._joint_state_callback,
            10,
        )

    @classmethod
    def tearDownClass(cls):
        """Destroy the inspection node and stop its ROS context."""
        cls.node.destroy_node()
        rclpy.shutdown()

    @classmethod
    def _joint_state_callback(cls, message):
        manipulator_joints = {
            'manipulator_arm_joint',
            'manipulator_left_finger_joint',
            'manipulator_lift_joint',
            'manipulator_mount_joint',
        }
        if manipulator_joints.issubset(message.name):
            cls.manipulator_joint_state_received = True

    def test_nodes_and_topics_are_available(self):
        """Expected nodes and typed topics should appear without RViz."""
        expected_nodes = {
            '/manipulator_control_node',
            '/robot_state_publisher',
            '/simple_diff_drive_sim',
        }
        expected_topics = {
            '/cmd_vel': {'geometry_msgs/msg/Twist'},
            '/joint_states': {'sensor_msgs/msg/JointState'},
            '/odom': {'nav_msgs/msg/Odometry'},
        }

        nodes, topics = self._wait_for_graph(expected_nodes, expected_topics)

        self.assertTrue(expected_nodes.issubset(nodes))
        for topic_name, topic_types in expected_topics.items():
            self.assertEqual(topics.get(topic_name), topic_types)
        self.assertNotIn('/rviz2', nodes)
        self.assertTrue(
            self._wait_for_manipulator_joint_state(),
            'No complete manipulator joint state received',
        )

    def _wait_for_manipulator_joint_state(self, timeout_sec=10.0):
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if self.manipulator_joint_state_received:
                return True
        return False

    def _wait_for_graph(self, expected_nodes, expected_topics, timeout_sec=10.0):
        deadline = time.monotonic() + timeout_sec
        nodes = set()
        topics = {}

        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            nodes = {
                f'{namespace}/{name}'.replace('//', '/')
                for name, namespace in self.node.get_node_names_and_namespaces()
            }
            topics = {
                name: set(topic_types)
                for name, topic_types in self.node.get_topic_names_and_types()
            }
            if (
                expected_nodes.issubset(nodes)
                and all(topics.get(name) == types for name, types in expected_topics.items())
            ):
                break

        return nodes, topics


@launch_testing.post_shutdown_test()
class TestDriveLaunchShutdown(unittest.TestCase):
    """Check that launched processes stop without errors."""

    def test_exit_codes(self, proc_info):
        """All launched processes should exit cleanly during shutdown."""
        launch_testing.asserts.assertExitCodes(proc_info)
