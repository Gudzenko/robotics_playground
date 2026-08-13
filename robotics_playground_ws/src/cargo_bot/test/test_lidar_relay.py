"""Tests for the ideal lidar relay configuration."""

import math
from pathlib import Path

from cargo_bot.lidar_relay import (
    filter_self_returns,
    load_lidar_topics,
    load_self_filter,
)
import pytest


SENSOR_CONFIG_PATH = Path(__file__).parents[1] / 'config' / 'sensors.yaml'


def test_project_lidar_topics_are_loaded():
    """The relay should use the agreed source and stable output topics."""
    assert load_lidar_topics(SENSOR_CONFIG_PATH) == ('/sim/scan', '/scan')


def test_project_self_filter_covers_body_and_wheels():
    """The configured filter should be enabled with three valid masks."""
    enabled, origin_x, origin_y, boxes = load_self_filter(SENSOR_CONFIG_PATH)
    assert enabled is True
    assert (origin_x, origin_y) == (0.395, 0.0)
    assert len(boxes) == 3


def test_self_filter_removes_robot_return_but_preserves_wall():
    """Only endpoints inside the configured robot mask should be invalidated."""
    ranges = [0.30, 2.0, math.inf]
    filtered = filter_self_returns(
        ranges,
        angle_min=math.pi,
        angle_increment=-math.pi,
        lidar_origin_x=0.395,
        lidar_origin_y=0.0,
        exclusion_boxes=[(-0.875, 0.875, -0.55, 0.55)],
    )
    assert math.isinf(filtered[0])
    assert filtered[1] == 2.0
    assert math.isinf(filtered[2])


@pytest.mark.parametrize(
    'lidar_yaml',
    [
        'source_topic: ""\noutput_topic: /scan\n',
        'source_topic: /sim/scan\noutput_topic: ""\n',
        'source_topic: /scan\noutput_topic: /scan\n',
    ],
)
def test_invalid_lidar_topic_contract_is_rejected(tmp_path, lidar_yaml):
    """Empty or identical topics would create a broken relay graph."""
    config_path = tmp_path / 'sensors.yaml'
    indented_lidar_yaml = ''.join(
        f'  {line}\n' for line in lidar_yaml.splitlines()
    )
    config_path.write_text(
        f'lidar:\n{indented_lidar_yaml}',
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='non-empty and different'):
        load_lidar_topics(config_path)
