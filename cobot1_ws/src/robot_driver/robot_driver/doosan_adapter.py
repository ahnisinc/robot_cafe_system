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
        robot_name,
        robot_model,
    ):
        self.node = node
        self.robot_name = robot_name
        self.robot_model = robot_model

        try:
            # DSR_ROBOT2 reads these at import time to create
            # its ROS2 clients/publishers, so they must be set
            # on DR_init before the import happens.
            import DR_init

            # NOTE: these are set via setattr(), not dotted
            # assignment. Inside a class body, an attribute name
            # starting with "__" (like __dsr__id) is name-mangled
            # by Python even when the target is an external module,
            # which would silently set the wrong attribute on
            # DR_init and leave __dsr__node as None for DSR_ROBOT2.
            setattr(DR_init, "__dsr__id", robot_name)
            setattr(DR_init, "__dsr__model", robot_model)
            setattr(DR_init, "__dsr__node", node)

            import DSR_ROBOT2 as dsr

            self.dsr = dsr
            self.available = True

        except Exception as exc:

            self.dsr = None
            self.available = False

            self.node.get_logger().warning(
                f"DSR_ROBOT2 is not available ({exc}). "
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
            self.dsr.ON if value else self.dsr.OFF,
        )

    def get_input(
        self,
        channel,
    ):

        self._require_api()

        return self.dsr.get_digital_input(
            channel
        )
