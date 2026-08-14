"""Validate the localization and planning-without-motion contracts."""

from pathlib import Path

import yaml


PACKAGE_PATH = Path(__file__).parents[1]
CONFIG_PATH = PACKAGE_PATH / 'config' / 'path_planning.yaml'
LAUNCH_PATH = PACKAGE_PATH / 'launch' / 'path_planning.launch.py'
RVIZ_PATH = PACKAGE_PATH / 'rviz' / 'path_planning.rviz'


def _config():
    with CONFIG_PATH.open(encoding='utf-8') as config_file:
        return yaml.safe_load(config_file)


def test_map_and_amcl_use_the_stable_frame_contract():
    config = _config()
    amcl = config['amcl']['ros__parameters']
    assert config['map_server']['ros__parameters']['yaml_filename'] == ''
    assert amcl['global_frame_id'] == 'map'
    assert amcl['odom_frame_id'] == 'odom'
    assert amcl['base_frame_id'] == 'base_axle'
    assert amcl['scan_topic'] == '/scan'
    assert amcl['set_initial_pose'] is True


def test_ideal_profile_keeps_map_to_odom_fixed():
    launch_text = LAUNCH_PATH.read_text(encoding='utf-8')
    assert "'tf_broadcast': ParameterValue(" in launch_text
    assert "EqualsSubstitution(sensor_profile, 'ideal')" in launch_text
    assert "name='ideal_map_to_odom'" in launch_text
    assert "'--frame-id', 'map', '--child-frame-id', 'odom'" in launch_text


def test_global_costmap_has_static_geometry_and_reviewed_footprint():
    parameters = _config()['global_costmap']['global_costmap']['ros__parameters']
    assert parameters['global_frame'] == 'map'
    assert parameters['robot_base_frame'] == 'base_axle'
    assert parameters['plugins'] == [
        'static_layer', 'persistent_memory_layer', 'obstacle_layer',
        'inflation_layer',
    ]
    obstacle = parameters['obstacle_layer']
    assert obstacle['scan']['topic'] == '/scan'
    assert obstacle['scan']['marking'] is True
    assert obstacle['scan']['clearing'] is True
    assert obstacle['scan']['observation_persistence'] == 0.0
    assert obstacle['scan']['max_obstacle_height'] >= 1.0
    memory = parameters['persistent_memory_layer']
    assert memory['plugin'] == (
        'cargo_bot_costmap_plugins::PersistentObstacleLayer'
    )
    assert memory['topic'] == '/persistent_obstacle_map'
    assert memory['enabled'] is True
    assert parameters['footprint'] == (
        '[[0.49, 0.33], [0.49, -0.33], '
        '[-0.585, -0.33], [-0.585, 0.33]]'
    )
    assert parameters['inflation_layer']['inflation_radius'] == 1.49
    assert parameters['inflation_layer']['cost_scaling_factor'] == 4.0


def test_differential_drive_smac_is_the_only_planner_and_no_motion_servers_launch():
    config = _config()
    planner = config['planner_server']['ros__parameters']
    assert planner['planner_plugins'] == ['GridBased']
    grid = planner['GridBased']
    assert grid['plugin'] == 'nav2_smac_planner::SmacPlanner2D'
    assert grid['max_planning_time'] == 8.0
    assert grid['max_iterations'] == 4000000
    assert 'motion_model_for_search' not in grid
    assert 'minimum_turning_radius' not in grid
    assert grid['use_final_approach_orientation'] is False
    launch_text = LAUNCH_PATH.read_text(encoding='utf-8')
    assert "DeclareLaunchArgument(\n            'map', default_value=''" in launch_text
    assert "'initial_pose_x'" in launch_text
    assert "'initial_pose_yaw'" in launch_text
    assert "'initial_pose_x', default_value='0.0'" in launch_text
    assert "'initial_pose_y', default_value='0.0'" in launch_text
    assert "'initial_pose_yaw', default_value='1.5708'" in launch_text
    for forbidden in (
        'controller_server', 'bt_navigator', 'behavior_server',
        'velocity_smoother',
    ):
        assert forbidden not in launch_text


def test_rviz_exposes_initial_pose_goal_and_planned_path():
    text = RVIZ_PATH.read_text(encoding='utf-8')
    assert 'Fixed Frame: map' in text
    assert 'rviz_default_plugins/SetInitialPose' in text
    assert 'Topic: /initialpose' in text
    assert 'rviz_default_plugins/SetGoal' in text
    assert 'Topic: /goal_pose' in text
    assert 'Value: /planned_path' in text
    assert 'Value: /global_costmap/costmap' in text
