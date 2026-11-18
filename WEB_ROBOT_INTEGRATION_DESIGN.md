# 웹 ↔ 로봇 실행 연결 설계

- 작성일: 2026-11-18
- 상태: 초안 (승인 대기)
- 범위: 웹에서 받은 주문으로 로봇이 레시피를 실행하는 경로 전체 + 일시정지/강제정지 + `coffee_process` 상태 발행 버그 수정

---

## 1. 목적

지금은 웹에서 주문하면 DB에 저장만 되고 로봇은 움직이지 않는다. 이 작업이 끝나면 다음이 된다.

- 키오스크에서 주문하면 로봇이 레시피(YAML)대로 커피를 만든다.
- 진행 상황(단계, 진행률)이 키오스크 화면에 실시간으로 표시된다.
- 웹에서 로봇을 **정지(일시정지)**, **재개**, **강제 정지**할 수 있다.

## 2. 목표 / 비목표 / 실패 기준

### 목표
1. 주문 → 대기열 → 한 잔씩 순서대로 제조 → 완료/실패가 화면과 DB에 반영된다.
2. **정지**: 로봇이 그 자리에서 멈추고(이동 중이면 이동 도중에), 대기열은 유지된다. **재개**하면 멈춘 지점부터 이어서 한다.
3. **강제 정지**: 로봇이 즉시 멈추고 만들던 주문은 실패 처리된다. **재개**하면 들고 있던 컵을 쓰레기통에 버리고 홈으로 돌아가 초기 상태가 된다. 이후 **시작** 명령을 받아야 대기열의 다음 주문을 진행한다.
4. 레시피 단계가 실패하면 강제 정지와 같은 상태로 처리한다.
5. 시뮬레이션(가상 M0609 + RG2)에서 끝까지 확인할 수 있다. RViz에서 그리퍼도 실제로 열리고 닫힌다.

### 비목표 (이번에 하지 않음)
- 레시피/포즈/IO YAML 파일의 최종 위치와 설치 방식 → 나중에 결정한다. 이번에는 노드 파라미터로 경로를 받는다.
- 실제 로봇 티칭 좌표 (`trash` 포즈 포함) → 샘플 값만 둔다.
- 하드웨어 비상정지(E-stop). 이번 정지 기능은 모두 소프트웨어 정지다.
- `io_controller`, `robot_monitor`, `robot_control_panel`(PyQt) 노드 개선.
- 여러 대 로봇 동시 제조, 주문 취소 기능, 결제.
- 전체 실행용 launch 파일 (있으면 편하지만 이번 범위 아님).

### 실패 기준 (동작은 해도 이러면 실패)
- 정지/강제 정지를 눌렀는데 로봇이 **현재 이동을 끝까지 마친 뒤에** 멈춘다.
- 일시정지가 길어졌다는 이유만으로(예: 30초 초과) 주문이 실패 처리된다.
- 강제 정지 후, 사람이 시작 명령을 주기 전에 다음 주문이 자동으로 시작된다.
- 한 잔을 만드는 중에 다음 주문이 겹쳐서 실행된다.
- 백엔드를 재시작했을 때 대기 중이던 주문이 사라진다.

## 3. 제약

- 두산 API(DSR_ROBOT2, `dsr_msgs2`, `dsr_controller2` 서비스)는 **`robot_driver` 패키지 안에서만** 다룬다 (프로젝트 원칙, README).
- 브라우저는 ROS에 직접 접속하지 않는다. 브라우저 → Flask → rosbridge(9090) → ROS 순서로만 간다 (WEB_ARCHITECTURE.md).
- DSR_ROBOT2는 모든 호출에서 **전역 executor**로 자기 노드를 spin한다. 그래서 드라이버 안에서 DSR_ROBOT2를 부르는 쪽과, 이동 중에 즉시 응답해야 하는 쪽은 서로 다른 executor/스레드를 써야 한다. (`~/ROS2_Executor_정리.md` 참고)
- RG2 그리퍼는 실제 로봇과 시뮬레이션 모두 `/onrobot/sendCommand` (`onrobot_rg_msgs/srv/SetCommand`, `'o'` 열기 / `'c'` 닫기) 서비스로 제어한다. 실제 로봇은 Modbus TCP로 연결돼 있음을 사용자가 확인했다.
- ROS 2 Jazzy, Python 3.12, Flask + Flask-SocketIO(threading 모드), SQLite.

