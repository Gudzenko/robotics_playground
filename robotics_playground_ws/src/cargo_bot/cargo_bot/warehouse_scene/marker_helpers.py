from visualization_msgs.msg import Marker


def make_cube_marker(
    frame_id,
    stamp,
    namespace,
    marker_id,
    position,
    scale,
    color,
):
    marker = Marker()
    marker.header.frame_id = frame_id
    marker.header.stamp = stamp
    marker.ns = namespace
    marker.id = marker_id
    marker.type = Marker.CUBE
    marker.action = Marker.ADD
    marker.pose.position.x = position['x']
    marker.pose.position.y = position['y']
    marker.pose.position.z = position['z']
    marker.pose.orientation.w = 1.0
    marker.scale.x = scale['x']
    marker.scale.y = scale['y']
    marker.scale.z = scale['z']
    marker.color.r = color['r']
    marker.color.g = color['g']
    marker.color.b = color['b']
    marker.color.a = color['a']
    return marker
