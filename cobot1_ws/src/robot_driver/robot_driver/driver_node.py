import rclpy
from rclpy.node import Node
from .robot_driver import RobotDriver


class DriverNode(Node):

    def __init__(self):

        super().__init__("robot_driver")

        self.declare_parameter(
            "robot_name",
            "dsr01",
        )

        robot_name = self.get_parameter("robot_name").get_parameter_value().string_value

        self.driver = RobotDriver(
            self,
            robot_name,
        )

        self.get_logger().info("Robot Driver initialized")


def main(args=None):

    rclpy.init(args=args)

    node = DriverNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
