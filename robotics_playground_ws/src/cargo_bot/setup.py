from glob import glob
from os.path import join

from setuptools import find_packages, setup

package_name = 'cargo_bot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (join('share', package_name, 'config'), glob('config/*.yaml')),
        (join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gudzenko',
    maintainer_email='o.gudzenko@weegree.com',
    description='Warehouse cargo robot model, RViz visualization, and control nodes',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_diff_drive_sim = cargo_bot.simple_diff_drive_sim:main',
            'manipulator_control_node = cargo_bot.manipulator_control_node:main',
            'passive_joint_state_publisher = cargo_bot.passive_joint_state_publisher:main',
            'warehouse_scene_publisher = cargo_bot.warehouse_scene_publisher:main',
        ],
    },
)