## 4. 결정 사항 (사용자 선택)

| # | 질문 | 후보 | 선택 | 이유 |
|---|---|---|---|---|
| 1 | 대기열을 어디서 관리할까 | A. 백엔드(DB) / B. coffee_process 메모리 | **A** | 재시작해도 대기열이 유지된다. ROS 쪽은 "한 잔 만들기"만 안다. 기존 `ExecuteRecipe.srv`와 `call_service()`를 재사용한다. |
| 2 | 정지 신호를 로봇에 어떻게 전달할까 | A. 드라이버 안에 별도 제어 통로 / B. robot_control이 두산 서비스 직접 호출 / C. 드라이버를 비동기 이동으로 변경 | **A** | 이동 중에도 즉시 응답하고, 두산 코드는 `robot_driver` 안에만 있다. B는 프로젝트 원칙 위반, C 단독으로는 정지 통로 문제가 해결되지 않는다. |
| 3 | 웹 → ROS 명령 형태 | 서비스 / 액션 | **서비스** | 백엔드에 rosbridge 서비스 호출이 이미 있다. 진행률은 토픽으로 이미 오고 있다. |
| - | 그리퍼 제어 | 디지털 출력 / `/onrobot/sendCommand` 서비스 | **서비스** | 실제 로봇(Modbus) 설정과 맞고, 시뮬레이션에서 눈으로 보이며, 동작 완료까지 기다려 준다. |
| - | 강제 정지된 주문 | 실패 / 재제조 | **실패(FAILED)** | 사용자 결정 |
| - | 강제 정지 시 들고 있던 컵 | 들고 홈 / 내려놓기 / 사람이 치움 | **쓰레기통 위치로 이동 후 버림** | 사용자 결정 |

### 4.1 설계 중 발견한 사항 → 결정 2의 구현에 반영

`dsr_controller2.cpp` 소스를 확인한 결과는 다음과 같다.

- `motion/move_joint`(동기 `movej`)는 **이동이 끝날 때까지 블로킹**하고, 컨트롤러 노드의 **기본 콜백 그룹**에 등록돼 있다.
- `motion/move_pause`, `motion/move_resume`, `motion/check_motion`도 **같은 기본 그룹**에 있다.
- `motion/move_stop`만 별도 그룹(`cb_group_`)에 있다. 원래 줄이 주석 처리되고 새로 등록된 흔적이 있다.

따라서 **동기 `movej`가 실행되는 동안에는 `move_pause`가 처리되지 않고, 이동이 끝난 뒤에야 실행될 가능성이 높다.** `move_stop`은 이동 중에도 동작한다.

그래서 드라이버의 이동은 **비동기 이동 + 완료 확인 반복** 방식으로 바꾼다.
- `amovej()` / `amovel()`로 이동을 시작한다. 컨트롤러는 바로 응답하고 기본 그룹이 비워진다.
- `check_motion()`으로 완료될 때까지 0.1초 간격으로 확인한다.

이 방식이면 이동 중에도 컨트롤러가 `move_pause`/`move_resume`을 처리할 수 있다. 정지 신호 자체는 결정 2-A의 별도 제어 통로로 들어간다.

**구현 0단계에서 시뮬레이션으로 먼저 검증한다 (§9).** 검증 결과 동기 `movej` 중에도 `move_pause`가 바로 처리된다면, 이동은 지금의 동기 `movej`로 두고 비동기 전환은 하지 않는다.

