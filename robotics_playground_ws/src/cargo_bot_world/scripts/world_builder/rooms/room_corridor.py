from world_builder.room import Room
from world_builder.wall import solid_wall_x
from world_builder.floor import room_floor
from world_builder.constants import C_OUTER

# Corridor: connects D and E, 8x2m
# Interior: x[-4, 4], y[6, 8]
# Doors: corridor↔D (west, handled by room_d), corridor↔E (east, handled by room_e)


def build():
    r = Room("room_corridor")

    r.add(room_floor("floor_corridor", 0.0, 10.5, 12.15, 3.0, (0.72, 0.72, 0.74)))

    r.add(solid_wall_x("wall_cor_n", 12.075, -6.075, 6.075, C_OUTER))
    r.add(solid_wall_x("wall_cor_s",  8.925, -6.075, 6.075, C_OUTER))

    return r
