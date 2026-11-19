# 웹 ↔ 로봇 실행 연결 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 키오스크 주문이 대기열을 거쳐 로봇의 레시피 실행으로 이어지고, 웹에서 정지/재개/강제 정지/시작을 제어할 수 있게 한다.

**Architecture:** Flask가 DB 대기열과 디스패처를 갖고 rosbridge 서비스로 `coffee_process`에 한 잔씩 보낸다. `coffee_process`는 ROS 비의존 상태 머신(`ProcessRunner`)을 작업 스레드에서 돌리고, 이동은 `robot_control`, DO는 `robot_driver`, 그리퍼는 `/onrobot/sendCommand`로 보낸다. `robot_driver`는 이동 중에도 응답하는 별도 제어 노드/스레드로 pause/resume/stop을 두산 컨트롤러에 직접 전달한다.

**Tech Stack:** ROS 2 Jazzy (rclpy), DSR_ROBOT2 / dsr_msgs2, onrobot_rg_msgs, std_srvs, Flask + Flask-SocketIO, websocket-client, SQLite, pytest, vanilla JS.

**Spec:** `docs/WEB_ROBOT_INTEGRATION_DESIGN.md`. 구현자는 이 계획과 함께 반드시 읽는다.

## Global Constraints

- 두산 API(`DSR_ROBOT2`, `dsr_msgs2`, `/dsr01/dsr_controller2/*`)는 `cobot1_ws/src/robot_driver` 안에서만 import/호출한다.
- 브라우저는 ROS에 직접 접속하지 않는다: Browser → Flask → rosbridge(`ws://localhost:9090`) → ROS.
- DSR_ROBOT2 호출은 전역 executor를 쓴다. 이동 중 즉시 응답해야 하는 코드는 전역 executor·드라이버 메인 executor와 다른 executor/스레드에서 돈다.
- 그리퍼: `/onrobot/sendCommand` (`onrobot_rg_msgs/srv/SetCommand`, `command='o'` 열기 / `'c'` 닫기). DO로 그리퍼를 제어하지 않는다.
- 홈 복귀는 robot_control 이름 포즈 `home`. 드라이버 `move_home`(기계 원점) 사용 금지.
- 강제 정지 두산 정지 모드: `stop_mode=1` (DR_QSTOP).
- robot_control 이동 타임아웃 30초, 일시정지 시간은 제외.
- 레시피/IO/포즈 YAML 경로는 노드 파라미터로 받는다 (`recipe_dir`, `io_file`, `poses_file`). 설치 위치는 이번에 정하지 않는다.
- 상태 이름(정확히): `STOPPED`, `RESETTING`, `HOMED`, `IDLE`, `RUNNING`, `PAUSED`. 주문 상태: `QUEUED`, `RUNNING`, `DONE`, `FAILED`.
- 테스트는 저장소 루트에서 `source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash && source cobot1_ws/install/setup.bash` 후 `python3 -m pytest` 로 실행한다. `python3-websocket` 설치 필요 (`sudo apt install python3-websocket ros-jazzy-rosbridge-suite`).

## Review Focus

1. 일시정지(이동 도중) 상태에서 강제 정지 → 로봇 재개 없이 `STOPPED`, 주문 `FAILED`. (Task 4 `test_force_stop_while_paused`)
2. `gripper`/`io`/단계 사이에서 일시정지 → 그 단계 완료 후 멈추고, 재개 시 `robot.resume()`을 부르지 않는다. (Task 4 `test_pause_during_gripper_applies_after_step`)
3. 백엔드가 `DONE` 순간의 상태 메시지를 놓침 → 다음 주기 메시지(`state=IDLE`, `order_state=DONE`)로 주문이 `DONE`이 된다. (Task 6 `test_done_detected_from_idle_message`)
4. 두 키오스크/중복 이벤트로 디스패치가 겹침 → `execute_recipe`는 한 번만 호출, coffee_process는 `IDLE` 아니면 거절. (Task 4 `test_execute_rejected_when_not_idle`, Task 6 `test_no_double_dispatch`)
5. coffee_process 재시작 후 DB에 남은 `RUNNING` 주문 → `FAILED`로 정리되고 다음 주문이 막히지 않는다. (Task 6 `test_orphan_running_order_failed`)

---

## File Structure

