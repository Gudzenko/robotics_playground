from world_builder.room import Room
from world_builder.wall import solid_wall_x, wall_with_door_y, wall_with_door_x, wall_gap
from world_builder.door_frame import door_frame_x, door_frame_y
from world_builder.floor import room_floor
from world_builder.furniture import shelf_y
from world_builder.constants import C_OUTER, C_INNER

# Room B: left room 5x5m
# Interior: x[-9, -4], y[-0.5, 4.5]
# Doors: B↔A (east), B↔D (north, x=-6.5), B↔G (west, y=2.0)


def build():
    r = Room("room_b")

    r.add(room_floor("floor_b", -9.75, 3.0, 7.5, 7.5, (0.83, 0.79, 0.71)))

    r.add(solid_wall_x("wall_b_s", -0.825, -13.575, -6.075, C_OUTER))
    r.add(*wall_with_door_y("wall_b_w", -13.575, -0.75, 6.75, 3.0, C_INNER))
    r.add(*door_frame_y("frm_bg", -13.575, 3.0))
    r.add(wall_gap("wall_b_e_gap", -6.075, 6.0, 6.75, C_INNER))
    r.add(*wall_with_door_x("wall_b_n", 6.825, -13.575, -6.075, -9.75, C_INNER))
    r.add(*door_frame_x("frm_bd", 6.825, -9.75))

    r.add(*shelf_y("shelf_b", 0.75, -13.5, +1))

    return r
