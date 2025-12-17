#!/bin/sh

# --- 1. 创建 EmulationStation 配置目录 ---
mkdir -p /userdata/system/configs/emulationstation/

# --- 2. 下载自定义菜单文件 ---
curl -L https://raw.githubusercontent.com/jamssismy/gamestore/main/es_systems_gamestore.cfg \
     -o /userdata/system/configs/emulationstation/es_systems_gamestore.cfg

# --- 3. 创建 gamestore ROM 文件夹 ---
mkdir -p /userdata/roms/gamestore/

echo "自定义菜单安装完成！"
echo "gamestore 文件夹已创建，可放置游戏资源。"
echo "请重启 EmulationStation 生效。"

