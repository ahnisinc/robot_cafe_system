#!/bin/bash

set -e

source /opt/ros/jazzy/setup.bash

ros2 launch rosbridge_server rosbridge_websocket_launch.xml
