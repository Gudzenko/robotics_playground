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
    assert amcl['base_frame_id'] == 'base_footprint'
    assert amcl['scan_topic'] == '/scan'
    assert amcl['set_initial_pose'] is True


def test_global_costmap_has_static_geometry_and_reviewed_footprint():
    parameters = _config()['global_costmap']['global_costmap']['ros__parameters']
    assert parameters['global_frame'] == 'map'
    assert parameters['robot_base_frame'] == 'base_footprint'
    assert parameters['plugins'] == ['static_layer', 'inflation_layer']
    assert 'obstacle_layer' not in parameters['plugins']
    assert parameters['footprint'] == (
        '[[1.30, 0.55], [1.30, -0.55], '
        '[-0.85, -0.55], [-0.85, 0.55]]'
    )
    assert parameters['inflation_layer']['inflation_radius'] >= 0.57


def test_navfn_is_the_only_planner_and_no_motion_servers_are_launched():
    config = _config()
    planner = config['planner_server']['ros__parameters']
    assert planner['planner_plugins'] == ['GridBased']
    assert planner['GridBased']['plugin'] == 'nav2_navfn_planner::NavfnPlanner'
    launch_text = LAUNCH_PATH.read_text(encoding='utf-8')
    assert "DeclareLaunchArgument(\n            'map', default_value=''" in launch_text
    assert "'initial_pose_x'" in launch_text
    assert "'initial_pose_yaw'" in launch_text
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
