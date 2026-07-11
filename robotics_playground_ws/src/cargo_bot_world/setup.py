import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'cargo_bot_world'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ] + [
        (os.path.join('share', package_name, 'models', d), glob(os.path.join('models', d, '*.*')))
        for d in os.listdir('models') if os.path.isdir(os.path.join('models', d))
    ] + [
        (os.path.join('share', package_name, 'models', d, sub), glob(os.path.join('models', d, sub, '*.*')))
        for d in os.listdir('models') if os.path.isdir(os.path.join('models', d))
        for sub in os.listdir(os.path.join('models', d)) if os.path.isdir(os.path.join('models', d, sub))
    ] + [
        (os.path.join('share', package_name, 'models', d, sub, subsub), glob(os.path.join('models', d, sub, subsub, '*.*')))
        for d in os.listdir('models') if os.path.isdir(os.path.join('models', d))
        for sub in os.listdir(os.path.join('models', d)) if os.path.isdir(os.path.join('models', d, sub))
        for subsub in os.listdir(os.path.join('models', d, sub)) if os.path.isdir(os.path.join('models', d, sub, subsub))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gudzenko',
    maintainer_email='o.gudzenko@weegree.com',
    description='Gazebo warehouse world for cargo_bot simulation',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [],
    },
)
