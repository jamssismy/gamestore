#!/bin/sh

# --- 路径配置 ---
ES_CONFIG_DIR="/userdata/system/configs/emulationstation"
CFG_FILE="$ES_CONFIG_DIR/es_systems_gamestore.cfg"
BASE_ROM_DIR="/userdata/roms/gamestore"
# 配置文件源码地址
REPO_CFG_URL="https://raw.githubusercontent.com/jamssismy/gamestore/main/es_systems_gamestore.cfg"
# 项目完整压缩包地址 (用于下载整个文件夹)
REPO_ZIP_URL="https://github.com/jamssismy/gamestore/archive/refs/heads/main.zip"

echo "------------------------------------------"
echo "正在开始 GameStore 自动安装程序..."
echo "------------------------------------------"

# --- 1. 彻底重建配置文件 ---
# 解决问题一：直接物理删除旧文件，确保绝无二次写入或冲突
echo "正在配置系统菜单..."
[ -f "$CFG_FILE" ] && rm -f "$CFG_FILE"
mkdir -p "$ES_CONFIG_DIR"

# --- 2. 清理旧的 NES 目录（不区分大小写） ---
# 解决问题二：查找并删除名为 nes/NES/Nes 的文件夹
if [ -d "$BASE_ROM_DIR" ]; then
    echo "正在扫描旧资源..."
    # 强制删除任何拼写形式的 nes 目录
    find "$BASE_ROM_DIR" -maxdepth 1 -type d -iname "nes" -exec rm -rf {} +
else
    mkdir -p "$BASE_ROM_DIR"
fi

# --- 3. 下载并解压项目文件 ---
echo "正在从远程仓库同步 NES 资源包..."
TEMP_ZIP="/tmp/gamestore_temp.zip"
TEMP_DIR="/tmp/gamestore_extract"

# 清理可能的残余临时目录
rm -rf "$TEMP_DIR" && mkdir -p "$TEMP_DIR"

if curl -L -f "$REPO_ZIP_URL" -o "$TEMP_ZIP"; then
    unzip -q -o "$TEMP_ZIP" -d "$TEMP_DIR"
    
    # 注意：GitHub ZIP 解压后文件夹名通常是 "仓库名-main"
    # 我们动态寻找解压出来的 nes 文件夹
    SRC_NES_PATH=$(find "$TEMP_DIR" -type d -iname "nes" | head -n 1)
    
    if [ -d "$SRC_NES_PATH" ]; then
        # 将整个 nes 文件夹及其子目录内容移动到目标位置
        # 这里使用 cp -r 确保结构一致
        cp -r "$SRC_NES_PATH" "$BASE_ROM_DIR/nes"
        echo "✅ NES 资源同步成功 (存放至: $BASE_ROM_DIR/nes)"
    else
        echo "❌ 错误: 压缩包内未找到 nes 文件夹"
        exit 1
    fi
    # 清理临时垃圾
    rm -rf "$TEMP_ZIP" "$TEMP_DIR"
else
    echo "❌ 错误: 无法连接到 GitHub 下载资源包"
    exit 1
fi

# --- 4. 下载并转码配置文件 ---
if curl -L -f "$REPO_CFG_URL" -o "$CFG_FILE"; then
    # 转换为 Unix 格式，防止 Windows 换行符导致 ES 读取失败
    sed -i 's/\r$//' "$CFG_FILE"
    chmod 644 "$CFG_FILE"
    echo "✅ 菜单配置文件更新完成"
else
    echo "❌ 错误: 菜单配置同步失败"
    exit 1
fi

# --- 5. 提示结束 ---
echo "------------------------------------------"
echo "安装圆满完成！"
echo "提示：请在系统设置中执行 '更新游戏列表' (UPDATE GAMES LISTS)"
echo "------------------------------------------"
