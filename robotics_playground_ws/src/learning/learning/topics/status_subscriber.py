import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from learning.constants import TOPIC_STATUS


class StatusSubscriber(Node):

    def __init__(self):
        super().__init__('status_subscriber')
        self._subscription = self.create_subscription(
            String,
            TOPIC_STATUS,
            self._on_status,
            10
        )

    def _on_status(self, msg: String):
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = StatusSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
