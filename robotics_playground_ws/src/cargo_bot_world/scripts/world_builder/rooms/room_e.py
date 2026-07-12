from world_builder.room import Room
from world_builder.wall import solid_wall_y, solid_wall_x, wall_with_door_y
from world_builder.door_frame import door_frame_y
from world_builder.floor import room_floor
from world_builder.furniture import desk, chair, plant
from world_builder.constants import C_OUTER, C_INNER

# Room E: back-right room 5x5m (office)
# Interior: x[4, 9], y[4.5, 9.5]
# Doors: E↔C (south), E↔corridor (west, y=7.0)


def build():
    r = Room("room_e")

    r.add(room_floor("floor_e", 9.75, 10.5, 7.5, 7.5, (0.83, 0.76, 0.71)))

    r.add(solid_wall_y("wall_e_e", 13.575, 6.75, 14.25, C_OUTER))
    r.add(solid_wall_x("wall_e_n", 14.325, 6.0, 13.725, C_OUTER))
    r.add(*wall_with_door_y("wall_e_w", 6.075, 6.75, 14.25, 10.5, C_INNER))
    r.add(*door_frame_y("frm_ec", 6.075, 10.5))

    r.add(*desk("desk_e1",   9.75,  9.0,   facing='x'))
    r.add(*chair("chair_e1", 9.75,  8.1,   back_dir='-y'))
    r.add(*desk("desk_e2",  12.0,  12.75,  facing='y'))
    r.add(*chair("chair_e2", 10.8, 12.75,  back_dir='-x'))
    r.add(*plant("plant_e", 12.75, 13.2))

    return r
