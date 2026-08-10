"""Publish an exact, unfiltered local TF for the ideal simulation profile."""

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class IdealOdometry(Node):
    """Expose Gazebo ground truth without adding EKF phase lag."""

    def __init__(self):
        super().__init__('ideal_odometry')
        self._tf_broadcaster = TransformBroadcaster(self)
        self._publisher = self.create_publisher(
            Odometry, '/odometry/filtered', 10,
        )
        self._subscription = self.create_subscription(
            Odometry,
            '/ground_truth/odometry',
            self._callback,
            10,
        )
        self.get_logger().info(
            'Ideal odometry started: Gazebo pose -> odom/base_footprint TF',
        )

    def _callback(self, source):
        odometry = Odometry()
        odometry.header = source.header
        odometry.header.frame_id = 'odom'
        odometry.child_frame_id = 'base_footprint'
        odometry.pose = source.pose
        odometry.twist = source.twist
        self._publisher.publish(odometry)

        transform = TransformStamped()
        transform.header = odometry.header
        transform.child_frame_id = odometry.child_frame_id
        transform.transform.translation.x = source.pose.pose.position.x
        transform.transform.translation.y = source.pose.pose.position.y
        transform.transform.translation.z = source.pose.pose.position.z
        transform.transform.rotation = source.pose.pose.orientation
        self._tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = IdealOdometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
