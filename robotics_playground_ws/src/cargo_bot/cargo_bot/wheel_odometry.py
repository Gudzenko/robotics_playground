"""Derive differential-drive odometry from quantized wheel joint positions."""

from dataclasses import dataclass
import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from cargo_bot.sensor_noise import (
    apply_encoder_noise,
    load_noise_profile,
    seeded_generator,
)
from cargo_bot.sensor_sources import resolve_source_topic
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
import yaml


TAU = 2.0 * math.pi
COVARIANCE_DIAGONAL_INDICES = (0, 7, 14, 21, 28, 35)


def _load_yaml(path):
    with Path(path).open(encoding='utf-8') as config_file:
        return yaml.safe_load(config_file)


def load_encoder_config(sensor_path=None, geometry_path=None):
    """Load and validate encoder topics, resolution, joints and geometry."""
    if sensor_path is None or geometry_path is None:
        package_share = Path(get_package_share_directory('cargo_bot'))
        sensor_path = sensor_path or package_share / 'config' / 'sensors.yaml'
        geometry_path = geometry_path or package_share / 'config' / 'cargo_bot_geometry.yaml'

    sensors = _load_yaml(sensor_path)
    geometry = _load_yaml(geometry_path)
    encoders = dict(sensors['encoders'])
    wheels = geometry['drive_wheels']
    localization = sensors['localization']

    encoders.update({
        'left_joint': wheels['left_joint'],
        'right_joint': wheels['right_joint'],
        'wheel_radius': float(wheels['radius']),
        'wheel_separation': 2.0 * float(wheels['y_offset']),
        'odom_frame': localization['odom_frame'],
        'base_frame': localization['base_frame'],
    })

    topics = (
        encoders['source_topic'],
        encoders['robot_state_topic'],
        encoders['output_topic'],
        encoders['ground_truth_topic'],
    )
    if any(not topic for topic in topics) or len(set(topics)) != len(topics):
        raise ValueError('Encoder topics must be non-empty and different')
    if int(encoders['ticks_per_revolution']) <= 0:
        raise ValueError('ticks_per_revolution must be positive')
    if float(encoders['update_rate']) <= 0.0:
        raise ValueError('update_rate must be positive')
    if encoders['wheel_radius'] <= 0.0 or encoders['wheel_separation'] <= 0.0:
        raise ValueError('Wheel radius and separation must be positive')
    return encoders


def angle_to_ticks(angle, ticks_per_revolution):
    """Quantize a wheel angle to the nearest integer encoder tick."""
    scaled = float(angle) * int(ticks_per_revolution) / TAU
    if not math.isfinite(scaled):
        raise ValueError('Wheel angle must be finite')
    if scaled >= 0.0:
        return int(math.floor(scaled + 0.5))
    return int(math.ceil(scaled - 0.5))


@dataclass(frozen=True)
class OdometryIncrement:
    """Planar pose and velocity increment from one encoder interval."""

    x: float
    y: float
    yaw: float
    linear_velocity: float
    angular_velocity: float


@dataclass(frozen=True)
class EncoderEstimate:
    """Cumulative pose paired with the newest motion increment."""

    x: float
    y: float
    yaw: float
    increment: OdometryIncrement


def integrate_encoder_ticks(
    left_delta_ticks,
    right_delta_ticks,
    ticks_per_revolution,
    wheel_radius,
    wheel_separation,
    heading,
    delta_time,
):
    """Calculate the exact differential-drive increment for one sample."""
    if delta_time <= 0.0 or not math.isfinite(delta_time):
        raise ValueError('delta_time must be finite and positive')

    meters_per_tick = TAU * wheel_radius / ticks_per_revolution
    left_distance = left_delta_ticks * meters_per_tick
    right_distance = right_delta_ticks * meters_per_tick
    distance = 0.5 * (left_distance + right_distance)
    yaw = (right_distance - left_distance) / wheel_separation

    if abs(yaw) < 1.0e-12:
        body_x = distance
        body_y = 0.0
    else:
        body_x = distance * math.sin(yaw) / yaw
        body_y = distance * (1.0 - math.cos(yaw)) / yaw

    cos_heading = math.cos(heading)
    sin_heading = math.sin(heading)
    return OdometryIncrement(
        x=cos_heading * body_x - sin_heading * body_y,
        y=sin_heading * body_x + cos_heading * body_y,
        yaw=yaw,
        linear_velocity=distance / delta_time,
        angular_velocity=yaw / delta_time,
    )


def stamp_to_seconds(stamp):
    """Convert a ROS timestamp to floating-point seconds."""
    return float(stamp.sec) + float(stamp.nanosec) * 1.0e-9


