import pygame
import os
import shutil
import updater  # 新增：引入更新逻辑模块
from joy_config import load_active_mappings, log_message

try:
    from game_menu import game_menu
except ImportError:
    log_message("致命错误: 无法找到 game_menu.py 模块")
    def game_menu(screen, font, mappings, json_path, save_dir): return "back"

pygame.init()
pygame.joystick.init()

for i in range(pygame.joystick.get_count()):
    try:
        j = pygame.joystick.Joystick(i); j.init()
    except: pass

active_mappings = load_active_mappings()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SW, SH = screen.get_size()

# 路径常量
BASE_DIR = "/userdata/roms/gamestore/nes" 
PYCACHE_DIR = os.path.join(BASE_DIR, "__pycache__")
JSON_BASE_DIR = os.path.join(BASE_DIR, "json") 
IMG_BASE_DIR = os.path.join(BASE_DIR, "images") 

# 字体加载
font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
title_font = pygame.font.Font(font_path, 64) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 64)
hint_font = pygame.font.Font(font_path, 30) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 30)
dialog_font = pygame.font.Font(font_path, 36) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 36)
log_font = pygame.font.Font(font_path, 24) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 24)

# --- UI 尺寸定义 ---
SLOT_W, SLOT_H = 340, 240  
COLS, ROWS = 3, 2
ITEMS_PER_PAGE = COLS * ROWS

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

# --- 配置 ---
GAME_CONFIGS = [
    {"name": "FC任天堂游戏", "image": "Nintendo Entertainment System.png", "json": "Nintendo Entertainment System.json", "path": "/userdata/roms/nes/"},
    {"name": "SEGA世嘉游戏", "image": "Sega Mega Drive.png", "json": "Sega Mega Drive.json", "path": "/userdata/roms/megadrive/"},
    {"name": "GBC世嘉掌机", "image": "Game Boy Color.png", "json": "Game Boy Color.json", "path": "/userdata/roms/gbc/"},
    {"name": "GBA模拟游戏", "image": "Game Boy.png", "json": "Game Boy.json", "path": "/userdata/roms/gba/"},
    {"name": "PS1经典游戏", "image": "Sony Playstation.png", "json": "Sony Playstation.json", "path": "/userdata/roms/psx/"},
    {"name": "PSP掌机游戏", "image": "Sony PSP.png", "json": "Sony PSP.json", "path": "/userdata/roms/psp/"},
    {"name": "PC Engine 游戏", "image": "NEC PC Engine.png", "json": "NEC PC Engine.json", "path": "/userdata/roms/pcengine/"},
    {"name": "PS2经典游戏", "image": "Sony Playstation 2.png", "json": "Sony Playstation 2.json", "path": "/userdata/roms/ps2/"},
    {"name": "Sega 八位机", "image": "Sega Mark III.png", "json": "Sega Mark III.json", "path": "/userdata/roms/mastersystem/"}
]

for config in GAME_CONFIGS:
    img_path = os.path.join(IMG_BASE_DIR, config["image"])
    config["surf_n"] = create_slot_surface(img_path, SLOT_W, SLOT_H, 0.8)
    config["surf_s"] = create_slot_surface(img_path, int(SLOT_W * 1.1), int(SLOT_H * 1.1), 0.8)

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
            if 'start' in mapping and event.button == mapping['start']['id']:
                return True
        return event.button in [6, 7, 10, 11]
    return False

def clear_pycache():
    if os.path.exists(PYCACHE_DIR):
        try:
            shutil.rmtree(PYCACHE_DIR)
            log_message(f"已清理缓存目录: {PYCACHE_DIR}")
            return True
        except: return False
    return True

