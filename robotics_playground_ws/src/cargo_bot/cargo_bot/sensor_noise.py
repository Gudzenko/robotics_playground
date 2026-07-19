"""Pure deterministic noise models shared by navigation sensor nodes."""

import math
from pathlib import Path
import random

from ament_index_python.packages import get_package_share_directory
import yaml


PROFILE_NAMES = ('ideal', 'realistic', 'harsh')
SENSOR_SEED_OFFSETS = {'lidar': 101, 'imu': 211, 'encoders': 307}


def load_noise_profile(sensor, profile=None, config_path=None):
    """Load and validate one sensor's selected ROS-side noise profile."""
    if config_path is None:
        package_share = Path(get_package_share_directory('cargo_bot'))
        config_path = package_share / 'config' / 'sensors.yaml'
    with Path(config_path).open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)

    profile = profile or config['profile']
    if profile not in PROFILE_NAMES or profile not in config['noise_profiles']:
        raise ValueError(f'Unknown sensor noise profile: {profile}')
    if sensor not in SENSOR_SEED_OFFSETS:
        raise ValueError(f'Unknown sensor type: {sensor}')

    parameters = dict(config['noise_profiles'][profile][sensor])
    enabled = profile != 'ideal' and _contains_nonzero(parameters)
    if config[sensor]['gazebo_native_noise'] and enabled:
        raise ValueError(
            f'{sensor} cannot enable Gazebo-native and ROS-side noise together',
        )
    _validate_parameters(sensor, parameters)
    seed = int(config['random_seed']) + SENSOR_SEED_OFFSETS[sensor]
    return profile, seed, parameters


def _contains_nonzero(value):
    if isinstance(value, dict):
        return any(_contains_nonzero(item) for item in value.values())
    if isinstance(value, list):
        return any(float(item) != 0.0 for item in value)
    return float(value) != 0.0


def _validate_probability(name, value):
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f'{name} must be between 0 and 1')


def _validate_vector(name, value, nonnegative=False):
    if len(value) != 3 or any(not math.isfinite(float(item)) for item in value):
        raise ValueError(f'{name} must contain three finite values')
    if nonnegative and any(float(item) < 0.0 for item in value):
        raise ValueError(f'{name} values must be nonnegative')


def _validate_parameters(sensor, parameters):
    if sensor == 'lidar':
        if (
            not math.isfinite(float(parameters['gaussian_stddev']))
            or float(parameters['gaussian_stddev']) < 0.0
        ):
            raise ValueError('lidar gaussian_stddev must be nonnegative')
        if not math.isfinite(float(parameters['bias'])):
            raise ValueError('lidar bias must be finite')
        _validate_probability('lidar dropout_probability', parameters['dropout_probability'])
    elif sensor == 'imu':
        _validate_vector(
            'angular_velocity_stddev',
            parameters['angular_velocity_stddev'],
            nonnegative=True,
        )
        _validate_vector('angular_velocity_bias', parameters['angular_velocity_bias'])
        _validate_vector(
            'linear_acceleration_stddev',
            parameters['linear_acceleration_stddev'],
            nonnegative=True,
        )
        _validate_vector('linear_acceleration_bias', parameters['linear_acceleration_bias'])
        _validate_vector(
            'bias_drift_stddev',
            parameters['bias_drift_stddev'],
            nonnegative=True,
        )
    else:
        _validate_probability(
            'encoder missed_tick_probability',
            parameters['missed_tick_probability'],
        )
        if not all(math.isfinite(float(parameters[key])) for key in (
            'left_scale_error', 'right_scale_error',
        )):
            raise ValueError('encoder scale errors must be finite')


def apply_lidar_noise(ranges, range_min, range_max, parameters, generator):
    """Return noisy ranges while preserving length and existing invalid samples."""
    result = []
    for value in ranges:
        if not math.isfinite(value):
            result.append(value)
        elif generator.random() < parameters['dropout_probability']:
            result.append(math.inf)
        else:
            noisy = (
                value
                + parameters['bias']
                + generator.gauss(0.0, parameters['gaussian_stddev'])
            )
            result.append(min(range_max, max(range_min, noisy)))
    return result


class ImuNoiseModel:
    """Apply white noise, constant bias and a seeded bias random walk."""

    def __init__(self, parameters, generator):
        self._parameters = parameters
        self._generator = generator
        self._drift = [0.0, 0.0, 0.0]

    def apply(self, angular_velocity, linear_acceleration):
        """Return noisy angular velocity and acceleration triples."""
        for index, stddev in enumerate(self._parameters['bias_drift_stddev']):
            self._drift[index] += self._generator.gauss(0.0, stddev)
        angular = self._apply_vector(
            angular_velocity,
            self._parameters['angular_velocity_bias'],
            self._parameters['angular_velocity_stddev'],
        )
        acceleration = self._apply_vector(
            linear_acceleration,
            self._parameters['linear_acceleration_bias'],
            self._parameters['linear_acceleration_stddev'],
        )
        return angular, acceleration

    def _apply_vector(self, values, biases, stddevs):
        return tuple(
            value + bias + self._drift[index] + self._generator.gauss(0.0, stddev)
            for index, (value, bias, stddev) in enumerate(zip(values, biases, stddevs))
        )


def apply_encoder_noise(left_ticks, right_ticks, parameters, generator):
    """Apply wheel scale error followed by independently missed integer ticks."""
    return (
        _apply_wheel_tick_noise(
            left_ticks,
            parameters['left_scale_error'],
            parameters['missed_tick_probability'],
            generator,
        ),
        _apply_wheel_tick_noise(
            right_ticks,
            parameters['right_scale_error'],
            parameters['missed_tick_probability'],
            generator,
        ),
    )


def _apply_wheel_tick_noise(ticks, scale_error, missed_probability, generator):
    scaled = int(round(ticks * (1.0 + scale_error)))
    if missed_probability == 0.0:
        return scaled
    if missed_probability == 1.0:
        return 0
    sign = 1 if scaled >= 0 else -1
    retained = sum(
        generator.random() >= missed_probability for _ in range(abs(scaled))
    )
    return sign * retained


def seeded_generator(seed):
    """Create the explicit PRNG used by a sensor processor."""
    return random.Random(seed)
