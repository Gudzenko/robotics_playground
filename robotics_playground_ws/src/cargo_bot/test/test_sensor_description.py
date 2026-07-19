"""Tests for the navigation sensor description and interface contracts."""

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
import xacro
import yaml


PACKAGE_PATH = Path(__file__).parents[1]
GEOMETRY_PATH = PACKAGE_PATH / 'config' / 'cargo_bot_geometry.yaml'
SENSOR_CONFIG_PATH = PACKAGE_PATH / 'config' / 'sensors.yaml'
XACRO_PATH = PACKAGE_PATH / 'urdf' / 'cargo_bot.urdf.xacro'
RVIZ_PATHS = (
    PACKAGE_PATH / 'rviz' / 'cargo_bot_drive.rviz',
    PACKAGE_PATH / 'rviz' / 'cargo_bot_warehouse.rviz',
)


@pytest.fixture(scope='module')
def geometry():
    """Load the shared robot geometry."""
    with GEOMETRY_PATH.open(encoding='utf-8') as geometry_file:
        return yaml.safe_load(geometry_file)


@pytest.fixture(scope='module')
def sensor_config():
    """Load the navigation sensor configuration."""
    with SENSOR_CONFIG_PATH.open(encoding='utf-8') as sensor_file:
        return yaml.safe_load(sensor_file)


@pytest.fixture(scope='module')
def robot():
    """Evaluate the complete robot Xacro and return its XML root."""
    return ET.fromstring(xacro.process_file(str(XACRO_PATH)).toxml())


def _named_elements(robot, tag):
    return {element.attrib['name']: element for element in robot.findall(tag)}


def test_sensor_links_and_fixed_joints_are_in_robot_description(robot, geometry):
    """Both configured sensor frames should be fixed to their configured parent."""
    links = _named_elements(robot, 'link')
    joints = _named_elements(robot, 'joint')

    for sensor in geometry['sensors'].values():
        assert sensor['link'] in links
        joint = joints[sensor['joint']]
        assert joint.attrib['type'] == 'fixed'
        assert joint.find('parent').attrib['link'] == sensor['parent']
        assert joint.find('child').attrib['link'] == sensor['link']


def test_sensor_joint_origins_match_shared_geometry(robot, geometry):
    """Xacro origins should use the values from the shared geometry file."""
    joints = _named_elements(robot, 'joint')

    for sensor in geometry['sensors'].values():
        origin = joints[sensor['joint']].find('origin')
        assert [float(value) for value in origin.attrib['xyz'].split()] == [
            sensor['x'], sensor['y'], sensor['z'],
        ]
        assert [float(value) for value in origin.attrib['rpy'].split()] == [
            sensor['roll'], sensor['pitch'], sensor['yaw'],
        ]


def test_lidar_is_low_and_inside_the_fixed_chassis_front(geometry):
    """The lidar should sit low on the fixed chassis without crossing its front edge."""
    lidar = geometry['sensors']['lidar']
    scan_height = geometry['base']['base_link_z'] + lidar['z']
    chassis_front = geometry['chassis']['length'] / 2.0
    chassis_top = geometry['chassis']['height'] / 2.0
    lidar_bottom = lidar['z'] - lidar['height'] / 2.0

    assert lidar['parent'] == geometry['frames']['base_link']
    assert lidar['x'] == pytest.approx(0.79)
    assert lidar['y'] == pytest.approx(0.0)
    assert scan_height == pytest.approx(0.3875)
    assert lidar_bottom == pytest.approx(chassis_top)
    assert lidar['x'] + lidar['radius'] < chassis_front
    assert lidar['radius'] == pytest.approx(0.025)


