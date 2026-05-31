import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from learning.constants import TOPIC_STATUS


class StatusPublisher(Node):

    def __init__(self):
        super().__init__('status_publisher')
        self._publisher = self.create_publisher(String, TOPIC_STATUS, 10)
        self._timer = self.create_timer(1.0, self._publish_status)

        self._battery = 100.0
        self._modes = ['manual', 'auto']
        self._mode_index = 0

    def _publish_status(self):
        self._battery = max(0.0, self._battery - random.uniform(0.5, 1.5))
        if self._battery == 0.0:
            self._battery = 100.0

        self._mode_index = (self._mode_index + 1) % len(self._modes)
        mode = self._modes[self._mode_index]
        speed = round(random.uniform(0.0, 1.0), 2)

        msg = String()
        msg.data = f'battery={self._battery:.1f}; mode={mode}; speed={speed}'
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = StatusPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
