"""Tests for manipulator command interpolation and validation."""

import math

from cargo_bot.manipulator_commands import (
    interpolate_position,
    validate_move_command,
)
from cargo_bot.manipulator_constants import ELEMENT_ARM, ELEMENT_LIFT
import pytest


ELEMENT_LIMITS = {
    ELEMENT_ARM: {'lower': 0.0, 'upper': 0.35},
    ELEMENT_LIFT: {'lower': -0.78, 'upper': 0.78},
}


@pytest.mark.parametrize(
    ('progress', 'expected'),
    [
        (-1.0, 2.0),
        (0.0, 2.0),
        (0.25, 3.0),
        (1.0, 6.0),
        (2.0, 6.0),
    ],
)
def test_interpolate_position_clamps_progress(progress, expected):
    """Interpolation should remain within its start and target positions."""
    assert interpolate_position(2.0, 6.0, progress) == pytest.approx(expected)


def test_interpolate_position_supports_descending_motion():
    """Interpolation should work when the target is below the start position."""
    assert interpolate_position(1.0, -1.0, 0.75) == pytest.approx(-0.5)


@pytest.mark.parametrize('position', [-0.78, 0.0, 0.78])
def test_validate_move_command_accepts_limits_and_zero_duration(position):
    """Limit boundaries and an immediate command should be valid."""
    assert validate_move_command(
        ELEMENT_LIFT,
        position,
        0.0,
        ELEMENT_LIMITS,
    ) == ''


def test_validate_move_command_rejects_unknown_element():
    """An element outside the public command set should be rejected."""
    error = validate_move_command(
        'camera',
        0.0,
        1.0,
        ELEMENT_LIMITS,
    )

    assert error == (
        "unknown element 'camera'. Allowed: rotation, lift, arm, gripper"
    )


def test_validate_move_command_requires_loaded_limits():
    """A known element without loaded limits should be rejected."""
    error = validate_move_command(ELEMENT_ARM, 0.1, 1.0, {})

    assert error == "limits for element 'arm' are not available"


def test_validate_move_command_rejects_busy_element():
    """A second command should not start while the element is moving."""
    error = validate_move_command(
        ELEMENT_ARM,
        0.1,
        1.0,
        ELEMENT_LIMITS,
        element_is_moving=True,
    )

    assert error == "element 'arm' is already moving"


@pytest.mark.parametrize('position', [math.nan, math.inf, -math.inf])
def test_validate_move_command_requires_finite_position(position):
    """Non-finite target positions should be rejected."""
    error = validate_move_command(ELEMENT_ARM, position, 1.0, ELEMENT_LIMITS)

    assert error == 'position must be a finite number'


@pytest.mark.parametrize('position', [-0.01, 0.36])
def test_validate_move_command_enforces_position_limits(position):
    """Positions outside the configured closed interval should be rejected."""
    error = validate_move_command(ELEMENT_ARM, position, 1.0, ELEMENT_LIMITS)

    assert error == "position for element 'arm' must be between 0.0 and 0.35"


@pytest.mark.parametrize('duration_sec', [math.nan, math.inf, -math.inf])
def test_validate_move_command_requires_finite_duration(duration_sec):
    """Non-finite durations should be rejected."""
    error = validate_move_command(
        ELEMENT_ARM,
        0.1,
        duration_sec,
        ELEMENT_LIMITS,
    )

    assert error == 'duration_sec must be a finite number'


def test_validate_move_command_rejects_negative_duration():
    """A command duration must not be negative."""
    error = validate_move_command(ELEMENT_ARM, 0.1, -0.01, ELEMENT_LIMITS)

    assert error == 'duration_sec must be greater than or equal to 0.0'
