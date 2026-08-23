class MotionManager:

    def __init__(
        self,
        robot_driver,
        poses,
    ):

        self.robot = robot_driver
        self.poses = poses

    def move_to_pose(
        self,
        pose_name,
        velocity=30.0,
        acceleration=30.0,
    ):

        if pose_name not in self.poses:
            raise KeyError(f"Unknown pose: {pose_name}")

        pose = self.poses[pose_name]

        pose_type = pose["type"]

        values = pose["values"]

        if pose_type == "joint":

            return self.robot.move_joint(
                values,
                velocity,
                acceleration,
            )

        if pose_type == "cartesian":

            return self.robot.move_line(
                values,
                velocity,
                acceleration,
            )

        raise ValueError(f"Unknown pose type: {pose_type}")

    def move_home(self):

        return self.robot.move_home()

    def stop(self):

        return self.robot.stop()
