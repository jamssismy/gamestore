#!/bin/bash
# Batocera Gamestore 安装脚本
# 这个脚本从 GitHub 下载并部署 自定义菜单 + NES 文件夹

# GitHub 仓库 RAW URL
REPO_RAW="https://raw.githubusercontent.com/jamssismy/gamestore/main"

# 目标目录
GAMSTORE="/userdata/roms/gamestore"
NESDIR="${GAMSTORE}/NES"

echo "创建目标目录..."
mkdir -p "${NESDIR}"

# 1. 下载 es_systems_gamestore.cfg 到系统配置
echo "下载自定义菜单配置..."
curl -fSL "${REPO_RAW}/es_systems_gamestore.cfg" -o "/userdata/system/configs/emulationstation/es_systems_gamestore.cfg"

# 2. 下载 NES 目录内容
echo "下载 NES 应用..."
# 创建 nes 目录
mkdir -p "${NESDIR}"

curl -fSL "${REPO_RAW}/NES/main.py" -o "${NESDIR}/main.py"
curl -fSL "${REPO_RAW}/NES/game_menu.py" -o "${NESDIR}/game_menu.py"
curl -fSL "${REPO_RAW}/NES/download.py" -o "${NESDIR}/download.py"
curl -fSL "${REPO_RAW}/NES/NES.sh" -o "${NESDIR}/NES.sh"

# 3. 字体
echo "下载字体..."
mkdir -p "${NESDIR}/fonts"
curl -fSL "${REPO_RAW}/NES/fonts/NotoSansSC-Regular.ttf" -o "${NESDIR}/fonts/NotoSansSC-Regular.ttf"

# 4. JSON 文件
echo "下载 JSON 游戏列表..."
mkdir -p "${NESDIR}/josn"
curl -fSL "${REPO_RAW}/NES/josn/Nintendo Entertainment System.json" -o "${NESDIR}/josn/Nintendo Entertainment System.json"

# 5. 设置权限
echo "设置可执行权限..."
chmod +x "${NESDIR}/NES.sh"

echo "安装完成，建议重启 EmulationStation 查看效果！"
