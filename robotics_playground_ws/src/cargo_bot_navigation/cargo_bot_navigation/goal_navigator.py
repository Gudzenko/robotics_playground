"""Expose an explicit service that cancels every Nav2 navigation goal."""

from action_msgs.srv import CancelGoal
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from std_srvs.srv import Trigger


def cancellation_accepted(result):
    """Return whether Nav2 accepted at least one active goal cancellation."""
    return (
        result.return_code == CancelGoal.Response.ERROR_NONE
        and bool(result.goals_canceling)
    )


class NavigationCancelService(Node):
    """Cancel NavigateToPose while Nav2 itself consumes RViz `/goal_pose`."""

    def __init__(self):
        super().__init__('navigation_cancel_service')
        action_name = self.declare_parameter(
            'navigate_action', '/navigate_to_pose',
        ).value
        group = ReentrantCallbackGroup()
        cancel_service = f'{action_name.rstrip("/")}/_action/cancel_goal'
        self._client = self.create_client(
            CancelGoal, cancel_service, callback_group=group,
        )
        self._cancel_service = self.create_service(
            Trigger, '/cancel_navigation', self._cancel_callback,
            callback_group=group,
        )
        self.get_logger().info(
            'Navigation cancellation ready on /cancel_navigation; '
            'BT Navigator consumes RViz /goal_pose directly.',
        )

    async def _cancel_callback(self, request, response):
        del request
        if not self._client.service_is_ready():
            response.success = False
            response.message = 'NavigateToPose action server is not ready.'
            return response
        result = await self._client.call_async(CancelGoal.Request())
        response.success = cancellation_accepted(result)
        if response.success:
            response.message = 'Nav2 accepted cancellation of active goals.'
            self.get_logger().info(response.message)
        else:
            response.message = (
                'Nav2 did not accept an active goal for cancellation '
                f'(return_code={result.return_code}).'
            )
            self.get_logger().warning(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = NavigationCancelService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