| 파일 | 책임 |
|---|---|
| `cobot1_ws/src/robot_driver/robot_driver/doosan_adapter.py` (수정) | 비동기 이동 + 완료 대기(`_wait_motion`), stop 이벤트 확인 |
| `cobot1_ws/src/robot_driver/robot_driver/driver_control.py` (신규) | 제어 노드: `/robot_driver/pause|resume|stop` → 두산 move_pause/resume/stop |
| `cobot1_ws/src/robot_driver/robot_driver/driver_node.py` (수정) | 제어 노드 스레드 기동, `/robot_driver/set_digital_output` |
| `cobot1_ws/src/robot_control/robot_control/pausable_wait.py` (신규) | 일시정지 시간 제외 타임아웃 대기 (ROS 비의존) |
| `cobot1_ws/src/robot_control/robot_control/driver_client.py`, `robot_control_node.py` (수정) | pause/resume 서비스, stop 경로 교체 |
| `cobot1_ws/src/coffee_process/coffee_process/process_runner.py` (신규) | 상태 머신 + 작업 스레드 (ROS 비의존). `process_manager.py` 대체 |
| `cobot1_ws/src/coffee_process/coffee_process/process_executor.py` (수정) | `wait` 단계를 주입된 대기 함수로 |
| `cobot1_ws/src/coffee_process/coffee_process/ros_clients.py` (신규) | `RobotClient`, `IOClient` (ROS 서비스 클라이언트) |
| `cobot1_ws/src/coffee_process/coffee_process/coffee_process_node.py` (재작성) | 서비스 5개, 상태 발행, 파라미터 |
| `cobot1_ws/src/cafe_interfaces/msg/ProcessStatus.msg` (수정) | `string order_state` |
| `config/robot/{virtual,real}/poses.yaml` (수정) | `trash` 포즈, 중복 키 제거 |
| `backend/database/db.py` (수정) | 대기열 조회/상태 변경 함수 |
| `backend/services/dispatcher.py` (신규) | 디스패처 |
| `backend/rosbridge/rosbridge_client.py`, `connection.py`, `backend/app.py` (수정) | 상태 콜백 → 디스패처, order_state 반영 |
| `backend/routes/api.py` (수정) | 제어 API, 대기 순번 |
| `backend/services/robot_service.py` (삭제) | 미사용 스텁 |
| `frontend/index.html`, `frontend/js/kiosk.js`, `frontend/js/robot_status.js` (수정) | 버튼 3개 + 상태별 전환 |
| `tests/conftest.py` (신규) | ROS 패키지 소스 경로를 `sys.path`에 추가 |

---

### Task 0: 브랜치

- [ ] **Step 1:** `git checkout -b feat/web-robot-integration` (main에서). 이후 모든 커밋은 이 브랜치에.

---

### Task 1: 검증 스파이크 (버리는 코드, 설계 §4.1 / §9 0단계)

**Files:**
- Create: 스크래치 스크립트 (저장소 밖, 커밋하지 않음)
- Modify: `WEB_ROBOT_INTEGRATION_DESIGN.md` §4.1 끝에 "0단계 결과" 단락

**전제:** 가상 로봇 실행 중 (`ros2 launch m0609_rg2_bringup bringup.launch.py`), 프로젝트 드라이버는 꺼 둔다.

- [ ] **Step 1:** `ros2 service call`만으로 아래를 측정하고 결과를 기록한다. `vel=10`으로 느린 이동 `[0,0,90,0,90,0] ↔ [60,0,60,0,90,0]` 사용.
  1. 터미널 A: 동기 `/dsr01/dsr_controller2/motion/move_joint` (`sync_type: 0`) 호출. 1초 뒤 터미널 B: `/dsr01/dsr_controller2/motion/move_pause` 호출 → B의 응답이 **즉시** 오는지, A가 끝난 뒤 오는지. `/dsr01/joint_states`로 실제 멈췄는지.
  2. `sync_type: 1`(비동기)로 이동 → `motion/check_motion` 값: 이동 중, `move_pause` 후, `move_resume` 후, 완료 후.
  3. 비동기 이동 중 `motion/move_stop` (`stop_mode: 1`) → `check_motion` 값, 관절 정지 여부.
  4. `move_pause` 후 `move_resume` → 원래 목표에 도달하는지.
- [ ] **Step 2:** 결정 기록. 규칙: 1번에서 pause 응답이 이동 완료를 기다리면 → **비동기 이동 채택** (Task 2 그대로). 즉시 응답하고 실제로 멈추면 → 동기 `movej` 유지, Task 2의 Step 3~5(비동기 전환) 생략하고 stop 이벤트 확인만 이동 후에 수행. 2번의 일시정지 중 `check_motion` 값을 Task 2 `_wait_motion`의 "계속 대기" 조건으로 사용(예상: `2`=BUSY).
- [ ] **Step 3:** 설계 문서에 결과 단락 추가 후 커밋.

```bash
git add WEB_ROBOT_INTEGRATION_DESIGN.md
git commit -m "docs: record controller pause/stop spike results"
```

---

### Task 2: robot_driver — 제어 노드, 비동기 이동, DO 서비스

**Files:**
- Create: `cobot1_ws/src/robot_driver/robot_driver/driver_control.py`
- Modify: `cobot1_ws/src/robot_driver/robot_driver/doosan_adapter.py` (move_joint/move_line), `robot_driver.py`, `driver_node.py`, `package.xml`
- Create: `tests/conftest.py`, `tests/test_driver_motion.py`

**Interfaces:**
- Produces (ROS): `/robot_driver/pause`, `/robot_driver/resume`, `/robot_driver/stop` — `std_srvs/srv/Trigger`; `/robot_driver/set_digital_output` — `cafe_interfaces/srv/SetDigitalOutput` (`channel:int32, value:bool → success, message`).
- Produces (Python): `DoosanAdapter.stop_event: threading.Event`; `DoosanAdapter._wait_motion(tick: float = 0.1) -> None` (stop이면 `RuntimeError("stopped")`).

- [ ] **Step 1: `tests/conftest.py`** — 저장소 루트 기준 `cobot1_ws/src/{robot_driver,robot_control,coffee_process}`를 `sys.path` 앞에 추가.

- [ ] **Step 2: 실패하는 테스트 `tests/test_driver_motion.py`**

