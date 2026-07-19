"""Relay ideal lidar measurements to the stable navigation topic."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from cargo_bot.sensor_noise import (
    apply_lidar_noise,
    load_noise_profile,
    seeded_generator,
)
from cargo_bot.sensor_sources import resolve_source_topic
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    qos_profile_sensor_data,
    QoSProfile,
    ReliabilityPolicy,
)
from sensor_msgs.msg import LaserScan
import yaml


def load_lidar_topics(config_path=None):
    """Return source and output lidar topics from the shared sensor config."""
    if config_path is None:
        package_share = Path(get_package_share_directory('cargo_bot'))
        config_path = package_share / 'config' / 'sensors.yaml'

    with Path(config_path).open(encoding='utf-8') as config_file:
        lidar_config = yaml.safe_load(config_file)['lidar']

    source_topic = lidar_config['source_topic']
    output_topic = lidar_config['output_topic']
    if not source_topic or not output_topic or source_topic == output_topic:
        raise ValueError('Lidar source and output topics must be non-empty and different')
    return source_topic, output_topic


class LidarRelay(Node):
    """Publish unchanged ideal scans under the stable navigation topic."""

    def __init__(self):
        super().__init__('lidar_relay')
        _, output_topic = load_lidar_topics()
        selected_source = self.declare_parameter('source', 'gazebo').value
        source_topic = resolve_source_topic('lidar', selected_source)
        selected_profile = self.declare_parameter('profile', 'ideal').value
        self._profile, seed, self._noise = load_noise_profile(
            'lidar',
            selected_profile,
        )
        self._generator = seeded_generator(seed)
        output_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._publisher = self.create_publisher(
            LaserScan,
            output_topic,
            output_qos,
        )
        self._subscription = self.create_subscription(
            LaserScan,
            source_topic,
            self._relay_scan,
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            f'Lidar relay started [{self._profile}/{selected_source}]: '
            f'{source_topic} -> {output_topic}',
        )

    def _relay_scan(self, message):
        message.ranges = apply_lidar_noise(
            message.ranges,
            message.range_min,
            message.range_max,
            self._noise,
            self._generator,
        )
        self._publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = LidarRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError as error:
        if 'Unable to convert call argument' not in str(error):
            raise
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        rclpy.try_shutdown()
