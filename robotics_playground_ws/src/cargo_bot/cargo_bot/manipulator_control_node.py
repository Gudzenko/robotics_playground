import math
import time
import uuid

from cargo_bot.cargo_bot_geometry import (
    CargoBotGeometry,
    LIMIT_LOWER_KEY,
    LIMIT_UPPER_KEY,
)
from cargo_bot.joint_state_constants import JOINT_STATE_PUBLISH_PERIOD_SEC
from cargo_bot.manipulator_constants import (
    ELEMENT_GRIPPER,
    MANIPULATOR_ELEMENTS,
)
from cargo_bot.manipulator_ros_names import (
    CANCEL_MANIPULATOR_OPERATION_SERVICE,
    GET_MANIPULATOR_STATE_SERVICE,
    JOINT_STATES_TOPIC,
    MOVE_MANIPULATOR_ELEMENT_ACTION,
)
from cargo_bot.manipulator_state_store import ManipulatorStateStore
from cargo_bot.manipulator_statuses import (
    STATUS_DONE,
    STATUS_ERROR,
    STATUS_STARTED,
)
from cargo_bot_interfaces.action import MoveManipulatorElement
from cargo_bot_interfaces.srv import (
    CancelManipulatorOperation,
    GetManipulatorState,
)
import rclpy
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState


EXECUTION_POLL_SEC = 0.05