`DoosanAdapter`를 DSR 없이 만들기 위해 `DoosanAdapter.__new__`로 생성 후 `dsr`, `available=True`, `stop_event`를 주입한다. 가짜 dsr: `amovej/amovel`은 호출 기록, `check_motion()`은 미리 준 값 시퀀스를 차례로 반환.

```python
def test_move_joint_waits_until_idle():
    a = make_adapter(check_values=[2, 2, 0])
    a.move_joint([0, 0, 90, 0, 90, 0], 30.0, 30.0)
    assert a.dsr.calls == [("amovej", [0, 0, 90, 0, 90, 0], 30.0, 30.0)]
    assert a.dsr.check_count == 3

def test_move_joint_raises_when_stopped():
    a = make_adapter(check_values=[2, 0])
    a.stop_event.set()
    with pytest.raises(RuntimeError, match="stopped"):
        a.move_joint([0] * 6, 30.0, 30.0)

def test_stop_event_cleared_on_new_motion():
    a = make_adapter(check_values=[0])
    a.stop_event.set()
    a.clear_stop()
    a.move_joint([0] * 6, 30.0, 30.0)   # 예외 없음
```

- [ ] **Step 3:** 실행 → FAIL (`amovej` 미호출 / `_wait_motion` 없음).
  Run: `python3 -m pytest tests/test_driver_motion.py -v`

- [ ] **Step 4: 구현 (`doosan_adapter.py`)**
  - `__init__`: `self.stop_event = threading.Event()`
  - `clear_stop(self) -> None`
  - `move_joint`: `self.dsr.amovej(joints, vel=velocity, acc=acceleration)` → `self._wait_motion()`
  - `move_line`: `self.dsr.amovel(pose, vel=[v, v], acc=[a, a])` → `self._wait_motion()`
  - `_wait_motion(tick=0.1)`: `check_motion()`이 `0`(DR_STATE_IDLE)이 될 때까지 `tick` 간격 대기. 반복 중 또는 종료 후 `stop_event`가 set이면 `RuntimeError("stopped")`. `check_motion()`이 `-1`(서비스 실패)이면 `RuntimeError("check_motion failed")`.
  - `DriverNode.execute_move_*`는 시작 시 `self.driver.adapter.clear_stop()` 호출 (`RobotDriver.clear_stop()` 위임 추가).

- [ ] **Step 5:** 실행 → PASS.

- [ ] **Step 6: `driver_control.py`**
  - `class DriverControlNode(rclpy.node.Node)`: `__init__(self, robot_name: str, stop_event: threading.Event)`. 노드 이름 `robot_driver_ctrl`.
  - 클라이언트: `dsr_msgs2.srv.MovePause|MoveResume|MoveStop` → `f"/{robot_name}/dsr_controller2/motion/move_pause"` 등.
  - 서비스 `/robot_driver/pause|resume|stop` (Trigger). 각 콜백은 `call_async` + `threading.Event` 대기(3초). 콜백과 클라이언트는 하나의 `ReentrantCallbackGroup`.
  - `stop`: 먼저 `stop_event.set()`, 그 다음 `MoveStop(stop_mode=1)` 호출.
  - 응답: 두산 `success`와 타임아웃 시 `message="timeout"`.

- [ ] **Step 7: `driver_node.py`**
  - `main()`: `DriverNode` 생성 후 `DriverControlNode(robot_name, node.driver.adapter.stop_event)`를 별도 `MultiThreadedExecutor`에 add하고 `threading.Thread(target=ctrl_executor.spin, daemon=True).start()`. 메인은 기존 `SingleThreadedExecutor`.
  - `DriverNode`에 서비스 `/robot_driver/set_digital_output` (`SetDigitalOutput`) → `self.driver.set_output(channel, value)`; 예외 시 `success=False, message=str(exc)`.
  - `package.xml`: `<depend>dsr_msgs2</depend>`, `<depend>std_srvs</depend>`.

- [ ] **Step 8: 시뮬레이션 확인** (빌드: `./scripts/build.sh`)
  - `ros2 action send_goal /robot_driver/move_joint ... "{position: [60,0,60,0,90,0], velocity: 10.0, acceleration: 10.0}"` 실행 중 `ros2 service call /robot_driver/pause std_srvs/srv/Trigger` → 응답 1초 이내, 관절 정지. `resume` → 목표 도달 후 액션 SUCCEEDED.
  - 이동 중 `/robot_driver/stop` → 액션 ABORTED, message `stopped`.
  - `ros2 service call /robot_driver/set_digital_output cafe_interfaces/srv/SetDigitalOutput "{channel: 1, value: true}"` → `success: true`.

- [ ] **Step 9: Commit**

```bash
git add cobot1_ws/src/robot_driver tests/conftest.py tests/test_driver_motion.py
git commit -m "feat(robot_driver): control channel for pause/resume/stop, async motion, DO service"
```

---

### Task 3: robot_control — pause/resume, stop 경로, 일시정지 제외 타임아웃

**Files:**
- Create: `cobot1_ws/src/robot_control/robot_control/pausable_wait.py`, `tests/test_pausable_wait.py`
- Modify: `driver_client.py`, `robot_control_node.py`, `robot_controller.py`, `motion_manager.py`, `package.xml`

