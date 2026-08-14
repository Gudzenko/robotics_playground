"""Tests for configurable Gazebo obstacles."""

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
