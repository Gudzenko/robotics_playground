"""Tests for replaceable sensor sources and deterministic mock fixtures."""

from pathlib import Path

from builtin_interfaces.msg import Time
from cargo_bot.mock_sensor_publisher import (
    make_mock_imu,
    make_mock_joint_state,
    make_mock_scan,
)
from cargo_bot.sensor_sources import resolve_source_topic, SOURCE_NAMES
import pytest


SENSOR_CONFIG_PATH = Path(__file__).parents[1] / 'config' / 'sensors.yaml'


EXPECTED_TOPICS = {
    'lidar': {
        'gazebo': '/sim/scan',
        'mock': '/mock/scan',
        'rosbag': '/bag/scan',
        'external': '/external/scan',
    },
    'imu': {
        'gazebo': '/sim/imu',
        'mock': '/mock/imu',
        'rosbag': '/bag/imu',
        'external': '/external/imu',
    },
    'encoders': {
        'gazebo': '/sim/joint_states',
        'mock': '/mock/joint_states',
        'rosbag': '/bag/joint_states',
        'external': '/external/joint_states',
    },
}


@pytest.mark.parametrize('sensor', EXPECTED_TOPICS)
@pytest.mark.parametrize('source', SOURCE_NAMES)
def test_each_sensor_source_resolves_independently(sensor, source):
    assert resolve_source_topic(sensor, source, SENSOR_CONFIG_PATH) == (
        EXPECTED_TOPICS[sensor][source]
    )


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError, match='Unknown lidar source'):
        resolve_source_topic('lidar', 'duplicate', SENSOR_CONFIG_PATH)


def test_mock_lidar_is_deterministic_and_navigation_compatible():
    stamp = Time(sec=12, nanosec=34)
    first = make_mock_scan(stamp)
    second = make_mock_scan(stamp)

    assert first == second
    assert first.header.stamp == stamp
    assert first.header.frame_id == 'lidar_link'
    assert len(first.ranges) == 720
    assert len(first.intensities) == 720
    assert all(first.range_min <= value <= first.range_max for value in first.ranges)


def test_mock_imu_is_deterministic_and_navigation_compatible():
    stamp = Time(sec=12, nanosec=34)
    first = make_mock_imu(stamp, 17)
    second = make_mock_imu(stamp, 17)

    assert first == second
    assert first.header.frame_id == 'imu_link'
    assert first.orientation.w == 1.0
    assert first.linear_acceleration.z == 9.8


def test_mock_encoder_sequence_is_deterministic_and_complete():
    stamp = Time(sec=12, nanosec=34)
    first = make_mock_joint_state(stamp, 17)
    second = make_mock_joint_state(stamp, 17)

    assert first == second
    assert first.name == ['left_wheel_joint', 'right_wheel_joint']
    assert list(first.position) == [0.17, 0.17]
