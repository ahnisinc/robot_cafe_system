import rclpy

from rclpy.node import Node


class IOControllerNode(Node):

    def __init__(self):

        super().__init__(
            "io_controller"
        )

        self.get_logger().info(
            "IO Controller started"
        )


def main(args=None):

    rclpy.init(args=args)

    node = IOControllerNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
