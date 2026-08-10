"""Read-independent writers for standard ROS occupancy-map artifacts."""

from math import atan2
from pathlib import Path


def occupancy_to_pgm(message):
    """Encode an OccupancyGrid as a binary PGM using ROS map conventions."""
    width = int(message.info.width)
    height = int(message.info.height)
    if width <= 0 or height <= 0:
        raise ValueError('occupancy map dimensions must be positive')
    if len(message.data) != width * height:
        raise ValueError('occupancy map data length does not match its dimensions')

    pixels = bytearray()
    for row in range(height - 1, -1, -1):
        offset = row * width
        for value in message.data[offset:offset + width]:
            if value < 0:
                pixels.append(205)
            elif value >= 65:
                pixels.append(0)
            elif value <= 19:
                pixels.append(254)
            else:
                pixels.append(205)
    header = f'P5\n# CREATOR: cargo_bot_navigation\n{width} {height}\n255\n'
    return header.encode('ascii') + bytes(pixels)


def occupancy_metadata(message, image_name):
    """Return portable YAML text describing an OccupancyGrid image."""
    origin = message.info.origin
    quaternion = origin.orientation
    yaw = atan2(
        2.0 * (
            quaternion.w * quaternion.z
            + quaternion.x * quaternion.y
        ),
        1.0 - 2.0 * (
            quaternion.y * quaternion.y
            + quaternion.z * quaternion.z
        ),
    )
    return (
        f'image: {image_name}\n'
        'mode: trinary\n'
        f'resolution: {message.info.resolution:.12g}\n'
        'origin: '
        f'[{origin.position.x:.12g}, {origin.position.y:.12g}, {yaw:.12g}]\n'
        'negate: 0\n'
        'occupied_thresh: 0.65\n'
        'free_thresh: 0.196\n'
    )


def write_occupancy_map(message, base_path):
    """Atomically write PGM and YAML files and return both final paths."""
    base_path = Path(base_path)
    pgm_path = base_path.with_suffix('.pgm')
    yaml_path = base_path.with_suffix('.yaml')
    pgm_temporary = base_path.with_suffix('.pgm.tmp')
    yaml_temporary = base_path.with_suffix('.yaml.tmp')

    pgm_temporary.write_bytes(occupancy_to_pgm(message))
    yaml_temporary.write_text(
        occupancy_metadata(message, pgm_path.name),
        encoding='utf-8',
    )
    pgm_temporary.replace(pgm_path)
    yaml_temporary.replace(yaml_path)
    return yaml_path, pgm_path
