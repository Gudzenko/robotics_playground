"""Publish deterministic sensor fixtures for replaceable-source tests."""

import math

from cargo_bot.sensor_sources import resolve_source_topic
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu, JointState, LaserScan


LIDAR_SAMPLES = 720


def make_mock_scan(stamp):
    """Create one deterministic 360-degree scan with a smooth obstacle pattern."""
    message = LaserScan()
    message.header.stamp = stamp
    message.header.frame_id = 'lidar_link'
    message.angle_min = -math.pi
    message.angle_max = math.pi
    message.angle_increment = 2.0 * math.pi / LIDAR_SAMPLES
    message.scan_time = 1.0 / 15.0
    message.time_increment = message.scan_time / LIDAR_SAMPLES
    message.range_min = 0.15
    message.range_max = 20.0
    message.ranges = [
        4.0 + 0.5 * math.sin(index * 2.0 * math.pi / LIDAR_SAMPLES)
        for index in range(LIDAR_SAMPLES)
    ]
    message.intensities = [1.0] * LIDAR_SAMPLES
    return message


def make_mock_imu(stamp, sample_index):
    """Create deterministic stationary IMU data with a small yaw-rate signal."""
    message = Imu()
    message.header.stamp = stamp
    message.header.frame_id = 'imu_link'
    message.orientation.w = 1.0
    message.angular_velocity.z = 0.05 * math.sin(sample_index * 0.02)
    message.linear_acceleration.z = 9.8
    return message


def make_mock_joint_state(stamp, sample_index):
    """Create deterministic equal wheel angles representing straight motion."""
    message = JointState()
    message.header.stamp = stamp
    message.name = ['left_wheel_joint', 'right_wheel_joint']
    angle = sample_index * 0.01
    message.position = [angle, angle]
    return message


class MockSensorPublisher(Node):
    """Publish reproducible private inputs without a simulator sensor bridge."""

    def __init__(self):
        super().__init__('mock_sensor_publisher')
        self._sample_index = 0
        self._scan_publisher = self.create_publisher(
            LaserScan,
            resolve_source_topic('lidar', 'mock'),
            qos_profile_sensor_data,
        )
        self._imu_publisher = self.create_publisher(
            Imu,
            resolve_source_topic('imu', 'mock'),
            qos_profile_sensor_data,
        )
        self._joint_publisher = self.create_publisher(
            JointState,
            resolve_source_topic('encoders', 'mock'),
            qos_profile_sensor_data,
        )
        self._scan_timer = self.create_timer(1.0 / 15.0, self._publish_scan)
        self._motion_timer = self.create_timer(1.0 / 50.0, self._publish_motion)
        self.get_logger().info('Deterministic mock sensor publisher started')

    def _publish_scan(self):
        self._scan_publisher.publish(make_mock_scan(self.get_clock().now().to_msg()))

    def _publish_motion(self):
        stamp = self.get_clock().now().to_msg()
        self._imu_publisher.publish(make_mock_imu(stamp, self._sample_index))
        self._joint_publisher.publish(
            make_mock_joint_state(stamp, self._sample_index),
        )
        self._sample_index += 1


def main(args=None):
    rclpy.init(args=args)
    node = MockSensorPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        rclpy.try_shutdown()
