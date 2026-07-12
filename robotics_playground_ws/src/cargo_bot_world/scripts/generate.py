"""
Generate all room model.sdf files from room definitions.

Usage (from scripts/ directory):
    python3 generate.py

Each room module in world_builder/rooms/ must export a build() -> Room function.
Generated files are written to ../models/{room_name}/model.sdf
"""

import os
import sys
import importlib

ROOMS = [
    'building_ground',
    'room_a',
    'room_b',
    'room_c',
    'room_d',
    'room_e',
    'room_f',
    'room_g',
    'room_corridor',
]

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

MODEL_DESCRIPTIONS = {
    'building_ground': 'Outdoor ground plane',
    'room_a':          'Entry hall (8x8m). Doors: outside, B, C.',
    'room_b':          'Left room (5x5m). Doors: A, D, G(dead-end).',
    'room_c':          'Right room (5x5m). Doors: A, E, F(dead-end).',
    'room_d':          'Back-left room (5x5m). Doors: B, corridor.',
    'room_e':          'Back-right room (5x5m). Doors: C, corridor.',
    'room_f':          'Dead-end room east of C (5x5m).',
    'room_g':          'Dead-end room west of B (5x5m).',
    'room_corridor':   'Corridor connecting D and E (8x2m).',
}

CONFIG_TEMPLATE = '''\
<?xml version="1.0"?>
<model>
  <name>{name}</name>
  <version>1.0</version>
  <sdf version="1.8">model.sdf</sdf>
  <description>{description}</description>
</model>
'''


def main():
    sys.path.insert(0, os.path.dirname(__file__))

    for room_name in ROOMS:
        module = importlib.import_module(f'world_builder.rooms.{room_name}')
        room = module.build()
        sdf = room.to_sdf()

        out_dir = os.path.normpath(os.path.join(MODELS_DIR, room_name))
        os.makedirs(out_dir, exist_ok=True)

        sdf_path = os.path.join(out_dir, 'model.sdf')
        with open(sdf_path, 'w') as f:
            f.write(sdf)

        cfg_path = os.path.join(out_dir, 'model.config')
        with open(cfg_path, 'w') as f:
            f.write(CONFIG_TEMPLATE.format(
                name=room_name,
                description=MODEL_DESCRIPTIONS.get(room_name, ''),
            ))

        link_count = sdf.count('<link name=')
        print(f'  {room_name:20s}  {link_count:2d} links  →  {os.path.relpath(sdf_path)}')

    print(f'\nGenerated {len(ROOMS)} models.')


if __name__ == '__main__':
    main()