### 4.2 0단계 검증 결과 (2026-11-18, 가상 M0609)

| 측정 | 결과 |
|---|---|
| 동기 `movej`(vel 10) 시작 1초 후 `move_pause` | **6.46초 뒤 응답** (이동이 끝난 뒤). 로봇은 멈추지 않음, 이후 `move_resume`은 `success=False` |
| 비동기 `movej` 응답 | 즉시, `check_motion=2`(BUSY) |
| 비동기 이동 중 `move_pause` | 즉시 응답, 관절 정지, 정지 중 `check_motion=2` |
| `move_resume` | 즉시 응답, 원래 목표까지 이어서 이동 후 `check_motion=0` |
| 비동기 이동 중 `move_stop(1)` | 0.15초 응답, 관절 정지, 이후 `check_motion=0` |
| 정지 후 새 이동 | 정상 동작 |

**결정:** §4.1의 추론이 맞았다. 드라이버 이동은 `amovej/amovel` + `check_motion` 폴링으로 바꾼다. 일시정지 중에는 `check_motion=2`가 유지되므로 폴링이 계속 기다린다. 정지 후에는 `check_motion=0`이 되므로, 드라이버는 정지 플래그로 "정상 완료"와 "정지됨"을 구분해야 한다.

## 5. 전체 구조

```
[Browser kiosk]
   │ HTTP: POST /api/orders, POST /api/control/<cmd>
   │ Socket.IO: coffee_progress (수신)
   ▼
[Flask backend]
   ├─ DB(orders): QUEUED → RUNNING → DONE / FAILED
   ├─ Dispatcher: 로봇이 IDLE이고 QUEUED 주문이 있으면 하나 보냄
   └─ ROSBridgeClient: 상태 구독 + call_service
   │ rosbridge (ws://localhost:9090)
   ▼
[coffee_process]  ── 레시피 실행 상태 머신, 작업 스레드
   ├─ 서비스: /coffee_process/execute_recipe, /pause, /resume, /force_stop, /start
   ├─ 토픽:   /coffee_process/status (ProcessStatus)
   ├─ 이동 ─────────► [robot_control] /robot_control/move_named_pose
   ├─ 정지 계열 ────► [robot_control] /robot_control/pause, /resume, /stop_process
   ├─ 디지털 출력 ──► [robot_driver]  /robot_driver/set_digital_output
   └─ 그리퍼 ───────► [OnRobot 드라이버 / gripper_virtual_node] /onrobot/sendCommand
                         ▼
[robot_control] ── 이름 포즈 → 좌표 변환, 액션 대기(일시정지 동안 타임아웃 정지)
   ├─ 액션 ──────► /robot_driver/move_joint, move_line
   └─ 정지 계열 ─► /robot_driver/pause, resume, stop
                         ▼
[robot_driver]
   ├─ 메인 노드 (SingleThreadedExecutor): 액션 서버, set_digital_output 서비스 → DSR_ROBOT2
   └─ 제어 노드 (별도 스레드·executor): pause / resume / stop 서비스
          → /dsr01/dsr_controller2/motion/move_pause, move_resume, move_stop 직접 호출
                         ▼
[dsr_controller2 / DRCF] → M0609
```

## 6. 상태 머신 (`coffee_process`)

### 6.1 상태

| 상태 | 의미 | 주문 받음 |
|---|---|---|
| `STOPPED` | 강제 정지·단계 실패·노드 시작 직후. **재개(초기화) 필요** | X |
| `RESETTING` | 초기화 중: (컵을 들고 있으면) 쓰레기통 → 그리퍼 열기 → 홈 | X |
| `HOMED` | 초기화 완료. **시작 명령 대기** | X |
| `IDLE` | 주문 대기 | O |
| `RUNNING` | 레시피 실행 중 | X |
| `PAUSED` | 일시정지 | X |

### 6.2 전이

