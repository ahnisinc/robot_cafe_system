from .doosan_adapter import DoosanAdapter


class RobotDriver:
    """
    Project-level Robot API.

    Doosan API details are intentionally hidden
    behind DoosanAdapter.
    """

    def __init__(
        self,
        node,
        robot_name="dsr01",
    ):

        self.adapter = DoosanAdapter(
            node,
            robot_name,
        )

    def get_state(self):
        return self.adapter.get_robot_state()

    def get_mode(self):
        return self.adapter.get_robot_mode()

    def get_system(self):
        return self.adapter.get_robot_system()

    def get_pose(self):
        return self.adapter.get_current_pose()

    def get_joint_position(self):
        return self.adapter.get_current_joint()

    def get_alarm(self):
        return self.adapter.get_last_alarm()

    def move_joint(
        self,
        joints,
        velocity=30.0,
        acceleration=30.0,
    ):

        return self.adapter.move_joint(
            joints,
            velocity,
            acceleration,
        )

    def move_line(
        self,
        pose,
        velocity=100.0,
        acceleration=100.0,
    ):

        return self.adapter.move_line(
            pose,
            velocity,
            acceleration,
        )

    def move_home(self):

        return self.adapter.move_home()

    def stop(
        self,
        stop_mode=1,
    ):

        return self.adapter.move_stop(stop_mode)

    def set_tcp(
        self,
        name,
    ):

        return self.adapter.set_tcp(name)

    def set_tool(
        self,
        name,
    ):

        return self.adapter.set_tool(name)

    def set_output(
        self,
        channel,
        value,
    ):

        return self.adapter.set_output(
            channel,
            value,
        )

    def get_input(
        self,
        channel,
    ):

        return self.adapter.get_input(channel)
