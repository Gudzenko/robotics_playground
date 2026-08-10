"""Unit tests for portable occupancy-map output."""

from pathlib import Path

from cargo_bot_navigation.map_io import (
    occupancy_metadata,
    occupancy_to_pgm,
    write_occupancy_map,
)
from geometry_msgs.msg import Pose
from nav_msgs.msg import OccupancyGrid


def sample_map():
    """Create a small map containing free, occupied and unknown cells."""
    message = OccupancyGrid()
    message.info.width = 3
    message.info.height = 2
    message.info.resolution = 0.05
    message.info.origin = Pose()
    message.info.origin.position.x = -1.0
    message.info.origin.position.y = -2.0
    message.info.origin.orientation.w = 1.0
    message.data = [0, 100, -1, 20, 64, 65]
    return message


def test_pgm_encoding_flips_rows_and_applies_trinary_thresholds():
    """PGM output should follow map-server orientation and cell values."""
    output = occupancy_to_pgm(sample_map())
    assert output.endswith(bytes([205, 205, 0, 254, 0, 205]))
    assert b'3 2\n255\n' in output


def test_metadata_uses_relative_image_and_map_origin():
    """YAML metadata should remain portable with a relative image path."""
    metadata = occupancy_metadata(sample_map(), 'test_map.pgm')
    assert 'image: test_map.pgm' in metadata
    assert 'resolution: 0.05' in metadata
    assert 'origin: [-1, -2, 0]' in metadata


def test_writer_creates_matching_yaml_and_pgm(tmp_path):
    """Both occupancy artifacts should be written under one base name."""
    yaml_path, pgm_path = write_occupancy_map(
        sample_map(),
        tmp_path / 'another_world',
    )
    assert yaml_path == Path(tmp_path / 'another_world.yaml')
    assert pgm_path == Path(tmp_path / 'another_world.pgm')
    assert yaml_path.is_file()
    assert pgm_path.is_file()


def test_pgm_rejects_inconsistent_dimensions():
    """Malformed occupancy messages must not produce partial map files."""
    message = sample_map()
    message.data = [0]
    try:
        occupancy_to_pgm(message)
    except ValueError as error:
        assert 'data length' in str(error)
    else:
        raise AssertionError('expected inconsistent map data to be rejected')
