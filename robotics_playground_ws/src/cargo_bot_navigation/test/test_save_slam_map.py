"""Tests for safe parameterized SLAM map output paths."""

from pathlib import Path

from cargo_bot_navigation.save_slam_map import validate_map_target
import pytest


def test_map_target_accepts_changeable_name_and_directory(tmp_path):
    """Map name and output directory should form one absolute base path."""
    assert validate_map_target('office_level_2', tmp_path) == (
        tmp_path / 'office_level_2'
    )


@pytest.mark.parametrize('name', ['', '../map', 'room/map', ' map', '.hidden'])
def test_map_target_rejects_unsafe_names(tmp_path, name):
    """Map names should not escape or obscure the selected directory."""
    with pytest.raises(ValueError):
        validate_map_target(name, tmp_path)


def test_map_target_refuses_existing_artifacts_by_default(tmp_path):
    """A canonical map should not be overwritten without explicit approval."""
    existing = tmp_path / 'indoor_rooms.yaml'
    existing.write_text('image: indoor_rooms.pgm\n', encoding='utf-8')

    with pytest.raises(FileExistsError, match='indoor_rooms.yaml'):
        validate_map_target('indoor_rooms', tmp_path)


def test_map_target_allows_explicit_overwrite(tmp_path):
    """Experimental reruns may opt into replacement explicitly."""
    Path(tmp_path / 'indoor_rooms.posegraph').touch()
    assert validate_map_target('indoor_rooms', tmp_path, overwrite=True) == (
        tmp_path / 'indoor_rooms'
    )
