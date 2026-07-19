"""Resolve replaceable private sensor inputs from the shared configuration."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
import yaml


SOURCE_NAMES = ('gazebo', 'mock', 'rosbag', 'external')


def resolve_source_topic(sensor, source, config_path=None):
    """Return the configured private topic for one selected sensor source."""
    if config_path is None:
        package_share = Path(get_package_share_directory('cargo_bot'))
        config_path = package_share / 'config' / 'sensors.yaml'
    with Path(config_path).open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)

    if sensor not in ('lidar', 'imu', 'encoders'):
        raise ValueError(f'Unknown sensor type: {sensor}')
    if source not in SOURCE_NAMES:
        raise ValueError(f'Unknown {sensor} source: {source}')

    topics = config[sensor]['source_topics']
    if set(topics) != set(SOURCE_NAMES):
        raise ValueError(f'{sensor} must configure all replaceable source topics')
    topic = topics[source]
    if not topic or topic == config[sensor]['output_topic']:
        raise ValueError(f'{sensor} private source topic is invalid')
    return topic
