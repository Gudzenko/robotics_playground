"""Validate the Cargo Bot mapping configuration and launch contracts."""

from pathlib import Path
import re

import yaml


PACKAGE_PATH = Path(__file__).parents[1]
CONFIG_PATH = PACKAGE_PATH / 'config' / 'slam_mapping.yaml'
MAPPING_LAUNCH_PATH = PACKAGE_PATH / 'launch' / 'slam_mapping.launch.py'
INDOOR_LAUNCH_PATH = (
    PACKAGE_PATH.parent / 'cargo_bot_world' / 'launch' / 'indoor_rooms.launch.py'
)
RVIZ_PATH = PACKAGE_PATH / 'rviz' / 'slam_mapping.rviz'


def test_mapping_configuration_owns_expected_frames_and_topics():
    """SLAM should use only the stable navigation-facing contract."""
    with CONFIG_PATH.open(encoding='utf-8') as config_file:
        parameters = yaml.safe_load(config_file)['slam_toolbox']['ros__parameters']

    assert parameters['mode'] == 'mapping'
    assert parameters['map_frame'] == 'map'
    assert parameters['odom_frame'] == 'odom'
    assert parameters['base_frame'] == 'base_footprint'
    assert parameters['scan_topic'] == '/scan'
    assert parameters['use_map_saver'] is True
    assert parameters['do_loop_closing'] is True
    assert '/ground_truth' not in CONFIG_PATH.read_text(encoding='utf-8')


def test_mapping_parameters_match_lidar_contract():
    """Mapping range and resolution should suit the installed lidar contract."""
    with CONFIG_PATH.open(encoding='utf-8') as config_file:
        parameters = yaml.safe_load(config_file)['slam_toolbox']['ros__parameters']

    assert parameters['min_laser_range'] == 0.15
    assert parameters['max_laser_range'] == 20.0
    assert parameters['resolution'] == 0.05
    assert parameters['map_update_interval'] == 1.0
    assert parameters['minimum_time_interval'] == 0.1
    assert parameters['minimum_travel_distance'] == 0.15
    assert parameters['minimum_travel_heading'] == 0.15
    assert parameters['transform_timeout'] == 0.5
    assert parameters['scan_queue_size'] == 10


def test_mapping_launch_exposes_replaceable_inputs_and_pose():
    """Profiles, sources and spawn pose should be launch-time selections."""
    launch_text = MAPPING_LAUNCH_PATH.read_text(encoding='utf-8')
    for argument in (
        'sensor_profile', 'lidar_source', 'imu_source', 'encoder_source',
        'spawn_x', 'spawn_y', 'spawn_z', 'spawn_yaw', 'slam_params_file',
        'pose_graph', 'map_start_at_dock',
    ):
        assert re.search(
            rf"DeclareLaunchArgument\(\s*'{argument}'",
            launch_text,
        )
    assert "'sensor_profile', default_value='ideal'" in launch_text
    assert "executable='async_slam_toolbox_node'" in launch_text


def test_indoor_world_spawn_pose_is_parameterized_with_stable_defaults():
    """Existing launches should retain room A while accepting pose overrides."""
    launch_text = INDOOR_LAUNCH_PATH.read_text(encoding='utf-8')
    expected_defaults = {
        'spawn_x': '0.0',
        'spawn_y': '0.0',
        'spawn_z': '0.1',
        'spawn_yaw': '1.5708',
    }
    for name, value in expected_defaults.items():
        assert f"'{name}',\n            default_value='{value}'" in launch_text
        assert f"LaunchConfiguration('{name}')" in launch_text


def test_rviz_mapping_scene_uses_map_and_public_scan():
    """The mapping scene should display the map, public scan, robot and TF."""
    rviz_text = RVIZ_PATH.read_text(encoding='utf-8')
    assert 'Fixed Frame: map' in rviz_text
    assert 'Value: /map' in rviz_text
    assert 'Value: /scan' in rviz_text
    assert 'Use Fixed Frame: true' in rviz_text
    assert 'rviz_default_plugins/RobotModel' in rviz_text
    assert 'rviz_default_plugins/TF' in rviz_text
