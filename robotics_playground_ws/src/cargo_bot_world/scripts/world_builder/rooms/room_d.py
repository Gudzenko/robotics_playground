from world_builder.constants import C_INNER, C_OUTER
from world_builder.door_frame import door_frame_y
from world_builder.floor import room_floor
from world_builder.furniture import chair, desk, plant
from world_builder.room import Room
from world_builder.wall import solid_wall_x, solid_wall_y, wall_with_door_y

# Room D: back-left room 5x5m (office)
# Interior: x[-9, -4], y[4.5, 9.5]
# Doors: D↔B (south), D↔corridor (east, y=7.0)


def build():
    r = Room('room_d')

    r.add(room_floor('floor_d', -9.75, 10.5, 7.5, 7.5, (0.76, 0.83, 0.71)))

    r.add(solid_wall_y('wall_d_w', -13.575, 6.75, 14.25, C_OUTER))
    r.add(solid_wall_x('wall_d_n', 14.325, -13.725, -6.0, C_OUTER))
    r.add(*wall_with_door_y('wall_d_e', -6.075, 6.75, 14.25, 10.5, C_INNER))
    r.add(*door_frame_y('frm_dc', -6.075, 10.5))

    r.add(*desk('desk_d1',   -11.25, 9.3,   facing='x'))
    r.add(*chair('chair_d1',  -12.0,  8.25,  back_dir='-y'))
    r.add(*desk('desk_d2',    -8.7,  12.75,  facing='y'))
    r.add(*chair('chair_d2',  -7.5,  12.75,  back_dir='+x'))
    r.add(*plant('plant_d', -12.75, 13.2))

    return r
