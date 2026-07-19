"""Deterministic tests for quantized differential-drive odometry."""

import math
from pathlib import Path

from cargo_bot.wheel_odometry import (
    angle_to_ticks,
    covariance_from_diagonal,
    EncoderIntegrator,
    integrate_encoder_ticks,
    load_encoder_config,
)
import pytest


PACKAGE_PATH = Path(__file__).parents[1]
SENSOR_CONFIG_PATH = PACKAGE_PATH / 'config' / 'sensors.yaml'
GEOMETRY_PATH = PACKAGE_PATH / 'config' / 'cargo_bot_geometry.yaml'


def test_project_encoder_contract_reuses_shared_geometry():
    config = load_encoder_config(SENSOR_CONFIG_PATH, GEOMETRY_PATH)

    assert config['source_topic'] == '/sim/joint_states'
    assert config['robot_state_topic'] == '/joint_states'
    assert config['output_topic'] == '/wheel/odometry'
    assert config['ground_truth_topic'] == '/ground_truth/odometry'
    assert config['left_joint'] == 'left_wheel_joint'
    assert config['right_joint'] == 'right_wheel_joint'
    assert config['ticks_per_revolution'] == 2048
    assert config['wheel_radius'] == pytest.approx(0.23)
    assert config['wheel_separation'] == pytest.approx(1.16)


def test_odometry_covariance_expands_to_ros_6x6_matrix():
    covariance = covariance_from_diagonal([1, 2, 3, 4, 5, 6])

    assert len(covariance) == 36
    assert [covariance[index] for index in (0, 7, 14, 21, 28, 35)] == [
        1, 2, 3, 4, 5, 6,
    ]
    assert sum(covariance) == 21


def test_angle_quantization_is_symmetric_and_configurable():
    assert angle_to_ticks(2.0 * math.pi, 2048) == 2048
    assert angle_to_ticks(math.pi, 100) == 50
    assert angle_to_ticks(-math.pi, 100) == -50
    assert angle_to_ticks(math.pi / 100.0, 100) == 1
    assert angle_to_ticks(-math.pi / 100.0, 100) == -1


def test_straight_motion():
    result = integrate_encoder_ticks(100, 100, 1000, 0.2, 0.8, 0.0, 0.5)
    distance = 100 * 2.0 * math.pi * 0.2 / 1000

    assert result.x == pytest.approx(distance)
    assert result.y == pytest.approx(0.0)
    assert result.yaw == pytest.approx(0.0)
    assert result.linear_velocity == pytest.approx(distance / 0.5)


def test_arc_motion_uses_exact_differential_drive_integration():
    result = integrate_encoder_ticks(50, 150, 1000, 0.2, 0.8, 0.0, 1.0)
    left = 50 * 2.0 * math.pi * 0.2 / 1000
    right = 150 * 2.0 * math.pi * 0.2 / 1000
    distance = (left + right) / 2.0
    yaw = (right - left) / 0.8

    assert result.x == pytest.approx(distance * math.sin(yaw) / yaw)
    assert result.y == pytest.approx(distance * (1.0 - math.cos(yaw)) / yaw)
    assert result.yaw == pytest.approx(yaw)


def test_in_place_rotation_has_no_translation():
    result = integrate_encoder_ticks(-100, 100, 1000, 0.2, 0.8, 1.2, 0.25)

    assert result.x == pytest.approx(0.0)
    assert result.y == pytest.approx(0.0)
    assert result.yaw > 0.0
    assert result.linear_velocity == pytest.approx(0.0)
    assert result.angular_velocity == pytest.approx(result.yaw / 0.25)


@pytest.mark.parametrize('delta_time', [0.0, -1.0, math.inf, math.nan])
def test_invalid_or_non_monotonic_time_is_rejected(delta_time):
    with pytest.raises(ValueError, match='delta_time'):
        integrate_encoder_ticks(1, 1, 100, 0.2, 0.8, 0.0, delta_time)


@pytest.mark.parametrize('angle', [math.inf, -math.inf, math.nan])
def test_invalid_wheel_angle_is_rejected(angle):
    with pytest.raises(ValueError, match='finite'):
        angle_to_ticks(angle, 2048)


def test_integrator_ignores_missing_joints_and_first_complete_sample():
    config = load_encoder_config(SENSOR_CONFIG_PATH, GEOMETRY_PATH)
    integrator = EncoderIntegrator(config)

    assert integrator.update({'left_wheel_joint': 0.0}, 1.0) is None
    assert integrator.update({
        'left_wheel_joint': 0.0,
        'right_wheel_joint': 0.0,
    }, 1.0) is None
    estimate = integrator.update({
        'left_wheel_joint': 0.1,
        'right_wheel_joint': 0.1,
    }, 2.0)

    assert estimate is not None
    assert estimate.x > 0.0


def test_non_monotonic_sample_does_not_corrupt_integrator_state():
    config = load_encoder_config(SENSOR_CONFIG_PATH, GEOMETRY_PATH)
    integrator = EncoderIntegrator(config)
    zero = {'left_wheel_joint': 0.0, 'right_wheel_joint': 0.0}
    forward = {'left_wheel_joint': 0.2, 'right_wheel_joint': 0.2}

    assert integrator.update(zero, 10.0) is None
    assert integrator.update(forward, 9.0) is None
    estimate = integrator.update(forward, 11.0)

    assert estimate is not None
    expected_ticks = angle_to_ticks(0.2, config['ticks_per_revolution'])
    expected_distance = expected_ticks * 2.0 * math.pi * 0.23 / 2048
    assert estimate.x == pytest.approx(expected_distance)


def test_update_rate_limits_output_without_losing_ticks():
    config = load_encoder_config(SENSOR_CONFIG_PATH, GEOMETRY_PATH)
    integrator = EncoderIntegrator(config)
    zero = {'left_wheel_joint': 0.0, 'right_wheel_joint': 0.0}
    partial = {'left_wheel_joint': 0.1, 'right_wheel_joint': 0.1}
    complete = {'left_wheel_joint': 0.2, 'right_wheel_joint': 0.2}

    assert integrator.update(zero, 1.0) is None
    assert integrator.update(partial, 1.01) is None
    estimate = integrator.update(complete, 1.02)

    expected_ticks = angle_to_ticks(0.2, config['ticks_per_revolution'])
    expected_distance = expected_ticks * 2.0 * math.pi * 0.23 / 2048
    assert estimate.x == pytest.approx(expected_distance)
