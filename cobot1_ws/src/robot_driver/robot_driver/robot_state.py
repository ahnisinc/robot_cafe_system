from dataclasses import dataclass, field
from typing import List


@dataclass
class RobotState:

    connected: bool = False

    system: str = "UNKNOWN"
    mode: str = "UNKNOWN"
    state: str = "UNKNOWN"

    servo_on: bool = False
    emergency_stopped: bool = False

    alarm: str = "NONE"

    joints: List[float] = field(
        default_factory=lambda: [0.0] * 6
    )

    pose: List[float] = field(
        default_factory=lambda: [0.0] * 6
    )

    tcp: str = ""
    tool: str = ""
