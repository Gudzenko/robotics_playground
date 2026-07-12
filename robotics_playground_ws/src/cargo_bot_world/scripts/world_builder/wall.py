from .constants import WALL_T, WALL_H, DOOR_W, DOOR_H, DOOR_HW, C_OUTER, C_INNER
from .sdf_helpers import solid_link


def solid_wall_y(name, wall_x, y_min, y_max, color=C_OUTER):
    """Solid wall along Y axis at x=wall_x (wall_x is the wall center)."""
    cy = (y_min + y_max) / 2
    length = y_max - y_min
    return solid_link(name, (wall_x, cy, WALL_H / 2), (WALL_T, length, WALL_H), color)


def solid_wall_x(name, wall_y, x_min, x_max, color=C_OUTER):
    """Solid wall along X axis at y=wall_y (wall_y is the wall center)."""
    cx = (x_min + x_max) / 2
    length = x_max - x_min
    return solid_link(name, (cx, wall_y, WALL_H / 2), (length, WALL_T, WALL_H), color)


def wall_with_door_y(name, wall_x, y_min, y_max, door_y, color=C_INNER):
    """Y-axis wall at x=wall_x with a door opening centered at y=door_y.
    Returns three links: bottom segment, top segment, above-door filler."""
    above_h = WALL_H - DOOR_H

    lower_len = (door_y - DOOR_HW) - y_min
    lower_cy  = (y_min + door_y - DOOR_HW) / 2
    lower = solid_link(
        f'{name}_bot',
        (wall_x, lower_cy, WALL_H / 2),
        (WALL_T, lower_len, WALL_H),
        color,
    )

    upper_len = y_max - (door_y + DOOR_HW)
    upper_cy  = (door_y + DOOR_HW + y_max) / 2
    upper = solid_link(
        f'{name}_top',
        (wall_x, upper_cy, WALL_H / 2),
        (WALL_T, upper_len, WALL_H),
        color,
    )

    above = solid_link(
        f'{name}_door_top',
        (wall_x, door_y, DOOR_H + above_h / 2),
        (WALL_T, DOOR_W, above_h),
        color,
    )

    return lower, upper, above


def wall_with_door_x(name, wall_y, x_min, x_max, door_x, color=C_INNER):
    """X-axis wall at y=wall_y with a door opening centered at x=door_x.
    Returns three links: left segment, right segment, above-door filler."""
    above_h = WALL_H - DOOR_H

    left_len = (door_x - DOOR_HW) - x_min
    left_cx  = (x_min + door_x - DOOR_HW) / 2
    left = solid_link(
        f'{name}_l',
        (left_cx, wall_y, WALL_H / 2),
        (left_len, WALL_T, WALL_H),
        color,
    )

    right_len = x_max - (door_x + DOOR_HW)
    right_cx  = (door_x + DOOR_HW + x_max) / 2
    right = solid_link(
        f'{name}_r',
        (right_cx, wall_y, WALL_H / 2),
        (right_len, WALL_T, WALL_H),
        color,
    )

    above = solid_link(
        f'{name}_top',
        (door_x, wall_y, DOOR_H + above_h / 2),
        (DOOR_W, WALL_T, above_h),
        color,
    )

    return left, right, above


def wall_gap(name, wall_x, y_min, y_max, color=C_INNER):
    """Small gap-filling segment on a Y-axis wall."""
    return solid_wall_y(name, wall_x, y_min, y_max, color)