```
            start                execute_recipe
  HOMED ───────────► IDLE ─────────────────────► RUNNING ──(레시피 완료)──► IDLE
    ▲                                              │  ▲
    │                                       pause  │  │ resume
    │                                              ▼  │
    │                                             PAUSED
    │                                              │
    │                  force_stop / 단계 실패        │ force_stop
    │        ┌─────────────────────────────────────┴──── (RUNNING에서도)
    │        ▼
    │     STOPPED ──── resume ────► RESETTING ──(완료)──┘ → HOMED
    │                                   │
    │                                   └─ force_stop / 실패 → STOPPED
  (노드 시작 시 초기 상태 = STOPPED)
```

- **노드 시작 직후는 `STOPPED`다.** 로봇이 어디 있는지 모르기 때문에, 재개(홈 이동) → 시작 순서를 거쳐야 첫 주문을 받는다. 이때는 컵을 들고 있지 않다고 가정하고 쓰레기통은 건너뛴다. (설계자 판단 — §11)
- 웹에는 별도의 재개 버튼이 없다. **정지** 버튼은 `PAUSED`에서 **재개**(이어서 실행)로 바뀌고, **강제 정지** 버튼은 `STOPPED`에서 **재개**(초기화)로 바뀐다 (§8.7). 두 재개는 같은 `/coffee_process/resume` 서비스를 호출하고, 동작은 상태로 구분된다.
- 허용되지 않는 상태에서 온 명령은 `success=false` + 이유 메시지로 거절하고, 상태는 바꾸지 않는다.

### 6.3 단계별 일시정지 동작

| 단계 | 정지 시 | 재개 시 |
|---|---|---|
| `move` | 로봇 이동을 그 자리에서 일시정지 (`move_pause`) | `move_resume`으로 같은 궤적을 이어서 이동 |
| `wait` | 남은 시간을 기록하고 대기를 멈춤 | 남은 시간만 이어서 대기 |
| `gripper`, `io` | 짧은 동작이라 중간에 멈추지 않음. 이 단계가 끝나면 다음 단계 시작 전에 멈춤 | 다음 단계부터 진행 |

강제 정지는 단계 종류와 관계없이 즉시 중단한다. `move`는 `move_stop`, `wait`는 대기 중단, `gripper`/`io`는 해당 호출이 끝나는 대로 중단한다.

### 6.4 컵 보유 추적

- `coffee_process`가 마지막으로 **성공시킨** 그리퍼 명령을 기억한다. 강제 정지가 그리퍼 닫기 도중에 들어왔다면 닫힌 것으로 본다.
- 초기화 순서:
  - 닫힘이면: `move_named_pose trash` → 그리퍼 `'o'` → `move_named_pose home`
  - 열림이면: `move_named_pose home`
- 홈은 `robot_control`의 이름 포즈 `home`을 쓴다. 드라이버의 `move_home`은 기계 원점(관절 전부 0)으로 가기 때문에 쓰지 않는다.

## 7. 인터페이스

### 7.1 ROS 서비스 / 토픽

