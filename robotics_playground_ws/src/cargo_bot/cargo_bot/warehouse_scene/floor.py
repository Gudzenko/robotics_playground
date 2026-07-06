from cargo_bot.warehouse_scene.marker_helpers import make_cube_marker


FLOOR_MARKER_ID = 1
FLOOR_LENGTH = 14.0
FLOOR_WIDTH = 9.0
FLOOR_THICKNESS = 0.02


def make_floor_marker(frame_id, stamp):
    return make_cube_marker(
        frame_id=frame_id,
        stamp=stamp,
        namespace='warehouse_floor',
        marker_id=FLOOR_MARKER_ID,
        position={
            'x': 0.0,
            'y': 0.0,
            'z': -0.02,
        },
        scale={
            'x': FLOOR_LENGTH,
            'y': FLOOR_WIDTH,
            'z': FLOOR_THICKNESS,
        },
        color={
            'r': 0.18,
            'g': 0.20,
            'b': 0.22,
            'a': 1.0,
        },
    )
