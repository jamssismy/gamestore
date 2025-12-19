import os
import requests
from requests.exceptions import RequestException

# 优化 1: 分离连接超时和读取超时
TIMEOUT_CONFIG = (10, 60) 

def download_file(name, url, save_dir="/userdata/roms/nes/", progress_dict=None):
    """
    优化版下载函数：
    - 增加浏览器伪装
    - 增强磁盘写入安全性
    - 错误处理更细致
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # 统一后缀处理，防止重复
    base_name = name if not name.lower().endswith('.zip') else name[:-4]
    local_path = os.path.join(save_dir, f"{base_name}.zip")
    temp_path = f"{local_path}.tmp"

    # 初始状态更新
    if progress_dict is not None:
        progress_dict["progress"] = 0
        progress_dict["status"] = "准备中..."

    # 清理旧的残留临时文件
    if os.path.exists(temp_path):
        try: os.remove(temp_path)
        except: pass

    # 优化 2: 增加 User-Agent，模拟正常浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_CONFIG, headers=headers)
        response.raise_for_status()

        total_length = response.headers.get("Content-Length")
        if total_length is not None:
            total_length = int(total_length)
        else:
            total_length = 0 # 某些服务器不返回长度

        downloaded = 0
        
        if progress_dict is not None:
            progress_dict["status"] = "下载中..."

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=16384): # 增加到 16KB 提高效率
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 优化 3: 进度更新逻辑增强
                    if progress_dict is not None:
                        if total_length > 0:
                            progress_dict["progress"] = downloaded / total_length
                            # 如果你想在状态栏看到百分比，可以取消下面这行的注释：
                            # progress_dict["status"] = f"下载中 {int(progress_dict['progress']*100)}%"
                        else:
                            # 无法获取总长度时显示已下大小
                            progress_dict["status"] = f"下载中 {downloaded // 1024}KB"

            # 优化 4: 强制将缓冲区写入磁盘
            f.flush()
            os.fsync(f.fileno())

        # 校验下载是否完整（如果服务器提供了长度）
        if total_length > 0 and downloaded < total_length:
            raise Exception("文件下载不完整")

        # 完成后重命名
        if os.path.exists(local_path):
            os.remove(local_path)
        os.rename(temp_path, local_path)

        if progress_dict is not None:
            progress_dict["progress"] = 1.0
            progress_dict["status"] = "已完成"
        
        return local_path

    except RequestException as e:
        error_msg = f"连接失败: {e.response.status_code if e.response else '超时'}"
        if progress_dict is not None:
            progress_dict["status"] = "下载失败"
        print(f"[{name}] {error_msg}")
        if os.path.exists(temp_path): os.remove(temp_path)
        return "failed"

    except Exception as e:
        if progress_dict is not None:
            progress_dict["status"] = "下载出错"
        print(f"[{name}] 未知错误: {str(e)}")
        if os.path.exists(temp_path): os.remove(temp_path)
        return "failed"