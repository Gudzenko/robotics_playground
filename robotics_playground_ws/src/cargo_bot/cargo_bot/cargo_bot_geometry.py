from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from cargo_bot.manipulator_constants import (
    ELEMENT_ARM,
    ELEMENT_GRIPPER,
    ELEMENT_LIFT,
    ELEMENT_ROTATION,
)
import yaml


LIMIT_LOWER_KEY = 'lower'
LIMIT_UPPER_KEY = 'upper'


class CargoBotGeometry:
    def __init__(self, geometry_path=None):
        if geometry_path is None:
            package_share_dir = Path(get_package_share_directory('cargo_bot'))
            geometry_path = package_share_dir / 'config' / 'cargo_bot_geometry.yaml'

        with Path(geometry_path).open('r', encoding='utf-8') as geometry_file:
            self._geometry = yaml.safe_load(geometry_file)

    def manipulator_limits(self):
        manipulator = self._geometry['manipulator']
        return {
            ELEMENT_ROTATION: self._read_limit(manipulator['mount']),
            ELEMENT_LIFT: self._read_limit(manipulator['lift']),
            ELEMENT_ARM: self._read_limit(manipulator['arm']['extension']),
            ELEMENT_GRIPPER: self._read_limit(manipulator['gripper']['fingers']),
        }

    def manipulator_joint_names(self):
        manipulator = self._geometry['manipulator']
        return {
            ELEMENT_ROTATION: manipulator['mount']['joint'],
            ELEMENT_LIFT: manipulator['lift']['joint'],
            ELEMENT_ARM: manipulator['arm']['extension']['joint'],
            ELEMENT_GRIPPER: manipulator['gripper']['fingers']['left_joint'],
        }

    def gripper_mimic_joint_name(self):
        return self._geometry['manipulator']['gripper']['fingers']['right_joint']

    def passive_joint_positions(self):
        return {
            self._geometry['drive_wheels']['left_joint']: 0.0,
            self._geometry['drive_wheels']['right_joint']: 0.0,
        }

    def _read_limit(self, geometry_section):
        return {
            LIMIT_LOWER_KEY: float(geometry_section[LIMIT_LOWER_KEY]),
            LIMIT_UPPER_KEY: float(geometry_section[LIMIT_UPPER_KEY]),
        }
