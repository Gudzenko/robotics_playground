"""Retain lidar obstacles until a later scan confirms that their cells are free."""

from collections import deque
import math
import time

from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    qos_profile_sensor_data,
    QoSProfile,
    ReliabilityPolicy,
)
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener


class PendingScanBuffer:
    """Keep scans until their timestamped transform becomes available."""

    def __init__(self, maximum_size=30, maximum_age=1.0):
        self.maximum_size = maximum_size
        self.maximum_age = maximum_age
        self._scans = deque()

    def add(self, scan, received_at=None):
        if received_at is None:
            received_at = time.monotonic()
        self._scans.append((received_at, scan))
        while len(self._scans) > self.maximum_size:
            self._scans.popleft()

    def resolve(self, transform_for_scan, now=None):
        if now is None:
            now = time.monotonic()
        ready = []
        pending = deque()
        expired = 0
        while self._scans:
            received_at, scan = self._scans.popleft()
            transform = transform_for_scan(scan)
            if transform is not None:
                ready.append((scan, transform))
            elif now - received_at <= self.maximum_age:
                pending.append((received_at, scan))
            else:
                expired += 1
        self._scans = pending
        return ready, expired


class PersistentObstacleGrid:
    """Store quantized hit cells and clear them only with free-ray evidence."""

    def __init__(
        self, resolution=0.05, maximum_range=12.0,
        clear_confirmations=10, clear_radius=0.10, minimum_range=0.80,
    ):
        self.resolution = resolution
        self.maximum_range = maximum_range
        self.minimum_range = minimum_range
        self.clear_confirmations = clear_confirmations
        self.clear_radius = clear_radius
        self.cells = set()
        self._clear_counts = {}

    def _cell(self, x, y):
        return (
            round(x / self.resolution),
            round(y / self.resolution),
        )

    def points(self):
        return [
            (column * self.resolution, row * self.resolution, 0.20)
            for column, row in self.cells
        ]

    def update(self, origin_x, origin_y, yaw, scan, ignored_cells=None):
        """Apply clearing rays first and then remember current finite hits."""
        cosine = math.cos(yaw)
        sine = math.sin(yaw)
        margin = self.resolution * 0.75
        current_cells = set()
        for index, measured in enumerate(scan.ranges):
            if not math.isfinite(measured):
                continue
            if measured < self.minimum_range or measured > self.maximum_range:
                continue
            angle = scan.angle_min + index * scan.angle_increment + yaw
            world_x = origin_x + measured * math.cos(angle)
            world_y = origin_y + measured * math.sin(angle)
            current_cells.add(self._cell(world_x, world_y))
        if ignored_cells:
            current_cells.difference_update(ignored_cells)
        cleared = set()
        for cell in self.cells:
            world_x = cell[0] * self.resolution
            world_y = cell[1] * self.resolution
            dx = world_x - origin_x
            dy = world_y - origin_y
            local_x = cosine * dx + sine * dy
            local_y = -sine * dx + cosine * dy
            distance = math.hypot(local_x, local_y)
            angle = math.atan2(local_y, local_x)
            index = round((angle - scan.angle_min) / scan.angle_increment)
            if not 0 <= index < len(scan.ranges):
                continue
            visible_range = min(scan.range_max, self.maximum_range)
            ray_radius = self.resolution * 1.5
            angular_radius = math.atan2(ray_radius, max(distance, 0.01))
            beam_radius = max(
                1, math.ceil(angular_radius / abs(scan.angle_increment)),
            )
            start = max(0, index - beam_radius)
            stop = min(len(scan.ranges), index + beam_radius + 1)
            measurements = scan.ranges[start:stop]
            confirmed_free = measurements and all(
                (math.isinf(measured) and distance <= visible_range)
                or (math.isfinite(measured) and measured > distance + margin)
                for measured in measurements
            )
            if confirmed_free:
                count = self._clear_counts.get(cell, 0) + 1
                self._clear_counts[cell] = count
                if count >= self.clear_confirmations:
                    cleared.add(cell)
            else:
                self._clear_counts.pop(cell, None)
        self.cells.difference_update(cleared)
        for cell in cleared:
            self._clear_counts.pop(cell, None)

        mark_radius = math.ceil(self.clear_radius / self.resolution)
        for column, row in current_cells:
            for dx in range(-mark_radius, mark_radius + 1):
                for dy in range(-mark_radius, mark_radius + 1):
                    if dx * dx + dy * dy > mark_radius * mark_radius:
                        continue
                    cell = (column + dx, row + dy)
                    self.cells.add(cell)
                    self._clear_counts.pop(cell, None)


