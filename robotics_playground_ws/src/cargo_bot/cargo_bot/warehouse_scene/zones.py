from cargo_bot.warehouse_scene.marker_helpers import make_cube_marker


LOADING_ZONE_MARKER_ID = 300
LOADING_ZONE_LENGTH = 1.8
LOADING_ZONE_WIDTH = 1.2
LOADING_ZONE_THICKNESS = 0.025


def make_loading_zone_marker(frame_id, stamp):
    return make_cube_marker(
        frame_id=frame_id,
        stamp=stamp,
        namespace='warehouse_loading_zones',
        marker_id=LOADING_ZONE_MARKER_ID,
        position={
            'x': -5.5,
            'y': 0.0,
            'z': 0.005,
        },
        scale={
            'x': LOADING_ZONE_LENGTH,
            'y': LOADING_ZONE_WIDTH,
            'z': LOADING_ZONE_THICKNESS,
        },
        color={
            'r': 0.05,
            'g': 0.55,
            'b': 0.34,
            'a': 0.75,
        },
    )
