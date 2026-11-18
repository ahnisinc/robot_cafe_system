# Coffee Process Backend Integration

설계: 프로젝트 루트 `WEB_ROBOT_INTEGRATION_DESIGN.md`

## 상태 발행

`coffee_process_node`가 직접 발행한다.

    /coffee_process/status   (cafe_interfaces/msg/ProcessStatus)

상태가 바뀔 때마다 즉시, 그리고 1초마다 발행한다.

- `state`: STOPPED / RESETTING / HOMED / IDLE / RUNNING / PAUSED
- `order_state`: RUNNING / DONE / FAILED / "" — 다음 주문이 시작될 때까지 마지막 값을 유지한다.

Flow:

    ProcessRunner (작업 스레드)
          |
          v
    /coffee_process/status
          |
          v
    rosbridge_server (ws://localhost:9090)
          |
          v
    Flask ROSBridgeClient → Dispatcher (DB 주문 상태, 다음 주문 전송)
          |
          v
    Flask-SocketIO → JavaScript kiosk

## 명령 서비스

| 서비스 | 타입 |
|---|---|
| `/coffee_process/execute_recipe` | `cafe_interfaces/srv/ExecuteRecipe` |
| `/coffee_process/pause` | `std_srvs/srv/Trigger` |
| `/coffee_process/resume` | `std_srvs/srv/Trigger` |
| `/coffee_process/force_stop` | `std_srvs/srv/Trigger` |
| `/coffee_process/start` | `std_srvs/srv/Trigger` |

## 실행

    ros2 run coffee_process coffee_process_node --ros-args \
      -p recipe_dir:=<repo>/cobot1_ws/src/coffee_process/config/recipes \
      -p io_file:=<repo>/config/robot/virtual/io.yaml

The backend does NOT call DSR_ROBOT2.

Robot control remains:

    coffee_process → robot_control → robot_driver → Doosan API
