#!/bin/bash
# NES.sh 启动脚本

set -e

BASE_DIR="$(dirname "$0")"
cd "$BASE_DIR"

# 停止 EmulationStation 抢占（可选）
batocera-es-swissknife --stop-es || true

# 启动 Python 程序
python3 ./main.py

# 程序退出后重启 ES
batocera-es-swissknife --restart-es