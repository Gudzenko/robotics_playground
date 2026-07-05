from threading import RLock

from cargo_bot.manipulator_constants import ELEMENT_GRIPPER, MANIPULATOR_ELEMENTS
from cargo_bot.manipulator_defaults import (
    INITIAL_MOVING,
    INITIAL_OPERATION_ID,
    INITIAL_POSITIONS,
    INITIAL_STATUS,
)
from cargo_bot.manipulator_statuses import STATUS_DONE, STATUS_STARTED
from cargo_bot_interfaces.msg import ManipulatorElementState


class ManipulatorStateStore:
    def __init__(self):
        self._lock = RLock()
        self._states = {
            element: self._make_element_state(element)
            for element in MANIPULATOR_ELEMENTS
        }

    def all_states(self):
        with self._lock:
            return [
                self._copy_element_state(state)
                for state in self._states.values()
            ]

    def start_move(self, element, operation_id):
        with self._lock:
            state = self._states[element]
            state.moving = True
            state.operation_id = operation_id
            state.status = STATUS_STARTED

    def finish_move(self, element, position, operation_id):
        with self._lock:
            state = self._states[element]
            if state.operation_id != operation_id:
                return

            state.position = position
            state.moving = False
            state.operation_id = operation_id
            state.status = STATUS_DONE

    def cancel_operation(self, operation_id):
        if not operation_id:
            return False

        with self._lock:
            for state in self._states.values():
                if state.operation_id == operation_id:
                    state.moving = False
                    state.operation_id = INITIAL_OPERATION_ID
                    state.status = STATUS_DONE
                    return True

        return False

    def is_operation_active(self, element, operation_id):
        with self._lock:
            state = self._states[element]
            return state.moving and state.operation_id == operation_id

    def is_element_moving(self, element):
        with self._lock:
            return self._states[element].moving

    def get_position(self, element):
        with self._lock:
            return self._states[element].position

    def set_position(self, element, position, operation_id):
        with self._lock:
            state = self._states[element]
            if state.operation_id != operation_id:
                return False

            state.position = position
            return True

    def joint_positions(self, elements):
        with self._lock:
            return {
                element: self._states[element].position
                for element in elements
                if element in self._states
            }

    def gripper_position(self):
        with self._lock:
            return self._states[ELEMENT_GRIPPER].position

    def _make_element_state(self, element):
        state = ManipulatorElementState()
        state.element = element
        state.position = INITIAL_POSITIONS[element]
        state.moving = INITIAL_MOVING
        state.operation_id = INITIAL_OPERATION_ID
        state.status = INITIAL_STATUS
        return state

    def _copy_element_state(self, source):
        state = ManipulatorElementState()
        state.element = source.element
        state.position = source.position
        state.moving = source.moving
        state.operation_id = source.operation_id
        state.status = source.status
        return state
