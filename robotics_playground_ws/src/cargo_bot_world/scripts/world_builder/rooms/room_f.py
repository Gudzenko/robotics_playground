from world_builder.room import Room
from world_builder.wall import solid_wall_y, solid_wall_x
from world_builder.floor import room_floor
from world_builder.furniture import shelf_y, shelf_x, floor_box
from world_builder.constants import C_OUTER

# Room F: dead-end room east of C, 5x5m
# Interior: x[9, 14], y[-0.5, 4.5]
# Door: F↔C (west, handled by room_c)


def build():
    r = Room("room_f")

    r.add(room_floor("floor_f", 17.25, 3.0, 7.5, 7.5, (0.78, 0.71, 0.83)))

    r.add(solid_wall_x("wall_f_s", -0.825, 13.575, 21.075, C_OUTER))
    r.add(solid_wall_y("wall_f_e", 21.075, -0.75, 6.75, C_OUTER))
    r.add(solid_wall_x("wall_f_n",  6.825, 13.575, 21.075, C_OUTER))

    r.add(*shelf_y("shelf_f1",  0.75, 21.0, -1))
    r.add(*shelf_y("shelf_f2",  3.75, 21.0, -1))
    r.add(*shelf_x("shelf_f3", 17.25,  6.75, -1))

    # Boxes near south and north walls — clear of entry path (door at y=3.0)
    r.add(*floor_box("fbox_f1", 14.5, -0.2, size=0.60))
    r.add(*floor_box("fbox_f2", 14.5,  6.2, size=0.55))
    r.add(*floor_box("fbox_f3", 20.0,  5.5, size=0.58))

    return r
