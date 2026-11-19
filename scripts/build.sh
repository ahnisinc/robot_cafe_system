#!/bin/bash

set -e

source /opt/ros/jazzy/setup.bash

cd "$(dirname "$0")/../cobot1_ws"

colcon build --symlink-install

source install/setup.bash

echo ""
echo "=========================================="
echo "Robot Cafe ROS2 build completed."
echo "=========================================="
