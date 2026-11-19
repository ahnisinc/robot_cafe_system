#!/bin/bash
# 로봇 카페 ROS 환경 설정. 사용: source scripts/cafe_env.sh  (start_sim.sh 가 자동으로 불러옴)
# 경로가 다르면 미리 지정: DOOSAN_WS(기본 ~/ros2_ws), ROS_DISTRO(기본 jazzy), ROS_DOMAIN_ID(기본 9)


CAFE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOOSAN_WS="${DOOSAN_WS:-$HOME/ros2_ws}"

for f in "/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash" \
         "$DOOSAN_WS/install/setup.bash" \
         "$CAFE_ROOT/cobot1_ws/install/setup.bash"; do
    if [ ! -f "$f" ]; then
        echo "없음: $f  (DOOSAN_WS 경로 확인 또는 scripts/build.sh 실행)" >&2
        return 1 2>/dev/null || exit 1
    fi
    source "$f"
done

unset ROS_DISCOVERY_SERVER ROS_SUPER_CLIENT
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-9}"
cd "$CAFE_ROOT"
