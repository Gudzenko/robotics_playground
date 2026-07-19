"""Tests for ideal IMU configuration and covariance processing."""

from pathlib import Path

from cargo_bot.imu_relay import (
    apply_ideal_covariances,
    apply_noise_covariances,
    covariance_from_diagonal,
    load_imu_config,
)
import pytest
from sensor_msgs.msg import Imu


SENSOR_CONFIG_PATH = Path(__file__).parents[1] / 'config' / 'sensors.yaml'


def test_project_imu_contract_is_loaded():
    """The relay should load the agreed ideal IMU contract."""
    config = load_imu_config(SENSOR_CONFIG_PATH)

    assert config['source_topic'] == '/sim/imu'
    assert config['output_topic'] == '/imu/data_raw'
    assert config['frame'] == 'imu_link'
    assert config['update_rate'] == 50.0


def test_covariance_diagonal_is_expanded_to_ros_matrix():
    """Three configured variances should form a row-major 3x3 diagonal."""
    assert covariance_from_diagonal([1.0, 2.0, 3.0]) == [
        1.0, 0.0, 0.0,
        0.0, 2.0, 0.0,
        0.0, 0.0, 3.0,
    ]


def test_ideal_covariances_are_applied_without_changing_measurements():
    """Covariance processing should preserve the ideal IMU measurements."""
    config = load_imu_config(SENSOR_CONFIG_PATH)
    message = Imu()
    message.angular_velocity.z = 0.75
    message.linear_acceleration.x = 1.25
    message.orientation.w = 1.0

    result = apply_ideal_covariances(message, config)

    assert result is message
    assert result.angular_velocity.z == 0.75
    assert result.linear_acceleration.x == 1.25
    assert result.orientation.w == 1.0
    assert list(result.orientation_covariance) == covariance_from_diagonal(
        config['orientation_covariance_diagonal'],
    )
    assert list(result.angular_velocity_covariance) == covariance_from_diagonal(
        config['angular_velocity_covariance_diagonal'],
    )
    assert list(result.linear_acceleration_covariance) == covariance_from_diagonal(
        config['linear_acceleration_covariance_diagonal'],
    )


def test_noise_covariance_covers_configured_white_noise():
    """Published covariance should not understate injected white noise."""
    config = load_imu_config(SENSOR_CONFIG_PATH)
    message = Imu()
    noise = {
        'angular_velocity_stddev': [0.01, 0.02, 0.03],
        'linear_acceleration_stddev': [0.1, 0.2, 0.3],
    }

    result = apply_noise_covariances(message, config, noise)

    assert list(result.angular_velocity_covariance) == pytest.approx(covariance_from_diagonal([
        0.0001, 0.0004, 0.0009,
    ]))
    assert list(result.linear_acceleration_covariance) == pytest.approx(covariance_from_diagonal([
        0.01, 0.04, 0.09,
    ]))


@pytest.mark.parametrize(
    'diagonal',
    ([1.0, 2.0], [1.0, 2.0, 0.0], [1.0, -1.0, 2.0]),
)
def test_invalid_covariance_diagonal_is_rejected(tmp_path, diagonal):
    """Each IMU covariance diagonal must contain three positive variances."""
    config_path = tmp_path / 'sensors.yaml'
    config_path.write_text(
        '\n'.join([
            'imu:',
            '  source_topic: /sim/imu',
            '  output_topic: /imu/data_raw',
            f'  orientation_covariance_diagonal: {diagonal}',
            '  angular_velocity_covariance_diagonal: [1.0, 1.0, 1.0]',
            '  linear_acceleration_covariance_diagonal: [1.0, 1.0, 1.0]',
        ]),
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='three positive values'):
        load_imu_config(config_path)
