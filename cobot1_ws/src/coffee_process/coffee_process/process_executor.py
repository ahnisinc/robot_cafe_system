import time


class ProcessExecutor:

    def __init__(
        self,
        robot_control,
        io_manager,
    ):

        self.robot = robot_control
        self.io = io_manager

    def execute_step(
        self,
        step,
    ):

        action = step["action"]

        if action == "move":

            return self.robot.move_to_pose(
                step["pose"],
                step.get(
                    "velocity",
                    30.0,
                ),
                step.get(
                    "acceleration",
                    30.0,
                ),
            )

        if action == "gripper":
            return self.io.set_gripper(step["command"])

        if action == "io":
            return self.io.set_output(
                step["output"],
                step["value"],
            )

        if action == "wait":
            time.sleep(float(step["seconds"]))

            return True

        if action == "home":
            return self.robot.move_home()

        if action == "stop":
            return self.robot.stop()

        raise ValueError(f"Unknown process action: " f"{action}")
