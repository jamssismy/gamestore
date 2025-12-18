import os
import json
import pygame
import threading
import traceback
import queue
from download import download_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "josn", "Nintendo Entertainment System.json")
SAVE_DIR = "/userdata/roms/nes/"

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 加载游戏数据
try:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        raw_games = json.load(f)
except Exception:
    raw_games = []

menu_items = []
for g in raw_games:
    filename = g[0]
    menu_items.append({
        "name": filename.replace(".zip", ""),
        "filename": filename,
        "url": g[1],
        "status": "已完成" if os.path.exists(os.path.join(SAVE_DIR, filename)) else "未下载"
    })

download_queue = queue.Queue()
_worker_init = False

def download_task():
    while True:
        item = download_queue.get()
        if item is None:
            break
        try:
            item["status"] = "下载中..."
            print("开始下载:", item["name"], item["url"])
            download_file(item["name"], item["url"], SAVE_DIR, progress_dict=item)
            item["status"] = "已完成" if os.path.exists(os.path.join(SAVE_DIR, item["filename"])) else "下载失败"
        except Exception as e:
            print("下载错误:", e)
            item["status"] = "下载错误"
        download_queue.task_done()

def start_worker():
    global _worker_init
    if not _worker_init:
        for _ in range(4):
            threading.Thread(target=download_task, daemon=True).start()
        _worker_init = True

def is_confirm_act(event):
    if event.type == pygame.KEYDOWN:
        return event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER]
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [1, 2]
    return False

def is_back_act(event):
    if event.type == pygame.KEYDOWN:
        return event.key == pygame.K_ESCAPE
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [0, 3]
    return False

def game_menu(screen, font):
    pygame.event.clear()
    start_worker()
    
    screen_width, screen_height = screen.get_size()

    FONT_SIZE = 36
    LINE_HEIGHT = 56
    LEFT_MARGIN, RIGHT_MARGIN = 120, 120
    TOP_MARGIN, BOTTOM_MARGIN = 80, 100
    HIGHLIGHT_PAD_Y = 8
    HIGHLIGHT_PAD_X = 20
    BORDER_RADIUS = 20   # 固定圆角半径

    available_height = screen_height - TOP_MARGIN - BOTTOM_MARGIN
    ITEMS_PER_PAGE = max(1, available_height // LINE_HEIGHT)
    total_pages = max(1, (len(menu_items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    current_page = 0
    selected_index = 0

    font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
    game_font = pygame.font.Font(font_path, FONT_SIZE) if os.path.isfile(font_path) else pygame.font.SysFont("simhei", FONT_SIZE)
    hint_font = pygame.font.Font(font_path, 28) if os.path.isfile(font_path) else pygame.font.SysFont("simhei", 28)

    font_height = game_font.get_height()
    clock = pygame.time.Clock()

    while True:
        try:
            screen.fill((20, 20, 30))
            start_idx = current_page * ITEMS_PER_PAGE
            page_data = menu_items[start_idx:start_idx + ITEMS_PER_PAGE]

            for i, item in enumerate(page_data):
                row_top = TOP_MARGIN + i * LINE_HEIGHT
                text_y = row_top + (LINE_HEIGHT - font_height) // 2

                name_color = (255, 255, 255) if i == selected_index else (220, 220, 220)
                name_surf = game_font.render(item["name"], True, name_color)

                status_color = (0, 255, 120) if item["status"] == "已完成" else \
                               (255, 255, 80) if "下载中" in item["status"] else \
                               (255, 100, 100) if "失败" in item["status"] or "错误" in item["status"] else \
                               (180, 180, 180)
                status_surf = game_font.render(item["status"], True, status_color)

                if i == selected_index:
                    rect_h = font_height + 2 * HIGHLIGHT_PAD_Y
                    rect_y = text_y - HIGHLIGHT_PAD_Y
                    rect_x = LEFT_MARGIN - HIGHLIGHT_PAD_X
                    usable_w = screen_width - LEFT_MARGIN - RIGHT_MARGIN
                    rect_w = usable_w + 2 * HIGHLIGHT_PAD_X

                    # 阴影层（圆角）
                    shadow_rect = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
                    pygame.draw.rect(shadow_rect, (0, 0, 0, 100), shadow_rect.get_rect(), border_radius=BORDER_RADIUS)
                    screen.blit(shadow_rect, (rect_x + 3, rect_y + 3))

                    # 渐变层（圆角）
                    gradient_rect = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
                    for y in range(rect_h):
                        alpha = int(180 - (y / rect_h) * 80)
                        pygame.draw.rect(gradient_rect, (40, 70, 120, alpha), (0, y, rect_w, 1), border_radius=BORDER_RADIUS)
                    screen.blit(gradient_rect, (rect_x, rect_y))

                screen.blit(name_surf, (LEFT_MARGIN, text_y))
                screen.blit(status_surf, (screen_width - RIGHT_MARGIN - status_surf.get_width(), text_y))

            title = hint_font.render(f"NES 游戏商城  -  第 {current_page + 1}/{total_pages} 页", True, (160, 200, 255))
            screen.blit(title, (screen_width // 2 - title.get_width() // 2, 30))
            hint = hint_font.render("↑↓ 选择   A 下载   B 返回   ←→ 翻页", True, (200, 200, 220))
            screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height - 60))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"

                if is_confirm_act(event):
                    idx = current_page * ITEMS_PER_PAGE + selected_index
                    if idx < len(menu_items) and menu_items[idx]["status"] == "未下载":
                        download_queue.put(menu_items[idx])
                    continue

                if is_back_act(event):
                    return "back"

                elif event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_UP, pygame.K_w] and selected_index > 0:
                        selected_index -= 1
                    elif event.key in [pygame.K_DOWN, pygame.K_s] and selected_index < len(page_data) - 1:
                        selected_index += 1
                    elif event.key in [pygame.K_LEFT, pygame.K_a] and current_page > 0:
                        current_page -= 1
                        selected_index = 0
                    elif event.key in [pygame.K_RIGHT, pygame.K_d] and current_page < total_pages - 1:
                        current_page += 1
                        selected_index = 0
                elif event.type == pygame.JOYHATMOTION:
                    hx, hy = event.value
                    if hy == 1 and selected_index > 0:
                        selected_index -= 1
                    elif hy == -1 and selected_index < len(page_data) - 1:
                        selected_index += 1
                    elif hx == -1 and current_page > 0:
                        current_page -= 1
                        selected_index = 0
                    elif hx == 1 and current_page < total_pages - 1:
                        current_page += 1
                        selected_index = 0

        except Exception:
            print(traceback.format_exc())
            return "back"

        clock.tick(60)
