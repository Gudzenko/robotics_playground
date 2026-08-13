"""Localize on a user map and calculate visible paths without robot motion."""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
    UnsetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EqualsSubstitution,
    IfElseSubstitution,
    LaunchConfiguration,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile, ParameterValue
import yaml


def _validate_user_map(context):
    """Fail before startup when the required user map is missing."""
    value = LaunchConfiguration('map').perform(context).strip()
    if not value:
        raise RuntimeError(
            'The required map argument is empty. Pass '
            'map:=/absolute/path/to/map.yaml',
        )
    map_path = Path(value).expanduser()
    if map_path.suffix.lower() not in ('.yaml', '.yml'):
        raise RuntimeError(f'Map must be a YAML file: {map_path}')
    if not map_path.is_file():
        raise RuntimeError(f'Map YAML does not exist: {map_path}')
    try:
        metadata = yaml.safe_load(map_path.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as error:
        raise RuntimeError(f'Cannot read map YAML {map_path}: {error}') from error
    image_value = metadata.get('image') if isinstance(metadata, dict) else None
    if not image_value:
        raise RuntimeError(f'Map YAML has no image field: {map_path}')
    image_path = Path(image_value).expanduser()
    if not image_path.is_absolute():
        image_path = map_path.parent / image_path
    if not image_path.is_file():
        raise RuntimeError(f'Map image does not exist: {image_path}')
    return []


def generate_launch_description():
    """Create the map-localization and global-planning launch graph."""
    navigation_share = get_package_share_directory('cargo_bot_navigation')
    world_share = get_package_share_directory('cargo_bot_world')
    map_path = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    use_path_requester = LaunchConfiguration('use_path_requester')
    use_lifecycle_manager = LaunchConfiguration('use_lifecycle_manager')
    sensor_profile = LaunchConfiguration('sensor_profile')
    initial_x = LaunchConfiguration('initial_pose_x')
    initial_y = LaunchConfiguration('initial_pose_y')
    initial_z = LaunchConfiguration('initial_pose_z')
    initial_yaw = LaunchConfiguration('initial_pose_yaw')
    gz_partition = LaunchConfiguration('gz_partition')
    navigation_start_delay = LaunchConfiguration('navigation_start_delay')

    indoor_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(world_share, 'launch', 'indoor_rooms.launch.py'),
        ),
        launch_arguments={
            'headless': headless,
            'sensor_profile': sensor_profile,
            'spawn_x': initial_x,
            'spawn_y': initial_y,
            'spawn_z': initial_z,
            'spawn_yaw': initial_yaw,
            'gz_partition': gz_partition,
        }.items(),
    )
    common_parameters = ParameterFile(params_file, allow_substs=True)

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[common_parameters, {
            'use_sim_time': True,
            'yaml_filename': map_path,
        }],
    )
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[common_parameters, {
            'use_sim_time': True,
            'initial_pose.x': initial_x,
            'initial_pose.y': initial_y,
            'initial_pose.z': 0.0,
            'initial_pose.yaw': initial_yaw,
            # Ideal Gazebo odometry is already exact. Letting AMCL correct
            # map->odom in that mode makes the displayed map drift and yaw.
            'tf_broadcast': ParameterValue(
                IfElseSubstitution(
                    EqualsSubstitution(sensor_profile, 'ideal'),
                    if_value='false',
                    else_value='true',
                ),
                value_type=bool,
            ),
        }],
    )
    ideal_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='ideal_map_to_odom',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'map', '--child-frame-id', 'odom',
        ],
        condition=IfCondition(EqualsSubstitution(sensor_profile, 'ideal')),
        output='screen',
    )
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[common_parameters, {'use_sim_time': True}],
    )
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_path_planning',
        output='screen',
        parameters=[common_parameters, {'use_sim_time': True}],
        condition=IfCondition(use_lifecycle_manager),
    )
    path_requester = Node(
        package='cargo_bot_navigation',
        executable='path_requester',
        output='screen',
        parameters=[common_parameters, {'use_sim_time': True}],
        condition=IfCondition(use_path_requester),
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=[
            '-d', os.path.join(
                navigation_share, 'rviz', 'path_planning.rviz',
            ),
        ],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        UnsetEnvironmentVariable('SNAP'),
        UnsetEnvironmentVariable('SNAP_COMMON'),
        DeclareLaunchArgument(
            'map', default_value='',
            description='Required path to a user-created occupancy-map YAML.',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(
                navigation_share, 'config', 'path_planning.yaml',
            ),
        ),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_path_requester', default_value='true'),
        DeclareLaunchArgument('use_lifecycle_manager', default_value='true'),
        DeclareLaunchArgument(
            'sensor_profile', default_value='ideal',
            choices=['ideal', 'realistic', 'harsh'],
        ),
        DeclareLaunchArgument('initial_pose_x', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_z', default_value='0.1'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='1.5708'),
        DeclareLaunchArgument(
            'gz_partition', default_value='cargo_bot_path_planning',
        ),
        DeclareLaunchArgument('navigation_start_delay', default_value='0.0'),
        OpaqueFunction(function=_validate_user_map),
        indoor_world,
        TimerAction(
            period=navigation_start_delay,
            actions=[
                map_server,
                amcl,
                ideal_map_to_odom,
                planner_server,
                lifecycle_manager,
                path_requester,
                rviz,
            ],
        ),
    ])
