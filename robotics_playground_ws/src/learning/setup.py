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
        ],
    },
)
