# Coffee Process Backend Integration

The coffee_process package publishes:

    /coffee_process/status

Message type:

    cafe_interfaces/msg/ProcessStatus


Flow:

    ProcessManager
          |
          v
    BackendProgressPublisher
          |
          v
    ROS2 Topic
          |
          v
    rosbridge_server
          |
          v
    Flask ROSBridgeClient
          |
          v
    Flask-SocketIO
          |
          v
    JavaScript kiosk


## Connecting it to ProcessManager

In coffee_process_node.py:

    from .backend_bridge import (
        BackendProgressPublisher
    )

Create:

    self.progress_publisher = (
        BackendProgressPublisher(self)
    )


During recipe execution:

    self.progress_publisher.publish(
        order_id,
        recipe_id,
        "RUNNING",
        step["name"],
        index,
        total,
        ((index + 1) / total) * 100,
        "Processing"
    )


The backend does NOT call DSR_ROBOT2.

Robot control remains:

    robot_control
         |
    robot_driver
         |
    Doosan API