**Interfaces:**
- Consumes: `/robot_driver/pause|resume|stop` (Task 2)
- Produces (ROS): `/robot_control/pause`, `/robot_control/resume` — `std_srvs/srv/Trigger`; `/robot_control/stop_process` (기존 `StopProcess`) → 드라이버 `stop`.
- Produces (Python): `wait_unless_paused(done: threading.Event, is_paused: Callable[[], bool], timeout: float, tick: float = 0.5) -> bool`

- [ ] **Step 1: 실패하는 테스트**

```python
def test_returns_true_when_done():
    e = threading.Event(); e.set()
    assert wait_unless_paused(e, lambda: False, timeout=1.0, tick=0.01) is True

def test_times_out_when_not_paused():
    assert wait_unless_paused(threading.Event(), lambda: False, timeout=0.05, tick=0.01) is False

def test_paused_time_not_counted():
    e = threading.Event()
    paused = {"v": True}
    threading.Timer(0.2, lambda: (paused.update(v=False), e.set())).start()
    assert wait_unless_paused(e, lambda: paused["v"], timeout=0.1, tick=0.01) is True
```

- [ ] **Step 2:** 실행 → FAIL (모듈 없음). `python3 -m pytest tests/test_pausable_wait.py -v`
- [ ] **Step 3:** `pausable_wait.py` 구현 (ROS import 금지). 경과 시간은 `is_paused()`가 False인 tick만 누적.
- [ ] **Step 4:** 실행 → PASS.
- [ ] **Step 5: `driver_client.py`**
  - `self.paused = False`; Trigger 클라이언트 3개 (`/robot_driver/pause|resume|stop`, 같은 Reentrant 그룹).
  - `_send_goal`: `result_done.wait(timeout)` → `wait_unless_paused(result_done, lambda: self.paused, timeout)`.
  - `pause()`: 드라이버 pause 성공 시 `paused=True`. `resume()`: 성공 시 `paused=False`. `stop()`: 드라이버 stop 호출 후 `paused=False` (기존 cancel_goal 방식 삭제). 실패 시 `RuntimeError(message)`.
  - Trigger 호출 헬퍼: `call_async` + Event, 타임아웃 5초.
- [ ] **Step 6: `robot_control_node.py`**: `/robot_control/pause`, `/robot_control/resume` (Trigger) 추가. 모든 서비스는 하나의 `ReentrantCallbackGroup` (이동 서비스가 블로킹 중에 pause가 들어와야 함). `RobotController`/`MotionManager`에 `pause()`/`resume()` 위임 추가. `package.xml`에 `std_srvs`.
- [ ] **Step 7: 시뮬레이션 확인**
  - `/robot_control/move_named_pose` (느린 속도로 먼 포즈) 호출 중 `/robot_control/pause` → 40초 대기 → `/robot_control/resume` → move_named_pose 응답 `success=True`.
  - 이동 중 `/robot_control/stop_process "{emergency: true}"` → move_named_pose `success=False`, message에 `stopped`.
- [ ] **Step 8: Commit**

```bash
git add cobot1_ws/src/robot_control tests/test_pausable_wait.py
git commit -m "feat(robot_control): pause/resume services, driver stop path, pause-aware timeout"
```

---

### Task 4: coffee_process — ProcessRunner 상태 머신 (ROS 비의존)

**Files:**
- Create: `cobot1_ws/src/coffee_process/coffee_process/process_runner.py`, `tests/test_process_runner.py`
- Modify: `process_executor.py`
- Delete: `process_manager.py` (ProcessRunner로 대체, 다른 곳에서 미사용)

**Interfaces:**
- Consumes: `RecipeManager.load_recipe(recipe_id) -> dict` (기존, `{"id","name","steps":[...]}`)
- Produces:

```python
class ProcessRunner:
    def __init__(self, recipe_manager, robot, io, on_status: Callable[[dict], None]): ...
    state: str                                   # 초기값 "STOPPED"
    def execute(self, order_id: str, recipe_id: str) -> tuple[bool, str]
    def pause(self) -> tuple[bool, str]
    def resume(self) -> tuple[bool, str]
    def force_stop(self) -> tuple[bool, str]
    def start(self) -> tuple[bool, str]
    def snapshot(self) -> dict   # keys: order_id, recipe_id, state, order_state, current_step,
                                 #       current_step_index, total_steps, progress, message
    def join(self, timeout: float | None = None) -> None   # 작업 스레드 종료 대기 (테스트·종료용)
```
  - `robot` 프로토콜: `move_to_pose(name: str, velocity: float, acceleration: float) -> None`, `pause()`, `resume()`, `stop()` — 실패 시 예외.
  - `io` 프로토콜: `set_output(name: str, value: bool) -> None`, `set_gripper(command: str) -> None` (`"open"|"close"`).
  - `ProcessExecutor(robot, io, wait: Callable[[float], None])` — `wait` 단계는 주입된 `wait(seconds)` 호출. `home` 액션은 `robot.move_to_pose("home", 30.0, 30.0)`. `stop` 액션 삭제.

