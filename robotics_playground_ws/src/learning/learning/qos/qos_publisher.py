import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from learning.constants import TOPIC_QOS

RELIABILITY_MAP = {
    'reliable': ReliabilityPolicy.RELIABLE,
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
}


class QosPublisher(Node):

    def __init__(self, reliability: str):
        super().__init__('qos_publisher')
        self._seq = 0

        qos = QoSProfile(
            reliability=RELIABILITY_MAP[reliability],
            depth=10,
        )

        self._publisher = self.create_publisher(String, TOPIC_QOS, qos)
        self._timer = self.create_timer(0.2, self._publish)
        self.get_logger().info(f'Publishing with reliability={reliability} at 5 Hz')

    def _publish(self):
        self._seq += 1
        msg = String()
        msg.data = f'seq={self._seq}'
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')


def main(args=None):
    rclpy.init(args=args)

    reliability = sys.argv[1] if len(sys.argv) > 1 else 'reliable'
    if reliability not in RELIABILITY_MAP:
        print('Usage: qos_publisher <reliable|best_effort>')
        rclpy.shutdown()
        return

    node = QosPublisher(reliability)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
