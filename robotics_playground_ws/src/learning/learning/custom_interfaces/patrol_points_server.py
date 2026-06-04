import rclpy
from rclpy.node import Node
from learning_interfaces.srv import SetPatrolPoints

from learning.constants import SERVICE_SET_PATROL_POINTS

MIN_POINTS = 2


class PatrolPointsServer(Node):

    def __init__(self):
        super().__init__('patrol_points_server')
        self._patrol_points = []
        self._srv = self.create_service(
            SetPatrolPoints, SERVICE_SET_PATROL_POINTS, self._handle_set_points
        )
        self.get_logger().info('Patrol points server ready')

    def _handle_set_points(self, request, response):
        points = request.points
        if len(points) < MIN_POINTS:
            response.success = False
            response.message = f'Need at least {MIN_POINTS} points, got {len(points)}'
            response.points_accepted = 0
            self.get_logger().warn(response.message)
            return response

        self._patrol_points = list(points)
        response.success = True
        response.points_accepted = len(points)
        response.message = f'Patrol route set with {len(points)} points'

        for i, p in enumerate(points):
            self.get_logger().info(f'  point[{i}]: x={p.x:.2f} y={p.y:.2f} z={p.z:.2f}')
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PatrolPointsServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
