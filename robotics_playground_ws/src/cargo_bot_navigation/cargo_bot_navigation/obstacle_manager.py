"""Spawn and remove one configurable static obstacle in Gazebo."""

from xml.sax.saxutils import escape

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SetEntityPose, SpawnEntity
from std_srvs.srv import Trigger


def obstacle_sdf(name, size_x, size_y, size_z):
    """Create SDF for a visible collision-enabled static box."""
    safe_name = escape(name, {'"': '&quot;'})
    size = f'{size_x} {size_y} {size_z}'
    return (
        '<?xml version="1.0"?>'
        '<sdf version="1.8">'
        f'<model name="{safe_name}"><static>true</static><link name="link">'
        f'<collision name="collision"><geometry><box><size>{size}</size>'
        '</box></geometry></collision>'
        '<visual name="visual"><geometry><box>'
        f'<size>{size}</size></box></geometry>'
        '<material><ambient>0.9 0.15 0.05 1</ambient>'
        '<diffuse>0.9 0.15 0.05 1</diffuse></material></visual>'
        '</link></model></sdf>'
    )


class ObstacleManager(Node):
    """Expose simple services for a parameterized Gazebo obstacle."""

    def __init__(self):
        super().__init__('obstacle_manager')
        self._name = self.declare_parameter(
            'obstacle_name', 'navigation_obstacle',
        ).value
        self._x = float(self.declare_parameter('x', 0.0).value)
        self._y = float(self.declare_parameter('y', 3.0).value)
        self._size_x = float(self.declare_parameter('size_x', 0.8).value)
        self._size_y = float(self.declare_parameter('size_y', 0.8).value)
        self._size_z = float(self.declare_parameter('size_z', 1.0).value)
        self._secondary_name = self.declare_parameter(
            'secondary_obstacle_name', 'secondary_navigation_obstacle',
        ).value
        self.declare_parameter('secondary_x', 1.0)
        self.declare_parameter('secondary_y', 3.0)
        self.declare_parameter('secondary_size_x', 0.6)
        self.declare_parameter('secondary_size_y', 0.6)
        self.declare_parameter('secondary_size_z', 1.0)
        self.declare_parameter('moving_target_x', 0.0)
        self.declare_parameter('moving_target_y', 4.0)
        self.declare_parameter('moving_duration', 4.0)
        world = self.declare_parameter('world', 'indoor_rooms').value
        group = ReentrantCallbackGroup()
        self._spawn_client = self.create_client(
            SpawnEntity, f'/world/{world}/create', callback_group=group,
        )
        self._delete_client = self.create_client(
            DeleteEntity, f'/world/{world}/remove', callback_group=group,
        )
        self._pose_client = self.create_client(
            SetEntityPose, f'/world/{world}/set_pose', callback_group=group,
        )
        self.create_service(
            Trigger, '/spawn_navigation_obstacle', self._spawn,
            callback_group=group,
        )
        self.create_service(
            Trigger, '/remove_navigation_obstacle', self._remove,
            callback_group=group,
        )
        self.create_service(
            Trigger, '/spawn_secondary_navigation_obstacle',
            self._spawn_secondary, callback_group=group,
        )
        self.create_service(
            Trigger, '/remove_secondary_navigation_obstacle',
            self._remove_secondary, callback_group=group,
        )
        self.create_service(
            Trigger, '/start_moving_navigation_obstacle',
            self._start_moving, callback_group=group,
        )
        self.create_service(
            Trigger, '/stop_moving_navigation_obstacle',
            self._stop_moving, callback_group=group,
        )
        self._moving = False
        self._moving_started_ns = 0
        self._moving_start = (self._x, self._y)
        self._pose_request = None
        self.create_timer(0.1, self._update_moving_obstacle)

    async def _spawn_entity(self, name, x, y, size_x, size_y, size_z):
        if not self._spawn_client.service_is_ready():
            return False
        spawn = SpawnEntity.Request()
        spawn.entity_factory.name = name
        spawn.entity_factory.allow_renaming = False
        spawn.entity_factory.sdf = obstacle_sdf(
            name, size_x, size_y, size_z,
        )
        spawn.entity_factory.pose.position.x = x
        spawn.entity_factory.pose.position.y = y
        spawn.entity_factory.pose.position.z = size_z / 2.0
        result = await self._spawn_client.call_async(spawn)
        return result.success

    async def _remove_entity(self, name):
        if not self._delete_client.service_is_ready():
            return False
        remove = DeleteEntity.Request()
        remove.entity.name = name
        remove.entity.type = Entity.MODEL
        result = await self._delete_client.call_async(remove)
        return result.success

    async def _spawn(self, request, response):
        del request
        self._x = float(self.get_parameter('x').value)
        self._y = float(self.get_parameter('y').value)
        self._size_x = float(self.get_parameter('size_x').value)
        self._size_y = float(self.get_parameter('size_y').value)
        self._size_z = float(self.get_parameter('size_z').value)
        response.success = await self._spawn_entity(
            self._name, self._x, self._y,
            self._size_x, self._size_y, self._size_z,
        )
        response.message = (
            f'Obstacle {self._name} spawned at ({self._x}, {self._y}).'
            if response.success else f'Could not spawn obstacle {self._name}.'
        )
        return response

    async def _remove(self, request, response):
        del request
        self._moving = False
        response.success = await self._remove_entity(self._name)
        response.message = (
            f'Obstacle {self._name} removed.'
            if response.success else f'Could not remove obstacle {self._name}.'
        )
        return response

    async def _spawn_secondary(self, request, response):
        del request
        x = float(self.get_parameter('secondary_x').value)
        y = float(self.get_parameter('secondary_y').value)
        size_x = float(self.get_parameter('secondary_size_x').value)
        size_y = float(self.get_parameter('secondary_size_y').value)
        size_z = float(self.get_parameter('secondary_size_z').value)
        response.success = await self._spawn_entity(
            self._secondary_name, x, y, size_x, size_y, size_z,
        )
        response.message = f'Secondary obstacle spawn: {response.success}.'
        return response

    async def _remove_secondary(self, request, response):
        del request
        response.success = await self._remove_entity(self._secondary_name)
        response.message = f'Secondary obstacle removal: {response.success}.'
        return response

    def _start_moving(self, request, response):
        del request
        if not self._pose_client.service_is_ready():
            response.message = 'Gazebo set-pose service is not ready.'
            return response
        self._moving_start = (self._x, self._y)
        self._moving_started_ns = self.get_clock().now().nanoseconds
        self._moving = True
        response.success = True
        response.message = 'Primary obstacle movement started.'
        return response

    def _stop_moving(self, request, response):
        del request
        self._moving = False
        response.success = True
        response.message = 'Primary obstacle movement stopped.'
        return response

    def _update_moving_obstacle(self):
        if not self._moving:
            return
        if self._pose_request is not None and not self._pose_request.done():
            return
        duration = max(float(self.get_parameter('moving_duration').value), 0.1)
        elapsed = (
            self.get_clock().now().nanoseconds - self._moving_started_ns
        ) / 1_000_000_000
        progress = min(max(elapsed / duration, 0.0), 1.0)
        target_x = float(self.get_parameter('moving_target_x').value)
        target_y = float(self.get_parameter('moving_target_y').value)
        self._x = self._moving_start[0] + progress * (
            target_x - self._moving_start[0]
        )
        self._y = self._moving_start[1] + progress * (
            target_y - self._moving_start[1]
        )
        pose = SetEntityPose.Request()
        pose.entity.name = self._name
        pose.entity.type = Entity.MODEL
        pose.pose.position.x = self._x
        pose.pose.position.y = self._y
        pose.pose.position.z = self._size_z / 2.0
        pose.pose.orientation.w = 1.0
        self._pose_request = self._pose_client.call_async(pose)
        if progress >= 1.0:
            self._moving = False


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleManager()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
