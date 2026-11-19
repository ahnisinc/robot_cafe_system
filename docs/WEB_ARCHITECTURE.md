# Web Architecture

## Browser

JavaScript kiosk_control_panel.

Responsibilities:

- Menu display
- Coffee order
- Order ID
- Coffee progress
- Current process
- Robot/server status
- Emergency stop UI


## Flask

Flask is the application gateway.

Responsibilities:

- HTTP API
- Socket.IO
- SQLite
- ROSBridge client
- Browser communication


## SQLite

Stores:

- orders
- coffee_process_status
- robot_status


## ROSBridge

Flask connects to:

    ws://localhost:9090

and subscribes to:

    /coffee_process/status

ROSBridge uses a JSON protocol over WebSocket.

The browser does not directly control ROS2.


## Coffee Process

coffee_process publishes:

    cafe_interfaces/msg/ProcessStatus

through:

    /coffee_process/status


The backend receives it through ROSBridge.


## Important Security Rule

Do not expose port 9090 directly to the public Internet.

The intended deployment is:

    Browser
       |
    Flask
       |
    ROSBridge
       |
    ROS2

not:

    Browser
       |
    ROSBridge
       |
    Robot
