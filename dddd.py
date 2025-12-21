import pygame
import os
from joy_config import load_active_mappings, log_message, get_mapping_value

# 尝试导入商城页面
try:
    from game_menu import game_menu
except ImportError:
    log_message("致命错误: 无法找到 game_menu.py 模块")
    def game_menu(screen, font, mappings, json_path, save_dir): return "back"

pygame.init()
pygame.joystick.init()

# 初始化手柄
for i in range(pygame.joystick.get_count()):
    try:
        j = pygame.joystick.Joystick(i)
        j.init()
    except: pass

# 加载手柄映射配置
active_mappings = load_active_mappings()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SW, SH = screen.get_size()

# --- 路径常量 ---
BASE_DIR = "/userdata/roms/gamestore/nes" 
JSON_BASE_DIR = os.path.join(BASE_DIR, "json") 
IMG_BASE_DIR = os.path.join(BASE_DIR, "images") 

# --- 字体加载 ---
font_path = os.path.join(BASE_DIR, "fonts", "NotoSansSC-Regular.ttf")
# 如果没有找到字体，回退到系统字体
title_font = pygame.font.Font(font_path, 64) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 64)
hint_font = pygame.font.Font(font_path, 30) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 30)
dialog_font = pygame.font.Font(font_path, 36) if os.path.exists(font_path) else pygame.font.SysFont("simhei", 36)

# --- UI 尺寸定义 ---
SLOT_W, SLOT_H = 340, 240  # 标准格子大小
COLS, ROWS = 3, 2          # 3列 2行
ITEMS_PER_PAGE = COLS * ROWS

# --- 核心函数：创建标准格子 ---
def create_slot_surface(img_path, slot_w, slot_h, scale_inner=0.85):
    """创建统一的格子背景，如果图片不存在，则显示带名字的占位图"""
    slot_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
    
    # 1. 绘制统一的深色底板 (确保无图时也有背景)
    pygame.draw.rect(slot_surf, (40, 45, 60), (0, 0, slot_w, slot_h), border_radius=15)
    
    # 2. 加载并缩放图片
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img_w, img_h = img.get_size()
            
            # 计算缩放比例 (scale_inner 控制留白)
            ratio = min((slot_w * scale_inner) / img_w, (slot_h * scale_inner) / img_h)
            new_w, new_h = int(img_w * ratio), int(img_h * ratio)
            
            scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
            
            # 居中绘制
            dest_x = (slot_w - new_w) // 2
            dest_y = (slot_h - new_h) // 2
            slot_surf.blit(scaled_img, (dest_x, dest_y))
        except Exception as e:
            log_message(f"图片加载失败 {img_path}: {e}")
            
    return slot_surf

# --- 游戏列表配置 ---
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

# --- 预加载图片资源 ---
for config in GAME_CONFIGS:
    img_path = os.path.join(IMG_BASE_DIR, config["image"])
    # 正常状态 (不缩放格子，内部图片 0.8)
    config["surf_n"] = create_slot_surface(img_path, SLOT_W, SLOT_H, 0.8)
    # 选中状态 (格子本身放大 10%，内部图片也相应放大)
    config["surf_s"] = create_slot_surface(img_path, int(SLOT_W * 1.1), int(SLOT_H * 1.1), 0.8)

# --- 按键判定逻辑 (对接 joy_config) ---
def is_confirm_key(event, mappings):
    if event.type == pygame.KEYDOWN: 
        return event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER]
    
    if event.type == pygame.JOYBUTTONDOWN:
        # 获取配置中的 'a' 键，如果找不到，默认接受 0, 1, 2 防止无法操作
        target_ids = get_mapping_value(mappings, event.joy, 'a', [0, 1, 2])
        return event.button in target_ids
    return False

def is_back_key(event, mappings):
    if event.type == pygame.KEYDOWN: 
        return event.key == pygame.K_ESCAPE
    
    if event.type == pygame.JOYBUTTONDOWN:
        # 获取配置中的 'b' 键，默认接受 1 (Xbox B键)
        target_ids = get_mapping_value(mappings, event.joy, 'b', [1])
        return event.button in target_ids
    return False

