from dataclasses import dataclass


@dataclass
class MonitorStatus:

    system            : str  = "UNKNOWN"
    mode              : str  = "UNKNOWN"
    state             : str  = "UNKNOWN"
    servo_on          : bool = False
    connected         : bool = False
    alarm             : str  = "NONE"
    emergency_stopped : bool = False
    joints            : list = None
    pose              : list = None
    tcp               : str  = ""
    tool              : str  = ""

    def __post_init__(self):

        if self.joints is None:
            self.joints = [0.0] * 6

        if self.pose is None:
            self.pose = [0.0] * 6

