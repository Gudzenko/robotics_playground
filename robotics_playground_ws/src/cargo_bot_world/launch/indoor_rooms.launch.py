import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EqualsSubstitution,
    IfElseSubstitution,
    LaunchConfiguration,
    PythonExpression,
)
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    cargo_bot_world_share = get_package_share_directory('cargo_bot_world')
    cargo_bot_share = get_package_share_directory('cargo_bot')
    sensor_profile = LaunchConfiguration('sensor_profile')
    lidar_source = LaunchConfiguration('lidar_source')
    imu_source = LaunchConfiguration('imu_source')
    encoder_source = LaunchConfiguration('encoder_source')
    headless = LaunchConfiguration('headless')
    gz_partition = LaunchConfiguration('gz_partition')

    models_path = os.path.join(cargo_bot_world_share, 'models')
    world_file = os.path.join(cargo_bot_world_share, 'worlds', 'indoor_rooms.sdf')
    urdf_file = os.path.join(cargo_bot_share, 'urdf', 'cargo_bot.urdf.xacro')
    ekf_config = os.path.join(cargo_bot_share, 'config', 'ekf.yaml')

    robot_description = xacro.process_file(urdf_file, mappings={'visual_mode': 'prod'}).toxml()

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py',
            )
        ),
        launch_arguments={
            'gz_args': [
                IfElseSubstitution(
                    headless,
                    if_value='-s -r ',
                    else_value='-r ',
                ),
                world_file,
            ],
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
    )

    # Robot spawns at the centre of Room A (x=0, y=0), facing north (+Y)
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name',  'cargo_bot',
            '-string', robot_description,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
            '-Y', '1.5708',   # face north (+Y)
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        parameters=[{'use_sim_time': True}],
        remappings=[('/odom', '/ground_truth/odometry')],
    )

    lidar_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='lidar_bridge',
        arguments=[
            '/sim/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        parameters=[{
            'use_sim_time': True,
            'override_frame_id': 'lidar_link',
        }],
        condition=IfCondition(EqualsSubstitution(lidar_source, 'gazebo')),
    )

    lidar_relay = Node(
        package='cargo_bot',
        executable='lidar_relay',
        parameters=[{
            'use_sim_time': True,
            'profile': sensor_profile,
            'source': lidar_source,
        }],
    )

    imu_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='imu_bridge',
        arguments=[
            '/sim/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        parameters=[{
            'use_sim_time': True,
            'override_frame_id': 'imu_link',
        }],
        condition=IfCondition(EqualsSubstitution(imu_source, 'gazebo')),
    )

    imu_relay = Node(
        package='cargo_bot',
        executable='imu_relay',
        parameters=[{
            'use_sim_time': True,
            'profile': sensor_profile,
            'source': imu_source,
        }],
    )

    encoder_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='encoder_bridge',
        arguments=[
            '/sim/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(EqualsSubstitution(encoder_source, 'gazebo')),
    )

    wheel_odometry = Node(
        package='cargo_bot',
        executable='wheel_odometry',
        parameters=[{
            'use_sim_time': True,
            'profile': sensor_profile,
            'source': encoder_source,
        }],
    )

    mock_sensor_publisher = Node(
        package='cargo_bot',
        executable='mock_sensor_publisher',
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(PythonExpression([
            "'", lidar_source, "' == 'mock' or '",
            imu_source, "' == 'mock' or '",
            encoder_source, "' == 'mock'",
        ])),
    )

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config, {'use_sim_time': True}],
        remappings=[('odometry/filtered', '/odometry/filtered')],
    )

    manipulator_control = Node(
        package='cargo_bot',
        executable='manipulator_control_node',
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run only the Gazebo server and start immediately.',
        ),
        DeclareLaunchArgument(
            'sensor_profile',
            default_value='ideal',
            description='Sensor noise profile: ideal, realistic or harsh.',
        ),
        DeclareLaunchArgument(
            'lidar_source',
            default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'imu_source',
            default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'encoder_source',
            default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'gz_partition',
            default_value='cargo_bot_indoor_rooms',
            description='Gazebo transport partition for launch isolation.',
        ),
        SetEnvironmentVariable('GZ_PARTITION', gz_partition),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', models_path),
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        lidar_bridge,
        lidar_relay,
        imu_bridge,
        imu_relay,
        encoder_bridge,
        wheel_odometry,
        mock_sensor_publisher,
        ekf,
        manipulator_control,
    ])
