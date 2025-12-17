#!/bin/sh
# 创建目录
mkdir -p /userdata/system/configs/emulationstation/

# 下载自定义菜单文件
curl -L https://raw.githubusercontent.com/jamssismy/gamestore/main/es_systems_gamestore.cfg -o /userdata/system/configs/emulationstation/es_systems_gamestore.cfg

echo "自定义菜单安装完成！请重启 EmulationStation 生效。"

