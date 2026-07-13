import sys

from geometry_msgs.msg import Point
from learning.constants import SERVICE_SET_PATROL_POINTS
from learning_interfaces.srv import SetPatrolPoints
import rclpy
from rclpy.node import Node


class PatrolPointsClient(Node):

    def __init__(self):
        super().__init__('patrol_points_client')
        self._client = self.create_client(SetPatrolPoints, SERVICE_SET_PATROL_POINTS)

    def send(self, points: list[Point]):
        if not self._client.wait_for_service(timeout_sec=3.0):
            self.get_logger().error('patrol_points_server not available')
            return

        request = SetPatrolPoints.Request()
        request.points = points

        future = self._client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()

        if response.success:
            self.get_logger().info(
                f'Route accepted: {response.points_accepted} points — {response.message}'
            )
        else:
            self.get_logger().error(f'Rejected: {response.message}')


def _parse_points(args: list[str]) -> list[Point]:
    points = []
    for arg in args:
        coords = arg.split(',')
        p = Point()
        p.x = float(coords[0])
        p.y = float(coords[1]) if len(coords) > 1 else 0.0
        p.z = float(coords[2]) if len(coords) > 2 else 0.0
        points.append(p)
    return points


def main(args=None):
    rclpy.init(args=args)

    raw = sys.argv[1:]
    if not raw:
        print('Usage: ci_set_patrol_points x1,y1 x2,y2 x3,y3 ...')
        print('Example: ci_set_patrol_points 0,0 1,0 1,1 0,1')
        rclpy.shutdown()
        return

    points = _parse_points(raw)
    node = PatrolPointsClient()
    node.send(points)
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
