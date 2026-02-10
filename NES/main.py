import pygame
import os
import shutil
import updater
from joy_config import load_active_mappings, log_message

# 确保 game_menu 存在，否则提供空函数防止崩溃
try:
    from game_menu import game_menu
except ImportError:
    log_message("致命错误: 无法找到 game_menu.py 模块")
    def game_menu(screen, font, mappings, json_path, save_dir): return "back"

pygame.init()
pygame.joystick.init()

# 启动时初始化所有已连接的手柄
for i in range(pygame.joystick.get_count()):
    try:
        j = pygame.joystick.Joystick(i); j.init()
    except: pass

active_mappings = load_active_mappings()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SW, SH = screen.get_size()

# --- 路径与资源定义 ---
BASE_DIR = "/userdata/roms/gamestore/nes" 
PYCACHE_DIR = os.path.join(BASE_DIR, "__pycache__")
JSON_BASE_DIR = os.path.join(BASE_DIR, "json") 
IMG_BASE_DIR = os.path.join(BASE_DIR, "images") 

# 字体加载逻辑
font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
title_font = pygame.font.Font(font_path, 64) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 64)
hint_font = pygame.font.Font(font_path, 30) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 30)
dialog_font = pygame.font.Font(font_path, 36) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 36)
log_font = pygame.font.Font(font_path, 24) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 24)

# --- UI 布局参数 ---
SLOT_W, SLOT_H = 340, 240  
COLS, ROWS = 3, 2
ITEMS_PER_PAGE = COLS * ROWS
COL_SPACING = SW // (COLS + 1)
ROW_START_Y = 340
V_SPACING = 360

