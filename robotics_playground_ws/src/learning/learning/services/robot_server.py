import random
import time

from example_interfaces.srv import SetBool
from learning.constants import SERVICE_GET_STATUS, SERVICE_RESET
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class RobotServer(Node):

    def __init__(self):
        super().__init__('robot_server')
        self._start_time = time.time()
        self._reset_count = 0

        self._reset_service = self.create_service(SetBool, SERVICE_RESET, self._handle_reset)
        self._status_service = self.create_service(
            Trigger,
            SERVICE_GET_STATUS,
            self._handle_get_status,
        )

        self.get_logger().info('Robot server is ready.')

    def _handle_reset(self, request: SetBool.Request, response: SetBool.Response):
        delay = round(random.uniform(2.0, 6.0), 2)
        self.get_logger().info(f'Processing reset... (delay: {delay}s)')
        time.sleep(delay)

        if request.data:
            self._reset_count += 1
            self._start_time = time.time()
            response.success = True
            response.message = f'Reset completed (total resets: {self._reset_count})'
        else:
            response.success = False
            response.message = 'Reset skipped'

        self.get_logger().info(f'Done in {delay}s -> {response.message}')
        return response

    def _handle_get_status(self, request: Trigger.Request, response: Trigger.Response):
        uptime = round(time.time() - self._start_time, 1)
        response.success = True
        response.message = f'uptime={uptime}s; resets={self._reset_count}'
        self.get_logger().info(f'Status requested -> {response.message}')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = RobotServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