| 이름 | 타입 | 제공 노드 | 설명 |
|---|---|---|---|
| `/coffee_process/execute_recipe` | `cafe_interfaces/srv/ExecuteRecipe` (기존) | coffee_process | `IDLE`일 때만 `accepted=true`. 즉시 응답하고 실행은 작업 스레드에서 한다. |
| `/coffee_process/pause` | `std_srvs/srv/Trigger` | coffee_process | `RUNNING` → `PAUSED` |
| `/coffee_process/resume` | `std_srvs/srv/Trigger` | coffee_process | `PAUSED` → `RUNNING`, `STOPPED` → `RESETTING` |
| `/coffee_process/force_stop` | `std_srvs/srv/Trigger` | coffee_process | `RUNNING`/`PAUSED`/`RESETTING` → `STOPPED` |
| `/coffee_process/start` | `std_srvs/srv/Trigger` | coffee_process | `HOMED` → `IDLE` |
| `/coffee_process/status` | `cafe_interfaces/msg/ProcessStatus` (필드 추가) | coffee_process | 상태가 바뀔 때마다 즉시 + 1초 주기로 발행 |
| `/robot_control/move_named_pose` | `MoveNamedPose` (기존) | robot_control | 일시정지 동안에는 타임아웃 시계를 멈춘다. |
| `/robot_control/pause`, `/robot_control/resume` | `std_srvs/srv/Trigger` | robot_control | 드라이버 제어 통로로 전달 |
| `/robot_control/stop_process` | `StopProcess` (기존) | robot_control | 드라이버 `stop`으로 전달 (기존의 액션 취소 방식 대체) |
| `/robot_driver/pause`, `/resume`, `/stop` | `std_srvs/srv/Trigger` | robot_driver 제어 노드 | 두산 `move_pause` / `move_resume` / `move_stop(stop_mode=1, DR_QSTOP)` |
| `/robot_driver/set_digital_output` | `cafe_interfaces/srv/SetDigitalOutput` (기존) | robot_driver 메인 노드 | DSR `set_digital_output` |
| `/onrobot/sendCommand` | `onrobot_rg_msgs/srv/SetCommand` | OnRobot 드라이버 / `gripper_virtual_node` | 외부 패키지 (기존) |

### 7.2 `ProcessStatus.msg` 변경

`string order_state`를 추가한다. 값은 `RUNNING` / `DONE` / `FAILED` / `""`.
- 프로세스 상태(`state`)와 주문 상태를 분리하기 위해서다. 레시피가 끝나면 `state`는 곧바로 `IDLE`이 되므로, 그것만 봐서는 주문이 성공했는지 알 수 없다.
- `order_id`, `order_state`는 다음 주문이 시작될 때까지 **마지막 주문 값을 유지**한다. 그래서 백엔드가 메시지를 하나 놓쳐도 다음 1초 주기 메시지에서 결과를 알 수 있다.

### 7.3 백엔드 HTTP API

| 메서드·경로 | 동작 |
|---|---|
| `POST /api/orders` (기존) | DB에 `QUEUED`로 저장 → 디스패처 깨움. 응답에 대기 순번 포함 |
| `GET /api/orders/<id>` (기존) | 주문 상태 조회 |
| `POST /api/control/pause` | `/coffee_process/pause` 호출 |
| `POST /api/control/resume` | `/coffee_process/resume` 호출 |
| `POST /api/control/force_stop` | `/coffee_process/force_stop` 호출 |
| `POST /api/control/start` | `/coffee_process/start` 호출 |

제어 API의 응답은 서비스의 `success`/`message`를 그대로 돌려준다. rosbridge에 연결되지 않았으면 503을 반환한다.

## 8. 구성 요소별 변경

### 8.1 robot_driver
- **이동을 비동기 + 완료 확인으로 변경** (§4.1, 0단계 결과에 따라 결정)
  - `DoosanAdapter.move_joint/move_line`: `amovej/amovel` 호출 후 `check_motion()`이 IDLE이 될 때까지 0.1초 간격으로 확인한다.
  - 제어 통로가 `stop`을 받았으면 이동 결과를 실패(`"stopped"`)로 반환한다.
  - 일시정지 중에는 `check_motion()`이 계속 BUSY로 나오는 것으로 예상하고, 그동안 계속 기다린다 (0단계에서 확인).
- **제어 노드 추가**: 같은 프로세스 안에 별도 노드(`robot_driver_ctrl`)를 만들고, 전용 `SingleThreadedExecutor`를 별도 스레드에서 spin한다.
  - 이 노드가 `/robot_driver/pause|resume|stop` 서비스를 제공한다.
  - 일반 rclpy 클라이언트로 `/<robot_name>/dsr_controller2/motion/move_pause|move_resume|move_stop`을 호출한다. DSR_ROBOT2는 거치지 않는다(전역 executor 충돌).
  - 응답 대기는 `call_async` + 이벤트로 하며 타임아웃은 3초.
  - `stop`이 호출되면 "정지됨" 플래그를 세운다. 플래그는 다음 이동 시작 시 초기화한다.
