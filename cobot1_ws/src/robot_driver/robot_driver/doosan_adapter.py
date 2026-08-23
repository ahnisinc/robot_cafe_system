from __future__ import annotations


class DoosanAdapter:
    '''
    Adapter for Doosan DSR_ROBOT2.

    Only this module should directly depend on
    the concrete Doosan Python API.
    '''

    def __init__(
        self,
        node,
        robot_name="dsr01",
    ):
        self.node = node
        self.robot_name = robot_name

        try:
            import DSR_ROBOT2 as dsr

            self.dsr = dsr
            self.available = True

        except ImportError:

            self.dsr = None
            self.available = False

            self.node.get_logger().warning(
                "DSR_ROBOT2 is not available. "
                "Driver is in interface-only mode."
            )

    def _require_api(self):

        if not self.available:
            raise RuntimeError(
                "DSR_ROBOT2 is not available"
            )

    # ------------------------------------------------
    # State
    # ------------------------------------------------

    def get_robot_state(self):

        self._require_api()

        return self.dsr.get_robot_state()

    def get_robot_mode(self):

        self._require_api()

        return self.dsr.get_robot_mode()

    def get_robot_system(self):

        self._require_api()

        return self.dsr.get_robot_system()

    def get_current_pose(self):

        self._require_api()

        return self.dsr.get_current_pose()

    def get_current_joint(self):

        self._require_api()

        return self.dsr.get_current_posj()

    def get_last_alarm(self):

        self._require_api()

        return self.dsr.get_last_alarm()

    # ------------------------------------------------
    # Motion
    # ------------------------------------------------

    def move_joint(
        self,
        joints,
        velocity,
        acceleration,
    ):

        self._require_api()

        return self.dsr.movej(
            joints,
            vel=velocity,
            acc=acceleration,
            sync_type=0,
        )

    def move_line(
        self,
        pose,
        velocity,
        acceleration,
    ):

        self._require_api()

        return self.dsr.movel(
            pose,
            vel=[velocity, velocity],
            acc=[acceleration, acceleration],
            sync_type=0,
        )

    def move_home(self):

        self._require_api()

        return self.dsr.move_home()

    def move_stop(
        self,
        stop_mode=1,
    ):

        self._require_api()

        return self.dsr.move_stop(
            stop_mode
        )

    # ------------------------------------------------
    # TCP / Tool
    # ------------------------------------------------

    def set_tcp(
        self,
        tcp_name,
    ):

        self._require_api()

        return self.dsr.set_current_tcp(
            tcp_name
        )

    def set_tool(
        self,
        tool_name,
    ):

        self._require_api()

        return self.dsr.set_current_tool(
            tool_name
        )

    # ------------------------------------------------
    # I/O
    # ------------------------------------------------

    def set_output(
        self,
        channel,
        value,
    ):

        self._require_api()

        return self.dsr.set_digital_output(
            channel,
            value,
        )

    def get_input(
        self,
        channel,
    ):

        self._require_api()

        return self.dsr.get_digital_input(
            channel
        )
