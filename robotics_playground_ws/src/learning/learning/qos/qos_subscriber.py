import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String

from learning.constants import TOPIC_QOS

RELIABILITY_MAP = {
    'reliable': ReliabilityPolicy.RELIABLE,
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
}


class QosSubscriber(Node):

    def __init__(self, reliability: str, depth: int, delay: float):
        super().__init__('qos_subscriber')
        self._delay = delay
        self._received = 0

        qos = QoSProfile(
            reliability=RELIABILITY_MAP[reliability],
            history=HistoryPolicy.KEEP_LAST,
            depth=depth,
        )

        self.create_subscription(String, TOPIC_QOS, self._callback, qos)
        self.get_logger().info(
            f'Subscribing: reliability={reliability}, depth={depth}, delay={delay}s'
        )

    def _callback(self, msg):
        self._received += 1
        self.get_logger().info(f'[#{self._received}] Received: {msg.data}')
        if self._delay > 0:
            time.sleep(self._delay)


def main(args=None):
    rclpy.init(args=args)

    reliability = sys.argv[1] if len(sys.argv) > 1 else 'reliable'
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    if reliability not in RELIABILITY_MAP:
        print('Usage: qos_subscriber <reliable|best_effort> [depth] [delay_sec]')
        rclpy.shutdown()
        return

    node = QosSubscriber(reliability, depth, delay)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
