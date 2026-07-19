"""Launch sensor-specific real-time diagnostic visualizations."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_rviz = LaunchConfiguration('use_rviz')
    use_imu_plots = LaunchConfiguration('use_imu_plots')
    use_encoder_plot = LaunchConfiguration('use_encoder_plot')
    lidar_input_topic = LaunchConfiguration('lidar_input_topic')
    imu_input_topic = LaunchConfiguration('imu_input_topic')
    encoder_input_topic = LaunchConfiguration('encoder_input_topic')
    rviz_config = PathJoinSubstitution([
        FindPackageShare('cargo_bot'),
        'rviz',
        'cargo_bot_sensor_diagnostics.rviz',
    ])

    gyro_topics = [
        PythonExpression(["'", imu_input_topic, "/angular_velocity/x'"]),
        PythonExpression(["'", imu_input_topic, "/angular_velocity/y'"]),
        PythonExpression(["'", imu_input_topic, "/angular_velocity/z'"]),
        '/imu/data_raw/angular_velocity/x',
        '/imu/data_raw/angular_velocity/y',
        '/imu/data_raw/angular_velocity/z',
    ]
    acceleration_topics = [
        PythonExpression(["'", imu_input_topic, "/linear_acceleration/x'"]),
        PythonExpression(["'", imu_input_topic, "/linear_acceleration/y'"]),
        PythonExpression(["'", imu_input_topic, "/linear_acceleration/z'"]),
        '/imu/data_raw/linear_acceleration/x',
        '/imu/data_raw/linear_acceleration/y',
        '/imu/data_raw/linear_acceleration/z',
    ]
    encoder_topics = [
        PythonExpression(["'", encoder_input_topic, "/position[0]'"]),
        PythonExpression(["'", encoder_input_topic, "/position[1]'"]),
    ]

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_imu_plots', default_value='true'),
        DeclareLaunchArgument('use_encoder_plot', default_value='true'),
        DeclareLaunchArgument('lidar_input_topic', default_value='/sim/scan'),
        DeclareLaunchArgument('imu_input_topic', default_value='/sim/imu'),
        DeclareLaunchArgument(
            'encoder_input_topic',
            default_value='/sim/joint_states',
        ),
        Node(
            package='cargo_bot',
            executable='odometry_path_publisher',
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='sensor_diagnostics_rviz',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            remappings=[('/sim/scan', lidar_input_topic)],
            condition=IfCondition(use_rviz),
        ),
        Node(
            package='rqt_plot',
            executable='rqt_plot',
            name='gyroscope_plot',
            arguments=['--empty', *gyro_topics],
            condition=IfCondition(use_imu_plots),
        ),
        Node(
            package='rqt_plot',
            executable='rqt_plot',
            name='accelerometer_plot',
            arguments=['--empty', *acceleration_topics],
            condition=IfCondition(use_imu_plots),
        ),
        Node(
            package='rqt_plot',
            executable='rqt_plot',
            name='encoder_plot',
            arguments=['--empty', *encoder_topics],
            condition=IfCondition(use_encoder_plot),
        ),
    ])
