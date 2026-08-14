"""Static contracts for the trajectory-execution milestone."""

from pathlib import Path

import yaml


PACKAGE = Path(__file__).parents[1]


def parameters(node_name):
    data = yaml.safe_load(
        (PACKAGE / 'config' / 'static_navigation.yaml').read_text(),
    )
    return data[node_name]['ros__parameters']


def test_controller_is_footprint_aware_and_collision_checked():
    controller = parameters('controller_server')
    data = yaml.safe_load(
        (PACKAGE / 'config' / 'static_navigation.yaml').read_text(),
    )
    local = data['local_costmap']['local_costmap']['ros__parameters']
    follow = controller['FollowPath']

    assert follow['plugin'].endswith('RegulatedPurePursuitController')
    assert follow['desired_linear_vel'] == 2.0
    assert follow['lookahead_dist'] == 0.60
    assert follow['min_lookahead_dist'] == 0.40
    assert follow['max_lookahead_dist'] == 0.80
    assert follow['lookahead_time'] == 0.40
    assert follow['use_velocity_scaled_lookahead_dist'] is True
    assert follow['use_collision_detection'] is True
    assert follow['max_allowed_time_to_collision_up_to_carrot'] == 0.40
    assert follow['use_cost_regulated_linear_velocity_scaling'] is False
    assert follow['use_rotate_to_heading'] is True
    assert follow['rotate_to_heading_min_angle'] <= 0.35
    assert follow['allow_reversing'] is False
    assert controller['failure_tolerance'] == 3.0
    assert controller['progress_checker']['plugin'].endswith(
        'SimpleProgressChecker'
    )
    assert controller['progress_checker']['required_movement_radius'] == 0.20
    assert 'required_movement_angle' not in controller['progress_checker']
    assert controller['progress_checker']['movement_time_allowance'] == 10.0
    goal_checker = controller['goal_checker']
    assert goal_checker['plugin'].endswith('PositionGoalChecker')
    assert goal_checker['xy_goal_tolerance'] == 0.30
    assert goal_checker['path_length_tolerance'] == 100.0
    assert 'yaw_goal_tolerance' not in goal_checker
    assert 'static_layer' in local['plugins']
    assert 'obstacle_layer' in local['plugins']
    obstacle = local['obstacle_layer']
    assert obstacle['scan']['topic'] == '/scan'
    assert obstacle['scan']['marking'] is True
    assert obstacle['scan']['clearing'] is True
    assert obstacle['scan']['observation_persistence'] >= 0.5
    assert obstacle['scan']['max_obstacle_height'] >= 1.0
    assert local['footprint'] == (
        '[[0.49, 0.33], [0.49, -0.33], [-0.585, -0.33], [-0.585, 0.33]]'
    )
    assert local['robot_base_frame'] == 'base_axle'
    assert local['inflation_layer']['inflation_radius'] == 0.75
    assert local['inflation_layer']['cost_scaling_factor'] == 4.0


def test_velocity_smoother_limits_speed_acceleration_and_timeout():
    smoother = parameters('velocity_smoother')

    assert smoother['max_velocity'] == [3.0, 0.0, 1.0]
    assert smoother['max_accel'][0] == 1.8
    assert smoother['max_accel'][2] == 2.2
    assert smoother['max_decel'][0] == -2.5
    assert smoother['max_decel'][2] == -2.2
    assert smoother['velocity_timeout'] <= 0.5
    assert smoother['feedback'] == 'OPEN_LOOP'


def test_collision_monitor_is_independent_and_uses_public_scan():
    monitor = parameters('collision_monitor')

    assert monitor['cmd_vel_in_topic'] == '/cmd_vel_smoothed'
    assert monitor['cmd_vel_out_topic'] == '/cmd_vel'
    assert monitor['polygons'] == ['StopZone', 'SlowZone']
    assert monitor['SlowZone']['action_type'] == 'slowdown'
    assert monitor['StopZone']['action_type'] == 'stop'
    assert monitor['scan']['topic'] == '/scan'


def test_bt_and_lifecycle_cover_complete_static_navigation_stack():
    lifecycle = parameters('lifecycle_manager_static_navigation')
    behaviors = parameters('behavior_server')

    assert lifecycle['autostart'] is True
    assert lifecycle['node_names'] == [
        'controller_server', 'behavior_server',
        'bt_navigator', 'velocity_smoother',
    ]
    assert behaviors['behavior_plugins'] == ['spin', 'backup', 'wait']


def test_launch_separates_raw_and_smoothed_velocity_topics():
    launch_text = (
        PACKAGE / 'launch' / 'static_navigation.launch.py'
    ).read_text()

    assert "('cmd_vel', '/cmd_vel_nav')" in launch_text
    assert "('cmd_vel_smoothed', IfElseSubstitution(" in launch_text
    assert "if_value='/cmd_vel_smoothed'" in launch_text
    assert "else_value='/cmd_vel'" in launch_text
    assert "'use_path_requester': 'false'" in launch_text
    assert "'use_lifecycle_manager': 'false'" in launch_text
    assert "'navigation_start_delay': '6.0'" in launch_text
    assert "'navigate_static_path.xml'" in launch_text
    assert "'initial_pose_x', default_value='0.0'" in launch_text
    assert "'initial_pose_y', default_value='0.0'" in launch_text
    assert "'initial_pose_yaw', default_value='1.5708'" in launch_text


def test_static_bt_always_replans_before_retry_and_never_spins():
    tree = (PACKAGE / 'behavior_trees' / 'navigate_static_path.xml').read_text()
    assert tree.index('<ComputePathToPose') < tree.index('<FollowPath')
    assert '<RecoveryNode number_of_retries="3"' in tree
    assert '<SequenceWithMemory name="PlanThenFollow">' in tree
    assert '<PipelineSequence' not in tree
    assert '<Spin' not in tree


def test_dynamic_bt_never_erases_global_obstacle_memory():
    tree = (
        PACKAGE / 'behavior_trees' / 'navigate_with_obstacles.xml'
    ).read_text()
    assert 'clear_entirely_global_costmap' not in tree
    assert 'clear_entirely_local_costmap' in tree
    assert '<RateController hz="1.0">' in tree


def test_manipulator_home_orientation_points_backwards():
    xacro = (
        PACKAGE.parent / 'cargo_bot' / 'urdf' / 'cargo_bot_manipulator.xacro'
    ).read_text()

    assert 'rpy="0 0 3.14159265359"' in xacro
