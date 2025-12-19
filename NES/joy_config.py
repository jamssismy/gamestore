import os
import pygame
import xml.etree.ElementTree as ET
from datetime import datetime

LOG_FILE = "/userdata/roms/gamestore/nes/debug_log.txt"

def log_message(msg):
    """仅用于记录严重错误"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(full_msg + "\n")
    except: pass

def load_active_mappings():
    # 移除“开始初始化”日志
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
            # 保留关键错误日志
            log_message(f"配置文件解析失败: {str(e)}")

    active_maps = {}
    joy_count = pygame.joystick.get_count()
    for i in range(joy_count):
        try:
            j = pygame.joystick.Joystick(i)
            if not j.get_init(): j.init()
            raw_name = j.get_name().strip().lower()
            
            # 1. 检查 XML 匹配
            if raw_name in all_configs:
                active_maps[i] = all_configs[raw_name]
            
            # 2. 针对 Pro Controller 的静默修正
            elif "pro controller" in raw_name:
                active_maps[i] = {
                    'a': {'id': 0},       # A键
                    'b': {'id': 1},       # B键
                    'confirm_alt': 2,     # Home键补丁
                    'up': {'id': 1},      # 轴
                    'left': {'id': 0}     # 轴
                }
            else:
                # 其他手柄默认值
                active_maps[i] = {'a': {'id': 0}, 'b': {'id': 1}}
        except Exception as e:
            log_message(f"手柄设备 [{i}] 加载异常: {str(e)}")
            
    return active_maps

def get_mapping_value(active_mappings, joy_id, key_name, default_id):
    if joy_id in active_mappings:
        conf = active_mappings[joy_id]
        # 支持多键位判定逻辑
        if key_name == 'a' and 'confirm_alt' in conf:
            return [conf['a']['id'], conf['confirm_alt']]
        
        if key_name in conf:
            return conf[key_name].get('id')
    return default_id