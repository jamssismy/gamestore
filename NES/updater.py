import os
import requests
import json
import zipfile
import shutil
from joy_config import log_message

# 配置信息
GITHUB_USER = "jamssismy"
GITHUB_REPO = "gamestore"
BASE_DIR = "/userdata/roms/gamestore/nes"
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

# GitHub Raw 链接（获取版本 JSON）
UPDATE_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/update.json"
# 备用加速链接 (如果原生链接不通，可以切换到这个)
UPDATE_JSON_URL_BACKUP = f"https://fastly.jsdelivr.net/gh/{GITHUB_USER}/{GITHUB_REPO}@main/update.json"

def get_local_version():
    """读取本地 version.txt"""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r") as f:
                return f.read().strip()
        except: pass
    return "v0.00"

def check_update():
    """
    通过 GitHub 检查是否有新版本
    返回: (是否有更新, 最新版本, 更新日志, 下载地址)
    """
    try:
        # 尝试从 GitHub 获取最新的 update.json
        response = requests.get(UPDATE_JSON_URL, timeout=10)
        if response.status_code != 200:
            # 失败则尝试备份链接
            response = requests.get(UPDATE_JSON_URL_BACKUP, timeout=10)
            
        if response.status_code == 200:
            data = response.json()
            remote_version = data.get("latest_version", "v1.00")
            
            if remote_version != get_local_version():
                return True, remote_version, data.get("changelog", ""), data.get("download_url", "")
    except Exception as e:
        log_message(f"检查更新出错: {e}")
        
    return False, None, None, None

def execute_update(zip_url, progress_callback=None):
    """
    下载并安装更新
    """
    tmp_zip = os.path.join(BASE_DIR, "update_temp.zip")
    extract_path = os.path.join(BASE_DIR, "update_extracted")
    
    try:
        # 1. 下载 ZIP (GitHub 的 ZIP 归档链接)
        response = requests.get(zip_url, stream=True, timeout=20)
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(tmp_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        # 计算百分比传回 UI
                        progress_callback(int(downloaded * 100 / total_size))

        # 2. 解压
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # 3. 覆盖文件 (简单方案：直接覆盖当前目录下的 py 文件)
        # 注意：GitHub ZIP 里面通常会有一层目录名为 "gamestore-main"
        inner_dir = os.path.join(extract_path, f"{GITHUB_REPO}-main")
        if not os.path.exists(inner_dir):
            # 如果不是 main 分支，可能是其他名字，遍历一下
            dirs = [d for d in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, d))]
            if dirs: inner_dir = os.path.join(extract_path, dirs[0])

        for item in os.listdir(inner_dir):
            s = os.path.join(inner_dir, item)
            d = os.path.join(BASE_DIR, item)
            if os.path.isdir(s):
                if os.path.exists(d): shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

        # 4. 清理临时文件并保存新版本号
        if os.path.exists(tmp_zip): os.remove(tmp_zip)
        if os.path.exists(extract_path): shutil.rmtree(extract_path)
        
        return True
    except Exception as e:
        log_message(f"执行更新失败: {e}")
        return False