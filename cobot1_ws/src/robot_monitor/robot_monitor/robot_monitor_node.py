# robot_monitor_node.py
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from cafe_interfaces.msg import RobotStatus

from .status_manager import MonitorStatus


class RobotMonitorNode(Node):

    def __init__(self):

        super().__init__("robot_monitor")

        self.status = MonitorStatus()

        self.status_publisher = self.create_publisher(
            RobotStatus,
            "/robot/status",
            10,
        )

        self.timer = self.create_timer(
            0.2,
            self.cb_update_status,
        )

        self.get_logger().info("Robot monitor started")

        self.get_logger().info("Publishing: /robot/status")

    def cb_update_status(self):

        msg = RobotStatus()

        msg.system            = self.status.system
        msg.mode              = self.status.mode
        msg.state             = self.status.state
        msg.servo_on          = self.status.servo_on
        msg.connected         = self.status.connected
        msg.alarm             = self.status.alarm
        msg.emergency_stopped = self.status.emergency_stopped
        msg.joints            = list(self.status.joints)
        msg.pose              = list(self.status.pose)
        msg.tcp               = self.status.tcp
        msg.tool              = self.status.tool

        self.status_publisher.publish(msg)

    # ================================================================
    # RobotDriver Integration
    # ================================================================

    def update_from_robot_driver(
        self,
        system=None,
        mode=None,
        state=None,
        servo_on=None,
        connected=None,
        alarm=None,
        emergency_stopped=None,
        joints=None,
        pose=None,
        tcp=None,
        tool=None,
    ):
        """
        RobotDriver에서 읽은 실제 로봇 상태를
        RobotMonitor의 내부 상태로 전달합니다.

        Doosan API를 이 함수에서 직접 호출하지 않습니다.

        RobotMonitor
            ↓
        RobotDriver
            ↓
        Doosan API
        """

        if system is not None:
            self.status.system = str(system)

        if mode is not None:
            self.status.mode = str(mode)

        if state is not None:
            self.status.state = str(state)

        if servo_on is not None:
            self.status.servo_on = bool(servo_on)

        if connected is not None:
            self.status.connected = bool(connected)

        if alarm is not None:
            self.status.alarm = str(alarm)

        if emergency_stopped is not None:
            self.status.emergency_stopped = bool(emergency_stopped)

        if joints is not None:

            if len(joints) == 6:
                self.status.joints = [float(value) for value in joints]

            else:
                self.get_logger().warning("Invalid joint data. " "Expected 6 values.")

        if pose is not None:

            if len(pose) == 6:
                self.status.pose = [float(value) for value in pose]

            else:
                self.get_logger().warning("Invalid pose data. " "Expected 6 values.")

        if tcp is not None:
            self.status.tcp = str(tcp)

        if tool is not None:
            self.status.tool = str(tool)


def main(args=None):

    rclpy.init(args=args)

    node = RobotMonitorNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
