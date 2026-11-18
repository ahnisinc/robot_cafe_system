import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import SingleThreadedExecutor

from cafe_interfaces.action import MoveJoint, MoveHome, MoveLine

from .robot_driver import RobotDriver


class DriverNode(Node):

    def __init__(self):

        super().__init__("robot_driver")

        self.declare_parameter(
            "robot_name",
            "dsr01",
        )

        self.declare_parameter(
            "robot_model",
            "m0609",
        )

        robot_name = self.get_parameter("robot_name").get_parameter_value().string_value
        robot_model = self.get_parameter("robot_model").get_parameter_value().string_value

        self.driver = RobotDriver(
            self,
            robot_name,
            robot_model,
        )

        self.get_logger().info("Robot Driver initialized")

        self._move_joint_server = ActionServer(
            self,
            MoveJoint,
            "/robot_driver/move_joint",
            execute_callback=self.execute_move_joint,
            goal_callback=self._accept_goal,
            cancel_callback=self._accept_cancel,
        )

        self._move_home_server = ActionServer(
            self,
            MoveHome,
            "/robot_driver/move_home",
            execute_callback=self.execute_move_home,
            goal_callback=self._accept_goal,
            cancel_callback=self._accept_cancel,
        )

        self._move_line_server = ActionServer(
            self,
            MoveLine,
            "/robot_driver/move_line",
            execute_callback=self.execute_move_line,
            goal_callback=self._accept_goal,
            cancel_callback=self._accept_cancel,
        )

        self.get_logger().info("Robot driver actions ready")
        self.get_logger().info("  /robot_driver/move_joint")
        self.get_logger().info("  /robot_driver/move_home")
        self.get_logger().info("  /robot_driver/move_line")

    def _accept_goal(self, goal_request):
        return GoalResponse.ACCEPT

    def _accept_cancel(self, goal_handle):
        return CancelResponse.ACCEPT

    def execute_move_joint(self, goal_handle):

        goal = goal_handle.request
        result = MoveJoint.Result()

        try:
            self.driver.move_joint(
                list(goal.position),
                goal.velocity,
                goal.acceleration,
            )

            goal_handle.succeed()

            result.success = True
            result.error_code = 0
            result.message = "OK"

        except Exception as exc:
            goal_handle.abort()

            result.success = False
            result.error_code = -1
            result.message = str(exc)

        return result

    def execute_move_home(self, goal_handle):

        result = MoveHome.Result()

        try:
            self.driver.move_home()

            goal_handle.succeed()

            result.success = True
            result.error_code = 0
            result.message = "OK"

        except Exception as exc:
            goal_handle.abort()

            result.success = False
            result.error_code = -1
            result.message = str(exc)

        return result

    def execute_move_line(self, goal_handle):

        goal = goal_handle.request
        result = MoveLine.Result()

        try:
            self.driver.move_line(
                list(goal.position),
                goal.linear_velocity,
                goal.linear_acceleration,
            )

            goal_handle.succeed()

            result.success = True
            result.error_code = 0
            result.message = "OK"

        except Exception as exc:
            goal_handle.abort()

            result.success = False
            result.error_code = -1
            result.message = str(exc)

        return result


def main(args=None):

    rclpy.init(args=args)

    node = DriverNode()

    executor = SingleThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
