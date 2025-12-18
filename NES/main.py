import pygame
import os
import shutil

# === 尝试导入商城页面 ===
try:
    from game_menu import game_menu
except ImportError:
    def game_menu(screen, font):
        print("错误: 找不到 game_menu.py 文件")
        return "back"

# === 基础初始化 ===
pygame.init()
pygame.joystick.init()
for j in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]:
    j.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
font = pygame.font.Font(font_path, 48) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 48)

# --- 按键判定函数 ---
def is_confirm_key(event):
    if event.type == pygame.KEYDOWN:
        return event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER]
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [1, 2]
    return False

def is_back_key(event):
    if event.type == pygame.KEYDOWN:
        return event.key == pygame.K_ESCAPE
    if event.type == pygame.JOYBUTTONDOWN:
        return event.button in [0, 3]
    return False

# --- 清理缓存功能 ---
def clear_cache():
    cache_dir = "/userdata/system/.cache"  # 可根据实际情况修改
    if os.path.exists(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            for f in files:
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print("删除文件失败:", e)
            for d in dirs:
                try:
                    shutil.rmtree(os.path.join(root, d))
                except Exception as e:
                    print("删除目录失败:", e)
        print("缓存已清理完成。")
    else:
        print("缓存目录不存在:", cache_dir)

# --- 菜单状态 ---
menu_items = ["游戏商城", "系统设置", "清理缓存", "退出程序"]
selected_index = 0
clock = pygame.time.Clock()
running = True

# UI 参数
LINE_HEIGHT = 100
HIGHLIGHT_HEIGHT = 80
HIGHLIGHT_PADDING = 10
FINAL_HIGHLIGHT_HEIGHT = HIGHLIGHT_HEIGHT + HIGHLIGHT_PADDING

while running:
    screen.fill((20, 20, 30))

    for i, item in enumerate(menu_items):
        y_pos = 250 + i * LINE_HEIGHT

        # 高亮背景矩形
        if i == selected_index:
            rect_x = SCREEN_WIDTH // 2 - 200
            rect_w = 400
            rect_y = y_pos - (FINAL_HIGHLIGHT_HEIGHT - font.get_height()) // 2
            pygame.draw.rect(screen, (40, 70, 120), (rect_x, rect_y, rect_w, FINAL_HIGHLIGHT_HEIGHT), border_radius=15)

        # 菜单文字
        color = (255, 255, 255) if i == selected_index else (200, 200, 200)
        text_surf = font.render(item, True, color)
        screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y_pos))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 确认键
        if is_confirm_key(event):
            if menu_items[selected_index] == "游戏商城":
                pygame.event.clear()
                res = game_menu(screen, font)
                if res == "exit":
                    running = False
                pygame.event.clear()
            elif menu_items[selected_index] == "清理缓存":
                clear_cache()
            elif menu_items[selected_index] == "退出程序":
                running = False
            continue

        # 返回键
        if is_back_key(event):
            running = False

        # 导航逻辑
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
