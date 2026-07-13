"""Tests for deterministic differential-drive calculations."""

import math

from cargo_bot.diff_drive_math import (
    integrate_pose,
    normalize_angle,
    wheel_angular_velocities,
    yaw_to_quaternion,
)
import pytest


@pytest.mark.parametrize(
    ('yaw', 'expected_z', 'expected_w'),
    [
        (0.0, 0.0, 1.0),
        (math.pi / 2.0, math.sqrt(0.5), math.sqrt(0.5)),
        (-math.pi, -1.0, 0.0),
    ],
)
def test_yaw_to_quaternion(yaw, expected_z, expected_w):
    """Planar yaw should produce a normalized Z-axis quaternion."""
    quaternion = yaw_to_quaternion(yaw)

    assert quaternion['x'] == 0.0
    assert quaternion['y'] == 0.0
    assert quaternion['z'] == pytest.approx(expected_z)
    assert quaternion['w'] == pytest.approx(expected_w, abs=1e-12)
    assert quaternion['z'] ** 2 + quaternion['w'] ** 2 == pytest.approx(1.0)


def test_normalize_angle_wraps_across_pi():
    """Angles beyond pi should wrap to the equivalent negative angle."""
    assert normalize_angle(math.pi + 0.25) == pytest.approx(-math.pi + 0.25)


def test_integrate_pose_uses_current_heading_and_wraps_yaw():
    """One integration step should match the simulator's Euler update."""
    x, y, yaw = integrate_pose(
        x=1.0,
        y=-2.0,
        yaw=math.pi / 2.0,
        linear_velocity=2.0,
        angular_velocity=math.pi,
        dt=0.5,
    )

    assert x == pytest.approx(1.0)
    assert y == pytest.approx(-1.0)
    assert yaw == pytest.approx(math.pi)


@pytest.mark.parametrize(
    ('linear', 'angular', 'expected_left', 'expected_right'),
    [
        (1.0, 0.0, 2.0, 2.0),
        (0.0, 2.0, -1.0, 1.0),
        (1.0, 2.0, 1.0, 3.0),
    ],
)
def test_wheel_angular_velocities(
    linear,
    angular,
    expected_left,
    expected_right,
):
    """Body twist should map to the expected wheel angular velocities."""
    left, right = wheel_angular_velocities(
        linear_velocity=linear,
        angular_velocity=angular,
        wheel_separation=0.5,
        wheel_radius=0.5,
    )

    assert left == pytest.approx(expected_left)
    assert right == pytest.approx(expected_right)