class ManipulatorControlNode(Node):
    def __init__(self):
        super().__init__('manipulator_control_node')
        self._callback_group = ReentrantCallbackGroup()
        self._state_store = ManipulatorStateStore()
        self._load_geometry()
        self._state_service = self.create_service(
            GetManipulatorState,
            GET_MANIPULATOR_STATE_SERVICE,
            self._handle_get_state,
            callback_group=self._callback_group,
        )
        self._cancel_service = self.create_service(
            CancelManipulatorOperation,
            CANCEL_MANIPULATOR_OPERATION_SERVICE,
            self._handle_cancel_operation,
            callback_group=self._callback_group,
        )
        self._move_action_server = ActionServer(
            self,
            MoveManipulatorElement,
            MOVE_MANIPULATOR_ELEMENT_ACTION,
            self._handle_move_element,
            callback_group=self._callback_group,
        )
        self._joint_state_publisher = self.create_publisher(
            JointState,
            JOINT_STATES_TOPIC,
            10,
        )
        self._joint_state_timer = self.create_timer(
            JOINT_STATE_PUBLISH_PERIOD_SEC,
            self._publish_joint_states,
            callback_group=self._callback_group,
        )
        self.get_logger().info('Manipulator control node started')

    def _load_geometry(self):
        try:
            geometry = CargoBotGeometry()
            self._element_limits = geometry.manipulator_limits()
            self._element_joint_names = geometry.manipulator_joint_names()
            self._gripper_mimic_joint_name = geometry.gripper_mimic_joint_name()
        except (KeyError, TypeError, OSError, ValueError) as error:
            self.get_logger().error(f'Failed to load manipulator geometry: {error}')
            self._element_limits = {}
            self._element_joint_names = {}
            self._gripper_mimic_joint_name = ''
            return

        self.get_logger().info(f'Manipulator limits loaded: {self._element_limits}')
        self.get_logger().info(
            f'Manipulator joint names loaded: {self._element_joint_names}'
        )
        self.get_logger().info(
            f'Gripper mimic joint name loaded: {self._gripper_mimic_joint_name}'
        )

    def _handle_get_state(self, request, response):
        del request
        response.states = self._state_store.all_states()
        response.message = 'manipulator state returned'
        return response

    def _publish_joint_states(self):
        joint_state = JointState()
        joint_state.header.stamp = self.get_clock().now().to_msg()

        positions = self._state_store.joint_positions(MANIPULATOR_ELEMENTS)

        for element in MANIPULATOR_ELEMENTS:
            if element not in self._element_joint_names:
                continue

            joint_state.name.append(self._element_joint_names[element])
            joint_state.position.append(positions[element])

        if self._gripper_mimic_joint_name:
            joint_state.name.append(self._gripper_mimic_joint_name)
            joint_state.position.append(-positions[ELEMENT_GRIPPER])

        self._joint_state_publisher.publish(joint_state)

    def _handle_cancel_operation(self, request, response):
        response.operation_id = request.operation_id

        if not self._state_store.cancel_operation(request.operation_id):
            response.status = STATUS_ERROR
            response.message = f"operation_id '{request.operation_id}' was not found"
            return response

        response.status = STATUS_DONE
        response.message = f"operation '{request.operation_id}' canceled"
        return response

    def _handle_move_element(self, goal_handle):
        operation_id = str(uuid.uuid4())
        goal = goal_handle.request
        result = MoveManipulatorElement.Result()
        result.operation_id = operation_id

        error_message = self._validate_move_goal(goal)
        if error_message:
            goal_handle.abort()
            result.status = STATUS_ERROR
            result.message = error_message
            return result

        self._state_store.start_move(goal.element, operation_id)

        feedback = MoveManipulatorElement.Feedback()
        feedback.operation_id = operation_id
        feedback.status = STATUS_STARTED
        goal_handle.publish_feedback(feedback)

        if not self._execute_element_move(
            goal.element,
            goal.position,
            operation_id,
            goal.duration_sec,
        ):
            goal_handle.succeed()
            result.status = STATUS_DONE
            result.message = f"operation '{operation_id}' canceled"
            return result

        self._state_store.finish_move(goal.element, goal.position, operation_id)

        goal_handle.succeed()
        result.status = STATUS_DONE
        result.message = 'move command completed'
        return result

    def _execute_element_move(self, element, target_position, operation_id, duration_sec):
        start_position = self._state_store.get_position(element)

        if duration_sec == 0.0:
            return self._state_store.set_position(
                element,
                target_position,
                operation_id,
            )

        deadline = time.monotonic() + duration_sec

        while time.monotonic() < deadline:
            if not self._state_store.is_operation_active(element, operation_id):
                return False

            now = time.monotonic()
            progress = 1.0 - ((deadline - now) / duration_sec)
            position = self._interpolate_position(
                start_position,
                target_position,
                progress,
            )
            if not self._state_store.set_position(element, position, operation_id):
                return False

            sleep_sec = min(EXECUTION_POLL_SEC, deadline - time.monotonic())
            if sleep_sec > 0.0:
                time.sleep(sleep_sec)

        return self._state_store.set_position(
            element,
            target_position,
            operation_id,
        )

    def _interpolate_position(self, start_position, target_position, progress):
        bounded_progress = min(max(progress, 0.0), 1.0)
        return start_position + ((target_position - start_position) * bounded_progress)

    def _validate_move_goal(self, goal):
        if goal.element not in MANIPULATOR_ELEMENTS:
            allowed_elements = ', '.join(MANIPULATOR_ELEMENTS)
            return f"unknown element '{goal.element}'. Allowed: {allowed_elements}"

        if goal.element not in self._element_limits:
            return f"limits for element '{goal.element}' are not available"

        if self._state_store.is_element_moving(goal.element):
            return f"element '{goal.element}' is already moving"

        if not math.isfinite(goal.position):
            return 'position must be a finite number'

        limits = self._element_limits[goal.element]
        if (
            goal.position < limits[LIMIT_LOWER_KEY]
            or goal.position > limits[LIMIT_UPPER_KEY]
        ):
            return (
                f"position for element '{goal.element}' must be between "
                f'{limits[LIMIT_LOWER_KEY]} and {limits[LIMIT_UPPER_KEY]}'
            )

        if not math.isfinite(goal.duration_sec):
            return 'duration_sec must be a finite number'

        if goal.duration_sec < 0.0:
            return 'duration_sec must be greater than or equal to 0.0'

        return ''


def main(args=None):
    rclpy.init(args=args)
    node = ManipulatorControlNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info('Manipulator control node stopped')
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
