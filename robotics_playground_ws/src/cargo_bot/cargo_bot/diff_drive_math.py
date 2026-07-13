"""Pure mathematical helpers for the differential-drive simulation."""

import math


def yaw_to_quaternion(yaw):
    """Convert a planar yaw angle to a quaternion dictionary."""
    half_yaw = yaw * 0.5
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(half_yaw),
        'w': math.cos(half_yaw),
    }


def normalize_angle(angle):
    """Normalize an angle to the interval from -pi to pi."""
    return math.atan2(math.sin(angle), math.cos(angle))


def integrate_pose(x, y, yaw, linear_velocity, angular_velocity, dt):
    """Integrate one Euler step of planar robot motion."""
    next_x = x + linear_velocity * math.cos(yaw) * dt
    next_y = y + linear_velocity * math.sin(yaw) * dt
    next_yaw = normalize_angle(yaw + angular_velocity * dt)
    return next_x, next_y, next_yaw


def wheel_angular_velocities(
    linear_velocity,
    angular_velocity,
    wheel_separation,
    wheel_radius,
):
    """Convert planar body velocity to left and right wheel velocities."""
    half_track_angular = angular_velocity * wheel_separation * 0.5
    left_velocity = (linear_velocity - half_track_angular) / wheel_radius
    right_velocity = (linear_velocity + half_track_angular) / wheel_radius
    return left_velocity, right_velocity
