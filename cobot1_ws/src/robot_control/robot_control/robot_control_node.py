import rclpy

from rclpy.node import Node

from robot_driver.robot_driver import RobotDriver

from .robot_controller import RobotController
from .motion_manager import MotionManager
from .safety_manager import SafetyManager


class RobotControlNode(Node):

    def __init__(self):

        super().__init__("robot_control")

        self.driver = RobotDriver(self)
        self.motion = MotionManager(self.driver, {})
        self.safety = SafetyManager()

        self.controller = RobotController(
            self.driver,
            self.motion,
            self.safety,
        )


def main(args=None):

    rclpy.init(args=args)

    node = RobotControlNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
