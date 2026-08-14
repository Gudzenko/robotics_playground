"""Navigate to RViz goals in the unchanged mapped indoor world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    UnsetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import IfElseSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterFile


SNAP_GRAPHICS_ENVIRONMENT = (
    'SNAP',
    'SNAP_COMMON',
    'SNAP_DATA',
    'SNAP_LIBRARY_PATH',
    'SNAP_USER_COMMON',
    'SNAP_USER_DATA',
    'GTK_EXE_PREFIX',
    'GTK_PATH',
    'GDK_PIXBUF_MODULEDIR',
    'GDK_PIXBUF_MODULE_FILE',
    'GIO_MODULE_DIR',
    'GSETTINGS_SCHEMA_DIR',
    'LOCPATH',
    'XDG_DATA_HOME',
    'XDG_DATA_DIRS',
)


def generate_launch_description():
    navigation_share = get_package_share_directory('cargo_bot_navigation')
    map_path = LaunchConfiguration('map')
    initial_x = LaunchConfiguration('initial_pose_x')
    initial_y = LaunchConfiguration('initial_pose_y')
    initial_z = LaunchConfiguration('initial_pose_z')
    initial_yaw = LaunchConfiguration('initial_pose_yaw')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    sensor_profile = LaunchConfiguration('sensor_profile')
    gz_partition = LaunchConfiguration('gz_partition')
    navigation_params = LaunchConfiguration('navigation_params_file')
    navigation_bt = LaunchConfiguration('navigation_bt_file')
    use_collision_monitor = LaunchConfiguration('use_collision_monitor')

    planning = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(navigation_share, 'launch', 'path_planning.launch.py'),
        ),
        launch_arguments={
            'map': map_path,
            'initial_pose_x': initial_x,
            'initial_pose_y': initial_y,
            'initial_pose_z': initial_z,
            'initial_pose_yaw': initial_yaw,
            'headless': headless,
            'use_rviz': use_rviz,
            'use_path_requester': 'false',
            'use_lifecycle_manager': 'false',
            'sensor_profile': sensor_profile,
            'gz_partition': gz_partition,
            'navigation_start_delay': '6.0',
        }.items(),
    )
    params = ParameterFile(navigation_params, allow_substs=True)

    controller = Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=[params, {'use_sim_time': True}],
        remappings=[('cmd_vel', '/cmd_vel_nav')],
    )
    behavior = Node(
        package='nav2_behaviors', executable='behavior_server',
        name='behavior_server', output='screen',
        parameters=[params, {'use_sim_time': True}],
        remappings=[('cmd_vel', '/cmd_vel_nav')],
    )
    navigator = Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[params, {
            'use_sim_time': True,
            'default_nav_to_pose_bt_xml': navigation_bt,
        }],
    )
    smoother = Node(
        package='nav2_velocity_smoother', executable='velocity_smoother',
        name='velocity_smoother', output='screen',
        parameters=[params, {'use_sim_time': True}],
        remappings=[
            ('cmd_vel', '/cmd_vel_nav'),
            ('cmd_vel_smoothed', IfElseSubstitution(
                use_collision_monitor,
                if_value='/cmd_vel_smoothed',
                else_value='/cmd_vel',
            )),
        ],
    )
    collision_monitor = Node(
        package='nav2_collision_monitor', executable='collision_monitor',
        name='collision_monitor', output='screen',
        parameters=[params, {'use_sim_time': True}],
        condition=IfCondition(use_collision_monitor),
    )
    collision_lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_collision_monitor', output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'bond_timeout': 4.0,
            'node_names': ['collision_monitor'],
        }],
        condition=IfCondition(use_collision_monitor),
    )
    lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_static_navigation', output='screen',
        parameters=[params, {
            'use_sim_time': True,
            'autostart': True,
            'node_names': [
                'map_server', 'amcl', 'planner_server',
                'controller_server', 'behavior_server',
                'bt_navigator', 'velocity_smoother',
            ],
        }],
    )
    goal_navigator = Node(
        package='cargo_bot_navigation', executable='goal_navigator',
        name='navigation_cancel_service', output='screen',
        parameters=[params, {'use_sim_time': True}],
    )
    return LaunchDescription([
        # VS Code installed through Snap leaks incompatible runtime libraries
        # into Gazebo and RViz processes started from its terminal.
        *(
            UnsetEnvironmentVariable(name)
            for name in SNAP_GRAPHICS_ENVIRONMENT
        ),
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
            'gz_partition', default_value='cargo_bot_static_navigation',
        ),
        DeclareLaunchArgument(
            'navigation_params_file',
            default_value=os.path.join(
                navigation_share, 'config', 'static_navigation.yaml',
            ),
        ),
        DeclareLaunchArgument(
            'navigation_bt_file',
            default_value=os.path.join(
                navigation_share,
                'behavior_trees',
                'navigate_static_path.xml',
            ),
        ),
        DeclareLaunchArgument('use_collision_monitor', default_value='false'),
        planning,
        TimerAction(
            period=6.0,
            actions=[
                controller,
                behavior,
                navigator,
                smoother,
                collision_monitor,
                collision_lifecycle,
                lifecycle,
                goal_navigator,
            ],
        ),
    ])
