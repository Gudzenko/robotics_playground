from cargo_bot.cargo_bot_geometry import CargoBotGeometry
from cargo_bot.joint_state_constants import JOINT_STATE_PUBLISH_PERIOD_SEC
from cargo_bot.manipulator_ros_names import JOINT_STATES_TOPIC
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class PassiveJointStatePublisher(Node):
    def __init__(self):
        super().__init__('passive_joint_state_publisher')
        self._joint_positions = self._load_passive_joint_positions()
        self._publisher = self.create_publisher(JointState, JOINT_STATES_TOPIC, 10)
        self._timer = self.create_timer(
            JOINT_STATE_PUBLISH_PERIOD_SEC,
            self._publish_joint_states,
        )
        self.get_logger().info('Passive joint state publisher started')

    def _load_passive_joint_positions(self):
        try:
            joint_positions = CargoBotGeometry().passive_joint_positions()
        except (KeyError, TypeError, OSError, ValueError) as error:
            self.get_logger().error(f'Failed to load passive joints: {error}')
            return {}

        self.get_logger().info(f'Passive joints loaded: {list(joint_positions)}')
        return joint_positions

    def _publish_joint_states(self):
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()
        joint_state.name = list(self._joint_positions)
        joint_state.position = list(self._joint_positions.values())
        self._publisher.publish(joint_state)


def main(args=None):
    rclpy.init(args=args)
    node = PassiveJointStatePublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Passive joint state publisher stopped')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