def create_slot_surface(img_path, slot_w, slot_h, scale_inner=0.85):
    slot_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
    pygame.draw.rect(slot_surf, (40, 45, 60), (0, 0, slot_w, slot_h), border_radius=15)
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img_w, img_h = img.get_size()
            ratio = min((slot_w * scale_inner) / img_w, (slot_h * scale_inner) / img_h)
            new_w, new_h = int(img_w * ratio), int(img_h * ratio)
            scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
            slot_surf.blit(scaled_img, ((slot_w - new_w) // 2, (slot_h - new_h) // 2))
            return slot_surf
        except: pass
    return slot_surf

# --- 新增：文本换行工具函数 (修复崩溃的关键) ---
def wrap_text(text, font, max_width):
    if not text: return ["无更新说明"]
    lines = []
    current_line = ""
    for char in str(text):
        test_line = current_line + char
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    return lines

# --- 完整的游戏分类配置 (绝对不删减) ---
GAME_CONFIGS = [
    {"name": "任天堂游戏(8位)", "image": "Nintendo Entertainment System.png", "json": "Nintendo Entertainment System.json", "path": "/userdata/roms/nes/"},
    {"name": "Sega Master(8位)", "image": "Sega Mark III.png", "json": "Sega Mark III.json", "path": "/userdata/roms/mastersystem/"},
    {"name": "NEC SuperGrafx(8位)", "image": "NEC PC Engine SuperGrafx.png", "json": "NEC PC Engine SuperGrafx.json", "path": "/userdata/roms/supergrafx/"},
    {"name": "SFC超级任天堂(16位)", "image": "Super Nintendo Entertainment System.png", "json": "Super Nintendo Entertainment System.json", "path": "/userdata/roms/sfc/"},
    {"name": "PC Engine 游戏(16位)", "image": "NEC PC Engine.png", "json": "NEC PC Engine.json", "path": "/userdata/roms/pcengine/"},
    {"name": "SEGA世嘉游戏(16位)", "image": "Sega Mega Drive.png", "json": "Mega Drive.json", "path": "/userdata/roms/megadrive/"},
    {"name": "GBC世嘉掌机", "image": "Game Boy Color.png", "json": "Game Boy Color.json", "path": "/userdata/roms/gbc/"},
    {"name": "GBA模拟游戏", "image": "Game Boy.png", "json": "Nintendo Game Boy Advance.json", "path": "/userdata/roms/gba/"},
    {"name": "NGO 街机游戏", "image": "Neo-Geo.png", "json": "Neo-Geo.json", "path": "/userdata/roms/neogeo/"},
    {"name": "PS1经典游戏", "image": "Sony Playstation.png", "json": "Sony Playstation.json", "path": "/userdata/roms/psx/"},
    {"name": "PSP掌机游戏", "image": "Sony PSP.png", "json": "Sony PSP.json", "path": "/userdata/roms/psp/"},
    {"name": "PS2经典游戏", "image": "Sony Playstation 2.png", "json": "Sony Playstation 2.json", "path": "/userdata/roms/ps2/"}
]

# 启动时预渲染所有图标
for config in GAME_CONFIGS:
    img_path = os.path.join(IMG_BASE_DIR, config["image"])
    config["surf_n"] = create_slot_surface(img_path, SLOT_W, SLOT_H, 0.8)
    config["surf_s"] = create_slot_surface(img_path, int(SLOT_W * 1.1), int(SLOT_H * 1.1), 0.8)

# --- 输入检测逻辑 ---
def is_confirm_key(event, mappings):
    if event.type == pygame.KEYDOWN: return event.key in [pygame.K_RETURN, pygame.K_SPACE]
    if event.type == pygame.JOYBUTTONDOWN: return event.button in [0, 1, 2]
    return False

def is_back_key(event, mappings):
    if event.type == pygame.KEYDOWN: return event.key == pygame.K_ESCAPE
    if event.type == pygame.JOYBUTTONDOWN: return event.button in [3, 4, 15]
    return False

def is_start_key(event, mappings):
    if event.type == pygame.KEYDOWN: return event.key == pygame.K_F1
    if event.type == pygame.JOYBUTTONDOWN:
        for joy_id, mapping in mappings.items():
            if 'start' in mapping and event.button == mapping['start']['id']: return True
        return event.button in [6, 7, 10, 11]
    return False

# --- UI 弹窗组件 ---
def show_update_dialog(screen, version, changelog):
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA); overlay.fill((0, 0, 0, 220))
    dw, dh = 650, 480
    dx, dy = (SW-dw)//2, (SH-dh)//2
    while True:
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (30, 40, 60), (dx, dy, dw, dh), border_radius=15)
        pygame.draw.rect(screen, (0, 150, 255), (dx, dy, dw, dh), 3, border_radius=15)
        title = dialog_font.render(f"发现新版本: {version}", True, (255, 215, 0))
        screen.blit(title, (SW//2 - title.get_width()//2, dy + 30))
        
        max_text_width = dw - 80
        wrapped_lines = wrap_text(changelog, log_font, max_text_width)

        for i, line in enumerate(wrapped_lines[:8]):
            line_surf = log_font.render(line, True, (200, 200, 200))
            screen.blit(line_surf, (dx + 40, dy + 100 + i * 35))
        
        hint = hint_font.render("A: 立即更新    B: 稍后再说", True, (255, 255, 255))
        screen.blit(hint, (SW//2 - hint.get_width()//2, dy + dh - 60))
        pygame.display.flip()
        for event in pygame.event.get():
            if is_confirm_key(event, active_mappings): return True
            if is_back_key(event, active_mappings): return False

def show_system_menu(screen):
    options = ["系统设置", "清理缓存", "版本更新", "退出系统"]
    sel_idx = 0
    menu_w, menu_h = 450, 350
    mx, my = (SW - menu_w)//2, (SH - menu_h)//2
    center_x = SW // 2
    while True:
        overlay = pygame.Surface((SW, SH), pygame.SRCALPHA); overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (30, 40, 60), (mx, my, menu_w, menu_h), border_radius=20)
        pygame.draw.rect(screen, (255, 215, 0), (mx, my, menu_w, menu_h), 3, border_radius=20)
        title = dialog_font.render("系统菜单", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(center_x, my + 45)))
        for i, opt in enumerate(options):
            item_y = my + 115 + i * 60
            if i == sel_idx:
                pygame.draw.rect(screen, (70, 80, 150), (mx+30, item_y-25, menu_w-60, 50), border_radius=10)
                color = (255, 255, 255)
            else: color = (150, 150, 150)
            txt = dialog_font.render(opt, True, color)
            screen.blit(txt, txt.get_rect(center=(center_x, item_y)))
        pygame.display.flip()
        for event in pygame.event.get():
            if is_confirm_key(event, active_mappings): return options[sel_idx]
            if is_back_key(event, active_mappings): return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: sel_idx = (sel_idx - 1) % len(options)
                elif event.key == pygame.K_DOWN: sel_idx = (sel_idx + 1) % len(options)
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1: sel_idx = (sel_idx - 1) % len(options)
                elif event.value[1] == -1: sel_idx = (sel_idx + 1) % len(options)

def show_exit_dialog(screen):
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA); overlay.fill((0, 0, 0, 210))
    dw, dh = 500, 250
    dx, dy = (SW-dw)//2, (SH-dh)//2
    while True:
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (35, 45, 65), (dx, dy, dw, dh), border_radius=15)
        pygame.draw.rect(screen, (255, 215, 0), (dx, dy, dw, dh), 3, border_radius=15)
        txt = dialog_font.render("确定要退出系统吗？", True, (255, 255, 255))
        screen.blit(txt, (SW//2 - txt.get_width()//2, dy + 60))
        hint = dialog_font.render("A: 确定    B: 取消", True, (200, 200, 200))
        screen.blit(hint, (SW//2 - hint.get_width()//2, dy + 150))
        pygame.display.flip()
        for event in pygame.event.get():
            if is_confirm_key(event, active_mappings): return True
            if is_back_key(event, active_mappings): return False

# --- 主循环变量 ---
selected_index = 0
running = True
clock = pygame.time.Clock()
notif_text, notif_timer = "", 0
local_ver = updater.get_local_version()

while running:
    screen.fill((20, 25, 35))
    current_page = selected_index // ITEMS_PER_PAGE
    total_pages = (len(GAME_CONFIGS) - 1) // ITEMS_PER_PAGE + 1
    
    # 渲染顶部标题
    title_text = f"复古游戏下载系统 {local_ver} ({current_page + 1}/{total_pages})"
    title_surf = title_font.render(title_text, True, (255, 215, 0))
    screen.blit(title_surf, (SW//2 - title_surf.get_width()//2, 50))
    pygame.draw.line(screen, (70, 75, 100), (100, 145), (SW-100, 145), 2)

    # 渲染九宫格游戏槽位
    start_idx = current_page * ITEMS_PER_PAGE
    for i in range(ITEMS_PER_PAGE):
        idx = start_idx + i
        if idx >= len(GAME_CONFIGS): break
        r, c = i // COLS, i % COLS
        x, y = (c + 1) * COL_SPACING, ROW_START_Y + (r * V_SPACING) 
        cfg = GAME_CONFIGS[idx]
        
        if idx == selected_index:
            img, color, width, name_color = cfg["surf_s"], (255, 215, 0), 4, (255, 255, 255)
        else:
            img, color, width, name_color = cfg["surf_n"], (80, 85, 100), 2, (130, 135, 150)
            
        rect = img.get_rect(center=(x, y))
        pygame.draw.rect(screen, color, rect, width, border_radius=15)
        screen.blit(img, rect)
        name_surf = hint_font.render(cfg["name"], True, name_color)
        screen.blit(name_surf, (x - name_surf.get_width()//2, rect.bottom + 12))

    # 页脚提示
    pygame.draw.line(screen, (70, 75, 100), (100, SH-100), (SW-100, SH-100), 2)
    hint_surf = hint_font.render("方向键: 移动    A: 确定    B: 返回/退出    Start: 系统菜单", True, (160, 160, 170))
    screen.blit(hint_surf, (SW//2 - hint_surf.get_width()//2, SH-65))

    # 热插拔状态通知框
    if notif_text and pygame.time.get_ticks() - notif_timer < 3000:
        msg_surf = hint_font.render(notif_text, True, (255, 255, 255))
        m_w, m_h = msg_surf.get_size()
        m_rect = pygame.Rect(SW//2 - m_w//2 - 20, 160, m_w + 40, 60)
        notif_bg = pygame.Surface((m_rect.width, m_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(notif_bg, (50, 100, 200, 220), (0, 0, m_rect.width, m_rect.height), border_radius=15)
        screen.blit(notif_bg, m_rect.topleft)
        screen.blit(msg_surf, (m_rect.centerx - m_w//2, m_rect.centery - m_h//2))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED:
            try:
                joy = pygame.joystick.Joystick(event.device_index); joy.init()
                notif_text = f"已连接: {joy.get_name()}"; notif_timer = pygame.time.get_ticks()
                active_mappings = load_active_mappings()
            except: pass
        elif event.type == pygame.JOYDEVICEREMOVED:
            notif_text = "手柄已断开连接"; notif_timer = pygame.time.get_ticks()
            active_mappings = load_active_mappings()

        # 系统菜单操作逻辑
        if is_start_key(event, active_mappings):
            choice = show_system_menu(screen)
            if choice == "版本更新":
                notif_text = "正在检查更新..."; notif_timer = pygame.time.get_ticks()
                has_upd, rem_ver, logs, url = updater.check_update()
                if has_upd:
                    if show_update_dialog(screen, rem_ver, logs):
                        notif_text = "正在安装更新，请勿断电..."; notif_timer = pygame.time.get_ticks()
                        screen.fill((20, 25, 35))
                        msg = title_font.render(notif_text, True, (255, 215, 0))
                        screen.blit(msg, (SW//2 - msg.get_width()//2, SH//2))
                        pygame.display.flip()

                        if updater.execute_update(url, rem_ver):
                            local_ver = rem_ver
                            screen.fill((20, 25, 35))
                            final_msg = title_font.render("更新成功！系统即将重启", True, (0, 255, 0))
                            screen.blit(final_msg, (SW//2 - final_msg.get_width()//2, SH//2))
                            pygame.display.flip(); pygame.time.wait(3000)
                            running = False
                        else: notif_text = "更新安装失败"; notif_timer = pygame.time.get_ticks()
                else: notif_text = "当前已是最新版本"; notif_timer = pygame.time.get_ticks()
            
            elif choice == "清理缓存":
                if updater.clear_pycache(): notif_text = "缓存已清理"; notif_timer = pygame.time.get_ticks()
            elif choice == "退出系统":
                if show_exit_dialog(screen): running = False

        # 进入二级菜单逻辑
        if is_confirm_key(event, active_mappings):
            cfg = GAME_CONFIGS[selected_index]
            pygame.event.clear()
            res = game_menu(screen, title_font, active_mappings, os.path.join(JSON_BASE_DIR, cfg["json"]), cfg["path"])
            active_mappings = load_active_mappings()
            if res == "exit": running = False
            continue

        if is_back_key(event, active_mappings):
            if show_exit_dialog(screen): running = False
        
        # 导航控制逻辑
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_RIGHT: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_UP and (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif event.key == pygame.K_DOWN and (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE:
                if selected_index + COLS < len(GAME_CONFIGS): selected_index += COLS
        elif event.type == pygame.JOYHATMOTION:
            hx, hy = event.value
            if hx == -1: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif hx == 1: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif hy == 1 and (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif hy == -1 and (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE:
                if selected_index + COLS < len(GAME_CONFIGS): selected_index += COLS

    clock.tick(60)
pygame.quit()