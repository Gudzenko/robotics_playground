import random

from learning.constants import TOPIC_ROBOT_STATUS
from learning_interfaces.msg import RobotStatus
import rclpy
from rclpy.node import Node

MODES = ['manual', 'auto', 'idle']


class RobotStatusPublisher(Node):

    def __init__(self):
        super().__init__('robot_status_publisher')
        self._publisher = self.create_publisher(RobotStatus, TOPIC_ROBOT_STATUS, 10)
        self._timer = self.create_timer(1.0, self._publish)
        self._battery = 100.0
        self._mode_index = 0
        self.get_logger().info('Robot status publisher started')

    def _publish(self):
        self._battery -= random.uniform(0.5, 1.5)
        self._battery = max(self._battery, 0.0)
        self._mode_index = (self._mode_index + 1) % len(MODES)

        msg = RobotStatus()
        msg.battery_percent = round(self._battery, 1)
        msg.speed = round(random.uniform(0.0, 1.0), 2)
        msg.mode = MODES[self._mode_index]
        msg.is_healthy = self._battery > 10.0

        self._publisher.publish(msg)
        self.get_logger().info(
            f'battery={msg.battery_percent}% speed={msg.speed} '
            f'mode={msg.mode} healthy={msg.is_healthy}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