def test_navigation_sensor_interface_contract(sensor_config, geometry):
    """Source and stable topic names should match the agreed navigation contract."""
    assert sensor_config['profile'] == 'ideal'
    assert sensor_config['random_seed'] == 42
    assert sensor_config['lidar']['source_topic'] == '/sim/scan'
    assert sensor_config['lidar']['output_topic'] == '/scan'
    assert sensor_config['lidar']['frame'] == geometry['sensors']['lidar']['link']
    assert sensor_config['imu']['source_topic'] == '/sim/imu'
    assert sensor_config['imu']['output_topic'] == '/imu/data_raw'
    assert sensor_config['imu']['frame'] == geometry['sensors']['imu']['link']
    assert sensor_config['encoders']['source_topic'] == '/sim/joint_states'
    assert sensor_config['encoders']['output_topic'] == '/wheel/odometry'
    assert sensor_config['encoders']['ground_truth_topic'] == '/ground_truth/odometry'
    assert sensor_config['encoders']['ticks_per_revolution'] == 2048
    assert sensor_config['localization']['output_topic'] == '/odometry/filtered'


def test_gazebo_lidar_matches_shared_sensor_config(robot, sensor_config, geometry):
    """The ideal GPU lidar should be configured from the shared YAML values."""
    lidar_config = sensor_config['lidar']
    lidar = robot.find(f".//sensor[@name='{lidar_config['name']}']")

    assert lidar is not None
    assert lidar.attrib['type'] == 'gpu_lidar'
    assert lidar.findtext('topic') == lidar_config['source_topic']
    assert float(lidar.findtext('update_rate')) == lidar_config['update_rate']
    assert int(lidar.findtext('lidar/scan/horizontal/samples')) == (
        lidar_config['horizontal_samples']
    )
    assert float(lidar.findtext('lidar/scan/horizontal/min_angle')) == (
        lidar_config['min_angle']
    )
    assert float(lidar.findtext('lidar/scan/horizontal/max_angle')) == (
        lidar_config['max_angle']
    )
    assert float(lidar.findtext('lidar/range/min')) == lidar_config['min_range']
    assert float(lidar.findtext('lidar/range/max')) == lidar_config['max_range']
    gazebo = robot.find(
        f"gazebo[@reference='{geometry['sensors']['lidar']['link']}']",
    )
    assert lidar in list(gazebo)


def test_gazebo_imu_matches_shared_sensor_config(robot, sensor_config, geometry):
    """The ideal Gazebo IMU should use the shared frame, topic and rate."""
    imu_config = sensor_config['imu']
    imu = robot.find(f".//sensor[@name='{imu_config['name']}']")

    assert imu is not None
    assert imu.attrib['type'] == 'imu'
    assert imu.findtext('topic') == imu_config['source_topic']
    assert float(imu.findtext('update_rate')) == imu_config['update_rate']
    gazebo = robot.find(
        f"gazebo[@reference='{geometry['sensors']['imu']['link']}']",
    )
    assert imu in list(gazebo)
    assert len(robot.findall('.//sensor')) == 2


def test_gazebo_publishes_both_drive_wheel_joint_states(robot, geometry):
    """Gazebo should provide the wheel transforms and future encoder input."""
    plugin = robot.find(
        ".//plugin[@name='gz::sim::systems::JointStatePublisher']",
    )

    assert plugin is not None
    assert plugin.findtext('topic') == '/sim/joint_states'
    assert [element.text for element in plugin.findall('joint_name')] == [
        geometry['drive_wheels']['left_joint'],
        geometry['drive_wheels']['right_joint'],
    ]


@pytest.mark.parametrize('rviz_path', RVIZ_PATHS)
def test_rviz_lidar_uses_reliable_public_scan_qos(rviz_path):
    """Saved RViz scenes should subscribe reliably to the stable public scan."""
    with rviz_path.open(encoding='utf-8') as rviz_file:
        rviz_config = yaml.safe_load(rviz_file)

    displays = rviz_config['Visualization Manager']['Displays']
    lidar_display = next(
        display for display in displays
        if display['Class'] == 'rviz_default_plugins/LaserScan'
    )
    assert lidar_display['Topic'] == '/scan'
    assert lidar_display['Unreliable'] is False
