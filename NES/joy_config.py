import pygame
import os
import xml.etree.ElementTree as ET
from datetime import datetime

LOG_FILE = "/userdata/roms/gamestore/nes/debug_log.txt"

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
    except:
        pass

# 新增：安全加载手柄数据库
def load_controller_db():
    db_path = "/usr/share/sdl-jstest/gamecontrollerdb.txt"
    if os.path.exists(db_path):
        try:
            os.environ['SDL_GAMECONTROLLERCONFIG_FILE'] = db_path
            log_message(f"手柄数据库加载成功: {db_path}")
            log_message("手柄兼容性已提升（数据库映射优先于ES配置）")
        except Exception as e:
            log_message(f"加载手柄数据库失败: {e}")
    else:
        log_message("未找到 gamecontrollerdb.txt，使用原始ES配置")

# 原始函数：解析ES输入配置
def load_active_mappings():
    load_controller_db()  # 新增：在解析前先加载数据库

    cfg_path = "/userdata/system/configs/emulationstation/es_input.cfg"
    all_configs = {}
    if os.path.exists(cfg_path):
        try:
            tree = ET.parse(cfg_path)
            root = tree.getroot()
            for config in root.findall('inputConfig'):
                dev_name = config.get('deviceName', '').strip().lower()
                all_configs[dev_name] = {
                    input_tag.get('name'): {'id': int(input_tag.get('id')), 'type': input_tag.get('type')}
                    for input_tag in config.findall('input')
                }
        except Exception as e:
            log_message(f"配置文件解析失败: {str(e)}")

    active_maps = {}
    joy_count = pygame.joystick.get_count()
    for i in range(joy_count):
        try:
            j = pygame.joystick.Joystick(i)
            if not j.get_init():
                j.init()
            raw_name = j.get_name().strip().lower()
            
            if raw_name in all_configs:
                active_maps[i] = all_configs[raw_name]
            elif "pro controller" in raw_name:
                active_maps[i] = {
                    'a': {'id': 0},
                    'b': {'id': 1},
                    'confirm_alt': 2,
                    'up': {'id': 1, 'type': 'hat'},
                    'left': {'id': 0, 'type': 'hat'}
                }
            else:
                active_maps[i] = {'a': {'id': 0}, 'b': {'id': 1}}
        except Exception as e:
            log_message(f"手柄设备 [{i}] 加载异常: {str(e)}")
            
    return active_maps

# 原始函数：获取映射值
def get_mapping_value(active_mappings, joy_id, key_name, default_id):
    if joy_id in active_mappings:
        conf = active_mappings[joy_id]
        if key_name == 'a' and 'confirm_alt' in conf:
            return [conf['a']['id'], conf['confirm_alt']]
        if key_name in conf:
            return conf[key_name].get('id')
    return default_id