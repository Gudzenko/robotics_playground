"""Spawn and remove one configurable static obstacle in Gazebo."""

from xml.sax.saxutils import escape

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity
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
        world = self.declare_parameter('world', 'indoor_rooms').value
        group = ReentrantCallbackGroup()
        self._spawn_client = self.create_client(
            SpawnEntity, f'/world/{world}/create', callback_group=group,
        )
        self._delete_client = self.create_client(
            DeleteEntity, f'/world/{world}/remove', callback_group=group,
        )
        self.create_service(
            Trigger, '/spawn_navigation_obstacle', self._spawn,
            callback_group=group,
        )
        self.create_service(
            Trigger, '/remove_navigation_obstacle', self._remove,
            callback_group=group,
        )

    async def _spawn(self, request, response):
        del request
        if not self._spawn_client.service_is_ready():
            response.message = 'Gazebo spawn service is not ready.'
            return response
        self._x = float(self.get_parameter('x').value)
        self._y = float(self.get_parameter('y').value)
        self._size_x = float(self.get_parameter('size_x').value)
        self._size_y = float(self.get_parameter('size_y').value)
        self._size_z = float(self.get_parameter('size_z').value)
        spawn = SpawnEntity.Request()
        spawn.entity_factory.name = self._name
        spawn.entity_factory.allow_renaming = False
        spawn.entity_factory.sdf = obstacle_sdf(
            self._name, self._size_x, self._size_y, self._size_z,
        )
        spawn.entity_factory.pose.position.x = self._x
        spawn.entity_factory.pose.position.y = self._y
        spawn.entity_factory.pose.position.z = self._size_z / 2.0
        result = await self._spawn_client.call_async(spawn)
        response.success = result.success
        response.message = (
            f'Obstacle {self._name} spawned at ({self._x}, {self._y}).'
            if result.success else f'Could not spawn obstacle {self._name}.'
        )
        return response

    async def _remove(self, request, response):
        del request
        if not self._delete_client.service_is_ready():
            response.message = 'Gazebo remove service is not ready.'
            return response
        remove = DeleteEntity.Request()
        remove.entity.name = self._name
        remove.entity.type = Entity.MODEL
        result = await self._delete_client.call_async(remove)
        response.success = result.success
        response.message = (
            f'Obstacle {self._name} removed.'
            if result.success else f'Could not remove obstacle {self._name}.'
        )
        return response


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
