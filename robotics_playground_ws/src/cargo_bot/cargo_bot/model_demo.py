"""Run a short, repeatable Cargo Bot model demonstration in RViz."""

import math
import time

from cargo_bot_interfaces.action import MoveManipulatorElement
from geometry_msgs.msg import Twist
import rclpy
from rclpy._rclpy_pybind11 import RCLError
from rclpy.action import ActionClient
from rclpy.node import Node


MOVE_ACTION = '/cargo_bot/move_manipulator_element'
CMD_VEL_TOPIC = '/cmd_vel'


class ModelDemo(Node):
    """Drive the base and manipulator through a video-friendly sequence."""

    def __init__(self):
        super().__init__('cargo_bot_model_demo')
        self._cmd_vel_publisher = self.create_publisher(Twist, CMD_VEL_TOPIC, 10)
        self._move_client = ActionClient(
            self,
            MoveManipulatorElement,
            MOVE_ACTION,
        )

    def wait_until_ready(self):
        """Wait until the manipulator action server is available."""
        self.get_logger().info('Waiting for the robot control nodes...')
        while rclpy.ok() and not self._move_client.wait_for_server(
            timeout_sec=1.0,
        ):
            self.get_logger().info('Manipulator action server is not ready yet')

    def rotate_base(self, angle, angular_speed=0.45):
        """Rotate the kinematic base through the requested angle in radians."""
        direction = 1.0 if angle >= 0.0 else -1.0
        command = Twist()
        command.angular.z = direction * abs(angular_speed)
        duration = abs(angle) / abs(angular_speed)
        deadline = time.monotonic() + duration

        self.get_logger().info('Rotating the base for a full model overview')
        try:
            while rclpy.ok() and time.monotonic() < deadline:
                self._cmd_vel_publisher.publish(command)
                rclpy.spin_once(self, timeout_sec=0.05)
        finally:
            self.stop_base()

    def stop_base(self):
        """Publish repeated zero commands so the base stops cleanly."""
        stop = Twist()
        for _ in range(3):
            if not rclpy.ok():
                return
            try:
                self._cmd_vel_publisher.publish(stop)
                rclpy.spin_once(self, timeout_sec=0.05)
            except RCLError:
                return

    def move_element(self, element, position, duration_sec):
        """Move one manipulator element and wait for completion."""
        goal = MoveManipulatorElement.Goal()
        goal.element = element
        goal.position = position
        goal.duration_sec = duration_sec

        self.get_logger().info(
            f'Moving {element} to {position:.3f} over {duration_sec:.1f} s'
        )
        goal_future = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future)
        goal_handle = goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            raise RuntimeError(f'Manipulator rejected the {element} goal')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()
        if result is None or result.result.status != 'done':
            raise RuntimeError(f'The {element} movement did not complete')

    def pause(self, duration_sec):
        """Keep processing callbacks during a short presentation pause."""
        deadline = time.monotonic() + duration_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def run(self):
        """Execute the complete demonstration choreography once."""
        self.wait_until_ready()
        self.pause(2.0)
        self.rotate_base(2.0 * math.pi)
        self.pause(1.0)

        self.move_element('lift', 0.30, 2.0)
        self.move_element('rotation', -1.25, 2.5)
        self.move_element('arm', 0.16, 2.0)
        self.move_element('gripper', 0.06, 1.2)
        self.pause(1.0)
        self.move_element('gripper', 0.0, 1.2)
        self.move_element('rotation', 1.25, 3.0)
        self.pause(1.5)

        self.get_logger().info('Returning the manipulator to its home pose')
        self.move_element('arm', 0.0, 2.0)
        self.move_element('rotation', 0.0, 2.0)
        self.move_element('lift', 0.0, 2.0)
        self.get_logger().info('Cargo Bot model demonstration completed')


def main(args=None):
    """Run the model demonstration node."""
    rclpy.init(args=args)
    node = ModelDemo()
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().info('Cargo Bot model demonstration interrupted')
    except RuntimeError as error:
        node.get_logger().error(str(error))
    finally:
        if rclpy.ok():
            node.stop_base()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
