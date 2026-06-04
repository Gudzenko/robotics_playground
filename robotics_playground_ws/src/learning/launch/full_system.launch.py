import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    publish_rate_arg = DeclareLaunchArgument(
        'publish_rate',
        default_value='1.0',
        description='Publish rate for configurable_pub in Hz',
    )

    learning_share = get_package_share_directory('learning')

    topics_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(learning_share, 'launch', 'topics.launch.py')
        )
    )

    return LaunchDescription([
        publish_rate_arg,
        LogInfo(msg='Starting full system...'),
        topics_launch,
        Node(
            package='learning',
            executable='services_robot_server',
        ),
        Node(
            package='learning',
            executable='actions_count_mission_server',
        ),
        Node(
            package='learning',
            executable='parameters_configurable_pub',
            parameters=[{'publish_rate': LaunchConfiguration('publish_rate')}],
        ),
    ])
