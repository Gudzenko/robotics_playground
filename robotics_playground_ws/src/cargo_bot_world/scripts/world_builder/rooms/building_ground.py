from world_builder.room import Room
from world_builder.floor import ground_plane


def build():
    r = Room("building_ground")
    r.add(ground_plane("ground", 0, 4, 60, 40))
    return r
