# Robot Cafe System

Doosan M0609 based autonomous barista robot system.

## Environment

- Ubuntu 24.04
- ROS 2 Jazzy
- Python 3.12
- Doosan DSR_ROBOT2
- PyQt5
- Flask
- WebSocket / Socket.IO
- SQLite3

## Architecture

Browser
    |
    v
Flask Backend
    |
    v
ROS2
    |
    v
coffee_process
    |
    v
robot_control
    |
    v
robot_driver
    |
    v
Doosan DSR_ROBOT2
    |
    v
M0609

## Important

Doosan API access is isolated in:

    robot_driver/doosan_adapter.py

Application code must not directly import DSR_ROBOT2.

Robot coordinates are stored in YAML configuration files.

Never use the sample coordinates on a real robot.

Real robot configuration must be created after:

1. Teaching
2. TCP verification
3. Tool verification
4. I/O verification
5. Safety verification
6. Dry-run testing

0. 필요 패키지 존재 확인(requirement.txt 파일에 있는 설치 패키지)
```bash
apt search python3-flask 
apt search python3-yaml 
apt search python3-requests 
apt search python3-socketio 
apt search python3-eventlet 
apt search python3-flask-socketio
```

1. 필요 패키지 설치
```bash
sudo apt update && sudo apt install \
    python3-flask \
    python3-flask-socketio \
    python3-yaml \
    python3-requests \
    python3-socketio \
    python3-eventlet \
    python3-pytest
```
2. rosbridge 설치

```bash
sudo apt update
sudo apt install ros-jazzy-rosbridge-suite
```

rosbridge_suite는 rosbridge_server, rosbridge_library, rosapi 등을 포함하는 메타 패키지입니다.

3. 설치 후 확인
```bash
ros2 pkg list | grep rosbridge

#정상이라면 대략:
#rosbridge_msgs
#rosbridge_server
#rosbridge_library
#rosapi
```
4. rosbridge_server 실행
```bash
source /opt/ros/jazzy/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```