class PersistentObstacleMemory(Node):
    """Convert public lidar scans into a persistent map-frame point cloud."""

    def __init__(self):
        super().__init__('persistent_obstacle_memory')
        resolution = float(self.declare_parameter('resolution', 0.05).value)
        maximum_range = float(
            self.declare_parameter('maximum_range', 12.0).value,
        )
        self._map_frame = self.declare_parameter('map_frame', 'map').value
        self._grid = PersistentObstacleGrid(resolution, maximum_range)
        self._map = None
        self._static_cells = set()
        self._last_update_ns = None
        self._last_publish_ns = None
        self._pending_scans = PendingScanBuffer()
        self._expired_scans = 0
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        self._publisher = self.create_publisher(
            OccupancyGrid, '/persistent_obstacle_map', 10,
        )
        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(
            OccupancyGrid, '/map', self._map_callback, map_qos,
        )
        self.create_subscription(
            LaserScan, '/scan', self._scan, qos_profile_sensor_data,
        )
        self.create_timer(0.02, self._retry_pending_scans)

    def _map_callback(self, message):
        self._map = message
        self._static_cells = set()
        info = message.info
        for index, value in enumerate(message.data):
            if value < 65:
                continue
            column = index % info.width
            row = index // info.width
            world_x = info.origin.position.x + (column + 0.5) * info.resolution
            world_y = info.origin.position.y + (row + 0.5) * info.resolution
            static_cell = self._grid._cell(world_x, world_y)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    self._static_cells.add((
                        static_cell[0] + dx, static_cell[1] + dy,
                    ))

    def _remove_static_cells(self):
        info = self._map.info
        dynamic_cells = set()
        for cell in self._grid.cells:
            world_x = cell[0] * self._grid.resolution
            world_y = cell[1] * self._grid.resolution
            column = int(
                (world_x - info.origin.position.x) / info.resolution
            )
            row = int(
                (world_y - info.origin.position.y) / info.resolution
            )
            if not 0 <= column < info.width or not 0 <= row < info.height:
                continue
            if self._map.data[row * info.width + column] < 65:
                dynamic_cells.add(cell)
        self._grid.cells = dynamic_cells

    def _scan(self, scan):
        self._pending_scans.add(scan)

    def _transform_for_scan(self, scan):
        try:
            return self._tf_buffer.lookup_transform(
                self._map_frame,
                scan.header.frame_id,
                rclpy.time.Time.from_msg(scan.header.stamp),
                timeout=Duration(),
            )
        except TransformException:
            try:
                return self._tf_buffer.lookup_transform(
                    self._map_frame,
                    scan.header.frame_id,
                    rclpy.time.Time(),
                    timeout=Duration(),
                )
            except TransformException:
                return None

    def _retry_pending_scans(self):
        ready, expired = self._pending_scans.resolve(
            self._transform_for_scan,
        )
        self._expired_scans += expired
        if expired:
            self.get_logger().warning(
                f'Dropped {self._expired_scans} lidar scans after waiting '
                '1.0 s for TF',
                throttle_duration_sec=5.0,
            )
        for scan, transform in ready:
            self._process_scan(scan, transform)

    def _process_scan(self, scan, transform):
        stamp_ns = (
            scan.header.stamp.sec * 1_000_000_000
            + scan.header.stamp.nanosec
        )
        if (
            self._last_update_ns is not None
            and stamp_ns - self._last_update_ns < 200_000_000
        ):
            return
        self._last_update_ns = stamp_ns
        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = math.atan2(
            2.0 * (rotation.w * rotation.z + rotation.x * rotation.y),
            1.0 - 2.0 * (rotation.y * rotation.y + rotation.z * rotation.z),
        )
        self._grid.update(
            translation.x, translation.y, yaw, scan, self._static_cells,
        )
        if self._map is None:
            return
        self._remove_static_cells()
        if (
            self._last_publish_ns is not None
            and stamp_ns - self._last_publish_ns < 500_000_000
        ):
            return
        self._last_publish_ns = stamp_ns
        message = OccupancyGrid()
        message.header.frame_id = self._map_frame
        message.header.stamp = scan.header.stamp
        message.info = self._map.info
        message.data = [0] * (message.info.width * message.info.height)
        for world_x, world_y, _ in self._grid.points():
            column = int(
                (world_x - message.info.origin.position.x)
                / message.info.resolution
            )
            row = int(
                (world_y - message.info.origin.position.y)
                / message.info.resolution
            )
            if 0 <= column < message.info.width and 0 <= row < message.info.height:
                message.data[row * message.info.width + column] = 100
        self._publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = PersistentObstacleMemory()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
