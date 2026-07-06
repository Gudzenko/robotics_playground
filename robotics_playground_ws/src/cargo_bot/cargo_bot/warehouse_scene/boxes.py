from cargo_bot.warehouse_scene.marker_helpers import make_cube_marker


BOX_MARKER_START_ID = 400
BOX_LENGTH = 0.45
BOX_WIDTH = 0.35
BOX_HEIGHT = 0.32
BOX_Z = BOX_HEIGHT / 2.0

BOXES = (
    {
        'id': BOX_MARKER_START_ID,
        'x': -5.0,
        'y': 2.15,
    },
    {
        'id': BOX_MARKER_START_ID + 1,
        'x': -3.7,
        'y': 2.15,
    },
    {
        'id': BOX_MARKER_START_ID + 2,
        'x': 0.0,
        'y': 2.15,
    },
    {
        'id': BOX_MARKER_START_ID + 3,
        'x': -5.0,
        'y': -2.15,
    },
    {
        'id': BOX_MARKER_START_ID + 4,
        'x': 0.0,
        'y': -2.15,
    },
    {
        'id': BOX_MARKER_START_ID + 5,
        'x': -5.5,
        'y': 0.65,
    },
)


def make_box_markers(frame_id, stamp):
    return [
        make_box_marker(frame_id, stamp, box)
        for box in BOXES
    ]


def make_box_marker(frame_id, stamp, box):
    return make_cube_marker(
        frame_id=frame_id,
        stamp=stamp,
        namespace='warehouse_boxes',
        marker_id=box['id'],
        position={
            'x': box['x'],
            'y': box['y'],
            'z': BOX_Z,
        },
        scale={
            'x': BOX_LENGTH,
            'y': BOX_WIDTH,
            'z': BOX_HEIGHT,
        },
        color={
            'r': 0.72,
            'g': 0.46,
            'b': 0.18,
            'a': 1.0,
        },
    )
