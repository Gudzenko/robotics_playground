"""Launch the RViz Cargo Bot model and its automatic demonstration."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Start the drive stack, RViz and delayed model choreography."""
    package_share = FindPackageShare('cargo_bot')
    drive_launch = PathJoinSubstitution([
        package_share,
        'launch',
        'drive_in_rviz.launch.py',
    ])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(drive_launch),
            launch_arguments={
                'visual_mode': 'prod',
                'use_rviz': 'true',
            }.items(),
        ),
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='cargo_bot',
                    executable='model_demo',
                    output='screen',
                ),
            ],
        ),
    ])
