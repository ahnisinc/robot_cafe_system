from dataclasses import dataclass


@dataclass
class ProcessState:

    order_id          : str   = ""
    recipe_id         : str   = ""
    state             : str   = "IDLE"
    current_step      : str   = ""
    current_step_index: int   = 0
    total_steps       : int   = 0
    progress          : float = 0.0
    message           : str   = ""
