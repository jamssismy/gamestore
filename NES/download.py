import os
import requests
from requests.exceptions import RequestException

TIMEOUT_SECONDS = 30

def download_file(name, url, save_dir="/userdata/roms/nes/", progress_dict=None):
    """
    线程安全的下载函数。
    progress_dict 是共享字典，用于记录下载进度和状态：
        progress_dict["progress"] = 0~1
        progress_dict["status"] = "下载中...", "已完成", "下载失败"
    """
    os.makedirs(save_dir, exist_ok=True)
    local_path = os.path.join(save_dir, name + ".zip")
    temp_path = local_path + ".tmp"

    if progress_dict is not None:
        progress_dict["progress"] = 0
        progress_dict["status"] = "下载中..."

    # 删除残留的临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        total_length = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_length > 0 and progress_dict is not None:
                        progress_dict["progress"] = downloaded / total_length

        os.rename(temp_path, local_path)
        if progress_dict is not None:
            progress_dict["status"] = "已完成"

        return local_path

    except RequestException as e:
        print(f"下载请求错误: {e}")
        if progress_dict is not None:
            progress_dict["status"] = "下载失败"
        return "failed"

    except Exception as e:
        print(f"未知下载错误: {e}")
        if progress_dict is not None:
            progress_dict["status"] = "下载失败"
        return "failed"
