"""Tests for sensor-specific diagnostic visualization contracts."""

from collections import deque
from pathlib import Path

from cargo_bot.odometry_paths import OdometryPathPublisher
from nav_msgs.msg import Odometry
import yaml


PACKAGE_PATH = Path(__file__).parents[1]
RVIZ_PATH = PACKAGE_PATH / 'rviz' / 'cargo_bot_sensor_diagnostics.rviz'
LAUNCH_PATH = PACKAGE_PATH / 'launch' / 'sensor_diagnostics.launch.py'


class RecordingPublisher:
    """Minimal publisher double recording the newest Path."""

    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def test_odometry_path_is_bounded_and_preserves_pose_metadata():
    poses = deque(maxlen=2)
    publisher = RecordingPublisher()

    for index in range(3):
        odometry = Odometry()
        odometry.header.frame_id = 'odom'
        odometry.header.stamp.sec = index
        odometry.pose.pose.position.x = float(index)
        OdometryPathPublisher._append_and_publish(
            odometry,
            poses,
            publisher,
        )

    path = publisher.messages[-1]
    assert path.header.frame_id == 'odom'
    assert path.header.stamp.sec == 2
    assert [pose.pose.position.x for pose in path.poses] == [1.0, 2.0]
    assert [pose.header.stamp.sec for pose in path.poses] == [1, 2]


def test_rviz_overlays_raw_and_processed_lidar_with_correct_qos():
    with RVIZ_PATH.open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)
    displays = config['Visualization Manager']['Displays']
    scans = {
        display['Topic']: display
        for display in displays
        if display['Class'] == 'rviz_default_plugins/LaserScan'
    }

    assert scans['/sim/scan']['Unreliable'] is True
    assert scans['/sim/scan']['Color'] == '40; 120; 255'
    assert scans['/scan']['Unreliable'] is False
    assert scans['/scan']['Color'] == '255; 40; 40'


def test_rviz_compares_wheel_and_ground_truth_paths():
    with RVIZ_PATH.open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)
    displays = config['Visualization Manager']['Displays']
    path_topics = {
        display['Topic']
        for display in displays
        if display['Class'] == 'rviz_default_plugins/Path'
    }

    assert path_topics == {
        '/debug/wheel_path',
        '/debug/filtered_path',
        '/debug/ground_truth_path',
    }


def test_diagnostic_launch_contains_sensor_specific_plot_fields():
    launch_source = LAUNCH_PATH.read_text(encoding='utf-8')

    assert "imu_input_topic, \"/angular_velocity/x'\"" in launch_source
    assert '/imu/data_raw/angular_velocity/z' in launch_source
    assert "imu_input_topic, \"/linear_acceleration/x'\"" in launch_source
    assert '/imu/data_raw/linear_acceleration/z' in launch_source
    assert "encoder_input_topic, \"/position[0]'\"" in launch_source
    assert "encoder_input_topic, \"/position[1]'\"" in launch_source