# --- 退出对话框 ---
def show_exit_dialog(screen):
    overlay = pygame.Surface((SW, SH), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    dw, dh = 500, 250
    dx, dy = (SW - dw)//2, (SH - dh)//2
    
    while True:
        screen.blit(overlay, (0, 0))
        # 弹窗背景
        pygame.draw.rect(screen, (35, 45, 65), (dx, dy, dw, dh), border_radius=15)
        pygame.draw.rect(screen, (255, 215, 0), (dx, dy, dw, dh), 3, border_radius=15)
        
        # 文字
        txt = dialog_font.render("确定要退出系统吗？", True, (255, 255, 255))
        screen.blit(txt, (SW//2 - txt.get_width()//2, dy + 60))
        
        hint = dialog_font.render("A: 确定    B: 取消", True, (200, 200, 200))
        screen.blit(hint, (SW//2 - hint.get_width()//2, dy + 150))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if is_confirm_key(event, active_mappings): return True
            if is_back_key(event, active_mappings): return False

# --- 主循环 ---
selected_index = 0
running = True
clock = pygame.time.Clock()

# --- 布局参数 (已调整为下移) ---
COL_SPACING = SW // (COLS + 1)
ROW_START_Y = 340  # 第一行图标的中心 Y 坐标 (下移以留出顶部空间)
V_SPACING = 360    # 行间距

while running:
    # 背景色
    screen.fill((20, 25, 35))
    
    # 计算分页
    current_page = selected_index // ITEMS_PER_PAGE
    total_pages = (len(GAME_CONFIGS) - 1) // ITEMS_PER_PAGE + 1
    
    # 1. 绘制标题
    title_text = f"复古游戏下载系统 ({current_page + 1}/{total_pages})"
    title_surf = title_font.render(title_text, True, (255, 215, 0))
    screen.blit(title_surf, (SW//2 - title_surf.get_width()//2, 50))
    
    # 装饰线
    pygame.draw.line(screen, (70, 75, 100), (100, 145), (SW-100, 145), 2)

    # 2. 绘制网格图标
    start_idx = current_page * ITEMS_PER_PAGE
    for i in range(ITEMS_PER_PAGE):
        idx = start_idx + i
        if idx >= len(GAME_CONFIGS): break
        
        # 计算行列
        r, c = i // COLS, i % COLS
        x = (c + 1) * COL_SPACING
        y = ROW_START_Y + (r * V_SPACING) 
        
        cfg = GAME_CONFIGS[idx]
        
        # 判断选中状态
        if idx == selected_index:
            img = cfg["surf_s"]
            rect = img.get_rect(center=(x, y))
            # 选中：绘制金色粗边框
            pygame.draw.rect(screen, (255, 215, 0), rect, 4, border_radius=15)
            name_color = (255, 255, 255)
        else:
            img = cfg["surf_n"]
            # img.set_alpha(160) # 可选：让未选中的稍微暗一点
            rect = img.get_rect(center=(x, y))
            # 未选中：绘制深灰细边框 (统一视觉)
            pygame.draw.rect(screen, (80, 85, 100), rect, 2, border_radius=15)
            name_color = (130, 135, 150)
            
        screen.blit(img, rect)
        
        # 绘制名称
        name_surf = hint_font.render(cfg["name"], True, name_color)
        screen.blit(name_surf, (x - name_surf.get_width()//2, rect.bottom + 12))

    # 3. 底部提示栏
    pygame.draw.line(screen, (70, 75, 100), (100, SH-100), (SW-100, SH-100), 2)
    hint_surf = hint_font.render("方向键: 移动    A: 确定    B: 返回/退出", True, (160, 160, 170))
    screen.blit(hint_surf, (SW//2 - hint_surf.get_width()//2, SH-65))

    pygame.display.flip()

    # --- 事件处理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if show_exit_dialog(screen): running = False
            
        # 确认键逻辑
        if is_confirm_key(event, active_mappings):
            cfg = GAME_CONFIGS[selected_index]
            pygame.event.clear()
            # 拼接 JSON 完整路径
            full_json_path = os.path.join(JSON_BASE_DIR, cfg["json"])
            
            # 进入商城子页面
            res = game_menu(screen, title_font, active_mappings, full_json_path, cfg["path"])
            
            # 如果在商城里选择了彻底退出
            if res == "exit": running = False
            
            # 重新加载手柄映射 (防止热插拔后失效)
            active_mappings = load_active_mappings()
            continue

        # 返回/退出键逻辑
        if is_back_key(event, active_mappings):
            if show_exit_dialog(screen): running = False

        # 键盘导航
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_RIGHT: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif event.key == pygame.K_UP: 
                # 跨行向上
                if (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif event.key == pygame.K_DOWN:
                # 跨行向下 (需确保目标存在且不超页)
                if (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE and selected_index + COLS < len(GAME_CONFIGS):
                    selected_index += COLS

        # 手柄摇杆/十字键导航
        elif event.type == pygame.JOYHATMOTION:
            hx, hy = event.value
            if hx == -1: selected_index = (selected_index - 1) % len(GAME_CONFIGS)
            elif hx == 1: selected_index = (selected_index + 1) % len(GAME_CONFIGS)
            elif hy == 1 and (selected_index % ITEMS_PER_PAGE) >= COLS: selected_index -= COLS
            elif hy == -1 and (selected_index % ITEMS_PER_PAGE) + COLS < ITEMS_PER_PAGE and selected_index + COLS < len(GAME_CONFIGS):
                selected_index += COLS

    clock.tick(60)

pygame.quit()