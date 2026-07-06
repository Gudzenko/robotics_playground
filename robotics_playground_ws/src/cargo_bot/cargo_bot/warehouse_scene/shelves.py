from cargo_bot.warehouse_scene.marker_helpers import make_cube_marker


SHELF_MARKER_START_ID = 200
SHELF_LENGTH = 2.4
SHELF_WIDTH = 0.55
SHELF_HEIGHT = 1.6
SHELF_Z = SHELF_HEIGHT / 2.0

SHELVES = (
    {
        'id': SHELF_MARKER_START_ID,
        'x': -4.0,
        'y': 2.8,
    },
    {
        'id': SHELF_MARKER_START_ID + 1,
        'x': 0.5,
        'y': 2.8,
    },
    {
        'id': SHELF_MARKER_START_ID + 2,
        'x': -4.0,
        'y': -2.8,
    },
    {
        'id': SHELF_MARKER_START_ID + 3,
        'x': 0.5,
        'y': -2.8,
    },
)


def make_shelf_markers(frame_id, stamp):
    return [
        make_shelf_marker(frame_id, stamp, shelf)
        for shelf in SHELVES
    ]


def make_shelf_marker(frame_id, stamp, shelf):
    return make_cube_marker(
        frame_id=frame_id,
        stamp=stamp,
        namespace='warehouse_shelves',
        marker_id=shelf['id'],
        position={
            'x': shelf['x'],
            'y': shelf['y'],
            'z': SHELF_Z,
        },
        scale={
            'x': SHELF_LENGTH,
            'y': SHELF_WIDTH,
            'z': SHELF_HEIGHT,
        },
        color={
            'r': 0.30,
            'g': 0.36,
            'b': 0.42,
            'a': 1.0,
        },
    )
