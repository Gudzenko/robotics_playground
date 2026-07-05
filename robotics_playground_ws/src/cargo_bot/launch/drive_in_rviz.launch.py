from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    package_share = FindPackageShare('cargo_bot')
    visual_mode = LaunchConfiguration('visual_mode')

    xacro_file = PathJoinSubstitution([
        package_share,
        'urdf',
        'cargo_bot.urdf.xacro',
    ])
    rviz_config = PathJoinSubstitution([
        package_share,
        'rviz',
        'cargo_bot_drive.rviz',
    ])

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' visual_mode:=', visual_mode]),
        value_type=str,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'visual_mode',
            default_value='dev',
            description=(
                'Visual material mode: dev uses transparent materials, '
                'prod uses opaque materials.'
            ),
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='cargo_bot',
            executable='simple_diff_drive_sim',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
        ),
    ])
