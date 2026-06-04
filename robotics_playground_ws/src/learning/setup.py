import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'learning'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gudzenko',
    maintainer_email='o.gudzenko@weegree.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'topics_status_pub = learning.topics.status_publisher:main',
            'topics_status_sub = learning.topics.status_subscriber:main',
            'topics_command_pub = learning.topics.command_publisher:main',
            'topics_command_sub = learning.topics.command_subscriber:main',
            'services_robot_server = learning.services.robot_server:main',
            'services_reset_client = learning.services.reset_client:main',
            'services_status_client = learning.services.status_client:main',
            'actions_count_mission_server = learning.actions.count_mission_server:main',
            'actions_count_mission_client = learning.actions.count_mission_client:main',
            'parameters_configurable_pub = learning.parameters.configurable_pub:main',
            'parameters_param_client = learning.parameters.param_client:main',
            'lifecycle_managed_sensor = learning.lifecycle.managed_sensor:main',
            'qos_publisher = learning.qos.qos_publisher:main',
            'qos_subscriber = learning.qos.qos_subscriber:main',
            'executors_blocking_demo = learning.executors.blocking_demo:main',
            'diagnostics_robot_monitor = learning.diagnostics.robot_monitor:main',
            'ci_robot_status_pub = learning.custom_interfaces.robot_status_pub:main',
            'ci_robot_status_sub = learning.custom_interfaces.robot_status_sub:main',
            'ci_patrol_points_server = learning.custom_interfaces.patrol_points_server:main',
            'ci_set_patrol_points = learning.custom_interfaces.patrol_points_client:main',
            'ci_patrol_server = learning.custom_interfaces.patrol_action_server:main',
            'ci_patrol_client = learning.custom_interfaces.patrol_action_client:main',
        ],
    },
)
