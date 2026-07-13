from learning.constants import SERVICE_GET_STATUS
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class StatusClient(Node):

    def __init__(self):
        super().__init__('status_client')
        self._client = self.create_client(Trigger, SERVICE_GET_STATUS)

    def send_request(self):
        while not self._client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for status server...')

        future = self._client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future)

        response = future.result()
        self.get_logger().info(
            f'Response: success={response.success}, message="{response.message}"'
        )


def main(args=None):
    rclpy.init(args=args)
    node = StatusClient()
    node.send_request()
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
