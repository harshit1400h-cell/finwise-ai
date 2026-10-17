import pytest

from src.goals import add_goal, delete_goal, get_goals, update_goal_progress


def test_goal_progress_and_contribution_estimate(db_path):
    goal_id = add_goal("Laptop", 12000, 3000, "2099-01-01", "Study laptop")
    goal = get_goals()[0]
    assert goal["target"] == 12000
    assert goal["saved"] == 3000
    assert goal["remaining"] == 9000
    assert goal["progress"] == 0.25
    assert goal["monthly_contribution"] > 0
    update_goal_progress(goal_id, 0)
    assert get_goals()[0]["saved"] == 0
    delete_goal(goal_id)
    assert get_goals() == []


def test_goal_validation(db_path):
    with pytest.raises(ValueError):
        add_goal("", 100, 0, "2099-01-01")
    with pytest.raises(ValueError):
        add_goal("Goal", 100, 101, "2099-01-01")
