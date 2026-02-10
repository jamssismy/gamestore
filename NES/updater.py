import os
import requests
import zipfile
import shutil
import time  # 新增：用于生成随机时间戳
from joy_config import log_message

# ======================
# 核心路径
# ======================
BASE_DIR = "/userdata/roms/gamestore/nes"
TEMP_DIR = os.path.join(BASE_DIR, "__pycache__")
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

# 【新增】RetroArch 配置目录（仅手动清理缓存使用）
RETROARCH_CONFIG_DIR = "/userdata/system/configs/retroarch"

GITHUB_USER = "jamssismy"
GITHUB_REPO = "gamestore"
# 增加时间戳防止 CDN 缓存旧的 json 文件
UPDATE_JSON_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/update.json"


def get_local_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return "v0.00"


def check_update():
    try:
        # 在 URL 后加随机参数强制刷新缓存
        nocache_url = f"{UPDATE_JSON_BASE}?t={int(time.time())}"
        response = requests.get(nocache_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            remote_ver = data.get("latest_version", "v1.00")
            local_ver = get_local_version()

            # 只要字符串不一致就触发更新
            if remote_ver != local_ver:
                return True, remote_ver, data.get("changelog", ""), data.get("download_url", "")
    except Exception as e:
        log_message(f"检查更新失败: {e}")
    return False, None, None, None


def execute_update(zip_url, remote_version):
    # 强制清理并准备中转站
    if os.path.exists(TEMP_DIR):
        os.system(f"rm -rf {TEMP_DIR}")
    os.makedirs(TEMP_DIR, exist_ok=True)

    tmp_zip = os.path.join(TEMP_DIR, "update.zip")
    extract_path = os.path.join(TEMP_DIR, "unpacked")

    try:
        # 1. 下载 (增加随机参数防止下载旧的 ZIP)
        r = requests.get(f"{zip_url}?t={int(time.time())}", timeout=30)
        with open(tmp_zip, 'wb') as f:
            f.write(r.content)

        # 2. 解压
        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # 3. 定位 NES 文件夹
        source_nes_dir = None
        for root, dirs, files in os.walk(extract_path):
            if os.path.basename(root).upper() == "NES":
                source_nes_dir = root
                break

        if not source_nes_dir:
            return False

        # 4. 覆盖安装
        for item in os.listdir(source_nes_dir):
            if item == "version.txt":
                continue
            s, d = os.path.join(source_nes_dir, item), os.path.join(BASE_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # 5. 写入版本号
        with open(VERSION_FILE, "w") as f:
            f.write(remote_version)

        # 6. 强制销毁中转站
        os.system(f"rm -rf {TEMP_DIR}")
        return True

    except:
        os.system(f"rm -rf {TEMP_DIR}")
        return False


# ======================
# 【新增】手动清理缓存函数
# ======================
def clear_pycache():
    """
    手动清理缓存（由系统菜单触发）：
    1. 删除 gamestore 更新缓存 (__pycache__)
    2. 删除 RetroArch 配置目录
    """
    success = True

    # 1. 清理 gamestore 更新缓存
    try:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            log_message("手动清理缓存：已删除 __pycache__")
    except Exception as e:
        log_message(f"手动清理缓存失败 (__pycache__): {e}")
        success = False

    # 2. 清理 RetroArch 配置目录
    try:
        if os.path.exists(RETROARCH_CONFIG_DIR):
            shutil.rmtree(RETROARCH_CONFIG_DIR)
            log_message("手动清理缓存：已删除 RetroArch 配置目录")
    except Exception as e:
        log_message(f"手动清理 RetroArch 配置失败: {e}")
        success = False

    return success
