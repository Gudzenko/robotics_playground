import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from learning.constants import TOPIC_COMMAND


class CommandSubscriber(Node):

    def __init__(self):
        super().__init__('command_subscriber')
        self._subscription = self.create_subscription(
            String,
            TOPIC_COMMAND,
            self._on_command,
            10
        )

    def _on_command(self, msg: String):
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = CommandSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
