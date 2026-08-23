from cafe_interfaces.msg import ProcessStatus


class BackendProgressPublisher:
    """
    coffee_process -> ROS2 topic
    Flask/backend does NOT directly import this class.
    Flow:

        coffee_process
             |
             v
        ProcessStatus
             |
             v
        rosbridge
             |
             v
        Flask
             |
             v
        Socket.IO
             |
             v
        Browser
    """

    TOPIC = "/coffee_process/status"

    def __init__(self, node):

        self.node = node
        self.publisher = node.create_publisher(ProcessStatus, self.TOPIC, 10)

    def publish(
        self,
        order_id,
        recipe_id,
        state,
        current_step,
        current_step_index,
        total_steps,
        progress,
        message="",
    ):

        msg = ProcessStatus()

        msg.order_id           = order_id or ""
        msg.recipe_id          = recipe_id or ""
        msg.state              = state or ""
        msg.current_step       = current_step or ""
        msg.current_step_index = int(current_step_index)
        msg.total_steps        = int(total_steps)
        msg.progress           = float(progress)
        msg.message            = message or ""

        self.publisher.publish(msg)
