from .constants import C_GROUND, FLOOR_T, GROUND_T
from .sdf_helpers import solid_link, visual_link


def room_floor(name, cx, cy, width, height, color):
    """Thin decorative floor tile (visual only, no collision)."""
    return visual_link(name, (cx, cy, FLOOR_T / 2), (width, height, FLOOR_T), color)


def ground_plane(name, cx, cy, width, height, color=C_GROUND):
    """Large outdoor ground slab with collision."""
    return solid_link(name, (cx, cy, -GROUND_T / 2), (width, height, GROUND_T), color)
