from cargo_bot.warehouse_scene.boxes import make_box_markers
from cargo_bot.warehouse_scene.floor import make_floor_marker
from cargo_bot.warehouse_scene.shelves import make_shelf_markers
from cargo_bot.warehouse_scene.walls import make_boundary_wall_markers
from cargo_bot.warehouse_scene.zones import make_loading_zone_marker
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import MarkerArray


WAREHOUSE_SCENE_TOPIC = 'warehouse_scene'
WAREHOUSE_FRAME_ID = 'odom'
PUBLISH_PERIOD_SEC = 1.0


class WarehouseScenePublisher(Node):
    def __init__(self):
        super().__init__('warehouse_scene_publisher')
        self._publisher = self.create_publisher(
            MarkerArray,
            WAREHOUSE_SCENE_TOPIC,
            10,
        )
        self._timer = self.create_timer(PUBLISH_PERIOD_SEC, self._publish_scene)
        self.get_logger().info('Warehouse scene publisher started')

    def _publish_scene(self):
        stamp = self.get_clock().now().to_msg()
        marker_array = MarkerArray()
        marker_array.markers.append(
            make_floor_marker(WAREHOUSE_FRAME_ID, stamp)
        )
        marker_array.markers.extend(
            make_boundary_wall_markers(WAREHOUSE_FRAME_ID, stamp)
        )
        marker_array.markers.extend(
            make_shelf_markers(WAREHOUSE_FRAME_ID, stamp)
        )
        marker_array.markers.extend(
            make_box_markers(WAREHOUSE_FRAME_ID, stamp)
        )
        marker_array.markers.append(
            make_loading_zone_marker(WAREHOUSE_FRAME_ID, stamp)
        )
        self._publisher.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = WarehouseScenePublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Warehouse scene publisher stopped')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