# --- 新增：版本更新确认对话框 ---
def show_update_dialog(screen, version, changelog):
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA); overlay.fill((0, 0, 0, 220))
    dw, dh = 600, 450
    dx, dy = (SW-dw)//2, (SH-dh)//2
    while True:
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (30, 40, 60), (dx, dy, dw, dh), border_radius=15)
        pygame.draw.rect(screen, (0, 150, 255), (dx, dy, dw, dh), 3, border_radius=15)
        
        title = dialog_font.render(f"检测到新版本: {version}", True, (255, 215, 0))
        screen.blit(title, (SW//2 - title.get_width()//2, dy + 30))
        
        # 渲染更新日志（简单换行处理）
        lines = changelog.split('\n')
        for i, line in enumerate(lines):
            line_surf = log_font.render(line, True, (200, 200, 200))
            screen.blit(line_surf, (dx + 40, dy + 100 + i * 35))
            
        hint = hint_font.render("A: 开始更新    B: 以后再说", True, (255, 255, 255))
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
            item_center_y = my + 115 + i * 60
            if i == sel_idx:
                highlight_rect = pygame.Rect(0, 0, menu_w - 60, 50)
                highlight_rect.center = (center_x, item_center_y)
                pygame.draw.rect(screen, (70, 80, 150), highlight_rect, border_radius=10)
                color = (255, 255, 255)
            else: color = (150, 150, 150)
            txt_surf = dialog_font.render(opt, True, color)
            screen.blit(txt_surf, txt_surf.get_rect(center=(center_x, item_center_y)))
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

selected_index = 0
running = True
clock = pygame.time.Clock()
notif_text, notif_timer = "", 0
COL_SPACING, ROW_START_Y, V_SPACING = SW // (COLS + 1), 340, 360

while running:
    screen.fill((20, 25, 35))
    current_page = selected_index // ITEMS_PER_PAGE
    total_pages = (len(GAME_CONFIGS) - 1) // ITEMS_PER_PAGE + 1
    
    local_ver = updater.get_local_version()
    title_text = f"复古游戏下载系统 {local_ver} ({current_page + 1}/{total_pages})"
    title_surf = title_font.render(title_text, True, (255, 215, 0))
    screen.blit(title_surf, (SW//2 - title_surf.get_width()//2, 50))
    pygame.draw.line(screen, (70, 75, 100), (100, 145), (SW-100, 145), 2)

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

    pygame.draw.line(screen, (70, 75, 100), (100, SH-100), (SW-100, SH-100), 2)
    hint_surf = hint_font.render("方向键: 移动    A: 确定    B: 返回/退出    Start: 系统菜单", True, (160, 160, 170))
    screen.blit(hint_surf, (SW//2 - hint_surf.get_width()//2, SH-65))

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

        if is_start_key(event, active_mappings):
            choice = show_system_menu(screen)
            if choice == "退出系统":
                if show_exit_dialog(screen): running = False
            elif choice == "清理缓存":
                if clear_pycache(): notif_text = "缓存文件夹已清理"
                else: notif_text = "清理失败"
                notif_timer = pygame.time.get_ticks()
            # --- 新增：版本更新逻辑分支 ---
            elif choice == "版本更新":
                notif_text = "正在检查更新..."; notif_timer = pygame.time.get_ticks()
                # 渲染一次提示
                msg_surf = hint_font.render(notif_text, True, (255, 255, 255))
                screen.blit(msg_surf, (SW//2 - msg_surf.get_width()//2, 175))
                pygame.display.flip()
                
                has_upd, rem_ver, logs, url = updater.check_update()
                if has_upd:
                    if show_update_dialog(screen, rem_ver, logs):
                        notif_text = "下载更新中，请稍候..."; notif_timer = pygame.time.get_ticks()
                        # 这里可以接入带进度条的 execute_update，目前先用基础版
                        if updater.execute_update(url):
                            notif_text = "更新成功！程序即将退出，请重启"
                            notif_timer = pygame.time.get_ticks()
                            # 强制渲染最后一条提示
                            screen.fill((20, 25, 35))
                            final_msg = hint_font.render(notif_text, True, (0, 255, 0))
                            screen.blit(final_msg, (SW//2 - final_msg.get_width()//2, SH//2))
                            pygame.display.flip()
                            pygame.time.wait(3000)
                            running = False
                        else:
                            notif_text = "更新下载失败"
                else:
                    notif_text = "当前已是最新版本"
                notif_timer = pygame.time.get_ticks()
            elif choice:
                notif_text = f"功能: {choice}"; notif_timer = pygame.time.get_ticks()

        if event.type == pygame.QUIT:
            if show_exit_dialog(screen): running = False
        if is_confirm_key(event, active_mappings):
            cfg = GAME_CONFIGS[selected_index]
            pygame.event.clear()
            res = game_menu(screen, title_font, active_mappings, os.path.join(JSON_BASE_DIR, cfg["json"]), cfg["path"])
            active_mappings = load_active_mappings()
            if res == "exit": running = False
            continue
        if is_back_key(event, active_mappings):
            if show_exit_dialog(screen): running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_RIGHT: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_UP and (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif event.key == pygame.K_DOWN and (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE and selected_index + COLS < len(GAME_CONFIGS):
                selected_index += COLS
        elif event.type == pygame.JOYHATMOTION:
            hx, hy = event.value
            if hx == -1: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif hx == 1: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif hy == 1 and (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif hy == -1 and (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE and selected_index + COLS < len(GAME_CONFIGS):
                selected_index += COLS

    clock.tick(60)
pygame.quit()