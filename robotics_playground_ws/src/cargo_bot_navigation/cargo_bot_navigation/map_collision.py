"""Check a rectangular robot footprint against an occupancy grid."""

import math


FOOTPRINT = (-0.585, 0.49, -0.33, 0.33)


def footprint_overlaps_occupied(grid, x, y, yaw, occupied_threshold=65):
    """Return true when an occupied cell centre lies inside the footprint."""
    info = grid.info
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    corners = (
        (FOOTPRINT[0], FOOTPRINT[2]),
        (FOOTPRINT[0], FOOTPRINT[3]),
        (FOOTPRINT[1], FOOTPRINT[2]),
        (FOOTPRINT[1], FOOTPRINT[3]),
    )
    world = tuple(
        (
            x + local_x * cos_yaw - local_y * sin_yaw,
            y + local_x * sin_yaw + local_y * cos_yaw,
        )
        for local_x, local_y in corners
    )
    origin_x = info.origin.position.x
    origin_y = info.origin.position.y
    resolution = info.resolution
    min_column = max(0, int((min(point[0] for point in world) - origin_x) / resolution))
    max_column = min(
        info.width - 1,
        int((max(point[0] for point in world) - origin_x) / resolution),
    )
    min_row = max(0, int((min(point[1] for point in world) - origin_y) / resolution))
    max_row = min(
        info.height - 1,
        int((max(point[1] for point in world) - origin_y) / resolution),
    )
    for row in range(min_row, max_row + 1):
        cell_y = origin_y + (row + 0.5) * resolution
        for column in range(min_column, max_column + 1):
            if grid.data[row * info.width + column] < occupied_threshold:
                continue
            cell_x = origin_x + (column + 0.5) * resolution
            delta_x = cell_x - x
            delta_y = cell_y - y
            local_x = cos_yaw * delta_x + sin_yaw * delta_y
            local_y = -sin_yaw * delta_x + cos_yaw * delta_y
            if (
                FOOTPRINT[0] <= local_x <= FOOTPRINT[1]
                and FOOTPRINT[2] <= local_y <= FOOTPRINT[3]
            ):
                return True
    return False
