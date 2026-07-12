from world_builder.room import Room
from world_builder.wall import solid_wall_x, wall_with_door_y, wall_with_door_x, wall_gap
from world_builder.door_frame import door_frame_x, door_frame_y
from world_builder.floor import room_floor
from world_builder.furniture import shelf_y
from world_builder.constants import C_OUTER, C_INNER

# Room C: right room 5x5m
# Interior: x[4, 9], y[-0.5, 4.5]
# Doors: C↔A (west), C↔E (north, x=6.5), C↔F (east, y=2.0)


def build():
    r = Room("room_c")

    r.add(room_floor("floor_c", 9.75, 3.0, 7.5, 7.5, (0.71, 0.79, 0.83)))

    r.add(solid_wall_x("wall_c_s", -0.825, 6.075, 13.575, C_OUTER))
    r.add(*wall_with_door_y("wall_c_e", 13.575, -0.75, 6.75, 3.0, C_INNER))
    r.add(*door_frame_y("frm_cf", 13.575, 3.0))
    r.add(wall_gap("wall_c_w_gap", 6.075, 6.0, 6.75, C_INNER))
    r.add(*wall_with_door_x("wall_c_n", 6.825, 6.075, 13.575, 9.75, C_INNER))
    r.add(*door_frame_x("frm_ce", 6.825, 9.75))

    r.add(*shelf_y("shelf_c", 0.75, 13.5, -1))

    return r
