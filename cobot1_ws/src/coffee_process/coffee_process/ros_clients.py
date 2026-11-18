import threading

from cafe_interfaces.srv import MoveNamedPose, SetDigitalOutput, StopProcess
from onrobot_rg_msgs.srv import SetCommand
from std_srvs.srv import Trigger


def call_service(client, request, timeout):
    """작업 스레드에서 쓰는 동기 서비스 호출. timeout=None이면 응답까지 기다린다."""

    if not client.wait_for_service(timeout_sec=2.0):
        raise RuntimeError(f"{client.srv_name} not available")

    done = threading.Event()
    future = client.call_async(request)
    future.add_done_callback(lambda _: done.set())

    if not done.wait(timeout):
        raise RuntimeError(f"{client.srv_name} timed out")

    return future.result()


class RobotClient:
    """ProcessRunner의 robot: robot_control 서비스로 전달한다."""

    def __init__(self, node, cb_group):

        self._move = node.create_client(
            MoveNamedPose, "/robot_control/move_named_pose", callback_group=cb_group)
        self._pause = node.create_client(
            Trigger, "/robot_control/pause", callback_group=cb_group)
        self._resume = node.create_client(
            Trigger, "/robot_control/resume", callback_group=cb_group)
        self._stop = node.create_client(
            StopProcess, "/robot_control/stop_process", callback_group=cb_group)

    def move_to_pose(self, name, velocity, acceleration):

        request = MoveNamedPose.Request(
            pose_name=name,
            motion_type="",
            velocity=float(velocity),
            acceleration=float(acceleration),
        )

        result = call_service(self._move, request, None)

        if not result.success:
            raise RuntimeError(result.message)

    def pause(self):
        self._check(call_service(self._pause, Trigger.Request(), 5.0))

    def resume(self):
        self._check(call_service(self._resume, Trigger.Request(), 5.0))

    def stop(self):
        self._check(call_service(self._stop, StopProcess.Request(emergency=True), 5.0))

    @staticmethod
    def _check(result):
        if not result.success:
            raise RuntimeError(result.message)


class IOClient:
    """ProcessRunner의 io: DO는 robot_driver, 그리퍼는 OnRobot 서비스로 보낸다."""

    GRIPPER_COMMANDS = {"open": "o", "close": "c"}

    def __init__(self, node, cb_group, channels):

        self.channels = channels
        self._output = node.create_client(
            SetDigitalOutput, "/robot_driver/set_digital_output", callback_group=cb_group)
        self._gripper = node.create_client(
            SetCommand, "/onrobot/sendCommand", callback_group=cb_group)

    def set_output(self, name, value):

        request = SetDigitalOutput.Request(channel=int(self.channels[name]), value=bool(value))
        result = call_service(self._output, request, 5.0)

        if not result.success:
            raise RuntimeError(result.message)

    def set_gripper(self, command):

        if command not in self.GRIPPER_COMMANDS:
            raise ValueError(f"Unknown gripper command: {command}")

        request = SetCommand.Request(command=self.GRIPPER_COMMANDS[command])
        result = call_service(self._gripper, request, 10.0)

        if not result.success:
            raise RuntimeError(f"gripper {command} failed: {result.message}")
