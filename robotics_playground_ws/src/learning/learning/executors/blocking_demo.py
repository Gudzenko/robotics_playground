import sys
import time

import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor, SingleThreadedExecutor
from rclpy.node import Node


class BlockingDemo(Node):

    def __init__(self, mode: str):
        super().__init__('blocking_demo')

        if mode == 'multi':
            group = ReentrantCallbackGroup()
        else:
            group = MutuallyExclusiveCallbackGroup()

        self._fast_count = 0
        self._slow_count = 0

        self.create_timer(0.5, self._fast_callback, callback_group=group)
        self.create_timer(2.0, self._slow_callback, callback_group=group)

        self.get_logger().info(f'Mode: {mode}')

    def _fast_callback(self):
        self._fast_count += 1
        self.get_logger().info(f'[fast #{self._fast_count}] tick')

    def _slow_callback(self):
        self._slow_count += 1
        count = self._slow_count
        self.get_logger().info(f'[slow #{count}] started — sleeping 3s')
        time.sleep(3)
        self.get_logger().info(f'[slow #{count}] done')


def main(args=None):
    rclpy.init(args=args)

    mode = sys.argv[1] if len(sys.argv) > 1 else 'single'
    if mode not in ('single', 'multi'):
        print('Usage: executors_blocking_demo <single|multi>')
        rclpy.shutdown()
        return

    node = BlockingDemo(mode)

    if mode == 'single':
        executor = SingleThreadedExecutor()
    else:
        executor = MultiThreadedExecutor(num_threads=2)

    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
