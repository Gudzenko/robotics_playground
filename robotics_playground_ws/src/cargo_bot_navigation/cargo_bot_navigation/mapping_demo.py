"""Drive a short, repeatable trajectory for an RViz SLAM recording."""

import time

from geometry_msgs.msg import Twist
import rclpy
from rclpy._rclpy_pybind11 import RCLError
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


CMD_VEL_TOPIC = '/cmd_vel'
SCAN_TOPIC = '/scan'
DRIVE_SPEED_MPS = 0.75
DRIVE_DURATION_SEC = 10.0


class MappingDemo(Node):
    """Wait for lidar data, then drive through a doorway for ten seconds."""

    def __init__(self):
        super().__init__('cargo_bot_mapping_demo')
        self._scan_received = False
        self._cmd_vel_publisher = self.create_publisher(
            Twist,
            CMD_VEL_TOPIC,
            10,
        )
        self._scan_subscription = self.create_subscription(
            LaserScan,
            SCAN_TOPIC,
            self._scan_callback,
            10,
        )

    def _scan_callback(self, _message):
        self._scan_received = True

    def wait_for_lidar(self):
        """Wait for Gazebo and the lidar relay before starting motion."""
        self.get_logger().info('Waiting for lidar data before the mapping drive')
        while rclpy.ok() and not self._scan_received:
            rclpy.spin_once(self, timeout_sec=0.25)

    def drive(self):
        """Drive from room A through the east doorway into room C."""
        command = Twist()
        command.linear.x = DRIVE_SPEED_MPS
        deadline = time.monotonic() + DRIVE_DURATION_SEC

        self.get_logger().info(
            'Starting the 10-second automatic SLAM mapping drive'
        )
        try:
            while rclpy.ok() and time.monotonic() < deadline:
                self._cmd_vel_publisher.publish(command)
                rclpy.spin_once(self, timeout_sec=0.05)
        finally:
            self.stop()
        self.get_logger().info('Automatic SLAM mapping drive completed')

    def stop(self):
        """Publish repeated zero commands so the robot stops cleanly."""
        stop = Twist()
        for _ in range(3):
            if not rclpy.ok():
                return
            try:
                self._cmd_vel_publisher.publish(stop)
                rclpy.spin_once(self, timeout_sec=0.05)
            except RCLError:
                return


def main(args=None):
    """Run one automatic mapping drive."""
    rclpy.init(args=args)
    node = MappingDemo()
    try:
        node.wait_for_lidar()
        node.drive()
    except KeyboardInterrupt:
        node.get_logger().info('Automatic SLAM mapping drive interrupted')
    finally:
        if rclpy.ok():
            node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
