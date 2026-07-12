from world_builder.room import Room
from world_builder.wall import solid_wall_y, solid_wall_x
from world_builder.floor import room_floor
from world_builder.furniture import shelf_y, shelf_x, floor_box
from world_builder.constants import C_OUTER

# Room G: dead-end room west of B, 5x5m
# Interior: x[-14, -9], y[-0.5, 4.5]
# Door: G↔B (east, handled by room_b)


def build():
    r = Room("room_g")

    r.add(room_floor("floor_g", -17.25, 3.0, 7.5, 7.5, (0.83, 0.80, 0.65)))

    r.add(solid_wall_x("wall_g_s", -0.825, -21.075, -13.575, C_OUTER))
    r.add(solid_wall_y("wall_g_w", -21.075, -0.75, 6.75, C_OUTER))
    r.add(solid_wall_x("wall_g_n",  6.825, -21.075, -13.575, C_OUTER))

    r.add(*shelf_y("shelf_g1",  0.75, -21.0, +1))
    r.add(*shelf_y("shelf_g2",  3.75, -21.0, +1))
    r.add(*shelf_x("shelf_g3", -17.25,  6.75, -1))

    # Boxes near south and north walls — clear of entry path (door at y=3.0)
    r.add(*floor_box("fbox_g1", -14.5, -0.2, size=0.60))
    r.add(*floor_box("fbox_g2", -14.5,  6.2, size=0.55))
    r.add(*floor_box("fbox_g3", -20.0,  5.5, size=0.58))

    return r
