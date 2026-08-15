"""Tests for configurable Gazebo obstacles."""

from pathlib import Path
from xml.etree import ElementTree

from cargo_bot_navigation.obstacle_manager import obstacle_sdf


def test_obstacle_sdf_has_static_collision_and_requested_size():
    root = ElementTree.fromstring(obstacle_sdf('box', 0.8, 0.6, 1.0))

    assert root.findtext('./model/static') == 'true'
    assert root.findtext('./model/link/collision/geometry/box/size') == '0.8 0.6 1.0'
    assert root.find('./model/link/visual') is not None


def test_obstacle_sdf_escapes_model_name():
    root = ElementTree.fromstring(obstacle_sdf('box"<&', 1.0, 1.0, 1.0))

    assert root.find('./model').attrib['name'] == 'box"<&'


def test_manager_exposes_motion_and_secondary_obstacle_services():
    source = (
        Path(__file__).parents[1]
        / 'cargo_bot_navigation' / 'obstacle_manager.py'
    ).read_text()

    assert '/spawn_secondary_navigation_obstacle' in source
    assert '/remove_secondary_navigation_obstacle' in source
    assert '/start_moving_navigation_obstacle' in source
    assert 'SetEntityPose' in source


def test_indoor_world_bridges_set_entity_pose():
    launch = (
        Path(__file__).parents[2]
        / 'cargo_bot_world' / 'launch' / 'indoor_rooms.launch.py'
    ).read_text()

    assert '/world/indoor_rooms/set_pose@ros_gz_interfaces/srv/SetEntityPose' in launch
