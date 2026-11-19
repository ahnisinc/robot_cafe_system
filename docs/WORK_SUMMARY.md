# 작업 정리 (2026-11-18)

브랜치: `feat/web-robot-integration` (main 대비 12커밋, 42파일, +2873/−296)
테스트: `python3 -m pytest tests -q` → 59 passed
상세 설계: [WEB_ROBOT_INTEGRATION_DESIGN.md](WEB_ROBOT_INTEGRATION_DESIGN.md) · 계획: [WEB_ROBOT_INTEGRATION_PLAN.md](WEB_ROBOT_INTEGRATION_PLAN.md)

---

## 1. 시뮬레이션 실행 문제 수정 (선행 작업)

| 문제 | 원인 | 수정 |
|------|------|------|
| `start_backend.sh`, `start_rosbridge.sh`, `build.sh` Permission denied | 실행 권한 없음 | `chmod +x` (git mode 100755) |
| `movej() got an unexpected keyword argument 'sync_type'` | DSR_ROBOT2 API에 없는 인자 | 인자 제거 |
| 서비스 호출 후 30초 무응답 | 서비스 콜백과 액션 클라이언트가 같은 MutuallyExclusive 그룹 | 콜백 그룹 분리 |
| `Executor is already spinning` | DSR_ROBOT2가 내부에서 글로벌 executor로 `spin_until_future_complete` 호출 | 전용 노드 `robot_driver_dsr` + 별도 executor로 분리 |
| `No module named 'DR_init'` | 드라이버 터미널에서 `~/ros2_ws` 미소싱 | `source ~/ros2_ws/install/setup.bash` 안내 |

참고 문서: `~/ROS2_Executor_정리.md` (executor / 스레드 / 콜백 그룹 정리)

## 2. 웹 ↔ 로봇 연동 — 확정된 동작

- **주문 큐**: 키오스크 주문은 DB 큐(QUEUED)에 쌓이고, 현재 커피가 끝나야 다음 주문 시작.
- **정지(Pause)**: 그 자리에서 멈춤. 현재 주문/큐 유지. 재개 시 같은 지점부터 계속.
- **강제 정지(Force stop)**: 즉시 정지 → 현재 주문 FAILED → 컵을 들고 있으면 `trash` 포즈에 버림 → 그리퍼 열기 → 홈 복귀 → **시작** 명령 전까지 다음 주문 대기.
- **버튼**: PAUSED일 때 `정지` → `재개`, STOPPED일 때 `강제 정지` → `재개`(시작).
- **그리퍼**: `/onrobot/sendCommand` 서비스(Modbus) 사용.

## 3. 구조

```
키오스크(JS) ──HTTP/Socket.IO──> Flask 백엔드 ──rosbridge──> coffee_process 노드
                                  │ Dispatcher(큐)              │ ProcessRunner(상태머신)
                                  └ SQLite                      ▼
                                                     robot_control ──> robot_driver ──> Doosan 컨트롤러
```

상태: `STOPPED → RESETTING → HOMED → IDLE → RUNNING ⇄ PAUSED`

## 4. 변경 내용 (패키지별)

### robot_driver
- `doosan_adapter.py`: 동기 `movej/movel` → **비동기 `amovej/amovel` + `check_motion` 폴링**. (스파이크 결과 동기 모션 중에는 `move_pause`가 모션 끝날 때까지 ~6.5초 막힘)
- 정지 래치(stop latch): stop 후 새 모션 차단, `clear_stop`으로만 해제.
- `driver_control.py`(신규): `/robot_driver/pause|resume|stop|clear_stop` 서비스 → 컨트롤러 `motion/move_pause|move_resume|move_stop` 호출. 액션 executor와 분리된 MultiThreadedExecutor(4스레드).
- `/robot_driver/set_digital_output` 서비스 추가.

### robot_control
- pause/resume/clear_stop 서비스 추가, stop 시 드라이버 stop 호출.
- `pausable_wait.py`(신규): 일시정지 시간은 타임아웃에서 제외.

### coffee_process
- `process_runner.py`(신규, ROS 비의존 상태머신): execute / pause / resume / force_stop / start, 단계별 체크포인트, 컵 보유 추적.
- `coffee_process_node.py`(재작성): 서비스 `execute_recipe, pause, resume, force_stop, start` + `/coffee_process/status` 발행.
- `ros_clients.py`(신규): Robot/IO/그리퍼 서비스 클라이언트.
- `process_manager.py` 삭제. `ProcessStatus.msg`에 `order_state` 추가.

### backend
- `services/dispatcher.py`(신규): coffee_process가 IDLE이면 다음 QUEUED 주문 디스패치. 중복 디스패치 방지, 고아 RUNNING → FAILED, 끝난 주문은 늦게 온 RUNNING 메시지로 되살아나지 않음.
- `POST /api/orders`: 큐 위치(`queue_position`) 반환.
- `POST /api/control/<pause|resume|force_stop|start>` 추가 (미지원 404, rosbridge 끊김 503).
- `app.py`: `manage_session=False` (Ubuntu Flask 3.0.2에서 Socket.IO 핸드셰이크 실패 수정).
- `services/robot_service.py`(스텁) 삭제.

### frontend
- 비상정지 섹션 → 정지/강제정지/시작 컨트롤, 상태별 버튼 라벨 전환, 한글 상태 표시.
- `alert` 제거, 주문 결과를 화면 메시지로 표시.

### config
- `config/robot/virtual/poses.yaml`: 도달 가능한 관절값 + `trash` 추가.
- `config/robot/real/poses.yaml`: `trash` 자리만 추가(0값, **티칭 필요**).

### tests (신규/확장)
`test_process_runner.py`(21), `test_dispatcher.py`(18), `test_driver_motion.py`(8), `test_pausable_wait.py`(3), `test_api.py`(+6), `conftest.py`.

## 5. 검증 결과

- 단위 테스트 59개 통과.
- 가상 로봇 시뮬레이션: 40초 정지 후 재개 완주, 강제 정지 → trash → 홈 → 시작 후 다음 주문.
- 브라우저 E2E 시나리오 0~5 통과: 초기 상태, 2건 큐, 브라우저 정지/재개, 에스프레소 대기 중 정지, 강제 정지 후 큐 보류→시작, 백엔드 재시작 후 큐 유지.
- 최종 코드리뷰 지적사항(정지 래치 유실, 러너 경쟁 조건, 모션 경계 재개, 정지 실패를 성공으로 보고, 끝난 주문 부활 등) 수정 완료.

## 6. 남은 일 / 주의

- **실로봇 미검증**: `trash` 포즈 티칭, trash 경로 충돌, DO 동작(가상에선 readback 0), RG2 Modbus.
- robot_control이 모션 중 죽으면 coffee_process가 대기 상태로 남음 (미처리).
- 사소한 것: 키오스크 에러 메시지가 1초 후 덮어써짐, 큐 위치는 주문 직후에만 표시, dispatcher가 서비스 호출(최대 5초) 동안 락 보유, 강제 정지 후 리셋 시 빈 그리퍼로 trash 재방문 가능.
- 설치 필요: `sudo apt install ros-jazzy-rosbridge-suite python3-websocket`
- 레시피 YAML 위치는 추후 결정 (현재 `recipe_dir` 파라미터).
- 브랜치 미병합·미푸시.
