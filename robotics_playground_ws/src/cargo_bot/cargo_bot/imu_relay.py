"""Relay ideal IMU measurements to the stable navigation topic."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from cargo_bot.sensor_noise import ImuNoiseModel, load_noise_profile, seeded_generator
from cargo_bot.sensor_sources import resolve_source_topic
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    qos_profile_sensor_data,
    QoSProfile,
    ReliabilityPolicy,
)
from sensor_msgs.msg import Imu
import yaml


COVARIANCE_SIZE = 9
COVARIANCE_DIAGONAL_INDICES = (0, 4, 8)


def load_imu_config(config_path=None):
    """Load and validate the shared ideal IMU topic and covariance contract."""
    if config_path is None:
        package_share = Path(get_package_share_directory('cargo_bot'))
        config_path = package_share / 'config' / 'sensors.yaml'

    with Path(config_path).open(encoding='utf-8') as config_file:
        imu_config = yaml.safe_load(config_file)['imu']

    source_topic = imu_config['source_topic']
    output_topic = imu_config['output_topic']
    if not source_topic or not output_topic or source_topic == output_topic:
        raise ValueError('IMU source and output topics must be non-empty and different')

    for key in (
        'orientation_covariance_diagonal',
        'angular_velocity_covariance_diagonal',
        'linear_acceleration_covariance_diagonal',
    ):
        diagonal = imu_config[key]
        if len(diagonal) != 3 or any(value <= 0.0 for value in diagonal):
            raise ValueError(f'{key} must contain three positive values')

    return imu_config


def covariance_from_diagonal(diagonal):
    """Expand a three-element diagonal into a ROS 3x3 covariance array."""
    covariance = [0.0] * COVARIANCE_SIZE
    for index, value in zip(COVARIANCE_DIAGONAL_INDICES, diagonal):
        covariance[index] = float(value)
    return covariance


def apply_ideal_covariances(message, imu_config):
    """Apply the explicit ideal-sensor covariance policy to an IMU message."""
    message.orientation_covariance = covariance_from_diagonal(
        imu_config['orientation_covariance_diagonal'],
    )
    message.angular_velocity_covariance = covariance_from_diagonal(
        imu_config['angular_velocity_covariance_diagonal'],
    )
    message.linear_acceleration_covariance = covariance_from_diagonal(
        imu_config['linear_acceleration_covariance_diagonal'],
    )
    return message


def apply_noise_covariances(message, imu_config, noise_config):
    """Raise IMU covariance diagonals to cover configured white noise."""
    apply_ideal_covariances(message, imu_config)
    angular_variances = [
        float(stddev) ** 2
        for stddev in noise_config['angular_velocity_stddev']
    ]
    acceleration_variances = [
        float(stddev) ** 2
        for stddev in noise_config['linear_acceleration_stddev']
    ]
    message.angular_velocity_covariance = covariance_from_diagonal([
        max(base, noise)
        for base, noise in zip(
            imu_config['angular_velocity_covariance_diagonal'],
            angular_variances,
        )
    ])
    message.linear_acceleration_covariance = covariance_from_diagonal([
        max(base, noise)
        for base, noise in zip(
            imu_config['linear_acceleration_covariance_diagonal'],
            acceleration_variances,
        )
    ])
    return message


class ImuRelay(Node):
    """Publish ideal IMU data with explicit covariance under the stable topic."""

    def __init__(self):
        super().__init__('imu_relay')
        self._config = load_imu_config()
        selected_source = self.declare_parameter('source', 'gazebo').value
        self._config['source_topic'] = resolve_source_topic('imu', selected_source)
        selected_profile = self.declare_parameter('profile', 'ideal').value
        self._profile, seed, self._noise = load_noise_profile(
            'imu', selected_profile,
        )
        self._noise_model = ImuNoiseModel(self._noise, seeded_generator(seed))
        output_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._publisher = self.create_publisher(
            Imu,
            self._config['output_topic'],
            output_qos,
        )
        self._subscription = self.create_subscription(
            Imu,
            self._config['source_topic'],
            self._relay_imu,
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            f'IMU relay started [{self._profile}/{selected_source}]: '
            f"{self._config['source_topic']} -> {self._config['output_topic']}",
        )

    def _relay_imu(self, message):
        angular, acceleration = self._noise_model.apply(
            (
                message.angular_velocity.x,
                message.angular_velocity.y,
                message.angular_velocity.z,
            ),
            (
                message.linear_acceleration.x,
                message.linear_acceleration.y,
                message.linear_acceleration.z,
            ),
        )
        (
            message.angular_velocity.x,
            message.angular_velocity.y,
            message.angular_velocity.z,
        ) = angular
        (
            message.linear_acceleration.x,
            message.linear_acceleration.y,
            message.linear_acceleration.z,
        ) = acceleration
        self._publisher.publish(
            apply_noise_covariances(message, self._config, self._noise),
        )


def main(args=None):
    rclpy.init(args=args)
    node = ImuRelay()
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