동작 (설계 §6 그대로):
- 상태 전이 표는 설계 §6.2. 허용되지 않은 명령은 `(False, "<state>에서는 <cmd> 불가")`, 상태 불변.
- `execute`: `IDLE`만 허용 → `RUNNING`, `order_state="RUNNING"`, 작업 스레드 시작, 즉시 `(True, "accepted")`.
- 단계마다 `current_step=step["name"]`, `current_step_index=i`, `total_steps`, 단계 완료 시 `progress=(i+1)/total*100` 발행.
- 완료 → `state="IDLE"`, `order_state="DONE"`, `progress=100`. `order_id`/`order_state`는 다음 `execute`까지 유지.
- `pause` (`RUNNING`만): 현재 단계가 `move`면 `robot.pause()` 후 `_robot_paused=True`. `wait` 단계는 남은 시간 보존. 그 외 단계는 완료 후 다음 단계 전에 멈춤. 상태 `PAUSED`.
- `resume`: `PAUSED` → `_robot_paused`면 `robot.resume()` → `RUNNING`. `STOPPED` → `RESETTING` + 초기화 스레드 시작.
- `force_stop` (`RUNNING|PAUSED|RESETTING`): 중단 플래그 → `robot.stop()` → 대기 깨움. 작업 스레드는 중단 감지 시 `state="STOPPED"`, 실행 중이던 주문은 `order_state="FAILED"`, `message="강제 정지"`.
- 단계 예외(중단 플래그 없음) → `STOPPED`, `order_state="FAILED"`, `message=str(exc)`.
- 컵 추적: 그리퍼 `close` 호출을 **시작한 시점**에 `_holding_cup=True`, `open` 성공 시 `False`.
- 초기화: `_holding_cup`이면 `move_to_pose("trash")` → `set_gripper("open")` → `move_to_pose("home")`; 아니면 `home`만. 성공 → `HOMED`. 실패/강제정지 → `STOPPED`.
- `start` (`HOMED`만) → `IDLE`.
- 모든 상태 변경 직후 `on_status(snapshot())` 호출. 상태 필드는 `threading.Lock`으로 보호, 대기는 `threading.Condition`.

- [ ] **Step 1: 실패하는 테스트 `tests/test_process_runner.py`**

공통 픽스처: 가짜 `RecipeManager`(steps 주입), `FakeRobot`(호출 기록, `move_to_pose`는 `block` 이벤트가 있으면 그것을 기다림, `stop()` 시 block 해제 후 `RuntimeError("stopped")`), `FakeIO`(호출 기록), `statuses` 리스트. 헬퍼 `ready_runner()` = `resume()` → `join()` → `start()`로 `IDLE`까지.

```python
def test_initial_state_is_stopped(): assert runner.state == "STOPPED"

def test_first_reset_goes_home_only():
    r.resume(); r.join()
    assert robot.calls == [("move", "home")] and r.state == "HOMED"

def test_full_recipe_done():
    ready_runner(); assert r.execute("ORD-1", "latte") == (True, "accepted"); r.join()
    s = r.snapshot()
    assert (s["state"], s["order_state"], s["progress"], s["order_id"]) == ("IDLE", "DONE", 100.0, "ORD-1")

def test_execute_rejected_when_not_idle():
    ready_runner(); robot.block = threading.Event()
    r.execute("ORD-1", "latte")
    ok, _ = r.execute("ORD-2", "latte")
    assert ok is False and r.snapshot()["order_id"] == "ORD-1"

def test_pause_resume_move_step():
    # 첫 단계 move에서 block → pause → robot.pause 호출, PAUSED → resume → robot.resume, 완료
    ...
    assert robot.calls.count(("pause",)) == 1 and robot.calls.count(("resume",)) == 1
    assert r.snapshot()["order_state"] == "DONE"

def test_pause_during_wait_keeps_remaining_time():
    # steps=[{"action":"wait","seconds":0.3}]; 0.1초 후 pause, 0.5초 유지, resume
    # 전체 경과 >= 0.3 + 0.5, 일시정지 동안 완료되지 않음, robot.pause 미호출
    ...

def test_pause_during_gripper_applies_after_step():
    # gripper 단계 실행 중 pause → gripper 호출 완료 후 다음 단계 시작 전 PAUSED
    # resume 시 robot.resume 미호출
    ...

def test_force_stop_running_marks_failed():
    ...; r.force_stop(); r.join()
    s = r.snapshot(); assert (s["state"], s["order_state"]) == ("STOPPED", "FAILED")

def test_force_stop_while_paused():
    # move 중 pause → force_stop → robot.stop 호출, robot.resume 미호출, STOPPED/FAILED
    ...

def test_step_failure_stops():
    # robot.move_to_pose가 RuntimeError("boom") → STOPPED, FAILED, message == "boom"

def test_reset_with_cup_goes_to_trash():
    # steps=[gripper close, move(block)] 중 force_stop → resume → join
    assert robot.calls[-2:] == [("move", "trash"), ("move", "home")]
    assert io.calls[-1] == ("gripper", "open") and r.state == "HOMED"

def test_force_stop_during_resetting():
    # 초기화 중 home 이동 block → force_stop → STOPPED

def test_next_order_requires_start_after_reset():
    # STOPPED → resume → HOMED 에서 execute → (False, ...); start 후 execute → True

def test_status_callback_on_every_transition():
    # statuses의 state 시퀀스가 전이 순서와 일치 (중복 허용)
```

- [ ] **Step 2:** 실행 → FAIL. `python3 -m pytest tests/test_process_runner.py -v`
- [ ] **Step 3:** `process_executor.py` 수정 + `process_runner.py` 구현. `process_manager.py` 삭제.
- [ ] **Step 4:** 실행 → 전부 PASS. 기존 테스트도: `python3 -m pytest tests -v`
- [ ] **Step 5: Commit**

