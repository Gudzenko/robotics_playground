from cargo_bot.warehouse_scene.floor import FLOOR_LENGTH, FLOOR_WIDTH
from cargo_bot.warehouse_scene.marker_helpers import make_cube_marker


WALL_MARKER_START_ID = 100
WALL_THICKNESS = 0.08
WALL_HEIGHT = 0.9
WALL_Z = WALL_HEIGHT / 2.0


def make_boundary_wall_markers(frame_id, stamp):
    half_length = FLOOR_LENGTH / 2.0
    half_width = FLOOR_WIDTH / 2.0

    walls = (
        {
            'id': WALL_MARKER_START_ID,
            'x': 0.0,
            'y': half_width,
            'length': FLOOR_LENGTH,
            'width': WALL_THICKNESS,
        },
        {
            'id': WALL_MARKER_START_ID + 1,
            'x': 0.0,
            'y': -half_width,
            'length': FLOOR_LENGTH,
            'width': WALL_THICKNESS,
        },
        {
            'id': WALL_MARKER_START_ID + 2,
            'x': half_length,
            'y': 0.0,
            'length': WALL_THICKNESS,
            'width': FLOOR_WIDTH,
        },
        {
            'id': WALL_MARKER_START_ID + 3,
            'x': -half_length,
            'y': 0.0,
            'length': WALL_THICKNESS,
            'width': FLOOR_WIDTH,
        },
    )

    return [
        make_wall_marker(frame_id, stamp, wall)
        for wall in walls
    ]


def make_wall_marker(frame_id, stamp, wall):
    return make_cube_marker(
        frame_id=frame_id,
        stamp=stamp,
        namespace='warehouse_boundary_walls',
        marker_id=wall['id'],
        position={
            'x': wall['x'],
            'y': wall['y'],
            'z': WALL_Z,
        },
        scale={
            'x': wall['length'],
            'y': wall['width'],
            'z': WALL_HEIGHT,
        },
        color={
            'r': 0.55,
            'g': 0.58,
            'b': 0.62,
            'a': 1.0,
        },
    )
