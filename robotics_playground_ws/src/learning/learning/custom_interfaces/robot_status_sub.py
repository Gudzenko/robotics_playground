import rclpy
from rclpy.node import Node
from learning_interfaces.msg import RobotStatus

from learning.constants import TOPIC_ROBOT_STATUS


class RobotStatusSubscriber(Node):

    def __init__(self):
        super().__init__('robot_status_subscriber')
        self.create_subscription(RobotStatus, TOPIC_ROBOT_STATUS, self._callback, 10)
        self.get_logger().info('Listening for robot status...')

    def _callback(self, msg: RobotStatus):
        health = 'OK' if msg.is_healthy else 'UNHEALTHY'
        self.get_logger().info(
            f'[{health}] battery={msg.battery_percent}% '
            f'speed={msg.speed} mode={msg.mode}'
        )
        if not msg.is_healthy:
            self.get_logger().warn('Robot health check failed — battery critical')


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