```bash
git add -A cobot1_ws/src/coffee_process tests/test_process_runner.py
git commit -m "feat(coffee_process): ProcessRunner state machine with pause/force-stop/reset"
```

---

### Task 5: coffee_process ROS 노드 + 인터페이스 + 포즈

**Files:**
- Create: `cobot1_ws/src/coffee_process/coffee_process/ros_clients.py`
- Modify: `coffee_process_node.py` (재작성), `package.xml`, `cobot1_ws/src/cafe_interfaces/msg/ProcessStatus.msg`, `config/robot/virtual/poses.yaml`, `config/robot/real/poses.yaml`
- Delete: `coffee_process/backend_bridge.py`, `BACKEND_INTEGRATION.md` 해당 단락 갱신 (노드가 직접 발행하므로 중복)

**Interfaces:**
- Consumes: `ProcessRunner` (Task 4), `/robot_control/move_named_pose|pause|resume|stop_process` (Task 3), `/robot_driver/set_digital_output` (Task 2), `/onrobot/sendCommand`.
- Produces (ROS): `/coffee_process/execute_recipe` (`ExecuteRecipe`: `recipe_id, order_id → accepted, message`), `/coffee_process/pause|resume|force_stop|start` (`std_srvs/Trigger`), `/coffee_process/status` (`ProcessStatus` + `order_state`).

- [ ] **Step 1: `ProcessStatus.msg`** 에 `string order_state` 추가 (기존 필드 뒤).
- [ ] **Step 2: `ros_clients.py`**
  - `class RobotClient`: `__init__(self, node, cb_group)`. `move_to_pose(name, velocity, acceleration)` → `MoveNamedPose(pose_name=name, motion_type="", velocity, acceleration)` 호출, **타임아웃 없음**(robot_control이 일시정지 제외 30초 타임아웃 담당), `success=False`면 `RuntimeError(message)`. `pause()/resume()` → `/robot_control/pause|resume` (5초). `stop()` → `/robot_control/stop_process` `emergency=True` (5초).
  - `class IOClient`: `__init__(self, node, cb_group, channels: dict[str, int])`. `set_output(name, value)` → 이름을 채널로 변환(`KeyError` 그대로) 후 `/robot_driver/set_digital_output` (5초). `set_gripper("open"|"close")` → `/onrobot/sendCommand` `command='o'|'c'` (10초).
  - 공통 동기 호출 헬퍼: `wait_for_service(2.0)` 실패 시 `RuntimeError("<service> not available")`, `call_async` + `threading.Event`.
- [ ] **Step 3: `coffee_process_node.py`**
  - 파라미터 `recipe_dir`(필수), `io_file`(필수, `outputs:` 매핑 사용). 비어 있으면 `RuntimeError` (robot_control의 `poses_file` 처리와 동일한 메시지 형식).
  - `ProcessRunner(RecipeManager(recipe_dir), RobotClient, IOClient, on_status=self.publish_status)`.
  - `publish_status(snapshot: dict)`: `ProcessStatus` 채워서 발행. 1초 타이머도 `publish_status(self.runner.snapshot())`. (원래 `self.publish_status()` 버그는 이 재작성으로 해소)
  - 서비스 5개는 runner 메서드를 그대로 호출해 `(ok, msg)` → `accepted/success`, `message`.
  - `MultiThreadedExecutor`, 서비스·클라이언트는 하나의 `ReentrantCallbackGroup`.
  - `package.xml`: `std_srvs`, `onrobot_rg_msgs` exec_depend.
- [ ] **Step 4: 포즈**: `virtual/poses.yaml` 중복 빈 `poses:` 키 제거, `trash: joint: [-60.0, 0.0, 90.0, 0.0, 90.0, 0.0]` (샘플, 주석 "NOT real"). `real/poses.yaml`에 `trash` 키를 다른 미티칭 포즈와 같은 형식의 주석 블록으로 추가.
- [ ] **Step 5: 시뮬레이션 확인** (build 후 rg2 bringup, driver, robot_control, coffee_process 실행)
  ```bash
  ros2 run coffee_process coffee_process_node --ros-args \
    -p recipe_dir:=$PWD/cobot1_ws/src/coffee_process/config/recipes \
    -p io_file:=$PWD/config/robot/virtual/io.yaml
  ros2 service call /coffee_process/resume std_srvs/srv/Trigger      # STOPPED → home → HOMED
  ros2 service call /coffee_process/start std_srvs/srv/Trigger       # IDLE
  ros2 service call /coffee_process/execute_recipe cafe_interfaces/srv/ExecuteRecipe "{recipe_id: latte, order_id: T-1}"
  ros2 topic echo /coffee_process/status
  ```
  Expected: 단계별 상태 발행, RViz에서 그리퍼 개폐, 최종 `state: IDLE`, `order_state: DONE`. 이동 중 `pause`/`resume`, `force_stop` → `resume`(쓰레기통 → 홈) 확인.
  ※ 샘플 포즈 다수가 관절 0이라 동작이 단조로운 것은 정상.
- [ ] **Step 6: Commit**

```bash
git add -A cobot1_ws/src/coffee_process cobot1_ws/src/cafe_interfaces config/robot
git commit -m "feat(coffee_process): ROS node with execute/pause/resume/force_stop/start services"
```

