import os
import json
import pygame
import threading
import queue
from joy_config import get_mapping_value, log_message, load_active_mappings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

download_queue = queue.Queue()
_worker_started = False

def download_worker():
    while True:
        item = download_queue.get()
        if item is None: break
        try:
            from download import download_file
            res = download_file(item["name"], item["url"], item["save_dir"], progress_dict=item)
            if res == "failed":
                log_message(f"下载失败: 游戏 {item['name']} URL: {item['url']}")
        except Exception as e:
            item["status"] = "下载出错"
            log_message(f"下载模块调用异常: {str(e)}")
        download_queue.task_done()

def start_download_threads():
    global _worker_started
    if not _worker_started:
        for _ in range(5): 
            t = threading.Thread(target=download_worker, daemon=True)
            t.start()
        _worker_started = True

def is_confirm_act(event):
    if event.type == pygame.KEYDOWN:
        return event.key in [pygame.K_RETURN, pygame.K_SPACE]
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [0, 2]
    return False

def is_back_act(event):
    if event.type == pygame.KEYDOWN:
        return event.key == pygame.K_ESCAPE
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [1, 3, 15]
    return False

def game_menu(screen, font, active_mappings, json_file, save_dir):
    start_download_threads()
    sw, sh = screen.get_size()
    
    # 手柄提示变量
    notif_text = ""
    notif_timer = 0
    
    if not os.path.exists(save_dir):
        try: os.makedirs(save_dir)
        except Exception as e: log_message(f"错误: 无法创建目录 {save_dir} - {str(e)}")

    menu_items = []
    try:
        if os.path.exists(json_file):
            with open(json_file, "r", encoding="utf-8") as f:
                raw_games = json.load(f)
                
                # --- 就在这个循环里进行修改 ---
                for g in raw_games:
                    filename = g[0]
                    
                    # 1. 提取原始名称
                    display_name = filename.replace(".zip", "")
                    
                    # 2. 这里的片段执行缩短逻辑 (新增部分)
                    if len(display_name) > 60: 
                        display_name = display_name[:58] + "..."
                    
                    menu_items.append({
                        "name": display_name,  # 修改后的名字存入这里用于显示
                        "filename": filename,
                        "url": g[1],
                        "save_dir": save_dir,
                        "status": "已完成" if os.path.exists(os.path.join(save_dir, filename)) else "未下载",
                        "progress": 0
                    })
        else:
            log_message(f"错误: 找不到数据文件 {json_file}")
    except Exception as e:
        log_message(f"错误: 解析 JSON 失败 - {str(e)}")

    if not menu_items:
        menu_items = [{"name": "无游戏数据", "status": "", "url": None}]

    FONT_SIZE, LINE_HEIGHT = 36, 56
    LEFT_MARGIN, RIGHT_MARGIN = 120, 120
    TOP_MARGIN, BOTTOM_MARGIN = 80, 100
    HIGHLIGHT_PAD_Y, HIGHLIGHT_PAD_X = 8, 20
    BORDER_RADIUS = 20

    available_h = sh - TOP_MARGIN - BOTTOM_MARGIN
    ITEMS_PER_PAGE = max(1, available_h // LINE_HEIGHT)
    total_pages = max(1, (len(menu_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    cur_page, sel_idx = 0, 0
    font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
    g_font = pygame.font.Font(font_path, FONT_SIZE) if os.path.exists(font_path) else pygame.font.SysFont("simhei", FONT_SIZE)
    h_font = pygame.font.Font(font_path, 24) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 24)
    clock = pygame.time.Clock()

    while True:
        screen.fill((20, 20, 30))
        start_i = cur_page * ITEMS_PER_PAGE
        page_data = menu_items[start_i : start_i + ITEMS_PER_PAGE]

        for i, item in enumerate(page_data):
            row_top = TOP_MARGIN + i * LINE_HEIGHT
            text_y = row_top + (LINE_HEIGHT - g_font.get_height()) // 2
            
            if i == sel_idx:
                rect_h = g_font.get_height() + 2 * HIGHLIGHT_PAD_Y
                rect_w = sw - LEFT_MARGIN - RIGHT_MARGIN + 2 * HIGHLIGHT_PAD_X
                rect_x, rect_y = LEFT_MARGIN - HIGHLIGHT_PAD_X, text_y - HIGHLIGHT_PAD_Y
                shadow = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
                pygame.draw.rect(shadow, (0, 0, 0, 100), shadow.get_rect(), border_radius=BORDER_RADIUS)
                screen.blit(shadow, (rect_x + 3, rect_y + 3))
                grad = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
                for gy in range(rect_h):
                    alpha = int(180 - (gy/rect_h)*80)
                    pygame.draw.rect(grad, (40, 70, 120, alpha), (0, gy, rect_w, 1), border_radius=BORDER_RADIUS)
                screen.blit(grad, (rect_x, rect_y))

            n_color = (255, 255, 255) if i == sel_idx else (200, 200, 200)
            n_surf = g_font.render(item["name"], True, n_color)
            screen.blit(n_surf, (LEFT_MARGIN, text_y))
            
            display_status = item["status"]
            if display_status == "下载中..." and item["progress"] > 0:
                display_status = f"下载中 {int(item['progress'] * 100)}%"
            s_color = (0, 255, 120) if item["status"] == "已完成" else \
                      (255, 255, 80) if "下载中" in item["status"] else \
                      (255, 100, 100) if "失败" in item["status"] else (150, 150, 150)
            s_surf = g_font.render(display_status, True, s_color)
            screen.blit(s_surf, (sw - RIGHT_MARGIN - s_surf.get_width(), text_y))

        footer_str = f"Page {cur_page+1}/{total_pages}  |  方向键选择  A 下载  B 返回"
        footer = h_font.render(footer_str, True, (150, 150, 170))
        screen.blit(footer, (sw//2 - footer.get_width()//2, sh - 50))

        # --- 子页面手柄提示框渲染 ---
        if notif_text and pygame.time.get_ticks() - notif_timer < 3000:
            msg_surf = h_font.render(notif_text, True, (255, 255, 255))
            m_w, m_h = msg_surf.get_size()
            m_rect = pygame.Rect(sw//2 - m_w//2 - 20, 20, m_w + 40, 50)
            n_bg = pygame.Surface((m_rect.width, m_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(n_bg, (50, 100, 200, 200), (0, 0, m_rect.width, m_rect.height), border_radius=10)
            screen.blit(n_bg, m_rect.topleft)
            screen.blit(msg_surf, (m_rect.centerx - m_w//2, m_rect.centery - m_h//2))

        pygame.display.flip()

        for event in pygame.event.get():
            # 新增手柄热插拔监听
            if event.type == pygame.JOYDEVICEADDED:
                try:
                    joy = pygame.joystick.Joystick(event.device_index); joy.init()
                    notif_text = f"已连接: {joy.get_name()}"; notif_timer = pygame.time.get_ticks()
                    active_mappings = load_active_mappings()
                except: pass
            elif event.type == pygame.JOYDEVICEREMOVED:
                notif_text = "手柄已断开连接"; notif_timer = pygame.time.get_ticks()
                active_mappings = load_active_mappings()

            if event.type == pygame.QUIT: return "exit"
            if is_confirm_act(event):
                idx = cur_page * ITEMS_PER_PAGE + sel_idx
                if idx < len(menu_items) and menu_items[idx]["status"] == "未下载":
                    download_queue.put(menu_items[idx])
            elif is_back_act(event):
                pygame.event.clear()
                return "back"
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w] and sel_idx > 0: sel_idx -= 1
                elif event.key in [pygame.K_DOWN, pygame.K_s] and sel_idx < len(page_data)-1: sel_idx += 1
                elif event.key in [pygame.K_LEFT, pygame.K_a] and cur_page > 0: 
                    cur_page -= 1; sel_idx = 0
                elif event.key in [pygame.S_RIGHT, pygame.K_d] and cur_page < total_pages-1: 
                    cur_page += 1; sel_idx = 0
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1 and sel_idx > 0: sel_idx -= 1
                elif event.value[1] == -1 and sel_idx < len(page_data)-1: sel_idx += 1
                elif event.value[0] == -1 and cur_page > 0: cur_page -= 1; sel_idx = 0
                elif event.value[0] == 1 and cur_page < total_pages-1: cur_page += 1; sel_idx = 0

        clock.tick(60)