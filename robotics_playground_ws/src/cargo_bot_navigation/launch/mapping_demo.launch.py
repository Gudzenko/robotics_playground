"""Launch a two-window, automatic Cargo Bot SLAM demonstration."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Start Gazebo and RViz, then begin motion after ten seconds."""
    navigation_share = get_package_share_directory('cargo_bot_navigation')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    slam_launch = os.path.join(
        navigation_share,
        'launch',
        'slam_mapping.launch.py',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run Gazebo without its GUI when true.',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Start RViz with the SLAM display.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={
                'headless': headless,
                'use_rviz': use_rviz,
                'sensor_profile': 'ideal',
                'spawn_x': '0.0',
                'spawn_y': '3.0',
                'spawn_yaw': '0.0',
                'gz_partition': 'cargo_bot_mapping_demo',
            }.items(),
        ),
        TimerAction(
            period=10.0,
            actions=[
                Node(
                    package='cargo_bot_navigation',
                    executable='mapping_demo',
                    output='screen',
                ),
            ],
        ),
    ])
