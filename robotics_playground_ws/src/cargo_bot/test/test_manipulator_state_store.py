"""Tests for deterministic manipulator state transitions."""

from cargo_bot.manipulator_constants import (
    ELEMENT_ARM,
    ELEMENT_GRIPPER,
    ELEMENT_LIFT,
    ELEMENT_ROTATION,
    MANIPULATOR_ELEMENTS,
)
from cargo_bot.manipulator_state_store import ManipulatorStateStore
from cargo_bot.manipulator_statuses import STATUS_DONE, STATUS_STARTED


def state_for(store, element):
    """Return a copied state for one manipulator element."""
    return next(state for state in store.all_states() if state.element == element)


def test_initial_state_is_idle_at_configured_positions():
    """Every manipulator element should start idle at position zero."""
    store = ManipulatorStateStore()

    states = store.all_states()

    assert [state.element for state in states] == list(MANIPULATOR_ELEMENTS)
    for state in states:
        assert state.position == 0.0
        assert state.moving is False
        assert state.operation_id == ''
        assert state.status == STATUS_DONE


def test_returned_states_are_copies():
    """Changing a returned message should not mutate the stored state."""
    store = ManipulatorStateStore()
    returned_state = state_for(store, ELEMENT_ARM)

    returned_state.position = 99.0
    returned_state.moving = True

    stored_state = state_for(store, ELEMENT_ARM)
    assert stored_state.position == 0.0
    assert stored_state.moving is False


def test_start_move_marks_only_requested_element_as_active():
    """Starting an operation should set its busy state and operation identity."""
    store = ManipulatorStateStore()

    store.start_move(ELEMENT_LIFT, 'lift-operation')

    state = state_for(store, ELEMENT_LIFT)
    assert state.moving is True
    assert state.operation_id == 'lift-operation'
    assert state.status == STATUS_STARTED
    assert store.is_element_moving(ELEMENT_LIFT) is True
    assert store.is_element_moving(ELEMENT_ARM) is False
    assert store.is_operation_active(ELEMENT_LIFT, 'lift-operation') is True
    assert store.is_operation_active(ELEMENT_LIFT, 'another-operation') is False


def test_matching_operation_updates_and_finishes_move():
    """The active operation should update position and finish successfully."""
    store = ManipulatorStateStore()
    store.start_move(ELEMENT_ROTATION, 'rotation-operation')

    updated = store.set_position(ELEMENT_ROTATION, 0.75, 'rotation-operation')
    store.finish_move(ELEMENT_ROTATION, 1.25, 'rotation-operation')

    state = state_for(store, ELEMENT_ROTATION)
    assert updated is True
    assert state.position == 1.25
    assert state.moving is False
    assert state.operation_id == 'rotation-operation'
    assert state.status == STATUS_DONE
    assert store.is_operation_active(ELEMENT_ROTATION, 'rotation-operation') is False


def test_stale_operation_cannot_update_or_finish_move():
    """Callbacks from an old operation should not overwrite the active move."""
    store = ManipulatorStateStore()
    store.start_move(ELEMENT_ARM, 'current-operation')

    updated = store.set_position(ELEMENT_ARM, 0.2, 'stale-operation')
    store.finish_move(ELEMENT_ARM, 0.3, 'stale-operation')

    state = state_for(store, ELEMENT_ARM)
    assert updated is False
    assert state.position == 0.0
    assert state.moving is True
    assert state.operation_id == 'current-operation'
    assert state.status == STATUS_STARTED


def test_cancel_active_operation_returns_element_to_idle():
    """Cancellation should stop the matching operation and preserve its position."""
    store = ManipulatorStateStore()
    store.start_move(ELEMENT_GRIPPER, 'gripper-operation')
    store.set_position(ELEMENT_GRIPPER, 0.05, 'gripper-operation')

    cancelled = store.cancel_operation('gripper-operation')

    state = state_for(store, ELEMENT_GRIPPER)
    assert cancelled is True
    assert state.position == 0.05
    assert state.moving is False
    assert state.operation_id == ''
    assert state.status == STATUS_DONE
    assert store.gripper_position() == 0.05


def test_cancel_unknown_or_empty_operation_changes_nothing():
    """Cancellation should report false when no operation matches."""
    store = ManipulatorStateStore()
    store.start_move(ELEMENT_ARM, 'active-operation')

    assert store.cancel_operation('') is False
    assert store.cancel_operation('unknown-operation') is False
    assert store.is_operation_active(ELEMENT_ARM, 'active-operation') is True


def test_joint_positions_filters_unknown_elements():
    """Joint position snapshots should contain only requested known elements."""
    store = ManipulatorStateStore()
    store.start_move(ELEMENT_LIFT, 'lift-operation')
    store.set_position(ELEMENT_LIFT, -0.4, 'lift-operation')

    positions = store.joint_positions(
        [ELEMENT_LIFT, ELEMENT_GRIPPER, 'unknown-element'],
    )

    assert positions == {
        ELEMENT_LIFT: -0.4,
        ELEMENT_GRIPPER: 0.0,
    }
