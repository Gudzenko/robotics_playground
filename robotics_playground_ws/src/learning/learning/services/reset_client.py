import sys
import rclpy
from rclpy.node import Node
from example_interfaces.srv import SetBool
from learning.constants import SERVICE_RESET


class ResetClient(Node):

    def __init__(self):
        super().__init__('reset_client')
        self._client = self.create_client(SetBool, SERVICE_RESET)

    def send_request(self, data: bool):
        while not self._client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for reset server...')

        request = SetBool.Request()
        request.data = data

        future = self._client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        response = future.result()
        self.get_logger().info(
            f'Response: success={response.success}, message="{response.message}"'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ResetClient()

    data = True
    if len(sys.argv) > 1:
        data = sys.argv[1].lower() in ('true', '1', 'yes')

    node.send_request(data)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
