import sys

from rcl_interfaces.msg import Parameter as ParameterMsg
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.parameter_client import AsyncParameterClient

TARGET_NODE = 'configurable_pub'


class ParamClient(Node):

    def __init__(self):
        super().__init__('param_client')
        self._client = AsyncParameterClient(self, TARGET_NODE)

    def get_params(self):
        if not self._client.wait_for_services(timeout_sec=3.0):
            self.get_logger().error(f'Node {TARGET_NODE!r} not available')
            return

        names = ['publish_rate', 'robot_name', 'max_speed']
        future = self._client.get_parameters(names)
        rclpy.spin_until_future_complete(self, future)

        for name, pv in zip(names, future.result().values):
            p = Parameter.from_parameter_msg(ParameterMsg(name=name, value=pv))
            self.get_logger().info(f'{p.name} = {p.value}')

    def set_rate(self, rate: float):
        if not self._client.wait_for_services(timeout_sec=3.0):
            self.get_logger().error(f'Node {TARGET_NODE!r} not available')
            return

        future = self._client.set_parameters([
            Parameter('publish_rate', Parameter.Type.DOUBLE, rate)
        ])
        rclpy.spin_until_future_complete(self, future)

        response = future.result()
        if response.results[0].successful:
            self.get_logger().info(f'publish_rate set to {rate} Hz')
        else:
            self.get_logger().error(f'Failed: {response.results[0].reason}')


def main(args=None):
    rclpy.init(args=args)
    node = ParamClient()

    if len(sys.argv) < 2:
        print('Usage:')
        print('  get             — read publish_rate, robot_name, max_speed')
        print('  set_rate <hz>   — change publish_rate at runtime')
        node.destroy_node()
        rclpy.shutdown()
        return

    command = sys.argv[1]

    if command == 'get':
        node.get_params()
    elif command == 'set_rate':
        rate = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        node.set_rate(rate)
    else:
        print(f'Unknown command: {command}')

    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
