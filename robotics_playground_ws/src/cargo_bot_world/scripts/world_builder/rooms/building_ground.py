from world_builder.floor import ground_plane
from world_builder.room import Room


def build():
    r = Room('building_ground')
    r.add(ground_plane('ground', 0, 4, 60, 40))
    return r
