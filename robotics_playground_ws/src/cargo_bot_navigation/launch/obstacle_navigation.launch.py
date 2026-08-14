"""Navigate while detecting, avoiding and safely stopping for new obstacles."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('cargo_bot_navigation')
    static_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(share, 'launch', 'static_navigation.launch.py'),
        ),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'initial_pose_x': LaunchConfiguration('initial_pose_x'),
            'initial_pose_y': LaunchConfiguration('initial_pose_y'),
            'initial_pose_z': LaunchConfiguration('initial_pose_z'),
            'initial_pose_yaw': LaunchConfiguration('initial_pose_yaw'),
            'headless': LaunchConfiguration('headless'),
            'use_rviz': LaunchConfiguration('use_rviz'),
            'sensor_profile': LaunchConfiguration('sensor_profile'),
            'gz_partition': LaunchConfiguration('gz_partition'),
            'use_collision_monitor': 'true',
            'navigation_bt_file': os.path.join(
                share, 'behavior_trees', 'navigate_with_obstacles.xml',
            ),
        }.items(),
    )
    obstacle_manager = Node(
        package='cargo_bot_navigation', executable='obstacle_manager',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'x': LaunchConfiguration('obstacle_x'),
            'y': LaunchConfiguration('obstacle_y'),
            'size_x': LaunchConfiguration('obstacle_size_x'),
            'size_y': LaunchConfiguration('obstacle_size_y'),
            'size_z': LaunchConfiguration('obstacle_size_z'),
        }],
    )
    obstacle_memory = Node(
        package='cargo_bot_navigation',
        executable='persistent_obstacle_memory',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=''),
        DeclareLaunchArgument('initial_pose_x', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_y', default_value='0.0'),
        DeclareLaunchArgument('initial_pose_z', default_value='0.1'),
        DeclareLaunchArgument('initial_pose_yaw', default_value='1.5708'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument(
            'sensor_profile', default_value='ideal',
            choices=['ideal', 'realistic', 'harsh'],
        ),
        DeclareLaunchArgument(
            'gz_partition', default_value='cargo_bot_obstacle_navigation',
        ),
        DeclareLaunchArgument('obstacle_x', default_value='0.0'),
        DeclareLaunchArgument('obstacle_y', default_value='3.0'),
        DeclareLaunchArgument('obstacle_size_x', default_value='0.8'),
        DeclareLaunchArgument('obstacle_size_y', default_value='0.8'),
        DeclareLaunchArgument('obstacle_size_z', default_value='1.0'),
        static_launch,
        obstacle_manager,
        obstacle_memory,
    ])
