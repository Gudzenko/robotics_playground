"""Tests for deterministic, ROS-independent sensor noise models."""

import math
from pathlib import Path

from cargo_bot.sensor_noise import (
    apply_encoder_noise,
    apply_lidar_noise,
    ImuNoiseModel,
    load_noise_profile,
    seeded_generator,
)
import pytest
import yaml


SENSOR_CONFIG_PATH = Path(__file__).parents[1] / 'config' / 'sensors.yaml'


@pytest.mark.parametrize('profile', ['ideal', 'realistic', 'harsh'])
@pytest.mark.parametrize('sensor', ['lidar', 'imu', 'encoders'])
def test_all_profiles_are_available_with_repeatable_sensor_seeds(profile, sensor):
    selected, seed, parameters = load_noise_profile(
        sensor,
        profile,
        SENSOR_CONFIG_PATH,
    )

    assert selected == profile
    assert isinstance(seed, int)
    assert parameters
    assert seeded_generator(seed).random() == seeded_generator(seed).random()


def test_ideal_profile_is_exact_pass_through():
    _, lidar_seed, lidar = load_noise_profile('lidar', 'ideal', SENSOR_CONFIG_PATH)
    _, imu_seed, imu = load_noise_profile('imu', 'ideal', SENSOR_CONFIG_PATH)
    _, encoder_seed, encoders = load_noise_profile(
        'encoders', 'ideal', SENSOR_CONFIG_PATH,
    )

    ranges = [0.5, math.inf, 3.0]
    assert apply_lidar_noise(
        ranges, 0.1, 10.0, lidar, seeded_generator(lidar_seed),
    ) == ranges
    assert ImuNoiseModel(imu, seeded_generator(imu_seed)).apply(
        (1.0, 2.0, 3.0),
        (4.0, 5.0, 6.0),
    ) == ((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))
    assert apply_encoder_noise(
        120, -80, encoders, seeded_generator(encoder_seed),
    ) == (120, -80)


def test_seed_reproduces_lidar_noise_and_preserves_dimensions():
    _, seed, parameters = load_noise_profile('lidar', 'realistic', SENSOR_CONFIG_PATH)
    ranges = [float(index) / 10.0 + 1.0 for index in range(100)]

    first = apply_lidar_noise(ranges, 0.15, 20.0, parameters, seeded_generator(seed))
    second = apply_lidar_noise(ranges, 0.15, 20.0, parameters, seeded_generator(seed))

    assert first == second
    assert len(first) == len(ranges)
    assert first != ranges


def test_lidar_bias_and_dropout_are_applied_to_valid_samples_only():
    parameters = {
        'gaussian_stddev': 0.0,
        'bias': 0.25,
        'dropout_probability': 1.0,
    }
    result = apply_lidar_noise(
        [1.0, math.inf, math.nan],
        0.1,
        5.0,
        parameters,
        seeded_generator(1),
    )

    assert math.isinf(result[0])
    assert math.isinf(result[1])
    assert math.isnan(result[2])


def test_seed_reproduces_imu_white_noise_bias_and_drift():
    _, seed, parameters = load_noise_profile('imu', 'harsh', SENSOR_CONFIG_PATH)
    first = ImuNoiseModel(parameters, seeded_generator(seed))
    second = ImuNoiseModel(parameters, seeded_generator(seed))

    first_sequence = [first.apply((0.0, 0.0, 0.0), (0.0, 0.0, 9.8)) for _ in range(3)]
    second_sequence = [second.apply((0.0, 0.0, 0.0), (0.0, 0.0, 9.8)) for _ in range(3)]

    assert first_sequence == second_sequence
    assert first_sequence[0] != first_sequence[1]
    assert first_sequence[0][1][2] != 9.8


def test_encoder_scale_and_missed_ticks_are_applied_independently():
    no_misses = {
        'missed_tick_probability': 0.0,
        'left_scale_error': 0.1,
        'right_scale_error': -0.1,
    }
    all_missed = dict(no_misses, missed_tick_probability=1.0)

    assert apply_encoder_noise(100, 100, no_misses, seeded_generator(1)) == (110, 90)
    assert apply_encoder_noise(100, -100, all_missed, seeded_generator(1)) == (0, 0)


def test_ros_noise_cannot_be_combined_with_gazebo_native_noise(tmp_path):
    with SENSOR_CONFIG_PATH.open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)
    config['lidar']['gazebo_native_noise'] = True
    config_path = tmp_path / 'sensors.yaml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')

    with pytest.raises(ValueError, match='Gazebo-native and ROS-side'):
        load_noise_profile('lidar', 'realistic', config_path)


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match='Unknown sensor noise profile'):
        load_noise_profile('lidar', 'unknown', SENSOR_CONFIG_PATH)
