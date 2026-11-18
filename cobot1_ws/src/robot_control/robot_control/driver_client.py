import threading

from rclpy.action import ActionClient
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from std_srvs.srv import Trigger

from cafe_interfaces.action import MoveJoint, MoveHome, MoveLine

from .pausable_wait import wait_unless_paused


class DriverActionClient:
    """
    robot_control -> robot_driver 액션 클라이언트.

    RobotDriver와 같은 인터페이스(move_joint / move_line /
    move_home / stop)를 제공하지만, Doosan API를 직접 부르지
    않고 robot_driver 노드의 액션 서버에 요청을 보낸다.
    """

    def __init__(self, node):

        self.node = node

        group = MutuallyExclusiveCallbackGroup()

        self._move_joint_client = ActionClient(node, MoveJoint, "/robot_driver/move_joint", callback_group=group)
        self._move_home_client = ActionClient(node, MoveHome, "/robot_driver/move_home", callback_group=group)
        self._move_line_client = ActionClient(node, MoveLine, "/robot_driver/move_line", callback_group=group)

        self._pause_client = node.create_client(Trigger, "/robot_driver/pause", callback_group=group)
        self._resume_client = node.create_client(Trigger, "/robot_driver/resume", callback_group=group)
        self._stop_client = node.create_client(Trigger, "/robot_driver/stop", callback_group=group)

        self.paused = False

    def _send_goal(self, client, goal_msg, timeout=30.0):

        if not client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError("robot_driver action server not available")

        result_done = threading.Event()
        outcome = {}

        def on_goal_response(future):

            goal_handle = future.result()

            if not goal_handle.accepted:
                outcome["error"] = "Goal rejected"
                result_done.set()
                return

            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(on_result)

        def on_result(future):

            outcome["result"] = future.result().result
            result_done.set()

        send_future = client.send_goal_async(goal_msg)
        send_future.add_done_callback(on_goal_response)

        if not wait_unless_paused(result_done, lambda: self.paused, timeout):
            raise RuntimeError("robot_driver action call timed out")

        if "error" in outcome:
            raise RuntimeError(outcome["error"])

        result = outcome["result"]

        if not result.success:
            raise RuntimeError(result.message)

        return result

    def move_joint(self, joints, velocity=30.0, acceleration=30.0):

        goal = MoveJoint.Goal()
        goal.position = [float(value) for value in joints]
        goal.velocity = float(velocity)
        goal.acceleration = float(acceleration)

        return self._send_goal(self._move_joint_client, goal)

    def move_line(self, pose, velocity=100.0, acceleration=100.0):

        goal = MoveLine.Goal()
        goal.position = [float(value) for value in pose]
        goal.linear_velocity = float(velocity)
        goal.linear_acceleration = float(acceleration)

        return self._send_goal(self._move_line_client, goal)

    def move_home(self):

        goal = MoveHome.Goal()
        goal.target = 0

        return self._send_goal(self._move_home_client, goal)

    def pause(self):

        self._trigger(self._pause_client)
        self.paused = True

    def resume(self):

        self._trigger(self._resume_client)
        self.paused = False

    def stop(self):

        self.paused = False
        self._trigger(self._stop_client)

    def _trigger(self, client, timeout=5.0):

        if not client.wait_for_service(timeout_sec=2.0):
            raise RuntimeError(f"{client.srv_name} not available")

        done = threading.Event()
        future = client.call_async(Trigger.Request())
        future.add_done_callback(lambda _: done.set())

        if not done.wait(timeout):
            raise RuntimeError(f"{client.srv_name} timed out")

        result = future.result()

        if not result.success:
            raise RuntimeError(f"{client.srv_name}: {result.message}")
