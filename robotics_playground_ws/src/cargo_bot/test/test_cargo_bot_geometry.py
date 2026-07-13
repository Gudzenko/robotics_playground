"""Tests for loading and reading the cargo bot geometry configuration."""

from pathlib import Path

from cargo_bot.cargo_bot_geometry import CargoBotGeometry
from cargo_bot.manipulator_constants import (
    ELEMENT_ARM,
    ELEMENT_GRIPPER,
    ELEMENT_LIFT,
    ELEMENT_ROTATION,
)
import pytest


GEOMETRY_PATH = Path(__file__).parents[1] / 'config' / 'cargo_bot_geometry.yaml'


def test_manipulator_limits_are_loaded_from_project_geometry():
    """Configured manipulator limits should map to the public element names."""
    limits = CargoBotGeometry(GEOMETRY_PATH).manipulator_limits()

    assert limits == {
        ELEMENT_ROTATION: {'lower': -3.14159, 'upper': 3.14159},
        ELEMENT_LIFT: {'lower': -0.78, 'upper': 0.78},
        ELEMENT_ARM: {'lower': 0.0, 'upper': 0.35},
        ELEMENT_GRIPPER: {'lower': 0.0, 'upper': 0.135},
    }


def test_manipulator_joint_names_are_loaded_from_project_geometry():
    """Configured joints should map to the element controlled by each joint."""
    geometry = CargoBotGeometry(GEOMETRY_PATH)

    assert geometry.manipulator_joint_names() == {
        ELEMENT_ROTATION: 'manipulator_mount_joint',
        ELEMENT_LIFT: 'manipulator_lift_joint',
        ELEMENT_ARM: 'manipulator_arm_joint',
        ELEMENT_GRIPPER: 'manipulator_left_finger_joint',
    }
    assert geometry.gripper_mimic_joint_name() == 'manipulator_right_finger_joint'


def test_passive_wheel_joints_start_at_zero():
    """Both configured drive wheel joints should receive a zero initial position."""
    positions = CargoBotGeometry(GEOMETRY_PATH).passive_joint_positions()

    assert positions == {
        'left_wheel_joint': 0.0,
        'right_wheel_joint': 0.0,
    }


def test_numeric_limit_strings_are_converted_to_float(tmp_path):
    """YAML limit values should be normalized to floats for validation logic."""
    geometry_path = tmp_path / 'geometry.yaml'
    geometry_path.write_text(
        """
manipulator:
  mount: {lower: '-1', upper: '1', joint: mount_joint}
  lift: {lower: '-2', upper: '2', joint: lift_joint}
  arm:
    extension: {lower: '0', upper: '3', joint: arm_joint}
  gripper:
    fingers:
      lower: '0'
      upper: '4'
      left_joint: left_finger_joint
      right_joint: right_finger_joint
drive_wheels:
  left_joint: left_wheel_joint
  right_joint: right_wheel_joint
""".lstrip(),
        encoding='utf-8',
    )

    limits = CargoBotGeometry(geometry_path).manipulator_limits()

    assert limits[ELEMENT_ROTATION] == {'lower': -1.0, 'upper': 1.0}
    assert limits[ELEMENT_GRIPPER] == {'lower': 0.0, 'upper': 4.0}


def test_missing_manipulator_section_is_reported(tmp_path):
    """An incomplete geometry file should fail instead of returning empty limits."""
    geometry_path = tmp_path / 'geometry.yaml'
    geometry_path.write_text('drive_wheels: {}\n', encoding='utf-8')

    with pytest.raises(KeyError, match='manipulator'):
        CargoBotGeometry(geometry_path).manipulator_limits()
