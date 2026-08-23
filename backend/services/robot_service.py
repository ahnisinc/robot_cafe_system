class RobotService:

    def __init__(self, rosbridge_client=None):

        self.rosbridge = rosbridge_client

    def request_home(self):

        # This is intentionally a boundary.
        #
        # The actual ROS2 service/action used
        # by robot_control must be configured
        # according to the final ROS2 interface.
        #
        # Do not call DSR_ROBOT2 here.

        return {"accepted": True, "message": "HOME request accepted"}

    def request_stop(self):
        return {"accepted": True, "message": "STOP request accepted"}
