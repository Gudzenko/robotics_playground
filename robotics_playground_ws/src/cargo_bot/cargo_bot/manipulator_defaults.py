from cargo_bot.manipulator_constants import (
    ELEMENT_ARM,
    ELEMENT_GRIPPER,
    ELEMENT_LIFT,
    ELEMENT_ROTATION,
)
from cargo_bot.manipulator_statuses import STATUS_DONE


INITIAL_POSITIONS = {
    ELEMENT_ROTATION: 0.0,
    ELEMENT_LIFT: 0.0,
    ELEMENT_ARM: 0.0,
    ELEMENT_GRIPPER: 0.0,
}

INITIAL_MOVING = False
INITIAL_OPERATION_ID = ''
INITIAL_STATUS = STATUS_DONE
