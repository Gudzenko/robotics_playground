"""Calculate and publish a global path for each RViz goal without moving."""

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from nav_msgs.msg import Path
import rclpy
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


class PathRequester(Node):
    """Convert `/goal_pose` clicks into planner actions and visible paths."""

    def __init__(self):
        super().__init__('path_requester')
        goal_topic = self.declare_parameter('goal_topic', '/goal_pose').value
        path_topic = self.declare_parameter('path_topic', '/planned_path').value
        action_name = self.declare_parameter(
            'planner_action', '/compute_path_to_pose',
        ).value
        self._planner_id = self.declare_parameter(
            'planner_id', 'GridBased',
        ).value
        self._global_frame = self.declare_parameter(
            'global_frame', 'map',
        ).value
        self._request_generation = 0
        self._active_goal_handle = None
        callback_group = ReentrantCallbackGroup()
        self._action_client = ActionClient(
            self,
            ComputePathToPose,
            action_name,
            callback_group=callback_group,
        )
        path_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._path_publisher = self.create_publisher(Path, path_topic, path_qos)
        self._goal_subscription = self.create_subscription(
            PoseStamped,
            goal_topic,
            self._goal_callback,
            10,
            callback_group=callback_group,
        )
        self.get_logger().info(
            f'Path requester ready: {goal_topic} -> {action_name} -> {path_topic}',
        )

    def _goal_callback(self, goal):
        self._request_generation += 1
        generation = self._request_generation
        self._publish_empty_path()
        if self._active_goal_handle is not None:
            self._active_goal_handle.cancel_goal_async()
            self._active_goal_handle = None
        if not self._action_client.server_is_ready():
            self.get_logger().error(
                'Planner is not ready; the previous path was cleared.',
            )
            return

        request = ComputePathToPose.Goal()
        request.goal = goal
        request.goal.header.frame_id = goal.header.frame_id or self._global_frame
        request.goal.header.stamp = self.get_clock().now().to_msg()
        request.planner_id = self._planner_id
        request.use_start = False
        future = self._action_client.send_goal_async(request)
        future.add_done_callback(
            lambda result: self._goal_response(result, generation),
        )
        self.get_logger().info(
            'Calculating path to '
            f'({goal.pose.position.x:.2f}, {goal.pose.position.y:.2f}).',
        )

    def _goal_response(self, future, generation):
        if generation != self._request_generation:
            return
        try:
            goal_handle = future.result()
        except Exception as error:  # noqa: B902 - ROS future exceptions are runtime-defined
            self.get_logger().error(f'Planner request failed: {error}')
            return
        if not goal_handle.accepted:
            self.get_logger().error('Planner rejected the goal; path remains empty.')
            return
        self._active_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda result: self._path_result(result, generation),
        )

    def _path_result(self, future, generation):
        if generation != self._request_generation:
            return
        self._active_goal_handle = None
        try:
            wrapped_result = future.result()
        except Exception as error:  # noqa: B902 - ROS future exceptions are runtime-defined
            self.get_logger().error(f'Planner result failed: {error}')
            return
        result = wrapped_result.result
        if (
            wrapped_result.status != GoalStatus.STATUS_SUCCEEDED
            or result.error_code != ComputePathToPose.Result.NONE
            or not result.path.poses
        ):
            reason = result.error_msg or f'error code {result.error_code}'
            self.get_logger().error(
                f'No valid path: {reason}. The displayed path was cleared.',
            )
            return
        self._path_publisher.publish(result.path)
        self.get_logger().info(
            f'Path ready with {len(result.path.poses)} poses.',
        )

    def _publish_empty_path(self):
        empty = Path()
        empty.header.frame_id = self._global_frame
        empty.header.stamp = self.get_clock().now().to_msg()
        self._path_publisher.publish(empty)


def main(args=None):
    rclpy.init(args=args)
    node = PathRequester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