- `/robot_driver/set_digital_output` 서비스 추가 (메인 노드).
- 의존성 추가: `dsr_msgs2`, `std_srvs`.

### 8.2 robot_control
- `/robot_control/pause`, `/resume` 서비스 추가. 드라이버 서비스로 전달하고 `paused` 플래그를 관리한다.
- `stop_process`는 액션 취소 대신 `/robot_driver/stop`을 호출한다.
- `DriverActionClient._send_goal` 대기 방식 변경: 0.5초 단위로 기다리고 **`paused`가 아닐 때만 경과 시간을 센다.** 타임아웃은 30초 그대로 둔다.
- 서비스 콜백과 드라이버 클라이언트를 Reentrant 그룹에 넣는다. 일시정지 요청은 이동 서비스가 블로킹 중일 때 들어오기 때문이다.

### 8.3 coffee_process
- **버그 수정**: `coffee_process_node.py:69` `self.publish_status()` → `self.cb_publish_status()`
- 노드를 `MultiThreadedExecutor`로 spin하고, 서비스 콜백과 클라이언트는 Reentrant 그룹에 둔다.
- 레시피는 **작업 스레드**에서 실행한다. 서비스 콜백은 상태 전이와 신호만 처리하고 바로 응답한다.
- 기존 `ProcessManager`/`ProcessExecutor`/`RecipeManager`를 재사용한다.
  - `ProcessExecutor`가 받는 `robot`/`io` 객체를 ROS 서비스 클라이언트로 구현한다.
    - `RobotClient`: move_to_pose / pause / resume / stop
    - `IOClient`: set_output은 이름→채널 변환 후 `/robot_driver/set_digital_output` 호출, set_gripper는 `/onrobot/sendCommand` 호출
  - `ProcessManager`에 일시정지 대기, 강제 정지 중단, 단계 콜백(진행률 발행)을 넣는다.
  - `wait` 단계는 `time.sleep` 대신 남은 시간을 관리하는 대기로 바꾼다.
- 파라미터: `recipe_dir`, `io_file` (YAML 위치는 추후 결정, §2 비목표)
- `io.yaml`의 그리퍼 항목(`gripper_open/close`, 입력 3·4)은 더 이상 쓰지 않는다. 파일에서 지울지는 YAML 정리 때 결정한다.
- 의존성 추가: `std_srvs`, `onrobot_rg_msgs`.

### 8.4 cafe_interfaces
- `ProcessStatus.msg`에 `string order_state` 추가.

### 8.5 config
- `config/robot/virtual/poses.yaml`, `real/poses.yaml`에 `trash` 포즈 추가 (샘플 값, 실제 로봇은 티칭 후 입력).
- `virtual/poses.yaml`의 중복된 빈 `poses:` 키 제거.

### 8.6 backend
- **디스패처** (Flask 프로세스 안의 스레드 하나)
  - 깨어나는 시점: 새 주문이 들어올 때, 상태 메시지가 올 때.
  - 조건: `state == IDLE`이고, DB에 `RUNNING` 주문이 없고, `QUEUED` 주문이 있으면 → 가장 오래된 주문을 `execute_recipe`로 보낸다.
  - `accepted=true`면 DB를 `RUNNING`으로 바꾼다. `false`면 그대로 두고 다음 상태 메시지 때 다시 시도한다.
  - 같은 주문이 두 번 나가지 않도록 잠금(lock)으로 보호한다. coffee_process도 `IDLE`이 아니면 거절하므로 이중 보호가 된다.
