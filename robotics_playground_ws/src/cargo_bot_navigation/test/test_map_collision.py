"""Tests for occupancy-grid footprint collision checks."""

from cargo_bot_navigation.map_collision import footprint_overlaps_occupied
from nav_msgs.msg import OccupancyGrid


def make_grid():
    grid = OccupancyGrid()
    grid.info.resolution = 0.1
    grid.info.width = 40
    grid.info.height = 40
    grid.info.origin.position.x = -2.0
    grid.info.origin.position.y = -2.0
    grid.data = [0] * (grid.info.width * grid.info.height)
    return grid


def occupy(grid, x, y):
    column = int((x - grid.info.origin.position.x) / grid.info.resolution)
    row = int((y - grid.info.origin.position.y) / grid.info.resolution)
    data = list(grid.data)
    data[row * grid.info.width + column] = 100
    grid.data = data


def test_detects_occupied_cell_inside_axis_aligned_footprint():
    grid = make_grid()
    occupy(grid, 0.4, 0.0)
    assert footprint_overlaps_occupied(grid, 0.0, 0.0, 0.0) is True


def test_ignores_cell_outside_footprint_and_handles_rotation():
    grid = make_grid()
    occupy(grid, 0.0, -0.5)
    assert footprint_overlaps_occupied(grid, 0.0, 0.0, 0.0) is False
    assert footprint_overlaps_occupied(grid, 0.0, 0.0, 1.5708) is True
