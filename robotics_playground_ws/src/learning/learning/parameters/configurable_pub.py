import random

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import String

from learning.constants import TOPIC_STATUS


class ConfigurablePub(Node):

    def __init__(self):
        super().__init__('configurable_pub')

        self.declare_parameter('publish_rate', 1.0)
        self.declare_parameter('robot_name', 'robot_1')
        self.declare_parameter('max_speed', 1.0)

        self._battery = 100.0
        self._mode_index = 0
        self._modes = ['manual', 'auto']

        self._publisher = self.create_publisher(String, TOPIC_STATUS, 10)
        self._timer = self._create_timer()

        self.add_on_set_parameters_callback(self._on_param_change)

        self.get_logger().info(
            f'Started: rate={self._publish_rate()} Hz, '
            f'robot={self._robot_name()!r}, '
            f'max_speed={self._max_speed()}'
        )

    def _publish_rate(self) -> float:
        return self.get_parameter('publish_rate').get_parameter_value().double_value

    def _robot_name(self) -> str:
        return self.get_parameter('robot_name').get_parameter_value().string_value

    def _max_speed(self) -> float:
        return self.get_parameter('max_speed').get_parameter_value().double_value

    def _create_timer(self):
        period = 1.0 / self._publish_rate()
        return self.create_timer(period, self._publish)

    def _on_param_change(self, params):
        for param in params:
            if param.name == 'publish_rate':
                if param.value <= 0.0:
                    return SetParametersResult(
                        successful=False, reason='publish_rate must be > 0'
                    )
                self._timer.cancel()
                self._timer = self.create_timer(1.0 / param.value, self._publish)
                self.get_logger().info(f'publish_rate changed to {param.value} Hz')

            elif param.name == 'robot_name':
                self.get_logger().info(f'robot_name changed to {param.value!r}')

            elif param.name == 'max_speed':
                self.get_logger().info(f'max_speed changed to {param.value}')

        return SetParametersResult(successful=True)

    def _publish(self):
        dt = 1.0 / self._publish_rate()
        self._battery -= random.uniform(0.5, 1.5) * dt
        if self._battery <= 0.0:
            self._battery = 100.0

        self._mode_index = (self._mode_index + 1) % len(self._modes)
        speed = random.uniform(0.0, self._max_speed())

        msg = String()
        msg.data = (
            f'robot={self._robot_name()}; '
            f'battery={self._battery:.1f}; '
            f'mode={self._modes[self._mode_index]}; '
            f'speed={speed:.2f}'
        )
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = ConfigurablePub()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
