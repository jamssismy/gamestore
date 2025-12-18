#!/bin/sh

# --- 定义路径变量 ---
ES_CONFIG_DIR="/userdata/system/configs/emulationstation"
CFG_FILE="$ES_CONFIG_DIR/es_systems_gamestore.cfg"
BASE_ROM_DIR="/userdata/roms/gamestore"
REPO_URL="https://raw.githubusercontent.com/jamssismy/gamestore/main/es_systems_gamestore.cfg"

echo "------------------------------------------"
echo "正在开始 GameStore 最终版安装程序..."
echo "------------------------------------------"

# --- 1. 彻底清理（忽略大小写删除旧目录） ---
if [ -d "$BASE_ROM_DIR" ]; then
    echo "正在扫描并清理 $BASE_ROM_DIR 下的旧资源..."
    # 查找并删除所有名为 nes (不区分大小写) 的目录
    find "$BASE_ROM_DIR" -maxdepth 1 -type d -iname "nes" -exec rm -rf {} +
    echo "✅ 旧的 nes/NES/Nes 目录已清理。"
else
    mkdir -p "$BASE_ROM_DIR"
fi

# --- 2. 重新初始化目录 ---
TARGET_NES_DIR="$BASE_ROM_DIR/nes"
mkdir -p "$ES_CONFIG_DIR"
mkdir -p "$TARGET_NES_DIR"
echo "✅ 目录结构已重置为标准路径: $TARGET_NES_DIR"

# --- 3. 下载并自动转码配置文件 ---
echo "正在同步配置文件并执行 Unix 转码..."
if curl -L -f "$REPO_URL" -o "$CFG_FILE"; then
    # --- 关键步骤：强制将 CRLF (Windows) 转换为 LF (Unix) ---
    sed -i 's/\r$//' "$CFG_FILE"
    
    chmod 644 "$CFG_FILE"
    echo "✅ 配置文件下载成功，并已强制转换为 Unix 格式。"
else
    echo "❌ 错误: 配置文件下载失败，请检查网络。"
    exit 1
fi

# --- 4. 完成安装 ---
echo "------------------------------------------"
echo "安装成功！"
echo "1. 请将 NES 游戏放入: $TARGET_NES_DIR"
echo "2. 在 ES 菜单中选择 'UPDATE GAMES LISTS' 即可看到新菜单。"
echo "------------------------------------------"