import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from learning.constants import TOPIC_COMMAND

COMMANDS = ['forward', 'backward', 'left', 'right', 'stop']


class CommandPublisher(Node):

    def __init__(self):
        super().__init__('command_publisher')
        self._publisher = self.create_publisher(String, TOPIC_COMMAND, 10)
        self._timer = self.create_timer(2.0, self._publish_command)
        self._index = 0

    def _publish_command(self):
        msg = String()
        msg.data = COMMANDS[self._index]
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self._index = (self._index + 1) % len(COMMANDS)


def main(args=None):
    rclpy.init(args=args)
    node = CommandPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
