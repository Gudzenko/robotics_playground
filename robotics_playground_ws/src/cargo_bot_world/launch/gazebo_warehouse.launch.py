import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    cargo_bot_world_share = get_package_share_directory('cargo_bot_world')
    cargo_bot_share = get_package_share_directory('cargo_bot')

    models_path = os.path.join(cargo_bot_world_share, 'models')
    world_file = os.path.join(cargo_bot_world_share, 'worlds', 'small_warehouse.sdf')

    urdf_file = os.path.join(cargo_bot_share, 'urdf', 'cargo_bot.urdf.xacro')
    robot_description = xacro.process_file(urdf_file).toxml()

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={'gz_args': world_file}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'cargo_bot',
            '-string', robot_description,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
        ],
        parameters=[{'use_sim_time': True}],
    )

    manipulator_control = Node(
        package='cargo_bot',
        executable='manipulator_control_node',
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', models_path),
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        manipulator_control,
    ])
