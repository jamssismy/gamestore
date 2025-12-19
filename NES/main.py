import pygame
import os
import shutil
from joy_config import load_active_mappings, get_mapping_value, log_message

# 尝试导入商城页面
try:
    from game_menu import game_menu
except ImportError:
    # 仅在找不到文件这一严重错误时记录日志
    log_message("致命错误: 无法找到 game_menu.py 模块")
    def game_menu(screen, font, mappings): return "back"

pygame.init()
pygame.joystick.init()

# 初始化所有手柄
for i in range(pygame.joystick.get_count()):
    try:
        j = pygame.joystick.Joystick(i)
        j.init()
    except Exception as e:
        log_message(f"手柄初始化失败 [Index {i}]: {str(e)}")

active_mappings = load_active_mappings()

# 设置全屏
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

# 字体加载
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
if os.path.exists(font_path):
    font = pygame.font.Font(font_path, 48)
else:
    font = pygame.font.SysFont("simhei", 48)

# --- 按键判定逻辑 ---
def is_confirm_key(event, mappings):
    if event.type == pygame.KEYDOWN:
        return event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER]
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [0, 1, 2]
    return False

def is_back_key(event, mappings):
    if event.type == pygame.KEYDOWN:
        return event.key == pygame.K_ESCAPE
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [3, 4, 15]
    return False

# --- 清理缓存 (增加错误处理) ---
def clear_cache():
    cache_dir = "/userdata/system/.cache"
    if os.path.exists(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            for f in files:
                try: os.remove(os.path.join(root, f))
                except Exception as e: 
                    log_message(f"清理文件失败: {f} - {str(e)}")
            for d in dirs:
                try: shutil.rmtree(os.path.join(root, d))
                except Exception as e:
                    log_message(f"清理目录失败: {d} - {str(e)}")

# --- UI 参数 ---
menu_items = ["游戏商城", "系统设置", "清理缓存", "退出程序"]
selected_index = 0
clock = pygame.time.Clock()
running = True

LINE_HEIGHT = 100
HIGHLIGHT_HEIGHT = 80
HIGHLIGHT_PADDING = 10
FINAL_HIGHLIGHT_HEIGHT = HIGHLIGHT_HEIGHT + HIGHLIGHT_PADDING

# === 主循环 ===
while running:
    screen.fill((20, 20, 30))

    # --- 渲染菜单项 ---
    for i, item in enumerate(menu_items):
        y_pos = 250 + i * LINE_HEIGHT
        
        if i == selected_index:
            rect_x = SCREEN_WIDTH // 2 - 200
            rect_w = 400
            rect_y = y_pos - (FINAL_HIGHLIGHT_HEIGHT - font.get_height()) // 2
            pygame.draw.rect(screen, (40, 70, 120), (rect_x, rect_y, rect_w, FINAL_HIGHLIGHT_HEIGHT), border_radius=15)

        color = (255, 255, 255) if i == selected_index else (200, 200, 200)
        text_surf = font.render(item, True, color)
        screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y_pos))

    pygame.display.flip()

    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 1. 确认键动作
        if is_confirm_key(event, active_mappings):
            if menu_items[selected_index] == "游戏商城":
                pygame.event.clear()
                # 调用商城，移除了此处的 log_message
                res = game_menu(screen, font, active_mappings)
                pygame.event.clear()
                if res == "exit": running = False
                continue 
            elif menu_items[selected_index] == "清理缓存":
                clear_cache()
            elif menu_items[selected_index] == "退出程序":
                running = False
            continue

        # 2. 返回键动作
        if is_back_key(event, active_mappings):
            running = False

        # 3. 导航逻辑
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                selected_index = (selected_index - 1) % len(menu_items)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                selected_index = (selected_index + 1) % len(menu_items)
        
        elif event.type == pygame.JOYHATMOTION:
            if event.value[1] == 1:
                selected_index = (selected_index - 1) % len(menu_items)
            elif event.value[1] == -1:
                selected_index = (selected_index + 1) % len(menu_items)

    clock.tick(60)

pygame.quit()