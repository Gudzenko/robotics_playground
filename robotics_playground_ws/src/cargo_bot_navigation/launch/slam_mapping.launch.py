"""Start the indoor Cargo Bot simulation and asynchronous SLAM Toolbox."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
    UnsetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.events import matches_action
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EqualsSubstitution,
    IfElseSubstitution,
    LaunchConfiguration,
)
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.parameter_descriptions import ParameterValue
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    """Create the parameterized indoor mapping launch graph."""
    navigation_share = get_package_share_directory('cargo_bot_navigation')
    world_share = get_package_share_directory('cargo_bot_world')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    sensor_profile = LaunchConfiguration('sensor_profile')
    lidar_source = LaunchConfiguration('lidar_source')
    imu_source = LaunchConfiguration('imu_source')
    encoder_source = LaunchConfiguration('encoder_source')
    gz_partition = LaunchConfiguration('gz_partition')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_z = LaunchConfiguration('spawn_z')
    spawn_yaw = LaunchConfiguration('spawn_yaw')
    slam_params_file = LaunchConfiguration('slam_params_file')
    pose_graph = LaunchConfiguration('pose_graph')
    map_start_at_dock = LaunchConfiguration('map_start_at_dock')

    indoor_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(world_share, 'launch', 'indoor_rooms.launch.py'),
        ),
        launch_arguments={
            'headless': headless,
            'sensor_profile': sensor_profile,
            'lidar_source': lidar_source,
            'imu_source': imu_source,
            'encoder_source': encoder_source,
            'gz_partition': gz_partition,
            'spawn_x': spawn_x,
            'spawn_y': spawn_y,
            'spawn_z': spawn_z,
            'spawn_yaw': spawn_yaw,
        }.items(),
    )

    slam = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
        parameters=[
            slam_params_file,
            {
                'use_sim_time': True,
                'map_file_name': pose_graph,
                'map_start_at_dock': map_start_at_dock,
                # Exact Gazebo odometry needs no scan-matcher corrections.
                # Keeping them enabled makes map->odom visibly jump.
                'use_scan_matching': ParameterValue(
                    IfElseSubstitution(
                        EqualsSubstitution(sensor_profile, 'ideal'),
                        if_value='false',
                        else_value='true',
                    ),
                    value_type=bool,
                ),
            },
        ],
    )
    configure_slam = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=matches_action(slam),
            transition_id=Transition.TRANSITION_CONFIGURE,
        ),
    )
    activate_slam = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slam,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                LogInfo(msg='SLAM Toolbox is activating.'),
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(slam),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    ),
                ),
            ],
        ),
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=[
            '-d', os.path.join(navigation_share, 'rviz', 'slam_mapping.rviz'),
        ],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        # VS Code installed through Snap leaks SNAP into integrated terminals.
        # SLAM Toolbox otherwise rewrites normal host paths into the Snap sandbox.
        UnsetEnvironmentVariable('SNAP'),
        UnsetEnvironmentVariable('SNAP_COMMON'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run Gazebo server-only when true.',
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Start the saved SLAM RViz scene.',
        ),
        DeclareLaunchArgument(
            'sensor_profile', default_value='ideal',
            choices=['ideal', 'realistic', 'harsh'],
            description='Sensor noise profile; ideal is the mapping baseline.',
        ),
        DeclareLaunchArgument(
            'lidar_source', default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'imu_source', default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'encoder_source', default_value='gazebo',
            choices=['gazebo', 'mock', 'rosbag', 'external'],
        ),
        DeclareLaunchArgument(
            'gz_partition', default_value='cargo_bot_slam_mapping',
            description='Gazebo transport partition for launch isolation.',
        ),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='0.0'),
        DeclareLaunchArgument('spawn_z', default_value='0.1'),
        DeclareLaunchArgument(
            'spawn_yaw', default_value='1.5708',
            description='Robot heading in radians; default faces north in room A.',
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(
                navigation_share, 'config', 'slam_mapping.yaml',
            ),
            description='SLAM Toolbox mapping parameter file.',
        ),
        DeclareLaunchArgument(
            'pose_graph', default_value='',
            description='Pose graph base path to continue, or empty for a new map.',
        ),
        DeclareLaunchArgument(
            'map_start_at_dock', default_value='false',
            description='Match a loaded pose graph at its first node.',
        ),
        indoor_world,
        slam,
        configure_slam,
        activate_slam,
        rviz,
    ])
