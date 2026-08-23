class IOManager:

    def __init__(
        self,
        robot_driver,
        io_config=None,
    ):

        self.robot = robot_driver

        self.io_config = (
            io_config or {}
        )

    def set_output(
        self,
        name,
        value,
    ):

        if name not in self.io_config:

            raise KeyError(
                f"Unknown output: {name}"
            )

        channel = self.io_config[name]

        return self.robot.set_output(
            channel,
            value,
        )

    def get_input(
        self,
        name,
    ):

        if name not in self.io_config:

            raise KeyError(
                f"Unknown input: {name}"
            )

        channel = self.io_config[name]

        return self.robot.get_input(
            channel
        )

    def set_gripper(
        self,
        command,
    ):

        if command == "open":
            return self.set_output(
                "gripper_open",
                True,
            )

        if command == "close":
            return self.set_output(
                "gripper_close",
                True,
            )

        raise ValueError(
            f"Unknown gripper command: "
            f"{command}"
        )
