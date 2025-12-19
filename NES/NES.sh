#!/bin/bash
# NES.sh 启动脚本 - 稳定运行版

set -e

# 获取脚本所在目录并切换进去
BASE_DIR="$(dirname "$0")"
cd "$BASE_DIR"

# 1. 停止 EmulationStation 抢占（防止手柄冲突）
batocera-es-swissknife --stop-es || true

# 2. 启动商城主程序
# 使用 python3 运行，确保路径正确
python3 ./main.py

# 3. 当商城退出后，重新启动 EmulationStation 回到系统界面
batocera-es-swissknife --restart-es