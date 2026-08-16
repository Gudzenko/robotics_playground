from glob import glob
from os.path import join

from setuptools import find_packages, setup


package_name = 'cargo_bot_navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (join('share', package_name, 'config'), glob('config/*.yaml')),
        (join('share', package_name, 'behavior_trees'),
            glob('behavior_trees/*.xml')),
        (join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (join('share', package_name, 'maps'), glob('maps/*')),
        (join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gudzenko',
    maintainer_email='o.gudzenko@weegree.com',
    description='SLAM, localization and navigation configuration for Cargo Bot',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'path_requester = cargo_bot_navigation.path_requester:main',
            'goal_navigator = cargo_bot_navigation.goal_navigator:main',
            'obstacle_manager = cargo_bot_navigation.obstacle_manager:main',
            'persistent_obstacle_memory = cargo_bot_navigation.persistent_obstacle_memory:main',
            'save_slam_map = cargo_bot_navigation.save_slam_map:main',
            'mapping_demo = cargo_bot_navigation.mapping_demo:main',
        ],
    },
)
