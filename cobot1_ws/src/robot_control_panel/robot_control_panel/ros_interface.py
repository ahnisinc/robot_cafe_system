class ROSInterface:
    """
    GUI-side ROS2 communication boundary.

    Actual ROS subscriptions/services should be
    implemented here.

    The Qt UI must not know about DSR_ROBOT2.
    """

    def __init__(self):
        self.connected = False

    def start(self):
        self.connected = True

    def stop(self):
        self.connected = False
