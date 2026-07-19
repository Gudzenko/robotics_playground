"""Publish bounded RViz paths for wheel and ground-truth odometry."""

from collections import deque

from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
import rclpy
from rclpy.node import Node


class OdometryPathPublisher(Node):
    """Convert two odometry streams into diagnostic path overlays."""

    def __init__(self):
        super().__init__('odometry_path_publisher')
        self._maximum_poses = self.declare_parameter('maximum_poses', 2000).value
        if self._maximum_poses <= 0:
            raise ValueError('maximum_poses must be positive')

        self._wheel_poses = deque(maxlen=self._maximum_poses)
        self._truth_poses = deque(maxlen=self._maximum_poses)
        self._filtered_poses = deque(maxlen=self._maximum_poses)
        self._wheel_publisher = self.create_publisher(Path, '/debug/wheel_path', 10)
        self._truth_publisher = self.create_publisher(
            Path,
            '/debug/ground_truth_path',
            10,
        )
        self._filtered_publisher = self.create_publisher(
            Path,
            '/debug/filtered_path',
            10,
        )
        self._wheel_subscription = self.create_subscription(
            Odometry,
            '/wheel/odometry',
            self._wheel_callback,
            10,
        )
        self._truth_subscription = self.create_subscription(
            Odometry,
            '/ground_truth/odometry',
            self._truth_callback,
            10,
        )
        self._filtered_subscription = self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self._filtered_callback,
            10,
        )
        self.get_logger().info(
            'Odometry path diagnostics started: wheel and ground truth',
        )

    def _wheel_callback(self, message):
        self._append_and_publish(
            message,
            self._wheel_poses,
            self._wheel_publisher,
        )

    def _truth_callback(self, message):
        self._append_and_publish(
            message,
            self._truth_poses,
            self._truth_publisher,
        )

    def _filtered_callback(self, message):
        self._append_and_publish(
            message,
            self._filtered_poses,
            self._filtered_publisher,
        )

    @staticmethod
    def _append_and_publish(message, poses, publisher):
        pose = PoseStamped()
        pose.header = message.header
        pose.pose = message.pose.pose
        poses.append(pose)

        path = Path()
        path.header = message.header
        path.poses = list(poses)
        publisher.publish(path)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryPathPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        rclpy.try_shutdown()