def covariance_from_diagonal(diagonal):
    """Expand a planar pose/twist diagonal into a ROS 6x6 covariance."""
    if len(diagonal) != 6 or any(float(value) <= 0.0 for value in diagonal):
        raise ValueError('Odometry covariance diagonal must contain six positive values')
    covariance = [0.0] * 36
    for index, value in zip(COVARIANCE_DIAGONAL_INDICES, diagonal):
        covariance[index] = float(value)
    return covariance


class EncoderIntegrator:
    """Stateful, ROS-independent encoder quantization and integration."""

    def __init__(self, config, noise_parameters=None, generator=None):
        self._config = config
        self._noise = noise_parameters or {
            'missed_tick_probability': 0.0,
            'left_scale_error': 0.0,
            'right_scale_error': 0.0,
        }
        self._generator = generator or seeded_generator(0)
        self._previous_ticks = None
        self._previous_time = None
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

    def update(self, positions, sample_time):
        """Process one joint sample, returning None when it is unusable."""
        left_joint = self._config['left_joint']
        right_joint = self._config['right_joint']
        if left_joint not in positions or right_joint not in positions:
            return None
        if not math.isfinite(sample_time):
            return None

        try:
            ticks = (
                angle_to_ticks(positions[left_joint], self._config['ticks_per_revolution']),
                angle_to_ticks(positions[right_joint], self._config['ticks_per_revolution']),
            )
        except (TypeError, ValueError):
            return None

        if self._previous_ticks is None:
            self._previous_ticks = ticks
            self._previous_time = sample_time
            return None

        delta_time = sample_time - self._previous_time
        if delta_time <= 0.0:
            return None
        if delta_time + 1.0e-12 < 1.0 / float(self._config['update_rate']):
            return None

        noisy_delta_ticks = apply_encoder_noise(
            ticks[0] - self._previous_ticks[0],
            ticks[1] - self._previous_ticks[1],
            self._noise,
            self._generator,
        )
        increment = integrate_encoder_ticks(
            noisy_delta_ticks[0],
            noisy_delta_ticks[1],
            self._config['ticks_per_revolution'],
            self._config['wheel_radius'],
            self._config['wheel_separation'],
            self.yaw,
            delta_time,
        )
        self.x += increment.x
        self.y += increment.y
        self.yaw += increment.yaw
        self._previous_ticks = ticks
        self._previous_time = sample_time
        return EncoderEstimate(self.x, self.y, self.yaw, increment)


class WheelOdometry(Node):
    """Publish encoder-derived odometry without owning the odom TF."""

    def __init__(self):
        super().__init__('wheel_odometry')
        self._config = load_encoder_config()
        selected_source = self.declare_parameter('source', 'gazebo').value
        self._config['source_topic'] = resolve_source_topic(
            'encoders',
            selected_source,
        )
        selected_profile = self.declare_parameter('profile', 'ideal').value
        self._profile, seed, noise = load_noise_profile(
            'encoders',
            selected_profile,
        )
        self._integrator = EncoderIntegrator(
            self._config,
            noise,
            seeded_generator(seed),
        )

        self._publisher = self.create_publisher(
            Odometry,
            self._config['output_topic'],
            10,
        )
        self._joint_state_publisher = self.create_publisher(
            JointState,
            self._config['robot_state_topic'],
            10,
        )
        self._subscription = self.create_subscription(
            JointState,
            self._config['source_topic'],
            self._joint_state_callback,
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            f'Wheel odometry started [{self._profile}/{selected_source}]: '
            f"{self._config['source_topic']} -> {self._config['output_topic']} "
            f"({self._config['ticks_per_revolution']} ticks/revolution)",
        )

    def _joint_state_callback(self, message):
        self._joint_state_publisher.publish(message)
        positions = dict(zip(message.name, message.position))
        sample_time = stamp_to_seconds(message.header.stamp)
        estimate = self._integrator.update(positions, sample_time)
        if estimate is not None:
            self._publish(message, estimate)

    def _publish(self, joint_state, estimate):
        message = Odometry()
        message.header.stamp = joint_state.header.stamp
        message.header.frame_id = self._config['odom_frame']
        message.child_frame_id = self._config['base_frame']
        message.pose.pose.position.x = estimate.x
        message.pose.pose.position.y = estimate.y
        message.pose.pose.orientation.z = math.sin(0.5 * estimate.yaw)
        message.pose.pose.orientation.w = math.cos(0.5 * estimate.yaw)
        message.pose.covariance = covariance_from_diagonal(
            self._config['pose_covariance_diagonal'],
        )
        message.twist.twist.linear.x = estimate.increment.linear_velocity
        message.twist.twist.angular.z = estimate.increment.angular_velocity
        message.twist.covariance = covariance_from_diagonal(
            self._config['twist_covariance_diagonal'],
        )
        self._publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = WheelOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError as error:
        if 'Unable to convert call argument' not in str(error):
            raise
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
