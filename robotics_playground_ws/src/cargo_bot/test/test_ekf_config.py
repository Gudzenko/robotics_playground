"""Tests for planar wheel-odometry and IMU EKF configuration."""

from pathlib import Path

import yaml


PACKAGE_PATH = Path(__file__).parents[1]
EKF_PATH = PACKAGE_PATH / 'config' / 'ekf.yaml'
WHEELS_XACRO_PATH = PACKAGE_PATH / 'urdf' / 'cargo_bot_wheels.xacro'


def _parameters():
    with EKF_PATH.open(encoding='utf-8') as config_file:
        return yaml.safe_load(config_file)['ekf_filter_node']['ros__parameters']


def test_ekf_is_planar_and_owns_local_odometry_tf():
    parameters = _parameters()

    assert parameters['two_d_mode'] is True
    assert parameters['publish_tf'] is True
    assert parameters['world_frame'] == 'odom'
    assert parameters['odom_frame'] == 'odom'
    assert parameters['base_link_frame'] == 'base_footprint'
    assert parameters['frequency'] == 50.0


def test_ekf_fuses_wheel_planar_pose_twist_and_only_imu_yaw_rate():
    parameters = _parameters()

    assert parameters['odom0'] == '/wheel/odometry'
    assert parameters['imu0'] == '/imu/data_raw'
    assert len(parameters['odom0_config']) == 15
    assert len(parameters['imu0_config']) == 15
    assert [index for index, enabled in enumerate(parameters['odom0_config']) if enabled] == [
        0, 1, 5, 6, 11,
    ]
    assert [index for index, enabled in enumerate(parameters['imu0_config']) if enabled] == [11]


def test_gazebo_ground_truth_tf_is_not_the_public_tf_topic():
    xacro_source = WHEELS_XACRO_PATH.read_text(encoding='utf-8')

    assert '<tf_topic>/ground_truth/tf</tf_topic>' in xacro_source
    assert '<tf_topic>/tf</tf_topic>' not in xacro_source
