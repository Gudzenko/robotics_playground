from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='learning',
            executable='topics_status_pub',
        ),
        Node(
            package='learning',
            executable='topics_status_sub',
        ),
    ])
