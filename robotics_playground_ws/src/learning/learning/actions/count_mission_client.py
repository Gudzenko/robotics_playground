import sys

from action_msgs.srv import CancelGoal
from example_interfaces.action import Fibonacci
from learning.constants import ACTION_COUNT_MISSION
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node


class CountMissionClient(Node):

    def __init__(self):
        super().__init__('count_mission_client')
        self._client = ActionClient(self, Fibonacci, ACTION_COUNT_MISSION)
        self._cancel_client = self.create_client(
            CancelGoal, f'{ACTION_COUNT_MISSION}/_action/cancel_goal'
        )

    def send_goal(self, order: int):
        self.get_logger().info(f'Sending goal: order={order}')

        if not self._client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error('Action server not available')
            return

        goal = Fibonacci.Goal()
        goal.order = order

        future = self._client.send_goal_async(
            goal,
            feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def cancel_goal(self):
        if not self._cancel_client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error('Action server not available')
            return

        future = self._cancel_client.call_async(CancelGoal.Request())
        rclpy.spin_until_future_complete(self, future)

        response = future.result()
        if response.goals_canceling:
            self.get_logger().info(f'Cancelling {len(response.goals_canceling)} goal(s)')
        else:
            self.get_logger().warn('No active goals to cancel')

    def _on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected by server')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted, waiting for result...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

    def _on_feedback(self, feedback_msg):
        sequence = list(feedback_msg.feedback.sequence)
        self.get_logger().info(f'Feedback: {sequence}')

    def _on_result(self, future):
        result = future.result().result
        status = future.result().status
        if status == 6:  # CANCELED
            self.get_logger().info('Mission was cancelled')
        else:
            self.get_logger().info(f'Result: {list(result.sequence)}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = CountMissionClient()

    if len(sys.argv) < 2:
        print('Usage:')
        print('  send <order>  — send a new goal')
        print('  cancel        — cancel current goal')
        node.destroy_node()
        rclpy.shutdown()
        return

    command = sys.argv[1]

    if command == 'cancel':
        node.cancel_goal()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    elif command == 'send':
        order = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        node.send_goal(order)
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()

    else:
        print(f'Unknown command: {command}')
        node.destroy_node()
        rclpy.shutdown()
