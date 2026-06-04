import random

import rclpy
from rclpy.node import Node
from diagnostic_updater import Updater, DiagnosticStatusWrapper


BATTERY_WARN_THRESHOLD = 20.0
BATTERY_ERROR_THRESHOLD = 5.0
MOTOR_OVERHEAT_INTERVAL = 30
MOTOR_RECOVERY_INTERVAL = 5
SENSOR_UPDATE_RATE = 10.0


class RobotMonitor(Node):

    def __init__(self):
        super().__init__('robot_monitor')

        self._updater = Updater(self)
        self._updater.setHardwareID('learning_robot')

        self._battery = 100.0
        self._motor_overheat_counter = 0
        self._motor_overheated = False
        self._sensor_count = 0

        self._updater.add('Battery', self._check_battery)
        self._updater.add('Motor', self._check_motor)
        self._updater.add('Sensor', self._check_sensor)

        self.create_timer(1.0, self._update_state)

    def _update_state(self):
        self._battery -= random.uniform(0.5, 1.5)
        self._battery = max(self._battery, 0.0)

        self._motor_overheat_counter += 1
        if not self._motor_overheated and self._motor_overheat_counter >= MOTOR_OVERHEAT_INTERVAL:
            self._motor_overheated = True
            self._motor_overheat_counter = 0
        elif self._motor_overheated and self._motor_overheat_counter >= MOTOR_RECOVERY_INTERVAL:
            self._motor_overheated = False
            self._motor_overheat_counter = 0

        self._sensor_count += 1

    def _check_battery(self, stat: DiagnosticStatusWrapper):
        stat.add('voltage_percent', f'{self._battery:.1f}')
        if self._battery >= BATTERY_WARN_THRESHOLD:
            stat.summary(DiagnosticStatusWrapper.OK, 'Battery nominal')
        elif self._battery >= BATTERY_ERROR_THRESHOLD:
            stat.summary(DiagnosticStatusWrapper.WARN, 'Battery low')
        else:
            stat.summary(DiagnosticStatusWrapper.ERROR, 'Battery critical')
        return stat

    def _check_motor(self, stat: DiagnosticStatusWrapper):
        stat.add('overheated', str(self._motor_overheated))
        if self._motor_overheated:
            stat.summary(DiagnosticStatusWrapper.WARN, 'Motor overheated — cooling down')
        else:
            stat.summary(DiagnosticStatusWrapper.OK, 'Motor temperature nominal')
        return stat

    def _check_sensor(self, stat: DiagnosticStatusWrapper):
        stat.add('update_count', str(self._sensor_count))
        stat.add('update_rate_hz', f'{SENSOR_UPDATE_RATE:.1f}')
        stat.summary(DiagnosticStatusWrapper.OK, 'Sensor operating normally')
        return stat


def main(args=None):
    rclpy.init(args=args)
    node = RobotMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
