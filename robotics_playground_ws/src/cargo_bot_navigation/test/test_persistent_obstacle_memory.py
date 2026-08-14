"""Tests for evidence-based persistent obstacle memory."""

import math
from types import SimpleNamespace

from cargo_bot_navigation.persistent_obstacle_memory import (
    PersistentObstacleGrid,
)


def scan(ranges, angle_min=0.0, angle_increment=0.1):
    """Create the LaserScan fields used by the pure grid model."""
    return SimpleNamespace(
        ranges=ranges,
        angle_min=angle_min,
        angle_increment=angle_increment,
        range_min=0.05,
        range_max=12.0,
    )


def test_hit_remains_when_later_scan_does_not_observe_its_direction():
    grid = PersistentObstacleGrid(resolution=0.05, maximum_range=12.0)
    grid.update(0.0, 0.0, 0.0, scan([2.0]))
    remembered = set(grid.cells)

    grid.update(0.0, 0.0, 0.0, scan([math.inf], angle_min=1.0))

    assert grid.cells == remembered


def test_hit_is_removed_only_when_a_ray_passes_through_its_cell():
    grid = PersistentObstacleGrid(resolution=0.05, maximum_range=12.0)
    grid.update(
        0.0, 0.0, 0.0,
        scan([math.inf, math.inf, 2.0, math.inf, math.inf], -0.2),
    )
    assert grid.cells

    grid.update(
        0.0, 0.0, 0.0,
        scan([math.inf, math.inf, 1.0, math.inf, math.inf], -0.2),
    )
    assert (20, 0) in grid.cells
    assert (40, 0) in grid.cells

    for _ in range(3):
        grid.update(
            0.0, 0.0, 0.0,
            scan([math.inf] * 5, -0.2),
        )
    assert not grid.cells


def test_current_obstacle_ray_preserves_observed_surface():
    grid = PersistentObstacleGrid(resolution=0.05, maximum_range=12.0)
    grid.update(0.0, 0.0, 0.0, scan([2.0, 2.0, 2.0]))
    for _ in range(5):
        grid.update(0.0, 0.0, 0.0, scan([math.inf, 2.0, math.inf]))

    assert (40, 4) in grid.cells
    assert len(grid.cells) >= 10


def test_map_cells_follow_sensor_pose_and_heading():
    grid = PersistentObstacleGrid(resolution=0.05, maximum_range=12.0)

    grid.update(1.0, 2.0, math.pi / 2.0, scan([1.0]))

    assert (20, 60) in grid.cells
