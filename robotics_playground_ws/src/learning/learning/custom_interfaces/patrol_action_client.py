import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Point
from learning_interfaces.action import Patrol

from learning.constants import ACTION_PATROL


class PatrolClient(Node):

    def __init__(self):
        super().__init__('patrol_client')
        self._action_client = ActionClient(self, Patrol, ACTION_PATROL)
        self._goal_handle = None
        self._done = False

    def send_goal(self, points: list[Point], loops: int):
        if not self._action_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error('Patrol action server not available')
            self._done = True
            return

        goal = Patrol.Goal()
        goal.points = points
        goal.loops = loops

        self.get_logger().info(f'Sending: {len(points)} points, {loops} loop(s)')
        future = self._action_client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def cancel(self):
        if self._goal_handle is not None:
            self.get_logger().info('Cancelling patrol...')
            cancel_future = self._goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, cancel_future, timeout_sec=3.0)

    def _on_goal_response(self, future):
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self.get_logger().error('Goal rejected')
            self._done = True
            return
        self.get_logger().info('Goal accepted — patrol in progress')
        result_future = self._goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

    def _on_feedback(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'[loop {fb.current_loop} point {fb.current_point}] '
            f'{fb.progress_percent:.1f}%'
        )

    def _on_result(self, future):
        result = future.result().result
        self.get_logger().info(
            f'Done: loops_completed={result.loops_completed} '
            f'reason={result.stop_reason}'
        )
        self._done = True


def _parse_args():
    raw = sys.argv[1:]
    loops = 1
    point_args = []
    for arg in raw:
        if arg.startswith('loops='):
            loops = int(arg.split('=')[1])
        else:
            point_args.append(arg)

    points = []
    for arg in point_args:
        coords = arg.split(',')
        p = Point()
        p.x = float(coords[0])
        p.y = float(coords[1]) if len(coords) > 1 else 0.0
        p.z = float(coords[2]) if len(coords) > 2 else 0.0
        points.append(p)
    return points, loops


def main(args=None):
    rclpy.init(args=args)

    points, loops = _parse_args()
    if len(points) < 2:
        print('Usage: ci_patrol_client x1,y1 x2,y2 ... [loops=N]')
        print('Example: ci_patrol_client 0,0 1,0 1,1 0,1 loops=2')
        rclpy.shutdown()
        return

    node = PatrolClient()
    node.send_goal(points, loops)

    try:
        while not node._done and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        node.cancel()
        deadline = time.time() + 3.0
        while not node._done and rclpy.ok() and time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