- **상태 수신**: `order_id`/`order_state`로 해당 주문을 `DONE`/`FAILED`로 갱신한다. 진행률 갱신은 기존 `update_order_progress`를 쓴다.
- **고아 주문 정리**: DB에 `RUNNING` 주문이 있는데 coffee_process가 그 `order_id`를 모르는 경우(노드 재시작 등)에는 그 주문을 `FAILED`로 바꾼다. 판단 기준은 상태 메시지의 `order_id`가 다르고 `state`가 `RUNNING`/`PAUSED`가 아닌 것.
- **제어 API** `POST /api/control/<cmd>` 추가. 기존 `RobotService` 스텁을 이것으로 교체한다.
- `call_service`는 기존 함수를 쓴다. 매 호출마다 새 웹소켓을 연다.

### 8.7 frontend (키오스크)
- 버튼은 **정지**, **강제 정지**, **시작** 세 개이고, 별도의 재개 버튼은 없다. 정지 버튼과 강제 정지 버튼이 상태에 따라 **재개 버튼으로 바뀐다.** 버튼 모양은 `/coffee_process/status`의 `state`로 정한다. 따라서 다른 키오스크에서 누른 경우나 단계 실패로 `STOPPED`가 된 경우에도 같은 화면이 된다.

| 상태 | 정지 버튼 자리 | 강제 정지 버튼 자리 | 시작 |
|---|---|---|---|
| `IDLE` | 정지 (비활성) | 강제 정지 (비활성) | 비활성 |
| `RUNNING` | **정지** → `pause` | **강제 정지** → `force_stop` | 비활성 |
| `PAUSED` | **재개** → `resume` (이어서 실행) | **강제 정지** → `force_stop` | 비활성 |
| `STOPPED` | 정지 (비활성) | **재개** → `resume` (쓰레기통 → 홈 초기화) | 비활성 |
| `RESETTING` | 정지 (비활성) | **강제 정지** → `force_stop` | 비활성 |
| `HOMED` | 정지 (비활성) | 강제 정지 (비활성) | **시작** → `start` |

- 기존 `emergencyStop()`의 `alert`를 제거하고 제어 API 호출로 바꾼다.
- 상태 표시: 프로세스 상태(한글 표기), 현재 단계, 진행률, 내 주문 상태(대기 n번째 / 제조 중 / 완료 / 실패).

```
RUNNING                                  PAUSED
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│ 로봇 상태: 제조 중                 │    │ 로봇 상태: 일시정지                │
│ ORD-1A2B3C4D Latte  제조 중        │    │ ORD-1A2B3C4D Latte  제조 중        │
│ [██████████░░░░░] 52% Milk Station│    │ [██████████░░░░░] 52% Milk Station│
│ [ 정지 ] [ 강제 정지 ] [ 시작 ]    │    │ [ 재개 ] [ 강제 정지 ] [ 시작 ]    │
└──────────────────────────────────┘    └──────────────────────────────────┘

STOPPED                                  HOMED
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│ 로봇 상태: 강제 정지 (초기화 필요)  │    │ 로봇 상태: 시작 대기               │
│ ORD-1A2B3C4D Latte  실패           │    │                                  │
│ [ 정지 ] [ 재개 ] [ 시작 ]          │    │ [ 정지 ] [ 강제 정지 ] [ 시작 ]    │
└──────────────────────────────────┘    └──────────────────────────────────┘
  (흐리게 표시된 버튼은 비활성)
```

## 9. 구현 순서와 검증

