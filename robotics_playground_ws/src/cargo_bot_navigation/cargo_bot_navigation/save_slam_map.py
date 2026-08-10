"""Save an occupancy map and SLAM Toolbox pose graph under one safe base name."""

import os
from pathlib import Path
import re
import sys
import time

from cargo_bot_navigation.map_io import write_occupancy_map
from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from slam_toolbox.srv import SerializePoseGraph


MAP_NAME_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')
KNOWN_SUFFIXES = ('.yaml', '.pgm', '.png', '.posegraph', '.data')


def default_output_directory():
    """Return the writable default used for experimental map outputs."""
    ros_home = os.environ.get('ROS_HOME')
    if ros_home:
        return Path(ros_home).expanduser() / 'cargo_bot' / 'maps'
    return Path.home() / '.ros' / 'cargo_bot' / 'maps'


def validate_map_target(map_name, output_directory, overwrite=False):
    """Validate a requested map target and return its absolute base path."""
    if not MAP_NAME_PATTERN.fullmatch(map_name):
        raise ValueError(
            'map_name must contain only letters, digits, dot, underscore or dash '
            'and must start with a letter or digit',
        )

    directory = Path(output_directory).expanduser().resolve()
    base_path = directory / map_name
    existing = [
        base_path.with_suffix(suffix)
        for suffix in KNOWN_SUFFIXES
        if base_path.with_suffix(suffix).exists()
    ]
    if existing and not overwrite:
        names = ', '.join(path.name for path in existing)
        raise FileExistsError(f'refusing to overwrite existing map files: {names}')
    return base_path


class SlamMapSaver(Node):
    """Call both SLAM Toolbox save services with a shared output base path."""

    def __init__(self):
        super().__init__('cargo_bot_slam_map_saver')
        self.declare_parameter('map_name', 'indoor_rooms')
        self.declare_parameter(
            'map_output_dir',
            str(default_output_directory()),
        )
        self.declare_parameter('overwrite', False)
        self.declare_parameter('service_timeout', 10.0)
        self.declare_parameter('map_timeout', 10.0)
        self.map = None
        map_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.map_subscription = self.create_subscription(
            OccupancyGrid,
            '/map',
            self._map_callback,
            map_qos,
        )

    def save(self):
        """Save the occupancy map and pose graph, returning their base path."""
        map_name = self.get_parameter('map_name').value
        output_directory = self.get_parameter('map_output_dir').value
        overwrite = self.get_parameter('overwrite').value
        timeout = float(self.get_parameter('service_timeout').value)
        map_timeout = float(self.get_parameter('map_timeout').value)
        base_path = validate_map_target(map_name, output_directory, overwrite)
        base_path.parent.mkdir(parents=True, exist_ok=True)

        self._wait_for_map(map_timeout)
        graph_client = self.create_client(
            SerializePoseGraph,
            '/slam_toolbox/serialize_map',
        )
        self._wait_for_service(graph_client, timeout)

        graph_request = SerializePoseGraph.Request()
        graph_request.filename = str(base_path)
        graph_response = self._call(graph_client, graph_request, timeout)
        if graph_response.result != SerializePoseGraph.Response.RESULT_SUCCESS:
            raise RuntimeError(
                f'pose graph save failed with result {graph_response.result}',
            )
        write_occupancy_map(self.map, base_path)
        return base_path

    def _map_callback(self, message):
        self.map = message

    def _wait_for_map(self, timeout):
        deadline = time.monotonic() + timeout
        while self.map is None and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.2)
        if self.map is None:
            raise TimeoutError('no occupancy map received on /map')

    def _wait_for_service(self, client, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if client.wait_for_service(timeout_sec=0.2):
                return
        raise TimeoutError(f'service {client.srv_name} is not available')

    def _call(self, client, request, timeout):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
        if not future.done():
            raise TimeoutError(f'service {client.srv_name} did not respond')
        if future.exception() is not None:
            raise RuntimeError(
                f'service {client.srv_name} failed: {future.exception()}',
            )
        return future.result()


def main(args=None):
    """Run the parameter-driven one-shot map saver."""
    rclpy.init(args=args)
    node = SlamMapSaver()
    exit_code = 0
    try:
        base_path = node.save()
        node.get_logger().info(f'saved map and pose graph as {base_path}')
    except (FileExistsError, OSError, RuntimeError, TimeoutError, ValueError) as error:
        node.get_logger().error(str(error))
        exit_code = 1
    finally:
        node.destroy_node()
        rclpy.shutdown()
    if exit_code:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
