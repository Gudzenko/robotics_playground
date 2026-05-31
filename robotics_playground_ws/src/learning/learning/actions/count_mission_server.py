import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from example_interfaces.action import Fibonacci
from learning.constants import ACTION_COUNT_MISSION


class CountMissionServer(Node):

    def __init__(self):
        super().__init__('count_mission_server')
        self._busy = False
        self._action_server = ActionServer(
            self,
            Fibonacci,
            ACTION_COUNT_MISSION,
            execute_callback=self._execute,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )
        self.get_logger().info('Count mission server is ready.')

    def _goal_callback(self, goal_request):
        if self._busy:
            self.get_logger().warn('Server is busy, rejecting goal')
            return GoalResponse.REJECT
        self.get_logger().info(f'Received goal: order={goal_request.order}')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel requested — accepted')
        return CancelResponse.ACCEPT

    def _execute(self, goal_handle):
        self._busy = True
        order = goal_handle.request.order
        self.get_logger().info(f'Executing: {order} steps')

        sequence = [0, 1]
        feedback = Fibonacci.Feedback()

        for i in range(1, order):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Mission cancelled')
                self._busy = False
                return Fibonacci.Result()

            sequence.append(sequence[i] + sequence[i - 1])
            feedback.sequence = sequence
            goal_handle.publish_feedback(feedback)
            self.get_logger().info(f'Step {i}/{order - 1}: {sequence}')
            time.sleep(0.5)

        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = sequence
        self.get_logger().info(f'Mission complete: {sequence}')
        self._busy = False
        return result


def main(args=None):
    rclpy.init(args=args)
    node = CountMissionServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