---

### Task 6: backend — DB 대기열 함수 + 디스패처

**Files:**
- Modify: `backend/database/db.py`
- Create: `backend/services/dispatcher.py`, `tests/test_dispatcher.py`

**Interfaces:**
- Produces (db.py):
  - `get_next_queued_order() -> dict | None` (가장 작은 `id`의 `QUEUED`)
  - `get_running_order() -> dict | None`
  - `set_order_status(order_id: str, status: str) -> None`
  - `get_queue_position(order_id: str) -> int` (해당 주문 앞의 `QUEUED` 수 + 1, `QUEUED` 아니면 0)
  - `update_order_progress(order_id, status, progress, current_step)` 기존 유지
- Produces (dispatcher.py):

```python
class Dispatcher:
    def __init__(self, call_service: Callable[[str, dict, str], dict]): ...
    def on_status(self, data: dict) -> None   # ProcessStatus dict
    def kick(self) -> None                    # 새 주문 시 호출, 마지막 상태로 디스패치 시도
```

동작:
- `on_status`: ① `order_id`가 DB에 있으면 `order_state`가 `DONE|FAILED`일 때 그 상태로, `RUNNING`이면 `update_order_progress(order_id, "RUNNING", progress, current_step)`. ② 고아 정리: `get_running_order()`가 있고 그 `order_id != data["order_id"]`이며 `data["state"]`가 `RUNNING|PAUSED`가 아니면 `FAILED`. ③ 마지막 상태 저장 후 `_try_dispatch()`.
- `_try_dispatch` (lock 보호): 마지막 `state == "IDLE"` and `get_running_order() is None` and 다음 `QUEUED` 존재 → `call_service("/coffee_process/execute_recipe", {"recipe_id", "order_id"}, "cafe_interfaces/srv/ExecuteRecipe")` → `accepted`면 `set_order_status(..., "RUNNING")` 그리고 마지막 상태를 `RUNNING`으로 간주(다음 IDLE 메시지까지 재디스패치 안 함). 예외/거절 시 아무것도 바꾸지 않음.

- [ ] **Step 1: 실패하는 테스트** — `monkeypatch.setattr(backend.database.db, "DATABASE_PATH", tmp_path / "t.db")` 후 `init_database()`. 가짜 `call_service`는 호출 기록, `{"accepted": True, "message": ""}` 반환.

```python
def test_dispatch_when_idle():
    save_order("A", "latte", "Latte"); d.on_status(status("IDLE"))
    assert calls == [("/coffee_process/execute_recipe", {"recipe_id": "latte", "order_id": "A"})]
    assert get_order("A")["status"] == "RUNNING"

def test_no_dispatch_when_not_idle():           # state in RUNNING/PAUSED/STOPPED/HOMED → 호출 없음
def test_fifo_order():                          # A, B 저장 → A만 전송
def test_no_double_dispatch():                  # IDLE 메시지 연속 2회 + kick → 호출 1회
def test_done_detected_from_idle_message():     # A RUNNING, status(state="IDLE", order_id="A", order_state="DONE") → A DONE, 그리고 B 전송
def test_failed_order_marked():                 # order_state FAILED → FAILED, STOPPED라 B 미전송
def test_orphan_running_order_failed():         # DB A RUNNING, status(state="STOPPED", order_id="") → A FAILED
def test_rejected_dispatch_keeps_queued():      # call_service → accepted False → A 그대로 QUEUED
def test_service_error_keeps_queued():          # call_service raises ConnectionError → QUEUED, 예외 전파 없음
def test_queue_position():                      # A RUNNING, B, C QUEUED → B=1, C=2, A=0
```

- [ ] **Step 2:** 실행 → FAIL. `python3 -m pytest tests/test_dispatcher.py -v`
- [ ] **Step 3:** db 함수 + `Dispatcher` 구현.
- [ ] **Step 4:** 실행 → PASS.
- [ ] **Step 5: Commit**

```bash
git add backend/database/db.py backend/services/dispatcher.py tests/test_dispatcher.py
git commit -m "feat(backend): order queue dispatcher"
```

---

### Task 7: backend — rosbridge 연결, 제어 API, 대기 순번

**Files:**
- Modify: `backend/rosbridge/rosbridge_client.py`, `backend/rosbridge/connection.py`, `backend/app.py`, `backend/routes/api.py`, `backend/services/order_service.py`
- Delete: `backend/services/robot_service.py`
- Modify: `tests/test_api.py`

**Interfaces:**
- Consumes: `Dispatcher` (Task 6), `ROSBridgeClient.call_service(service, args, service_type, timeout=5)` (기존)
- Produces (HTTP): `POST /api/control/<cmd>` (`cmd ∈ {pause, resume, force_stop, start}`) → `200 {"success": bool, "message": str}` / 알 수 없는 cmd `404` / rosbridge 연결 실패(`OSError`, `ConnectionError`, `websocket.WebSocketException`) `503 {"error": ...}`. `POST /api/orders` 응답에 `"queue_position": int`.
- `connection.py`: `get_dispatcher() -> Dispatcher`.

- [ ] **Step 1: 실패하는 테스트 (`tests/test_api.py`에 추가)** — `create_app()` 후 `backend.routes.api`가 쓰는 클라이언트/디스패처를 monkeypatch.

