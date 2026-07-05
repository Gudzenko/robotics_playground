import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster
import yaml


def yaw_to_quaternion(yaw):
    half_yaw = yaw * 0.5
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(half_yaw),
        'w': math.cos(half_yaw),
    }


class SimpleDiffDriveSim(Node):
    def __init__(self):
        super().__init__('simple_diff_drive_sim')

        geometry = self._load_geometry()
        frames = geometry['frames']
        drive_wheels = geometry['drive_wheels']

        self.odom_frame = 'odom'
        self.base_frame = frames['base_footprint']
        self.left_wheel_joint = drive_wheels['left_joint']
        self.right_wheel_joint = drive_wheels['right_joint']
        self.wheel_radius = float(drive_wheels['radius'])
        self.wheel_separation = 2.0 * float(drive_wheels['y_offset'])

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.left_wheel_position = 0.0
        self.right_wheel_position = 0.0
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.last_cmd_time = self.get_clock().now()
        self.last_update_time = self.get_clock().now()
        self.cmd_timeout_sec = 0.5

        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10,
        )
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.joint_state_pub = self.create_publisher(JointState, '/joint_states', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(0.02, self.update)

        self.get_logger().info(
            'Simple diff-drive sim started: '
            f'wheel_radius={self.wheel_radius:.3f}, '
            f'wheel_separation={self.wheel_separation:.3f}'
        )

    def _load_geometry(self):
        package_share = Path(get_package_share_directory('cargo_bot'))
        geometry_path = package_share / 'config' / 'cargo_bot_geometry.yaml'
        with geometry_path.open('r', encoding='utf-8') as geometry_file:
            return yaml.safe_load(geometry_file)

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def update(self):
        now = self.get_clock().now()
        dt = (now - self.last_update_time).nanoseconds * 1e-9
        self.last_update_time = now

        if dt <= 0.0:
            return

        if (now - self.last_cmd_time).nanoseconds * 1e-9 > self.cmd_timeout_sec:
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0

        linear = self.linear_velocity
        angular = self.angular_velocity

        delta_x = linear * math.cos(self.yaw) * dt
        delta_y = linear * math.sin(self.yaw) * dt
        delta_yaw = angular * dt

        self.x += delta_x
        self.y += delta_y
        self.yaw = math.atan2(math.sin(self.yaw + delta_yaw), math.cos(self.yaw + delta_yaw))

        left_velocity = linear - angular * self.wheel_separation * 0.5
        right_velocity = linear + angular * self.wheel_separation * 0.5
        self.left_wheel_position += left_velocity / self.wheel_radius * dt
        self.right_wheel_position += right_velocity / self.wheel_radius * dt

        self.publish_tf(now)
        self.publish_odom(now, linear, angular)
        self.publish_joint_states(now)

    def publish_tf(self, stamp):
        transform = TransformStamped()
        transform.header.stamp = stamp.to_msg()
        transform.header.frame_id = self.odom_frame
        transform.child_frame_id = self.base_frame
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0

        quaternion = yaw_to_quaternion(self.yaw)
        transform.transform.rotation.x = quaternion['x']
        transform.transform.rotation.y = quaternion['y']
        transform.transform.rotation.z = quaternion['z']
        transform.transform.rotation.w = quaternion['w']

        self.tf_broadcaster.sendTransform(transform)

    def publish_odom(self, stamp, linear, angular):
        odom = Odometry()
        odom.header.stamp = stamp.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        quaternion = yaw_to_quaternion(self.yaw)
        odom.pose.pose.orientation.x = quaternion['x']
        odom.pose.pose.orientation.y = quaternion['y']
        odom.pose.pose.orientation.z = quaternion['z']
        odom.pose.pose.orientation.w = quaternion['w']
        odom.twist.twist.linear.x = linear
        odom.twist.twist.angular.z = angular

        self.odom_pub.publish(odom)

    def publish_joint_states(self, stamp):
        joint_state = JointState()
        joint_state.header.stamp = stamp.to_msg()
        joint_state.name = [
            self.left_wheel_joint,
            self.right_wheel_joint,
        ]
        joint_state.position = [
            self.left_wheel_position,
            self.right_wheel_position,
        ]

        self.joint_state_pub.publish(joint_state)


def main(args=None):
    rclpy.init(args=args)
    node = SimpleDiffDriveSim()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
