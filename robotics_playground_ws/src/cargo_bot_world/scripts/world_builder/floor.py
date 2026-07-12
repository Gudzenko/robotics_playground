from .constants import FLOOR_T, GROUND_T, C_GROUND
from .sdf_helpers import visual_link, solid_link


def room_floor(name, cx, cy, width, height, color):
    """Thin decorative floor tile (visual only, no collision)."""
    return visual_link(name, (cx, cy, FLOOR_T / 2), (width, height, FLOOR_T), color)


def ground_plane(name, cx, cy, width, height, color=C_GROUND):
    """Large outdoor ground slab with collision."""
    return solid_link(name, (cx, cy, -GROUND_T / 2), (width, height, GROUND_T), color)
