import random

import rclpy
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn
from std_msgs.msg import String

from learning.constants import TOPIC_SENSOR


class ManagedSensor(LifecycleNode):

    def __init__(self):
        super().__init__('managed_sensor')
        self._publisher = None
        self._timer = None
        self._temperature = 20.0

    def on_configure(self, state) -> TransitionCallbackReturn:
        self._publisher = self.create_lifecycle_publisher(String, TOPIC_SENSOR, 10)
        self._temperature = 20.0
        self.get_logger().info('Sensor configured')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state) -> TransitionCallbackReturn:
        super().on_activate(state)
        self._timer = self.create_timer(1.0, self._publish)
        self.get_logger().info('Sensor activated — publishing started')
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state) -> TransitionCallbackReturn:
        self._timer.cancel()
        self._timer.destroy()
        self._timer = None
        super().on_deactivate(state)
        self.get_logger().info('Sensor deactivated — publishing stopped')
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state) -> TransitionCallbackReturn:
        self._publisher.destroy()
        self._publisher = None
        self.get_logger().info('Sensor cleaned up')
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state) -> TransitionCallbackReturn:
        self.get_logger().info('Sensor shutting down')
        return TransitionCallbackReturn.SUCCESS

    def _publish(self):
        self._temperature += random.uniform(-0.5, 0.5)
        msg = String()
        msg.data = f'temperature={self._temperature:.1f}; status=ok'
        self._publisher.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = ManagedSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
