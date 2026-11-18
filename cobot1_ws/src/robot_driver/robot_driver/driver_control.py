import threading

from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from std_srvs.srv import Trigger
from dsr_msgs2.srv import CheckMotion, MovePause, MoveResume, MoveStop

DR_QSTOP = 1


class DriverControlNode(Node):
    """
    이동 중에도 즉시 응답하는 제어 통로.

    메인 드라이버 노드는 이동이 끝날 때까지 콜백 안에서 기다리므로,
    pause/resume/stop은 별도 노드·executor·스레드에서 받아
    DSR_ROBOT2(전역 executor)를 거치지 않고 컨트롤러 서비스를 직접 호출한다.
    """

    def __init__(self, robot_name, stop_event):

        super().__init__("robot_driver_ctrl")

        self.stop_event = stop_event
        group = ReentrantCallbackGroup()

        prefix = f"/{robot_name}/dsr_controller2/motion/"
        self._pause = self.create_client(MovePause, prefix + "move_pause", callback_group=group)
        self._resume = self.create_client(MoveResume, prefix + "move_resume", callback_group=group)
        self._stop = self.create_client(MoveStop, prefix + "move_stop", callback_group=group)
        self._check = self.create_client(CheckMotion, prefix + "check_motion", callback_group=group)

        self.create_service(Trigger, "/robot_driver/pause", self.cb_pause, callback_group=group)
        self.create_service(Trigger, "/robot_driver/resume", self.cb_resume, callback_group=group)
        self.create_service(Trigger, "/robot_driver/stop", self.cb_stop, callback_group=group)
        self.create_service(Trigger, "/robot_driver/clear_stop", self.cb_clear_stop, callback_group=group)

        self.get_logger().info("Robot driver control ready: /robot_driver/pause, resume, stop")

    def cb_pause(self, request, response):
        return self._forward(self._pause, MovePause.Request(), response)

    def cb_resume(self, request, response):

        self._forward(self._resume, MoveResume.Request(), response)

        if not response.success and self._is_idle():
            response.success = True
            response.message = "no motion to resume"

        return response

    def cb_clear_stop(self, request, response):
        self.stop_event.clear()
        response.success = True
        response.message = "OK"
        return response

    def _is_idle(self):

        if not self._check.wait_for_service(timeout_sec=1.0):
            return False

        done = threading.Event()
        future = self._check.call_async(CheckMotion.Request())
        future.add_done_callback(lambda _: done.set())

        return done.wait(3.0) and future.result().status == 0

    def cb_stop(self, request, response):
        self.stop_event.set()
        return self._forward(self._stop, MoveStop.Request(stop_mode=DR_QSTOP), response)

    def _forward(self, client, request, response, timeout=3.0):

        if not client.wait_for_service(timeout_sec=1.0):
            response.success = False
            response.message = f"{client.srv_name} not available"
            return response

        done = threading.Event()
        future = client.call_async(request)
        future.add_done_callback(lambda _: done.set())

        if not done.wait(timeout):
            response.success = False
            response.message = "timeout"
            return response

        response.success = bool(future.result().success)
        response.message = "OK" if response.success else "controller rejected"
        return response