```python
def test_control_pause_calls_service(): # call_service 기록 == ("/coffee_process/pause", {}, "std_srvs/srv/Trigger"), 200, json success True
def test_control_unknown_cmd_404():
def test_control_rosbridge_down_503():  # call_service raises ConnectionRefusedError
def test_order_returns_queue_position_and_kicks():  # kick 1회, queue_position == 1
```

- [ ] **Step 2:** 실행 → FAIL.
- [ ] **Step 3: 구현**
  - `ROSBridgeClient.__init__`에 `on_status: Callable[[dict], None] | None = None`. `_handle_message`: socket emit, `save_process_status`는 유지, 기존 `update_order_progress(order_id, state, ...)` 호출은 **삭제**(process state를 주문 status에 쓰던 버그) → `on_status(data)` 호출. `on_status` 예외는 로그만.
  - `connection.init_rosbridge_client`: `Dispatcher(client.call_service)` 생성, `on_status=dispatcher.on_status`로 연결, 모듈 전역에 보관.
  - `api.py`: 제어 라우트, 주문 생성 후 `get_dispatcher().kick()`, 응답에 `get_queue_position`.
  - `robot_service.py` 삭제.
- [ ] **Step 4:** 실행 → PASS. 전체 `python3 -m pytest tests -v`.
- [ ] **Step 5: Commit**

```bash
git add -A backend tests/test_api.py
git commit -m "feat(backend): control API, dispatcher wiring, queue position"
```

---

### Task 8: frontend — 버튼 3개 + 상태별 전환

**Files:**
- Modify: `frontend/index.html` (`section.emergency` 교체), `frontend/js/kiosk.js`, `frontend/js/robot_status.js`, `frontend/css/kiosk.css`

**Interfaces:**
- Consumes: `POST /api/control/<cmd>`, Socket.IO `coffee_progress` (ProcessStatus dict, `state`, `order_state` 포함), `POST /api/orders` 응답 `queue_position`.

- [ ] **Step 1: HTML** — `section.emergency`를 `section.controls`로: `<button id="btn-pause">`, `<button id="btn-force">`, `<button id="btn-start">`, 상태 텍스트 `#robot-state` 재사용.
- [ ] **Step 2: `robot_status.js`** — `renderControls(state)`가 설계 §8.7 표를 그대로 적용:

| state | btn-pause | btn-force | btn-start |
|---|---|---|---|
| IDLE | 정지·비활성 | 강제 정지·비활성 | 비활성 |
| RUNNING | 정지 → pause | 강제 정지 → force_stop | 비활성 |
| PAUSED | **재개** → resume | 강제 정지 → force_stop | 비활성 |
| STOPPED | 정지·비활성 | **재개** → resume | 비활성 |
| RESETTING | 정지·비활성 | 강제 정지 → force_stop | 비활성 |
| HOMED | 정지·비활성 | 강제 정지·비활성 | 시작 → start |

  상태 한글 표기: IDLE `주문 대기`, RUNNING `제조 중`, PAUSED `일시정지`, STOPPED `강제 정지 (초기화 필요)`, RESETTING `초기화 중`, HOMED `시작 대기`. `coffee_progress` 수신 시마다 `renderControls(data.state)`. 주문 상태: 내 주문 ID가 `data.order_id`와 같으면 `order_state`(RUNNING `제조 중`/DONE `완료`/FAILED `실패`) 표시.
- [ ] **Step 3: `kiosk.js`** — `emergencyStop()` 삭제. `sendControl(cmd)`: `fetch("/api/control/" + cmd, {method: "POST"})`, `success=false`면 `message`를 `#process-message`에 표시(alert 금지). 버튼 클릭은 현재 매핑된 cmd 호출. 주문 성공 시 `queue_position > 0`이면 `대기 n번째` 표시.
- [ ] **Step 4: 수동 확인** — rosbridge, backend, ROS 노드 전부 실행 후 브라우저 `http://localhost:5000`. 표의 6개 상태에서 버튼 텍스트/활성 상태가 일치하는지 확인.
- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat(frontend): pause/force-stop/start controls with state-based toggle"
```

---

### Task 9: 통합 시뮬레이션 시나리오

**Files:** 없음 (결과는 PR/커밋 메시지에 기록)

- [ ] **Step 1:** 설계 §9 통합 시나리오 1~5를 브라우저에서 순서대로 수행. 각 시나리오의 기대 결과:
  1. 강제 정지 자리 **재개** → 홈 → **시작** → 주문 2건 → 순서대로 `완료`, 두 번째는 첫 번째 완료 후 시작.
  2. 이동 중 **정지** → 40초 → **재개** → 같은 궤적으로 이어서 `완료`.
  3. Espresso Wait 중 **정지** → **재개** → 남은 시간만 대기.
  4. Grip Cup 이후 **강제 정지** → 주문 `실패` → **재개** → trash → 그리퍼 열림(RViz) → home → `시작 대기`, 시작 전까지 대기 주문 미시작 → **시작** → 다음 주문 진행.
  5. 대기 주문이 있는 상태에서 백엔드 재시작 → 대기 주문 유지, 이어서 디스패치.
- [ ] **Step 2:** 실패한 시나리오는 해당 Task로 돌아가 테스트 추가 후 수정.
- [ ] **Step 3:** 전체 테스트 `python3 -m pytest tests -v` PASS 확인.
