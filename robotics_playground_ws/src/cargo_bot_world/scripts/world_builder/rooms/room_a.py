from world_builder.room import Room
from world_builder.wall import solid_wall_x, wall_with_door_y, wall_with_door_x
from world_builder.door_frame import door_frame_x, door_frame_y
from world_builder.floor import room_floor
from world_builder.furniture import shelf_x, plant, floor_box
from world_builder.constants import C_OUTER, C_INNER

# Room A: entry hall 8x8m
# Interior: x[-4, 4], y[-4, 4]
# Doors: entry (south, x=0), A↔B (west, y=2.0), A↔C (east, y=2.0)


def build():
    r = Room("room_a")

    r.add(room_floor("floor_a", 0.0, 0.0, 12.0, 12.0, (0.78, 0.72, 0.60)))

    r.add(*wall_with_door_x("wall_a_s", -6.075, -6.075, 6.075, 0.0, C_OUTER))
    r.add(*door_frame_x("frm_entry", -6.075, 0.0))
    r.add(solid_wall_x("wall_a_n", 6.075, -6.075, 6.075, C_OUTER))
    r.add(*wall_with_door_y("wall_a_w", -6.075, -6.0, 6.0, 3.0, C_INNER))
    r.add(*door_frame_y("frm_ab", -6.075, 3.0))
    r.add(*wall_with_door_y("wall_a_e", 6.075, -6.0, 6.0, 3.0, C_INNER))
    r.add(*door_frame_y("frm_ac", 6.075, 3.0))

    r.add(*shelf_x("shelf_a_r1a", -3.0, -1.95, -1))
    r.add(*shelf_x("shelf_a_r1b",  3.0, -1.95, -1))
    r.add(*shelf_x("shelf_a_r2a", -3.0,  1.95, +1))
    r.add(*shelf_x("shelf_a_r2b",  3.0,  1.95, +1))

    r.add(*plant("plant_a_sw", -5.0, -5.0))
    r.add(*plant("plant_a_se",  5.0, -5.0))
    r.add(*plant("plant_a_nw", -5.0,  5.0))
    r.add(*plant("plant_a_ne",  5.0,  5.0))

    r.add(*floor_box("fbox_a1",  5.5, -4.5))
    r.add(*floor_box("fbox_a2", -5.5, -4.5, size=0.52))

    return r
