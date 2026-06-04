import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from learning_interfaces.action import Patrol

from learning.constants import ACTION_PATROL

MIN_POINTS = 2


class PatrolActionServer(Node):

    def __init__(self):
        super().__init__('patrol_action_server')
        self._action_server = ActionServer(
            self,
            Patrol,
            ACTION_PATROL,
            execute_callback=self._execute,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=ReentrantCallbackGroup(),
        )
        self.get_logger().info('Patrol action server ready')

    def _goal_callback(self, goal_request):
        if len(goal_request.points) < MIN_POINTS:
            self.get_logger().warn(
                f'Goal rejected: need at least {MIN_POINTS} points, '
                f'got {len(goal_request.points)}'
            )
            return GoalResponse.REJECT
        self.get_logger().info(
            f'Goal accepted: {len(goal_request.points)} points, '
            f'{goal_request.loops} loop(s)'
        )
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel request received')
        return CancelResponse.ACCEPT

    def _execute(self, goal_handle):
        points = goal_handle.request.points
        loops = goal_handle.request.loops
        total_steps = len(points) * loops

        step = 0
        for loop in range(loops):
            for point_idx, point in enumerate(points):
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result = Patrol.Result()
                    result.loops_completed = loop
                    result.stop_reason = 'cancelled'
                    self.get_logger().info(f'Patrol cancelled after {loop} complete loop(s)')
                    return result

                self.get_logger().info(
                    f'Loop {loop + 1}/{loops} — moving to point [{point_idx}] '
                    f'x={point.x:.1f} y={point.y:.1f}'
                )
                time.sleep(1.0)
                step += 1

                feedback = Patrol.Feedback()
                feedback.current_loop = loop + 1
                feedback.current_point = point_idx + 1
                feedback.progress_percent = round(step / total_steps * 100.0, 1)
                goal_handle.publish_feedback(feedback)

        goal_handle.succeed()
        result = Patrol.Result()
        result.loops_completed = loops
        result.stop_reason = 'completed'
        self.get_logger().info('Patrol completed successfully')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = PatrolActionServer()
    executor = MultiThreadedExecutor()
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
