from .constants import (
    C_FRAME,
    DOOR_H,
    DOOR_HW,
    DOOR_W,
    FRAME_LINTEL_H,
    FRAME_POST_D,
    FRAME_POST_W,
)
from .sdf_helpers import visual_link

_POST_Z = DOOR_H / 2
_LINTEL_Z = DOOR_H + FRAME_LINTEL_H / 2
_OFFSET = DOOR_HW + FRAME_POST_W / 2


def door_frame_y(name, wall_x, door_y, color=C_FRAME):
    """Create a door frame for a wall parallel to the Y axis."""
    lintel_len = DOOR_W + FRAME_POST_W
    left = visual_link(
        f'{name}_l',
        (wall_x, door_y - _OFFSET, _POST_Z),
        (FRAME_POST_D, FRAME_POST_W, DOOR_H),
        color,
    )
    right = visual_link(
        f'{name}_r',
        (wall_x, door_y + _OFFSET, _POST_Z),
        (FRAME_POST_D, FRAME_POST_W, DOOR_H),
        color,
    )
    lintel = visual_link(
        f'{name}_t',
        (wall_x, door_y, _LINTEL_Z),
        (FRAME_POST_D, lintel_len, FRAME_LINTEL_H),
        color,
    )
    return left, right, lintel


def door_frame_x(name, wall_y, door_x, color=C_FRAME):
    """Create a door frame for a wall parallel to the X axis."""
    lintel_len = DOOR_W + FRAME_POST_W
    left = visual_link(
        f'{name}_l',
        (door_x - _OFFSET, wall_y, _POST_Z),
        (FRAME_POST_W, FRAME_POST_D, DOOR_H),
        color,
    )
    right = visual_link(
        f'{name}_r',
        (door_x + _OFFSET, wall_y, _POST_Z),
        (FRAME_POST_W, FRAME_POST_D, DOOR_H),
        color,
    )
    lintel = visual_link(
        f'{name}_t',
        (door_x, wall_y, _LINTEL_Z),
        (lintel_len, FRAME_POST_D, FRAME_LINTEL_H),
        color,
    )
    return left, right, lintel
