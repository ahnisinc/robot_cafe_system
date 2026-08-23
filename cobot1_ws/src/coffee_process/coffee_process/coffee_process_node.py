#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from cafe_interfaces.msg import ProcessStatus


class CoffeeProcessNode(Node):

    def __init__(self):

        super().__init__("coffee_process")

        self.status_publisher = self.create_publisher(
            ProcessStatus, "/coffee_process/status", 10
        )

        self.order_id = ""
        self.recipe_id = ""
        self.state = "STANDBY"
        self.current_step = ""
        self.current_step_index = 0
        self.total_steps = 0
        self.progress = 0.0
        self.message = ""

        self.status_timer = self.create_timer(1.0, self.cb_publish_status)

        self.get_logger().info("Coffee process node started")
        self.get_logger().info("Publishing: /coffee_process/status")

    def cb_publish_status(self):

        msg = ProcessStatus()

        msg.order_id           = self.order_id
        msg.recipe_id          = self.recipe_id
        msg.state              = self.state
        msg.current_step       = self.current_step
        msg.current_step_index = self.current_step_index
        msg.total_steps        = self.total_steps
        msg.progress           = self.progress
        msg.message            = self.message

        self.status_publisher.publish(msg)

    def update_process_state(
        self,
        state,
        current_step       = "",
        current_step_index = 0,
        total_steps        = 0,
        progress           = 0.0,
        message            = "",
    ):

        self.state = state

        self.current_step       = current_step
        self.current_step_index = current_step_index
        self.total_steps        = total_steps
        self.progress           = float(progress)
        self.message            = message

        self.get_logger().info(
            f"Coffee process: " f"{state} / " f"{current_step} / " f"{progress:.1f}%"
        )

        self.publish_status()

    def set_order(self, order_id, recipe_id):

        self.order_id = order_id
        self.recipe_id = recipe_id

        self.get_logger().info(f"Order started: " f"{order_id} / {recipe_id}")


def main(args=None):

    rclpy.init(args=args)

    node = CoffeeProcessNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
