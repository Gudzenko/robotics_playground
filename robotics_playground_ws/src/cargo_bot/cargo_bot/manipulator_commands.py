"""Pure helpers for manipulator command interpolation and validation."""

import math

from cargo_bot.cargo_bot_geometry import LIMIT_LOWER_KEY, LIMIT_UPPER_KEY
from cargo_bot.manipulator_constants import MANIPULATOR_ELEMENTS


def interpolate_position(start_position, target_position, progress):
    """Interpolate between positions with progress clamped from zero to one."""
    bounded_progress = min(max(progress, 0.0), 1.0)
    return start_position + ((target_position - start_position) * bounded_progress)


def validate_move_command(
    element,
    position,
    duration_sec,
    element_limits,
    element_is_moving=False,
):
    """Return an error message for an invalid command or an empty string."""
    if element not in MANIPULATOR_ELEMENTS:
        allowed_elements = ', '.join(MANIPULATOR_ELEMENTS)
        return f"unknown element '{element}'. Allowed: {allowed_elements}"

    if element not in element_limits:
        return f"limits for element '{element}' are not available"

    if element_is_moving:
        return f"element '{element}' is already moving"

    if not math.isfinite(position):
        return 'position must be a finite number'

    limits = element_limits[element]
    if (
        position < limits[LIMIT_LOWER_KEY]
        or position > limits[LIMIT_UPPER_KEY]
    ):
        return (
            f"position for element '{element}' must be between "
            f'{limits[LIMIT_LOWER_KEY]} and {limits[LIMIT_UPPER_KEY]}'
        )

    if not math.isfinite(duration_sec):
        return 'duration_sec must be a finite number'

    if duration_sec < 0.0:
        return 'duration_sec must be greater than or equal to 0.0'

    return ''