| 단계 | 내용 | 확인 방법 |
|---|---|---|
| 0 | **검증 스파이크** (버리는 코드): 시뮬레이션에서 ① 동기 `movej` 중 `move_pause` 응답 시점 ② `amovej` + `check_motion` 값의 변화(이동 중/일시정지 중/정지 후) ③ `move_resume` 후 이동 이어짐 ④ `amovej` 중 `move_stop` | 결과에 따라 §8.1 이동 방식 확정 |
| 1 | robot_driver: 제어 노드, 비동기 이동, DO 서비스 | `ros2 service call /robot_driver/pause` 등으로 이동 중 정지/재개 확인 |
| 2 | robot_control: pause/resume, stop 경로, 타임아웃 | 30초 이상 일시정지 후 재개해도 `success=True` |
| 3 | coffee_process: 상태 머신, 작업 스레드, 클라이언트, 버그 수정 | 상태 머신은 가짜 robot/io로 **pytest 단위 테스트**. ROS 서비스로 레시피 1회 실행 |
| 4 | backend: 디스패처, 제어 API, order_state 반영 | 가짜 rosbridge로 디스패처 **pytest** (중복 디스패치 없음, IDLE일 때만 전송) |
| 5 | frontend: 버튼, 상태 표시 | 브라우저에서 수동 확인 |
| 6 | 통합 시뮬레이션 | 아래 시나리오 |

**통합 시나리오 (시뮬레이션)**
1. 시작 → 재개(홈) → 시작 → 주문 2건 → 순서대로 완료되고 화면 반영
2. 이동 중 정지 → 40초 대기 → 재개 → 같은 궤적으로 이어서 완료
3. 에스프레소 대기(`wait`) 중 정지 → 재개 → 남은 시간만 대기
4. 그리퍼 닫은 뒤 강제 정지 → 주문 FAILED → 재개 → 쓰레기통 → 그리퍼 열림 → 홈 → HOMED → 시작 전까지 다음 주문 시작 안 함 → 시작 → 다음 주문 진행
5. 백엔드 재시작 → 대기 주문 유지

## 10. 위험 요소

- **§4.1 가정**: 기본 그룹 직렬화로 `move_pause`가 막힌다는 판단은 소스를 읽고 내린 추론이다. 0단계에서 확인한다. 반대로, `amovej` 중 일시정지했을 때 `check_motion` 값이 예상과 다르면 일시정지 판정 로직을 바꿔야 한다.
- **실제 로봇에서의 쓰레기통 경로**: 정지 위치에서 `trash`까지 바로 이동하므로 충돌할 수 있다. 티칭할 때 경유 포즈가 필요한지 확인해야 한다.
- **이동 중 정지는 여전히 소프트웨어**: 드라이버 프로세스가 죽으면 정지 명령도 전달되지 않는다. 하드웨어 E-stop은 별도로 필요하다.
- **DSR 호출에 타임아웃이 없음**: 컨트롤러가 응답하지 않으면 드라이버 메인 노드는 멈춘다. 다만 제어 통로(stop)는 별도 executor라서 계속 동작한다.

## 11. 설계자 판단으로 정한 것 (검토 요청)

1. 노드 시작 직후 상태는 `STOPPED`다 (재개 → 홈 → 시작을 거쳐야 첫 주문을 받음).
2. (사용자 결정으로 변경) 정지 버튼은 `PAUSED`에서, 강제 정지 버튼은 `STOPPED`에서 재개 버튼으로 바뀐다. 단계 실패로 `STOPPED`가 된 경우에도 강제 정지 자리가 재개로 바뀐다. `RESETTING` 중에는 강제 정지가 다시 활성화된다.
3. `gripper`/`io` 단계 도중의 일시정지는 그 단계가 끝난 뒤 적용한다.
4. 강제 정지 시 두산 정지 모드는 `DR_QSTOP`(1, Stop Category 2)이다.
5. 이동 명령 타임아웃 30초는 유지하되, 일시정지 시간은 세지 않는다.
6. 그리퍼 제어용 DO 항목은 쓰지 않는다 (파일 정리는 YAML 위치 결정 때).
7. `io_controller` 노드는 이번에 쓰지 않는다. DO는 coffee_process가 드라이버 서비스를 직접 호출한다.
8. 노드 시작 시 그리퍼는 열려 있다고 가정한다 (첫 초기화에서 쓰레기통 생략).
