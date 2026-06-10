import os
import requests
from requests.exceptions import RequestException

# 分离连接超时和读取超时
TIMEOUT_CONFIG = (10, 60) 

# 优化: 使用全局 Session 复用连接，提升多次下载时的握手速度
download_session = requests.Session()

def download_file(name, url, save_dir="/userdata/roms/nes/", progress_dict=None):
    """
    深度优化版下载函数：
    - 支持断点续传 (HTTP Range)
    - 增加缓冲区大小至 128KB
    - 连接池复用
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # 统一后缀处理
    base_name = name if not name.lower().endswith('.zip') else name[:-4]
    local_path = os.path.join(save_dir, f"{base_name}.zip")
    temp_path = f"{local_path}.tmp"

    # 初始状态更新
    if progress_dict is not None:
        progress_dict["progress"] = 0
        progress_dict["status"] = "准备中..."

    # 浏览器伪装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # --- 优化点 1: 获取已下载的进度 (断点续传准备) ---
    initial_pos = 0
    if os.path.exists(temp_path):
        initial_pos = os.path.getsize(temp_path)
        # 如果有旧进度，在 Header 中加入 Range 参数
        headers["Range"] = f"bytes={initial_pos}-"

    try:
        # 使用 session 发起请求
        response = download_session.get(url, stream=True, timeout=TIMEOUT_CONFIG, headers=headers)
        
        # 处理断点续传的响应码 (206 为部分内容)
        if initial_pos > 0 and response.status_code == 416:
            # 416 表示请求范围不符合，可能是文件已下完或服务器不支持
            pass 
        else:
            response.raise_for_status()

        # 获取总长度 (注意：断点续传时 Content-Length 是剩余长度)
        content_range_len = response.headers.get("Content-Length")
        total_length = int(content_range_len) + initial_pos if content_range_len else initial_pos

        downloaded = initial_pos
        
        if progress_dict is not None:
            progress_dict["status"] = "下载中..."

        # --- 优化点 2: 使用 'ab' 模式追加写入，支持续传 ---
        mode = "ab" if initial_pos > 0 else "wb"
        with open(temp_path, mode) as f:
            # 优化点 3: 增加 chunk_size 至 128KB，大文件下载更流畅
            for chunk in response.iter_content(chunk_size=131072): 
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_dict is not None:
                        if total_length > 0:
                            progress_dict["progress"] = downloaded / total_length
                        else:
                            progress_dict["status"] = f"下载中 {downloaded // 1024}KB"

            f.flush()
            os.fsync(f.fileno())

        # 校验
        if total_length > 0 and downloaded < total_length:
            raise Exception("文件未接收完毕")

        # 完成重命名
        if os.path.exists(local_path):
            os.remove(local_path)
        os.rename(temp_path, local_path)

        if progress_dict is not None:
            progress_dict["progress"] = 1.0
            progress_dict["status"] = "已完成"
        
        return local_path

    except RequestException as e:
        # 注意：不要在失败时删除 temp_path，以便下次支持续传
        error_msg = f"连接失败: {e.response.status_code if e.response else '超时'}"
        if progress_dict is not None:
            progress_dict["status"] = "下载中断(待续)"
        print(f"[{name}] {error_msg}")
        return "failed"

    except Exception as e:
        if progress_dict is not None:
            progress_dict["status"] = "下载出错"
        print(f"[{name}] 未知错误: {str(e)}")
        # 未知严重错误建议清理
        if os.path.exists(temp_path): os.remove(temp_path)
        return "failed"