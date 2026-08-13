"""Unit tests for navigation cancellation responses."""

from action_msgs.msg import GoalInfo
from action_msgs.srv import CancelGoal

from cargo_bot_navigation.goal_navigator import cancellation_accepted


def test_cancellation_requires_success_and_an_active_goal():
    accepted = CancelGoal.Response()
    accepted.return_code = CancelGoal.Response.ERROR_NONE
    accepted.goals_canceling = [GoalInfo()]

    no_active_goal = CancelGoal.Response()
    no_active_goal.return_code = CancelGoal.Response.ERROR_NONE

    rejected = CancelGoal.Response()
    rejected.return_code = CancelGoal.Response.ERROR_REJECTED
    rejected.goals_canceling = [GoalInfo()]

    assert cancellation_accepted(accepted) is True
    assert cancellation_accepted(no_active_goal) is False
    assert cancellation_accepted(rejected) is False
