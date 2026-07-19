"""Tests for the ideal lidar relay configuration."""

from pathlib import Path

from cargo_bot.lidar_relay import load_lidar_topics
import pytest


SENSOR_CONFIG_PATH = Path(__file__).parents[1] / 'config' / 'sensors.yaml'


def test_project_lidar_topics_are_loaded():
    """The relay should use the agreed source and stable output topics."""
    assert load_lidar_topics(SENSOR_CONFIG_PATH) == ('/sim/scan', '/scan')


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
