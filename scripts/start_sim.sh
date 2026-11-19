#!/bin/bash
# 가상 로봇 + ROS 노드 + rosbridge + 백엔드를 한 번에 실행. Ctrl+C 한 번으로 전부 종료.
# 각 프로세스 로그: log/sim/<이름>.log

source "$(dirname "$0")/cafe_env.sh" || exit 1
ROOT="$CAFE_ROOT"
LOG="$ROOT/log/sim"
mkdir -p "$LOG"

if pgrep -f "ros2_control_node|run_emulator|driver_node|robot_control_node|coffee_process_node|rosbridge_websocket|backend.app" > /dev/null; then
    echo "이미 실행 중인 시뮬레이션/노드가 있습니다. 먼저 종료하세요."
    exit 1
fi

trap 'echo; echo "종료 중..."; kill -INT 0 2>/dev/null; wait' EXIT
trap 'exit' INT TERM

wait_log() {
    for _ in $(seq "$3"); do grep -q "$2" "$1" 2>/dev/null && return 0; sleep 1; done
    echo "시간 초과: $1 에서 '$2' 를 못 찾았습니다."; exit 1
}

echo "[1/6] 가상 로봇 (RViz)"
ros2 launch m0609_rg2_bringup bringup.launch.py > "$LOG/bringup.log" 2>&1 &
wait_log "$LOG/bringup.log" "Configured and activated dsr_controller2" 90

echo "[2/6] robot_driver"
ros2 run robot_driver driver_node > "$LOG/driver.log" 2>&1 &
echo "[3/6] robot_control"
ros2 run robot_control robot_control_node --ros-args \
    -p poses_file:="$ROOT/config/robot/virtual/poses.yaml" > "$LOG/control.log" 2>&1 &
echo "[4/6] coffee_process"
ros2 run coffee_process coffee_process_node --ros-args \
    -p recipe_dir:="$ROOT/cobot1_ws/src/coffee_process/config/recipes" \
    -p io_file:="$ROOT/config/robot/virtual/io.yaml" > "$LOG/coffee.log" 2>&1 &
echo "[5/6] rosbridge"
ros2 launch rosbridge_server rosbridge_websocket_launch.xml > "$LOG/rosbridge.log" 2>&1 &
wait_log "$LOG/rosbridge.log" "Rosbridge WebSocket server started" 30

echo "[6/6] 백엔드 → http://localhost:${FLASK_PORT:-5000}"
echo "로그: $LOG   (종료: Ctrl+C)"
"$ROOT/scripts/start_backend.sh" 2>&1 | tee "$LOG/backend.log"
