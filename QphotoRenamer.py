import os
import sys
import datetime
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, Entry, messagebox, Text, WORD, END, INSERT
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread, Event, Lock
import logging
import re
import subprocess
import webbrowser
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from collections import OrderedDict
from functools import lru_cache
import configparser
import tkinter as tk
import gc
import time
import multiprocessing
import shutil
import queue
import threading

# 获取当前脚本所在的目录路径
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'icon.ico')

# 常用日期格式
COMMON_DATE_FORMATS = [
    "%Y%m%d_%H%M%S",    # 20240729_141530
    "%Y-%m-%d %H:%M:%S",  # 2024-07-29 14:15:30
    "%d-%m-%Y %H:%M:%S",  # 29-07-2024 14:15:30
    "%Y%m%d",            # 20240729
    "%H%M%S",            # 141530
    "%Y-%m-%d",          # 2024-07-29
    "%d-%m-%Y"           # 29-07-2024
]

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic'}

# 多语言支持
LANGUAGES = {
    "简体中文": {
        "window_title": "文件与照片批量重命名工具 QphotoRenamer 2.4 —— QwejayHuang",
        "description_base": "拖放文件或照片，将按照",
        "description_suffix": "重命名文件。若无法获取拍摄日期（或非媒体文件），则使用",
        "start_renaming": "开始重命名",
        "stop_renaming": "停止重命名",
        "settings": "设置",
        "clear_list": "清空列表",
        "add_files": "添加文件",
        "help": "帮助",
        "auto_scroll": "自动滚动",
        "check_for_updates": "反馈&检查更新",
        "ready": "准备就绪",
        "rename_pattern": "重命名格式:",
        "language": "语言",
        "save_settings": "保存设置",
        "clear_list": "清空列表",
        "add_files": "添加文件",
        "help": "帮助",
        "auto_scroll": "自动滚动",
        "check_for_updates": "反馈&检查更新",
        "ready": "准备就绪",
        "rename_pattern": "重命名格式:",
        "language": "语言",
        "save_settings": "保存设置",
        "formats_explanation": "常用日期格式示例:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "正在重命名，请稍候...",
        "renaming_stopped": "重命名操作已停止。",
        "renaming_success": "成功重命名 {0} 个文件，未重命名 {1} 个文件。",
        "renaming_partial": "部分重命名完成：成功 {0} 个，失败 {1} 个。",
        "filename": "文件路径",
        "status": "命名依据",
        "renamed_name": "新名称",
        "prepare_rename_by": "{}",
        "prepare_rename_keep_name": "准备保留原文件名",
        "already_rename_by": "已按 {} 命名",
        "ready_to_rename": "待重命名",
        "help_text": """使用说明:
1. 将文件或文件夹拖放到列表中，或点击"添加文件"按钮选择文件。
2. 点击"开始重命名"按钮，程序将根据设置的日期格式重命名文件。
3. 若无法获取拍摄日期，程序将根据设置的备用日期（修改日期、创建日期或保留原文件名）进行处理。
4. 双击列表中的文件名可打开文件。
5. 右键点击列表中的文件名可移除文件。
6. 点击"设置"按钮可调整日期格式、前缀、后缀等设置。
7. 勾选"自动滚动"选项，列表将自动滚动至最新添加的文件。
8. 点击"清空列表"按钮可清空文件列表。
9. 点击"停止重命名"按钮可停止当前的重命名操作。
10. 重命名完成后，已重命名的文件项将显示为绿色，重命名失败的文件项将显示为红色。
11. 点击文件名可查看文件的EXIF信息。""",
        "settings_window_title": "设置",
        "prefix": "前缀:",
        "suffix": "后缀:",
        "skip_extensions": "跳过重命名的文件类型（空格分隔）:",
        "file_count": "文件总数: {0}",
        "fast_add_mode": "启用快速添加模式:",
        "name_conflict_prompt": "重命名后文件名冲突时:",
        "add_suffix_option": "增加后缀",
        "keep_original_option": "保留原文件名",
        "other_settings": "其他设置",
        "file_handling_settings": "文件处理设置",
        "rename_pattern_settings": "重命名格式设置",
        "date_bases": [
            {"display": "拍摄日期", "value": "拍摄日期"},
            {"display": "修改日期", "value": "修改日期"},
            {"display": "创建日期", "value": "创建日期"}
        ],
        "alternate_dates": [
            {"display": "修改日期", "value": "修改日期"},
            {"display": "创建日期", "value": "创建日期"},
            {"display": "保留原文件名", "value": "保留原文件名"}
        ],
        "suffix_options": ["_001", "-01", "_1"],
        "suffix_edit_label": "编辑后缀名称:",
        "show_errors_only": "仅显示错误",
        "name_conflicts": [
            {"display": "增加后缀", "value": "add_suffix"},
            {"display": "保留原文件名", "value": "keep_original"}
        ],
        "date_settings": "日期设置",
        "date_basis": "日期基准",
        "preferred_date": "首选日期:",
        "alternate_date": "备选日期:",
        "file_filter": "文件过滤",
        "conflict_handling": "冲突处理:",
        "suffix_format": "后缀格式:",
        "performance_optimization": "性能优化",
        "enable_fast_add": "启用快速添加模式（适用于大量文件）",
        "file_count_threshold": "文件数量阈值:",
        "ui_settings": "界面设置",
        "language_settings": "语言设置",
        "interface_language": "界面语言:",
        "auto_scroll_to_latest": "自动滚动到最新文件",
        "about": "关于",
        "save_template": "保存",
        "delete_template": "删除",
        "start_processing_files": "开始处理文件...",
        "added_files_to_queue": "已添加 {0} 个文件/目录到队列...",
        "start_processing_batch": "开始处理前 {0} 个文件...",
        "processing_files": "正在处理文件...（队列中还有{0}个文件待处理）",
        "processing_in_progress": "正在处理中...",
        "files_ready": "文件已就绪！",
        "operation_stopped": "操作已停止",
        "drag_hint": "拖入文件，优先使用",
        "rename_hint": "重命名，如无拍摄日期则使用",
        "rename_end_hint": "重命名。",
        "rename_skipped_keep_name": "已跳过（保留原文件名）",
        "rename_skipped_no_date": "无拍摄日期",
        "rename_skipped_no_name": "无法生成新文件名",
        "rename_skipped_exists": "目标文件已存在"
    },
    "English": {
        "window_title": "QphotoRenamer 2.4 —— QwejayHuang",
        "description_base": "Drag and drop files or photos to rename them based on ",
        "description_suffix": ". If the shooting date is unavailable, use ",
        "start_renaming": "Start Renaming",
        "stop_renaming": "Stop Renaming",
        "settings": "Settings",
        "clear_list": "Clear List",
        "add_files": "Add Files",
        "help": "Help",
        "auto_scroll": "Auto Scroll",
        "check_for_updates": "CheckUpdates",
        "ready": "Ready",
        "rename_pattern": "Rename Pattern:",
        "language": "Language",
        "save_settings": "Save Settings",
        "formats_explanation": "Common date format examples:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "Renaming in progress, please wait...",
        "renaming_stopped": "Renaming operation stopped.",
        "renaming_success": "Successfully renamed {0} files, {1} files not renamed.",
        "renaming_partial": "Partial renaming completed: {0} successful, {1} failed.",
        "filename": "File Path",
        "status": "Naming Basis",
        "renamed_name": "New Name",
        "prepare_rename_by": "Prepare to rename by {}",
        "prepare_rename_keep_name": "Prepare to keep original filename",
        "already_rename_by": "Already named by {}",
        "ready_to_rename": "Ready to rename",
        "help_text": """Instructions:
1. Drag and drop files or folders into the list, or click the "Add Files" button to select files.
2. Click the "Start Renaming" button, and the program will rename files according to the set date format.
3. If the shooting date cannot be obtained, the program will process according to the set alternate date (modification date, creation date, or keep original filename).
4. Double-click the filename in the list to open the file.
5. Right-click the filename in the list to remove the file.
6. Click the "Settings" button to adjust date format, prefix, suffix, and other settings.
7. Check the "Auto Scroll" option, and the list will automatically scroll to the latest added file.
8. Click the "Clear List" button to clear the file list.
9. Click the "Stop Renaming" button to stop the current renaming operation.
10. After renaming is complete, successfully renamed file items will be displayed in green, and failed file items will be displayed in red.
11. Click the filename to view the file's EXIF information.""",
        "settings_window_title": "Settings",
        "prefix": "Prefix:",
        "suffix": "Suffix:",
        "skip_extensions": "Skip renaming file types (space separated):",
        "file_count": "Total Files: {0}",
        "fast_add_mode": "Enable Fast Add Mode:",
        "name_conflict_prompt": "When filename conflicts after renaming:",
        "add_suffix_option": "Add Suffix",
        "keep_original_option": "Keep Original Filename",
        "other_settings": "Other Settings",
        "file_handling_settings": "File Handling Settings",
        "rename_pattern_settings": "Rename Pattern Settings",
        "date_bases": [
            {"display": "Shooting Date", "value": "Shooting Date"},
            {"display": "Modification Date", "value": "Modification Date"},
            {"display": "Creation Date", "value": "Creation Date"}
        ],
        "alternate_dates": [
            {"display": "Modification Date", "value": "Modification Date"},
            {"display": "Creation Date", "value": "Creation Date"},
            {"display": "Keep Original Filename", "value": "Keep Original Filename"}
        ],
        "suffix_options": ["_001", "-01", "_1"],
        "suffix_edit_label": "Edit Suffix Name:",
        "show_errors_only": "Show Errors Only",
        "name_conflicts": [
            {"display": "Add Suffix", "value": "add_suffix"},
            {"display": "Keep Original", "value": "keep_original"}
        ],
        "date_settings": "Date Settings",
        "date_basis": "Date Basis",
        "preferred_date": "Preferred Date:",
        "alternate_date": "Alternate Date:",
        "file_filter": "File Filter",
        "conflict_handling": "Conflict Handling:",
        "suffix_format": "Suffix Format:",
        "performance_optimization": "Performance Optimization",
        "enable_fast_add": "Enable Fast Add Mode (for large number of files)",
        "file_count_threshold": "File Count Threshold:",
        "ui_settings": "UI Settings",
        "language_settings": "Language Settings",
        "interface_language": "Interface Language:",
        "auto_scroll_to_latest": "Auto Scroll to Latest File",
        "about": "About",
        "save_template": "Save",
        "delete_template": "Delete",
        "start_processing_files": "Start processing files...",
        "added_files_to_queue": "{0} files/folders added to queue...",
        "start_processing_batch": "Start processing first {0} files...",
        "processing_files": "Processing files... ({0} files left in queue)",
        "processing_in_progress": "Processing...",
        "files_ready": "Files are ready!",
        "operation_stopped": "Operation stopped",
        "drag_hint": "Rename files using: ",
        "rename_hint": "or",
        "rename_end_hint": "",
        "rename_skipped_keep_name": "Skipped (keep original filename)",
        "rename_skipped_no_date": "No shooting date",
        "rename_skipped_no_name": "Cannot generate new filename",
        "rename_skipped_exists": "Target file already exists"
    }
}

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
            
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()

class FileInfoCache:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
    
    def get(self, file_path):
        with self.lock:
            return self.cache.get(file_path)
    
    def set(self, file_path, info):
        with self.lock:
            self.cache[file_path] = info
    
    def remove(self, file_path):
        with self.lock:
            self.cache.pop(file_path, None)
    
    def clear(self):
        with self.lock:
            self.cache.clear()

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.template_var = ttk.StringVar(value="%Y%m%d_%H%M%S")  # 设置默认模板
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.language_var = ttk.StringVar(value="简体中文")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")
        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.show_errors_only_var = ttk.BooleanVar(value=False)
        self.fast_add_mode_var = ttk.BooleanVar(value=True)
        self.fast_add_threshold_var = ttk.IntVar(value=100)
        self.date_format = "%Y%m%d_%H%M%S"  # 设置默认日期格式
        self.stop_event = Event()
        self.renaming_in_progress = False
        self.processed_files = set()
        self.unrenamed_files = 0
        self.current_renaming_file = None
        self.skip_extensions = []
        self.exif_cache = LRUCache(1000)
        self.status_cache = LRUCache(1000)
        self.file_hash_cache = LRUCache(1000)
        self.error_cache = {}
        self._settings_cache = None
        self._update_timer = None
        self._pending_updates = set()
        self.name_conflict_var = ttk.StringVar(value="add_suffix")
        self.suffix_option_var = ttk.StringVar(value="_001")
        self.skip_extensions_var = ttk.StringVar(value="")
        self.lang = LANGUAGES[self.language_var.get()]
        self.file_queue = Queue()
        self.processing_thread = None
        self.toplevel_windows = []
        self.batch_size = 50  # 增加批处理大小到50
        self.processing_batch = False
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 300
        self.root.title("文件&照片批量重命名 QphotoRenamer 2.4 —— QwejayHuang")
        self.root.geometry("850x600")
        self.root.iconbitmap(icon_path)
        self.style = ttk.Style('litera')
        self.lock = Lock()
        self.initialize_ui()
        self.load_or_create_settings()
        self.remove_invalid_files()  # 启动后自动清理无效文件
        self.root.after(300000, self.cleanup_cache)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.file_info_cache = FileInfoCache()
        self.update_queue = queue.Queue()
        self.update_thread = None
        self.stop_update_event = threading.Event()
        
    def remove_invalid_files(self):
        """自动移除列表中已不存在的文件"""
        invalid_items = []
        for item in self.files_tree.get_children():
            file_path = self.files_tree.item(item)['values'][0]
            if not os.path.exists(file_path):
                invalid_items.append(item)
        for item in invalid_items:
            self.files_tree.delete(item)
        if invalid_items:
            self.update_file_count()

    def on_closing(self):
        """程序关闭时的清理工作"""
        try:
            # 停止所有操作
            self.stop_all_operations()
            
            # 清理缓存
            try:
                self.cleanup_cache()
            except Exception as e:
                logging.error(f"清理缓存失败: {e}")
            
            # 关闭所有子窗口
            for window in self.toplevel_windows:
                try:
                    window.destroy()
                except:
                    pass
            
            # 销毁主窗口
            self.root.destroy()
            
        except Exception as e:
            logging.error(f"关闭程序时出错: {e}")
            self.root.destroy()

    def load_or_create_settings(self):
        """加载或创建配置文件"""
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_file):
                # 创建默认配置
                config = {
                    'General': {
                        'language': 'zh_CN',
                        'prefix': '',
                        'suffix': '',
                        'skip_extensions': '.txt,.log',
                        'fast_add_threshold': '100'
                    },
                    'Template': {
                        'default_template': '{date}_{time}',
                        'template1': '{date}_{time}',
                        'template2': '{date}_{time}_{camera}',
                        'template3': '{date}_{time}_{location}',
                        'template4': '{date}_{time}_{description}',
                        'template5': '{date}_{time}_{camera}_{location}'
                    }
                }
                # 保存配置文件
                try:
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4)
                    logging.info("默认配置文件创建成功")
                except Exception as e:
                    logging.error(f"创建默认配置文件失败: {e}")
                    raise
            else:
                logging.info("配置文件已存在，加载现有配置")
            
            # 加载配置
            self.load_settings()
                
        except Exception as e:
            logging.error(f"加载或创建设置时出错: {e}")
            self.handle_error(e, "加载或创建设置")

    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                
                # 加载基本设置
                if 'General' in self.config:
                    self.language_var.set(self.config['General'].get('language', 'zh_CN'))
                    self.prefix_var.set(self.config['General'].get('prefix', ''))
                    self.suffix_var.set(self.config['General'].get('suffix', ''))
                    self.skip_extensions_var.set(self.config['General'].get('skip_extensions', '.txt,.log'))
                    self.fast_add_threshold_var.set(self.config['General'].get('fast_add_threshold', '100'))
                
                # 加载模板设置
                if 'Template' in self.config:
                    # 加载默认模板
                    default_template = self.config['Template'].get('default_template', '{date}_{time}')
                    self.template_var.set(default_template)
                    
                    # 加载用户模板列表
                    self.templates = []
                    for i in range(1, 6):  # 最多5个用户模板
                        template = self.config['Template'].get(f'template{i}')
                        if template:
                            self.templates.append(template)
                    
                    # 如果没有找到任何模板，使用默认模板
                    if not self.templates:
                        self.templates = [
                            '{date}_{time}',
                            '{date}_{time}_{camera}',
                            '{date}_{time}_{location}',
                            '{date}_{time}_{description}',
                            '{date}_{time}_{camera}_{location}'
                        ]
            
            # 加载日期设置
            if 'Date' in self.config:
                try:
                    date_basis = self.config['Date'].get('date_basis', '拍摄日期')
                    alternate_date_basis = self.config['Date'].get('alternate_date_basis', '修改日期')
                    self.date_basis_var.set(next(item['display'] for item in self.lang["date_bases"] if item['value'] == date_basis))
                    self.alternate_date_var.set(next(item['display'] for item in self.lang["alternate_dates"] if item['value'] == alternate_date_basis))
                except Exception as e:
                    logging.error(f"加载日期设置失败: {e}")
            
            # 加载文件处理设置
            if 'FileHandling' in self.config:
                try:
                    self.fast_add_mode_var.set(self.config['FileHandling'].getboolean('fast_add_mode', False))
                    self.fast_add_threshold_var.set(self.config['FileHandling'].getint('fast_add_threshold', 10))
                    name_conflict = self.config['FileHandling'].get('name_conflict', 'add_suffix')
                    self.name_conflict_var.set(next(item['display'] for item in self.lang["name_conflicts"] if item['value'] == name_conflict))
                    self.suffix_option_var.set(self.config['FileHandling'].get('suffix_option', '_001'))
                    self.auto_scroll_var.set(self.config['FileHandling'].getboolean('auto_scroll', True))
                    self.show_errors_only_var.set(self.config['FileHandling'].getboolean('show_errors_only', False))
                except Exception as e:
                    logging.error(f"加载文件处理设置失败: {e}")
                    
        except Exception as e:
            logging.error(f"加载设置失败: {e}")
            self.handle_error(e, "加载设置")

    def get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        try:
            # 规范化文件路径
            file_path = os.path.abspath(file_path)
            file_path = os.path.normpath(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return ""
                
            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                logging.error(f"无法访问文件: {file_path}，权限不足")
                return ""
                
            # 优化：仅读取文件的前8KB来计算哈希值
            with open(file_path, 'rb') as f:
                data = f.read(8192)  # 只读取前8KB
                return hashlib.md5(data).hexdigest()
        except PermissionError as e:
            logging.error(f"权限错误: {file_path}, 错误: {e}")
            return ""
        except OSError as e:
            logging.error(f"系统错误: {file_path}, 错误: {e}")
            return ""
        except Exception as e:
            logging.error(f"计算文件哈希值时出错: {file_path}, 错误: {e}")
            return ""

    def cleanup_cache(self):
        """清理过期缓存"""
        try:
            current_time = time.time()
            
            # 清理错误缓存
            expired_errors = [
                error_id for error_id, data in self.error_cache.items()
                if (current_time - data['last_time']) > 3600  # 1小时后过期
            ]
            for error_id in expired_errors:
                del self.error_cache[error_id]
                
            # 清理设置缓存
            if self._settings_cache and (current_time - self._settings_cache['timestamp']) > 300:  # 5分钟后过期
                self._settings_cache = None
                
            # 清理文件哈希缓存
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache = LRUCache(1000)
                
            # 清理EXIF缓存
            if hasattr(self, 'exif_cache'):
                self.exif_cache = LRUCache(1000)
                
            # 清理状态缓存
            if hasattr(self, 'status_cache'):
                self.status_cache = LRUCache(1000)
                
            # 强制进行垃圾回收
            gc.collect()
            
        except Exception as e:
            logging.error(f"清理缓存时出错: {e}")
            
        finally:
            # 设置下一次清理
            self.root.after(300000, self.cleanup_cache)  # 5分钟后再次清理

    @lru_cache(maxsize=1000)
    def get_exif_data(self, file_path: str) -> Optional[Dict]:
        try:
            # 检查是否需要清理缓存
            current_time = time.time()
            if current_time - self.last_cleanup_time > self.cleanup_interval:
                self.cleanup_cache()
                self.last_cleanup_time = current_time
                
            # 现有的EXIF读取逻辑
            if file_path.lower().endswith('.heic'):
                return self.get_heic_data(file_path)
            
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if not tags:
                    return None
                    
                exif_data = {}
                
                # 尝试获取拍摄日期时间
                date_time_original = None
                if 'EXIF DateTimeOriginal' in tags:
                    date_time_original = str(tags['EXIF DateTimeOriginal'])
                elif 'Image DateTime' in tags:
                    date_time_original = str(tags['Image DateTime'])
                
                if date_time_original:
                    try:
                        # 尝试多种日期格式
                        formats = [
                            '%Y:%m:%d %H:%M:%S',
                            '%Y:%m:%d %H:%M',
                            '%Y/%m/%d %H:%M:%S',
                            '%Y/%m/%d %H:%M'
                        ]
                        for fmt in formats:
                            try:
                                exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_time_original, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logging.error(f"解析EXIF日期格式失败: {file_path}, 原始日期字符串: {date_time_original}, 错误: {e}")
                
                # 获取其他EXIF信息
                for tag, value in tags.items():
                    if tag.startswith('EXIF'):
                        exif_data[tag] = str(value)
                    elif tag == 'Image Model':
                        exif_data['Model'] = str(value)
                    elif tag == 'EXIF LensModel':
                        exif_data['LensModel'] = str(value)
                    elif tag == 'EXIF ISOSpeedRatings':
                        exif_data['ISOSpeedRatings'] = str(value)
                    elif tag == 'EXIF FNumber':
                        exif_data['FNumber'] = str(value)
                    elif tag == 'EXIF ExposureTime':
                        exif_data['ExposureTime'] = str(value)
                    elif tag == 'EXIF ExifImageWidth':
                        exif_data['ImageWidth'] = str(value)
                    elif tag == 'EXIF ExifImageLength':
                        exif_data['ImageHeight'] = str(value)
                
                return exif_data
        except Exception as e:
            self.handle_error(e, f"读取EXIF数据: {file_path}")
            return None

    def handle_error(self, error: Exception, context: str):
        """处理错误，显示在状态栏"""
        error_msg = ""
        if isinstance(error, PermissionError):
            error_msg = f"权限错误: 无法访问文件: {context}\n请检查文件权限。"
        elif isinstance(error, FileNotFoundError):
            error_msg = f"文件未找到: 无法找到文件: {context}"
        elif isinstance(error, OSError):
            error_msg = f"系统错误: 操作失败: {context}\n{str(error)}"
        elif isinstance(error, ValueError):
            error_msg = f"数据错误: 无效的数据: {context}\n{str(error)}"
        else:
            error_msg = f"发生未知错误: {context}\n{str(error)}"
            
        logging.error(error_msg)
        self.update_status_bar(error_msg)

    def initialize_ui(self):
        # 主界面布局
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        
        # 日期基准选择框和备选日期基准选择框
        date_basis_frame = ttk.Frame(main_frame)
        date_basis_frame.pack(fill=ttk.X, pady=5)
        self.drag_hint_label = ttk.Label(date_basis_frame, text=self.lang["drag_hint"])
        self.drag_hint_label.pack(side=ttk.LEFT)
        self.date_basis_var = ttk.StringVar(value=self.lang["date_bases"][0]["display"])
        self.date_basis_combobox = ttk.Combobox(
            date_basis_frame,
            textvariable=self.date_basis_var,
            values=[item["display"] for item in self.lang["date_bases"]],
            state="readonly", width=15)  # 调整宽度
        self.date_basis_combobox.pack(side=ttk.LEFT, padx=5)
        self.date_basis_combobox.bind("<<ComboboxSelected>>", self.on_date_basis_selected)
        self.rename_hint_label = ttk.Label(date_basis_frame, text=self.lang["rename_hint"])
        self.rename_hint_label.pack(side=ttk.LEFT, padx=5)

        self.alternate_date_var = ttk.StringVar(value=self.lang["alternate_dates"][0]["display"])
        self.alternate_date_combobox = ttk.Combobox(
            date_basis_frame,
            textvariable=self.alternate_date_var,
            values=[item["display"] for item in self.lang["alternate_dates"]],
            state="readonly", width=15)  # 调整宽度
        self.alternate_date_combobox.pack(side=ttk.LEFT, padx=5)
        self.alternate_date_combobox.bind("<<ComboboxSelected>>", self.on_alternate_date_selected)  # 添加事件绑定
        self.rename_end_hint_label = ttk.Label(date_basis_frame, text=self.lang["rename_end_hint"])
        self.rename_end_hint_label.pack(side=ttk.LEFT, padx=5)

        # 文件列表
        columns = ('filename', 'renamed_name', 'status')
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        self.files_tree.heading('filename', text=self.lang["filename"], anchor='w')
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"], anchor='w')
        self.files_tree.heading('status', text="命名依据", anchor='w')
        self.files_tree.column('filename', anchor='w', stretch=True, width=400)
        self.files_tree.column('renamed_name', anchor='w', stretch=True, width=200)
        self.files_tree.column('status', anchor='w', width=100, minwidth=100)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=vsb.set)
        self.files_tree.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)
        vsb.pack(side=ttk.RIGHT, fill=ttk.Y)
        self.files_tree.drop_target_register(DND_FILES)
        self.files_tree.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_tree.bind('<Button-3>', self.remove_file)
        self.files_tree.bind('<Double-1>', self.open_file)
        self.files_tree.bind('<Button-1>', self.show_exif_info)
        self.files_tree.bind('<ButtonRelease-1>', self.show_omitted_info)

        # 进度条
        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=ttk.X, padx=10, pady=10)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=ttk.X, padx=10, pady=10)
        self.start_button = ttk.Button(button_frame, text=self.lang["start_renaming"], command=lambda: self.rename_photos())
        self.start_button.pack(side=ttk.LEFT, padx=5)
        self.start_button.text_key = "start_renaming"
        self.stop_button = ttk.Button(button_frame, text=self.lang["stop_renaming"], command=self.stop_all_operations, bootstyle="danger")
        self.stop_button.pack(side=ttk.LEFT, padx=5)
        self.stop_button.text_key = "stop_renaming"
        self.settings_button = ttk.Button(button_frame, text=self.lang["settings"], command=self.open_settings)
        self.settings_button.pack(side=ttk.LEFT, padx=5)
        self.settings_button.text_key = "settings"
        self.clear_button = ttk.Button(button_frame, text=self.lang["clear_list"], command=lambda: self.clear_file_list())
        self.clear_button.pack(side=ttk.LEFT, padx=5)
        self.clear_button.text_key = "clear_list"
        self.select_files_button = ttk.Button(button_frame, text=self.lang["add_files"], command=lambda: self.select_files())
        self.select_files_button.pack(side=ttk.LEFT, padx=5)
        self.select_files_button.text_key = "add_files"
        self.help_button = ttk.Button(button_frame, text=self.lang["help"], command=self.show_help)
        self.help_button.pack(side=ttk.LEFT, padx=5)
        self.help_button.text_key = "help"
        self.auto_scroll_checkbox = ttk.Checkbutton(button_frame, text=self.lang["auto_scroll"], variable=self.auto_scroll_var)
        self.auto_scroll_checkbox.pack(side=ttk.LEFT, padx=5)
        self.auto_scroll_checkbox.text_key = "auto_scroll"
        self.show_errors_only_checkbox = ttk.Checkbutton(button_frame, text=self.lang["show_errors_only"], variable=self.show_errors_only_var)
        self.show_errors_only_checkbox.pack(side=ttk.LEFT, padx=5)
        self.show_errors_only_checkbox.text_key = "show_errors_only"
        self.update_link = ttk.Label(button_frame, text=self.lang.get("check_for_updates", "反馈&检查更新"), foreground="blue", cursor="hand2")
        self.update_link.pack(side=ttk.RIGHT, padx=5)
        self.update_link.bind("<Button-1>", lambda e: self.open_update_link())
        self.update_link.text_key = "check_for_updates"
        
        # 状态栏
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)
        self.status_label = ttk.Label(self.status_bar, text=self.lang["ready"], anchor=ttk.W)
        self.status_label.pack(side=ttk.LEFT, fill=ttk.X, expand=True)
        self.status_label.text_key = "ready"
        self.file_count_label = ttk.Label(self.status_bar, text="文件总数: 0", anchor=ttk.E)
        self.file_count_label.pack(side=ttk.RIGHT, padx=10)
        self.file_count_label.text_key = "file_count"

    def on_date_basis_selected(self, event):
        """当日期基准选择改变时，更新文件列表"""
        try:
            self.remove_invalid_files()  # 切换命名依据前自动清理无效文件
            
            # 清除缓存，强制重新计算状态
            if hasattr(self, 'status_cache'):
                self.status_cache.clear()
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache.clear()
            
            # 更新文件状态和新名称
            for item in self.files_tree.get_children():
                file_path = self.files_tree.item(item)['values'][0]
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    # 如果文件不存在，尝试从新名称列获取实际路径
                    new_name = self.files_tree.item(item)['values'][1]
                    if new_name and new_name != self.lang["ready_to_rename"]:
                        directory = os.path.dirname(file_path)
                        new_path = os.path.join(directory, new_name)
                        if os.path.exists(new_path):
                            # 更新树形视图中的文件路径
                            self.files_tree.item(item, values=(new_path, new_name, self.files_tree.item(item)['values'][2]))
                            file_path = new_path
                
                exif_data = self.get_exif_data(file_path)
                
                # 检查是否有拍摄日期
                has_shooting_date = exif_data and 'DateTimeOriginalParsed' in exif_data
                
                # 强制重新计算状态
                if not has_shooting_date:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        status = self.lang["prepare_rename_keep_name"]
                    else:
                        # 直接使用备选日期选项
                        status = self.lang["prepare_rename_by"].format(alternate)
                else:
                    # 如果有拍摄日期，保持使用拍摄日期
                    status = self.lang["prepare_rename_by"].format("拍摄日期")
                
                self.files_tree.set(item, 'status', status)
                
                # 强制刷新新名称
                new_name = self.generate_new_name(file_path, exif_data)
                self.files_tree.set(item, 'renamed_name', new_name)
            
            # 更新UI
            self.update_renamed_name_column()
            self.root.update_idletasks()  # 强制刷新界面
            
        except Exception as e:
            logging.error(f"更新日期基准选择时出错: {e}")
            self.handle_error(e, "更新日期基准选择")

    def on_alternate_date_selected(self, event):
        """当备选日期选择改变时，更新文件列表"""
        try:
            self.remove_invalid_files()  # 切换命名依据前自动清理无效文件
            
            # 清除缓存，强制重新计算状态
            if hasattr(self, 'status_cache'):
                self.status_cache.clear()
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache.clear()
            
            # 更新文件状态和新名称
            for item in self.files_tree.get_children():
                file_path = self.files_tree.item(item)['values'][0]
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    # 如果文件不存在，尝试从新名称列获取实际路径
                    new_name = self.files_tree.item(item)['values'][1]
                    if new_name and new_name != self.lang["ready_to_rename"]:
                        directory = os.path.dirname(file_path)
                        new_path = os.path.join(directory, new_name)
                        if os.path.exists(new_path):
                            # 更新树形视图中的文件路径
                            self.files_tree.item(item, values=(new_path, new_name, self.files_tree.item(item)['values'][2]))
                            file_path = new_path
                
                exif_data = self.get_exif_data(file_path)
                
                # 检查是否有拍摄日期
                has_shooting_date = exif_data and 'DateTimeOriginalParsed' in exif_data
                
                # 强制重新计算状态
                if not has_shooting_date:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        status = self.lang["prepare_rename_keep_name"]
                    else:
                        # 直接使用备选日期选项
                        status = self.lang["prepare_rename_by"].format(alternate)
                else:
                    # 如果有拍摄日期，保持使用拍摄日期
                    status = self.lang["prepare_rename_by"].format("拍摄日期")
                
                self.files_tree.set(item, 'status', status)
                
                # 强制刷新新名称
                new_name = self.generate_new_name(file_path, exif_data)
                self.files_tree.set(item, 'renamed_name', new_name)
            
            # 更新UI
            self.update_renamed_name_column()
            self.root.update_idletasks()  # 强制刷新界面
            
        except Exception as e:
            logging.error(f"更新备选日期选择时出错: {e}")
            self.handle_error(e, "更新备选日期选择")

    def on_template_selected(self, event=None):
        """当选择模板时更新编辑器内容"""
        try:
            selected_template = self.template_combobox.get()
            current_template = self.template_text.get("1.0", tk.END).strip()
            
            # 如果选择的不是当前正在编辑的模板
            if selected_template != "(新模板)" and selected_template != current_template:
                # 检查是否有未保存的修改
                if self.is_modified:
                    if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                        # 如果当前是新模板且用户希望保存
                        if "(新模板)" in self.template_combobox['values'] and self.template_combobox.get() == "(新模板)":
                            # 保存新模板内容
                            if current_template and current_template not in self.templates:
                                self.templates.append(current_template)
                                # 通知用户新模板已保存
                                self.update_status_bar("新模板已保存")
                        self.save_current_template()
                
                # 现在获取并显示选择的模板
                if selected_template in self.templates:
                    # 直接更新模板文本
                    self.template_text.delete("1.0", tk.END)
                    self.template_text.insert("1.0", selected_template)
                    
                    # 更新默认模板
                    self.default_template = selected_template
                    
                    # 更新主程序的模板变量
                    if self.template_var:
                        self.template_var.set(selected_template)
                    
                    # 重置修改标志并更新保存的内容
                    self.is_modified = False
                    self.last_saved_content = selected_template
                    
                    # 立即更新预览
                    self.update_preview()
                    
                    # 更新主程序的文件列表预览
                    if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
                        self.main_app.update_renamed_name_column()
                    
                    # 更新状态
                    self.update_status_bar(f"已加载模板: {selected_template}")
                
        except Exception as e:
            error_msg = f"加载模板失败: {str(e)}"
            logging.error(error_msg)
            self.update_status_bar(error_msg)

    def generate_new_name(self, file_path, exif_data, add_suffix=True):
        try:
            file_path = os.path.abspath(os.path.normpath(file_path))
            directory = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            template = self.template_var.get()
            if not template:
                try:
                    if os.path.exists('QphotoRenamer.ini'):
                        config = configparser.ConfigParser()
                        config.read('QphotoRenamer.ini', encoding='utf-8')
                        if config.has_option('Template', 'default_template'):
                            template = config.get('Template', 'default_template')
                except Exception as e:
                    logging.error(f"加载默认模板失败: {e}")
            if not template:
                template = "{date}_{time}"
            date_basis = self.date_basis_var.get()
            date_obj = None
            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        return os.path.basename(file_path)
                    elif alternate == "修改日期":
                        date_obj = self.get_file_modification_date(file_path)
                        if not date_obj:
                            date_obj = self.get_file_creation_date(file_path)
                    elif alternate == "创建日期":
                        date_obj = self.get_file_creation_date(file_path)
                        if not date_obj:
                            date_obj = self.get_file_modification_date(file_path)
                    if not date_obj:
                        return os.path.basename(file_path)
            elif date_basis == "修改日期":
                date_obj = self.get_file_modification_date(file_path)
                if not date_obj:
                    date_obj = self.get_file_creation_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            elif date_basis == "创建日期":
                date_obj = self.get_file_creation_date(file_path)
                if not date_obj:
                    date_obj = self.get_file_modification_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            if date_obj:
                template = template.replace("{date}", date_obj.strftime("%Y%m%d"))
                template = template.replace("{time}", date_obj.strftime("%H%M%S"))
                if exif_data:
                    if 'Model' in exif_data:
                        template = template.replace("{camera}", exif_data['Model'])
                    if 'LensModel' in exif_data:
                        template = template.replace("{lens}", exif_data['LensModel'])
                    if 'ISOSpeedRatings' in exif_data:
                        template = template.replace("{iso}", exif_data['ISOSpeedRatings'])
                    if 'FNumber' in exif_data:
                        template = template.replace("{aperture}", f"f{exif_data['FNumber']}")
                    if 'ExposureTime' in exif_data:
                        template = template.replace("{shutter}", exif_data['ExposureTime'])
                    if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                        template = template.replace("{width}", exif_data['ImageWidth'])
                        template = template.replace("{height}", exif_data['ImageHeight'])
                template = template.replace("{original}", os.path.splitext(os.path.basename(file_path))[0])
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = template
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = template + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)

    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        """生成唯一文件名，避免批量重命名冲突"""
        try:
            # 确保目录路径是绝对路径
            directory = os.path.abspath(os.path.normpath(directory))
            
            # 初始化计数器
            counter = 1
            max_counter = 999  # 最大计数器值
            
            while counter <= max_counter:
                # 根据不同的后缀样式生成后缀
                if suffix_style == "_001":
                    suffix = f"_{counter:03d}"
                elif suffix_style == "-01":
                    suffix = f"-{counter:02d}"
                elif suffix_style == "_1":
                    suffix = f"_{counter}"
                else:
                    suffix = f"_{counter:03d}"
                    
                # 生成新文件名
                new_filename = f"{base_name}{suffix}{ext}"
                
                # 确保文件名不超过系统限制
                if len(new_filename) > 255:
                    # 如果文件名太长，截断基础名称
                    max_base_length = 255 - len(suffix) - len(ext)
                    base_name = base_name[:max_base_length]
                    new_filename = f"{base_name}{suffix}{ext}"
                
                # 检查完整路径是否存在
                full_path = os.path.join(directory, new_filename)
                if not os.path.exists(full_path):
                    return new_filename
                    
                counter += 1
            
            # 如果超过最大计数器，使用时间戳
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            new_filename = f"{base_name}_{timestamp}{ext}"
            
            # 最后一次检查文件名长度
            if len(new_filename) > 255:
                max_base_length = 255 - len(timestamp) - len(ext) - 1
                base_name = base_name[:max_base_length]
                new_filename = f"{base_name}_{timestamp}{ext}"
            
            return new_filename
            
        except Exception as e:
            logging.error(f"生成唯一文件名失败: {e}")
            # 发生错误时返回带时间戳的文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            return f"{base_name}_{timestamp}{ext}"

    def open_settings(self):
        """打开设置窗口"""
        try:
            settings_window = Toplevel(self.root)
            settings_window.title(self.lang["settings"])
            settings_window.geometry("660x620")
            settings_window.resizable(True, True)
            settings_window.transient(self.root)
            settings_window.grab_set()
            self.toplevel_windows.append(settings_window)
            
            def on_close():
                # 检查模板编辑器是否有未保存的修改
                if hasattr(self, 'template_editor') and self.template_editor.has_unsaved_changes():
                    if messagebox.askyesno("未保存的修改", "模板编辑器中有未保存的修改，是否保存？"):
                        self.template_editor.save_current_template()
                
                if settings_window in self.toplevel_windows:
                    self.toplevel_windows.remove(settings_window)
                settings_window.destroy()
                
            settings_window.protocol("WM_DELETE_WINDOW", on_close)
            
            # 创建主Notebook
            notebook = ttk.Notebook(settings_window)
            notebook.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            
            # --------------------
            # 重命名模板标签页
            # --------------------
            template_frame = ttk.Frame(notebook)
            notebook.add(template_frame, text=self.lang.get("rename_pattern_settings", "重命名格式设置"))
            
            # 添加模板编辑器，传入当前语言设置和main_app
            template_editor = TemplateEditor(template_frame, self.template_var, lang=self.lang, main_app=self)
            template_editor.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            self.template_editor = template_editor  # 保存引用以便在关闭时访问
            
            # --------------------
            # 日期设置标签页
            # --------------------
            date_frame = ttk.Frame(notebook)
            notebook.add(date_frame, text=self.lang.get("date_settings", "日期设置"))
            
            # 日期基准设置
            date_basis_frame = ttk.LabelFrame(date_frame, text=self.lang.get("date_basis", "日期基准"))
            date_basis_frame.pack(fill=ttk.X, padx=10, pady=5)
            
            date_basis_select_frame = ttk.Frame(date_basis_frame)
            date_basis_select_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(date_basis_select_frame, text=self.lang.get("preferred_date", "首选日期:")).pack(side=ttk.LEFT)
            date_basis_combobox = ttk.Combobox(date_basis_select_frame, 
                                             textvariable=self.date_basis_var,
                                             values=[item['display'] for item in self.lang["date_bases"]],
                                             state="readonly")
            date_basis_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            alternate_date_select_frame = ttk.Frame(date_basis_frame)
            alternate_date_select_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(alternate_date_select_frame, text=self.lang.get("alternate_date", "备选日期:")).pack(side=ttk.LEFT)
            alternate_date_combobox = ttk.Combobox(alternate_date_select_frame, 
                                                 textvariable=self.alternate_date_var,
                                                 values=[item['display'] for item in self.lang["alternate_dates"]],
                                                 state="readonly")
            alternate_date_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            # --------------------
            # 文件处理标签页
            # --------------------
            file_frame = ttk.Frame(notebook)
            notebook.add(file_frame, text=self.lang.get("file_handling_settings", "文件处理设置"))
            
            # 文件过滤设置
            filter_frame = ttk.LabelFrame(file_frame, text=self.lang.get("file_filter", "文件过滤"))
            filter_frame.pack(fill=ttk.X, padx=10, pady=5)
            
            skip_extensions_frame = ttk.Frame(filter_frame)
            skip_extensions_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(skip_extensions_frame, text=self.lang.get("skip_extensions", "跳过的扩展名:")).pack(side=ttk.LEFT)
            skip_extensions_entry = ttk.Entry(skip_extensions_frame, textvariable=self.skip_extensions_var)
            skip_extensions_entry.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            # 冲突处理设置
            conflict_frame = ttk.LabelFrame(file_frame, text=self.lang.get("name_conflict_prompt", "名称冲突处理"))
            conflict_frame.pack(fill=ttk.X, padx=10, pady=5)
            
            conflict_select_frame = ttk.Frame(conflict_frame)
            conflict_select_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(conflict_select_frame, text=self.lang.get("conflict_handling", "冲突处理:")).pack(side=ttk.LEFT)
            name_conflict_combobox = ttk.Combobox(conflict_select_frame, 
                                                textvariable=self.name_conflict_var,
                                                values=[item['display'] for item in self.lang["name_conflicts"]],
                                                state="readonly")
            name_conflict_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            suffix_option_frame = ttk.Frame(conflict_frame)
            suffix_option_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(suffix_option_frame, text=self.lang.get("suffix_format", "后缀格式:")).pack(side=ttk.LEFT)
            suffix_option_combobox = ttk.Combobox(suffix_option_frame, 
                                                textvariable=self.suffix_option_var,
                                                values=["_001", "_1", " (1)"],
                                                state="readonly" if self.name_conflict_var.get() == "增加后缀" else "disabled")
            suffix_option_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            # 性能优化设置
            performance_frame = ttk.LabelFrame(file_frame, text=self.lang.get("performance_optimization", "性能优化"))
            performance_frame.pack(fill=ttk.X, padx=10, pady=5)
            
            fast_add_checkbox = ttk.Checkbutton(performance_frame, 
                                             text=self.lang.get("enable_fast_add", "启用快速添加模式（适用于大量文件）"), 
                                             variable=self.fast_add_mode_var,
                                             command=lambda: self.toggle_fast_add_threshold_entry(threshold_entry))
            fast_add_checkbox.pack(anchor=ttk.W, padx=5, pady=5)
            
            threshold_frame = ttk.Frame(performance_frame)
            threshold_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(threshold_frame, text=self.lang.get("file_count_threshold", "文件数量阈值:")).pack(side=ttk.LEFT)
            
            threshold_validate = (settings_window.register(self.validate_threshold_input), '%P')
            threshold_entry = ttk.Entry(threshold_frame, 
                                     textvariable=self.fast_add_threshold_var, 
                                     width=5,
                                     validate="key", 
                                     validatecommand=threshold_validate,
                                     state="normal" if self.fast_add_mode_var.get() else "disabled")
            threshold_entry.pack(side=ttk.LEFT, padx=5)
            
            # --------------------
            # 界面设置标签页
            # --------------------
            ui_frame = ttk.Frame(notebook)
            notebook.add(ui_frame, text=self.lang.get("ui_settings", "界面设置"))
            
            # 语言设置
            language_frame = ttk.LabelFrame(ui_frame, text=self.lang.get("language_settings", "语言设置"))
            language_frame.pack(fill=ttk.X, padx=10, pady=5)
            ttk.Label(language_frame, text=self.lang.get("interface_language", "界面语言:")).pack(side=ttk.LEFT, padx=5)
            language_combobox = ttk.Combobox(language_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
            language_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
            
            # 其他界面设置
            other_frame = ttk.LabelFrame(ui_frame, text=self.lang.get("other_settings", "其他设置"))
            other_frame.pack(fill=ttk.X, padx=10, pady=5)
            
            auto_scroll_checkbox = ttk.Checkbutton(other_frame, 
                                             text=self.lang.get("auto_scroll_to_latest", "自动滚动到最新文件"), 
                                             variable=self.auto_scroll_var)
            auto_scroll_checkbox.pack(anchor=ttk.W, padx=5, pady=5)
            
            show_errors_checkbox = ttk.Checkbutton(other_frame, 
                                             text=self.lang.get("show_errors_only", "仅显示错误信息"), 
                                             variable=self.show_errors_only_var)
            show_errors_checkbox.pack(anchor=ttk.W, padx=5, pady=5)
            
            # 关于标签页
            about_frame = ttk.Frame(notebook)
            notebook.add(about_frame, text=self.lang.get("about", "关于"))
            
            # 软件信息
            about_text = """
QphotoRenamer 2.4

一个简单易用的文件与照片批量重命名工具

功能特点：
• 支持拖拽文件/文件夹
• 支持多种日期格式
• 支持EXIF信息提取
• 支持HEIC格式
• 支持多语言
• 支持快速添加模式
• 支持文件名冲突处理

作者：QwejayHuang
GitHub：https://github.com/Qwejay/QphotoRenamer

使用说明：
1. 将文件或文件夹拖放到列表中
2. 设置重命名格式和选项
3. 点击"开始重命名"按钮

注意事项：
• 请确保对目标文件夹有写入权限
• 建议在重命名前备份重要文件
• 快速添加模式可能会影响性能
"""
            about_label = ttk.Label(about_frame, text=about_text, justify=ttk.LEFT)
            about_label.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            
            # 保存设置按钮
            save_button = ttk.Button(settings_window, text=self.lang["save_settings"], 
                               command=lambda: self.save_settings(self.template_var.get(), 
                                                               self.language_var.get(),
                                                               self.prefix_var.get(),  # 使用prefix_var的值
                                                               self.suffix_var.get(),  # 使用suffix_var的值
                                                               self.skip_extensions_var.get(),
                                                               settings_window))
            save_button.pack(pady=10)
            save_button.text_key = "save_settings"
            
            # 调整列权重
            template_frame.columnconfigure(0, weight=1)
            date_frame.columnconfigure(0, weight=1)
            file_frame.columnconfigure(0, weight=1)
            ui_frame.columnconfigure(0, weight=1)
            about_frame.columnconfigure(0, weight=1)
            
            # 为所有Label/Button/Checkbutton/Combobox加text_key属性
            for widget in settings_window.winfo_children():
                if isinstance(widget, (ttk.Label, ttk.Button, ttk.Checkbutton)):
                    widget.text_key = widget.cget("text")
            
        except Exception as e:
            logging.error(f"打开设置窗口时出错: {e}")
            self.handle_error(e, "打开设置窗口")

    def toggle_suffix_option_edit(self, suffix_option_combobox):
        """根据命名冲突处理方式启用或禁用后缀选项"""
        logging.info(f"切换后缀选项编辑状态, 当前name_conflict_var值: {self.name_conflict_var.get()}")
        logging.info(f"当前语言'增加后缀'对应的文本: {self.lang['add_suffix_option']}")
        # 检查命名冲突值是否匹配当前语言中的"增加后缀"文本
        add_suffix_value = self.lang["add_suffix_option"]
        if self.name_conflict_var.get() == add_suffix_value or self.name_conflict_var.get() == "增加后缀":
            logging.info("启用后缀选项编辑")
            suffix_option_combobox.config(state="normal")
        else:
            logging.info("禁用后缀选项编辑")
            suffix_option_combobox.config(state="disabled")

    def toggle_fast_add_threshold_entry(self, entry_widget):
        """根据快速添加模式勾选框的状态启用或禁用文件数量阈值输入框"""
        if self.fast_add_mode_var.get():
            entry_widget.config(state="normal")
        else:
            entry_widget.config(state="disabled")

    def validate_threshold_input(self, value):
        """验证文件数量阈值输入是否为 1 到 1000 的数字"""
        if value.isdigit():
            return 1 <= int(value) <= 1000  # 增加最大阈值到1000
        return False

    def save_settings(self, template, language, prefix, suffix, skip_extensions_input, settings_window):
        """保存设置到配置文件"""
        try:
            config = configparser.ConfigParser(interpolation=None)
            if os.path.exists("QphotoRenamer.ini"):
                config.read("QphotoRenamer.ini", encoding="utf-8")
            
            # 更新General部分
            if 'General' not in config:
                config['General'] = {}
            
            config['General']['language'] = language
            config['General']['template'] = template
            config['General']['prefix'] = prefix
            config['General']['suffix'] = suffix
            config['General']['skip_extensions'] = skip_extensions_input
            
            # 保存配置文件
            with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
                config.write(f)
            
            # 应用设置
            self._apply_settings(config)
            
            # 关闭设置窗口
            settings_window.destroy()
            
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def fix_config_encoding(self, config: Dict):
        """修复配置文件中的编码问题（只支持INI格式）"""
        # 此方法已被删除，不再使用
        pass

    def _apply_settings(self, config: Dict):
        """应用设置到界面"""
        if 'Settings' in config:
            settings = config['Settings']
            self.template_var.set(settings.get('template', ''))
            self.language_var.set(settings.get('language', '简体中文'))
            self.prefix_var.set(settings.get('prefix', ''))
            self.suffix_var.set(settings.get('suffix', ''))
            self.skip_extensions = settings.get('skip_extensions', '').split()
            self.skip_extensions_var.set(" ".join([ext[1:] for ext in self.skip_extensions]))
            self.set_language(self.language_var.get())

    def update_file_count(self):
        """更新状态栏右侧的文件总数"""
        file_count = len(self.files_tree.get_children())
        self.file_count_label.config(text=self.lang["file_count"].format(file_count))

    def select_files(self):
        file_paths = filedialog.askopenfilenames()
        self.add_files_to_queue(file_paths)

    def on_drop(self, event):
        paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
        self.add_files_to_queue(paths)

    def add_files_to_queue(self, paths):
        """添加文件到队列"""
        try:
            # 规范化所有文件路径
            normalized_paths = []
            for path in paths:
                # 转换为绝对路径
                abs_path = os.path.abspath(path)
                # 规范化路径
                norm_path = os.path.normpath(abs_path)
                normalized_paths.append(norm_path)
            
            # 禁用开始按钮，启用停止按钮
            self.start_button.config(state=ttk.DISABLED)
            self.stop_button.config(state=ttk.NORMAL)
            
            # 重置停止事件
            self.stop_event.clear()
            
            # 清空文件队列
            while not self.file_queue.empty():
                self.file_queue.get()
            
            # 添加文件到队列
            for path in normalized_paths:
                if os.path.isfile(path):
                    self.file_queue.put((path, 'file'))
                elif os.path.isdir(path):
                    self.file_queue.put((path, 'directory'))
            
            # 启动处理线程
            if not self.processing_thread or not self.processing_thread.is_alive():
                self.processing_thread = Thread(target=self.process_files_from_queue)
                self.processing_thread.start()
            
            # 更新状态栏
            self.update_status_bar("processing_in_progress")
            
        except Exception as e:
            logging.error(f"添加文件到队列时出错: {e}")
            self.handle_error(e, "添加文件到队列")
            # 恢复按钮状态
            self.start_button.config(state=ttk.NORMAL)
            self.stop_button.config(state=ttk.DISABLED)

    def process_files_from_queue(self):
        """处理文件队列中的文件"""
        try:
            while not self.file_queue.empty() and not self.stop_event.is_set():
                path, path_type = self.file_queue.get()
                
                if path_type == 'file':
                    # 检查文件是否已存在
                    is_duplicate = False
                    for item in self.files_tree.get_children():
                        current_path = self.files_tree.item(item)['values'][0]
                        if path == current_path:
                            is_duplicate = True
                            break
                            
                    if not is_duplicate:
                        # 添加文件到列表
                        self.add_file_to_list(path)
                        
                elif path_type == 'directory':
                    # 处理目录
                    self.process_directory(path)
                    
                # 更新状态栏
                self.root.after(0, lambda: self.update_status_bar("processing_files", self.file_queue.qsize()))
                
            # 所有文件处理完成后
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.update_status_bar("files_ready"))
                # 重新启用开始按钮
                self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
                # 禁用停止按钮
                self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))
                
        except Exception as e:
            logging.error(f"处理文件队列时出错: {e}")
            self.handle_error(e, "处理文件队列")
            # 发生错误时也要重新启用开始按钮
            self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))

    def process_directory(self, dir_path: str):
        """处理目录，使用生成器减少内存使用"""
        try:
            file_count = 0
            max_files_per_batch = 200  # 增加每批次处理的文件数到200
            file_batch = []
            
            for root, _, files in os.walk(dir_path):
                # 检查是否设置了停止事件
                if self.stop_event.is_set():
                    return
                
                for file in files:
                    # 再次检查是否设置了停止事件
                    if self.stop_event.is_set():
                        return
                    
                    file_path = os.path.join(root, file)
                    file_batch.append(file_path)
                    file_count += 1
                    
                    # 当收集到足够数量的文件时，将它们添加到队列中批量处理
                    if len(file_batch) >= max_files_per_batch:
                        for path in file_batch:
                            self.file_queue.put((path, 'file'))
                        file_batch = []
                        
                        # 更新状态栏，显示处理进度
                        self.root.after(0, lambda count=file_count: self.update_status_bar("added_files_to_queue", count))
                        
                        # 允许UI更新，避免卡顿
                        self.root.update_idletasks()
            
            # 处理剩余的文件
            for path in file_batch:
                if self.stop_event.is_set():
                    return
                self.file_queue.put((path, 'file'))
            
            # 最终更新状态栏
            self.root.after(0, lambda count=file_count: self.update_status_bar("added_files_to_queue", count))
            
        except Exception as e:
            logging.error(f"处理目录时出错: {dir_path}, 错误: {e}")
            self.handle_error(e, f"处理目录: {dir_path}")

    def schedule_ui_update(self):
        """调度UI更新"""
        if self._update_timer is None:
            self._update_timer = self.root.after(100, self.process_ui_updates)

    def process_ui_updates(self):
        """处理待处理的UI更新"""
        try:
            if 'update_file_count' in self._pending_updates:
                self.root.after(0, self.update_file_count)
                self._pending_updates.remove('update_file_count')
                
            if 'update_status' in self._pending_updates:
                self.root.after(0, lambda: self.update_status_bar("processing_in_progress"))
                self._pending_updates.remove('update_status')
                
            if self._pending_updates:
                self._update_timer = self.root.after(100, self.process_ui_updates)
            else:
                self._update_timer = None
        except Exception as e:
            logging.error(f"处理UI更新时出错: {e}")
            self.handle_error(e, "处理UI更新")

    def add_file_to_list(self, file_path):
        """添加文件到列表，使用线程安全的方式更新UI"""
        try:
            # 先检查文件是否已存在
            for item in self.files_tree.get_children():
                if file_path == self.files_tree.item(item, 'values')[0]:
                    logging.info(f"文件已存在，跳过添加: {file_path}")
                    return

            # 获取文件状态和新名称
            file_count = len(self.files_tree.get_children())
            
            # 如果启用了快速添加模式且文件数量超过阈值，或者处理的文件总数超过100
            if self.fast_add_mode_var.get() and (file_count >= self.fast_add_threshold_var.get() or len(self.files_tree.get_children()) > 100):
                status = self.lang["ready_to_rename"]  # 直接标记为"待重命名"
                new_name = ""  # 在新名称列中显示占位符
            else:
                # 优化：快速检查文件后缀决定是否读取EXIF
                ext = os.path.splitext(file_path)[1].lower()
                status = ""
                new_name = ""
                
                try:
                    # 获取EXIF数据
                    exif_data = None
                    if ext in SUPPORTED_IMAGE_FORMATS:
                        if ext == '.heic':
                            exif_data = self.get_heic_data(file_path) 
                        else:
                            exif_data = self.get_exif_data(file_path)
                    elif ext in ['.mov', '.mp4', '.avi', '.mkv']:
                        # 对于视频文件，尝试获取媒体创建日期
                        date_obj = self.get_video_creation_date(file_path)
                        if date_obj:
                            exif_data = {'DateTimeOriginalParsed': date_obj}
                    
                    # 生成新名称和状态
                    if exif_data:
                        status = self.detect_file_status(file_path, exif_data)
                        new_name = self.generate_new_name(file_path, exif_data)
                    else:
                        # 如果没有获取到EXIF数据，使用备用日期
                        status = self.lang["ready_to_rename"]
                        new_name = self.generate_new_name(file_path, None)
                        
                except Exception as e:
                    logging.error(f"读取文件信息失败: {file_path}, 错误: {e}")
                    self.handle_error(e, f"读取文件信息: {file_path}")
                    status = self.lang["ready_to_rename"]
                    new_name = os.path.basename(file_path)

            # 使用 after 方法在主线程中更新 UI
            values = (file_path, new_name, status)
            basename = os.path.basename(file_path)
            
            def update_ui():
                try:
                    self.status_label.config(text=f"正在加载: {basename}")
                    self.files_tree.insert('', 'end', values=values)
                    if self.auto_scroll_var.get() and self.files_tree.get_children():
                        self.files_tree.see(self.files_tree.get_children()[-1])
                    self.update_file_count()  # 更新文件总数
                except Exception as e:
                    logging.error(f"更新UI时出错: {e}")
                    self.handle_error(e, "更新UI")

            self.root.after(0, update_ui)
            
        except Exception as e:
            logging.error(f"添加文件到列表时出错: {file_path}, 错误: {e}")
            self.handle_error(e, f"添加文件到列表: {file_path}")

    def update_renamed_name_column(self):
        self.remove_invalid_files()  # 刷新前自动清理无效文件
        for item in self.files_tree.get_children():
            file_path = self.files_tree.item(item)['values'][0]
            exif_data = None
            if file_path.lower().endswith('.heic'):
                exif_data = self.get_heic_data(file_path)
            elif file_path.lower().endswith(tuple(SUPPORTED_IMAGE_FORMATS)):
                exif_data = self.get_exif_data(file_path)
            elif file_path.lower().endswith(('.mov', '.mp4', '.avi', '.mkv')):
                date_obj = self.get_video_creation_date(file_path)
                if date_obj:
                    exif_data = {'DateTimeOriginalParsed': date_obj}
            new_name = self.generate_new_name(file_path, exif_data)
            self.files_tree.set(item, 'renamed_name', new_name)

    def set_language(self, language):
        """设置界面语言"""
        self.lang = LANGUAGES[language]
        self.language_var.set(language)
        self.update_status_bar("ready")

        def update_widget_text(widget):
            if hasattr(widget, 'text_key'):
                key = widget.text_key
                if key in self.lang:
                    widget.config(text=self.lang[key])
            for child in widget.winfo_children():
                update_widget_text(child)

        update_widget_text(self.root)
        self.root.title(self.lang["window_title"])
        self.files_tree.heading('filename', text=self.lang["filename"])
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"])
        self.files_tree.heading('status', text="命名依据")
        self.update_file_count()
        self.update_renamed_name_column()
        # 同步刷新下拉框内容和选中项及提示语
        self.date_basis_combobox["values"] = [item["display"] for item in self.lang["date_bases"]]
        self.alternate_date_combobox["values"] = [item["display"] for item in self.lang["alternate_dates"]]
        self.date_basis_var.set(self.lang["date_bases"][0]["display"])
        self.alternate_date_var.set(self.lang["alternate_dates"][0]["display"])
        self.drag_hint_label.config(text=self.lang["drag_hint"])
        self.rename_hint_label.config(text=self.lang["rename_hint"])
        self.alternate_date_combobox.config(state="readonly")
        self.rename_end_hint_label.config(text=self.lang["rename_end_hint"])

    def rename_photos(self):
        """启动重命名线程，并在操作期间禁用按钮，结束后恢复"""
        # 重置停止事件
        self.stop_event.clear()
        self.renaming_in_progress = True
        self.start_button.config(state=ttk.DISABLED)
        self.stop_button.config(state=ttk.NORMAL)
        Thread(target=self.rename_photos_thread).start()

    def is_already_renamed(self, filename, template, suffix_style, file_path):
        """判断文件名是否已经符合当前模板+后缀规则，并检查日期基准"""
        try:
            # 获取当前日期基准
            current_date_basis = self.date_basis_var.get()
            
            # 从文件名中提取日期部分
            date_match = re.match(r"(\d{8})_(\d{6})", filename)
            if not date_match:
                return False
                
            file_date = date_match.group(1)
            file_time = date_match.group(2)
            
            # 获取文件的各个日期
            exif_data = self.get_exif_data(file_path)
            
            # 根据当前日期基准检查文件名是否匹配
            if current_date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    exif_date = exif_data['DateTimeOriginalParsed'].strftime("%Y%m%d")
                    exif_time = exif_data['DateTimeOriginalParsed'].strftime("%H%M%S")
                    if file_date != exif_date or file_time != exif_time:
                        return False
            elif current_date_basis == "修改日期":
                mod_date = self.get_file_modification_date(file_path)
                if mod_date:
                    mod_date_str = mod_date.strftime("%Y%m%d")
                    mod_time_str = mod_date.strftime("%H%M%S")
                    if file_date != mod_date_str or file_time != mod_time_str:
                        return False
            elif current_date_basis == "创建日期":
                create_date = self.get_file_creation_date(file_path)
                if create_date:
                    create_date_str = create_date.strftime("%Y%m%d")
                    create_time_str = create_date.strftime("%H%M%S")
                    if file_date != create_date_str or file_time != create_time_str:
                        return False
            
            # 检查后缀格式
            if suffix_style == "_001":
                suffix_regex = r"_\d{3}"
            elif suffix_style == "-01":
                suffix_regex = r"-\d{2}"
            elif suffix_style == "_1":
                suffix_regex = r"_\d+"
            else:
                suffix_regex = r"_\d{3}"
                
            ext_regex = r"\.[a-zA-Z0-9]+$"
            pattern = f"^{file_date}_{file_time}{suffix_regex}{ext_regex}"
            return re.match(pattern, filename) is not None
            
        except Exception as e:
            logging.error(f"判断文件名格式失败: {filename}, 错误: {e}")
            return False

    def rename_photos_thread(self):
        """重命名照片的线程函数，结束后恢复按钮"""
        try:
            total_files = len(self.files_tree.get_children())
            renamed_count = 0
            error_count = 0
            skipped_count = 0
            for item in self.files_tree.get_children():
                if self.stop_event.is_set():
                    break
                file_path = self.files_tree.item(item)['values'][0]
                try:
                    success, result = self.rename_photo(file_path, item)
                    if success:
                        renamed_count += 1
                        self.update_status_bar("renaming_success", renamed_count, total_files)
                    else:
                        error_count += 1
                        logging.error(f"重命名文件失败: {file_path}, 错误: {result}")
                except Exception as e:
                    error_count += 1
                    self.handle_error(e, f"重命名文件失败: {file_path}")
            if not self.stop_event.is_set():
                if error_count > 0:
                    self.update_status_bar("renaming_complete_with_errors", renamed_count, error_count, skipped_count)
                else:
                    self.update_status_bar("renaming_complete", renamed_count, skipped_count)
        except Exception as e:
            self.handle_error(e, "重命名过程发生错误")
        finally:
            self.renaming_in_progress = False
            self.stop_event.set()
            self.update_status_bar("ready")
            self.start_button.config(state=ttk.NORMAL)
            self.stop_button.config(state=ttk.DISABLED)

    def sanitize_filename(self, name):
        """过滤文件名中的非法字符并限制长度"""
        illegal_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\0']
        for char in illegal_chars:
            name = name.replace(char, '-')
        
        max_length = 255
        if len(name) > max_length:
            name = name[:max_length-5] + name[-5:]
        
        name = name.strip().rstrip('.')
        return name

    def generate_new_name(self, file_path, exif_data, add_suffix=True):
        try:
            file_path = os.path.abspath(os.path.normpath(file_path))
            directory = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            template = self.template_var.get()
            if not template:
                try:
                    if os.path.exists('QphotoRenamer.ini'):
                        config = configparser.ConfigParser()
                        config.read('QphotoRenamer.ini', encoding='utf-8')
                        if config.has_option('Template', 'default_template'):
                            template = config.get('Template', 'default_template')
                except Exception as e:
                    logging.error(f"加载默认模板失败: {e}")
            if not template:
                template = "{date}_{time}"
            date_basis = self.date_basis_var.get()
            date_obj = None
            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        return os.path.basename(file_path)
                    elif alternate == "修改日期":
                        date_obj = self.get_file_modification_date(file_path)
                        if not date_obj:
                            date_obj = self.get_file_creation_date(file_path)
                    elif alternate == "创建日期":
                        date_obj = self.get_file_creation_date(file_path)
                        if not date_obj:
                            date_obj = self.get_file_modification_date(file_path)
                    if not date_obj:
                        return os.path.basename(file_path)
            elif date_basis == "修改日期":
                date_obj = self.get_file_modification_date(file_path)
                if not date_obj:
                    date_obj = self.get_file_creation_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            elif date_basis == "创建日期":
                date_obj = self.get_file_creation_date(file_path)
                if not date_obj:
                    date_obj = self.get_file_modification_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            if date_obj:
                template = template.replace("{date}", date_obj.strftime("%Y%m%d"))
                template = template.replace("{time}", date_obj.strftime("%H%M%S"))
                if exif_data:
                    if 'Model' in exif_data:
                        template = template.replace("{camera}", exif_data['Model'])
                    if 'LensModel' in exif_data:
                        template = template.replace("{lens}", exif_data['LensModel'])
                    if 'ISOSpeedRatings' in exif_data:
                        template = template.replace("{iso}", exif_data['ISOSpeedRatings'])
                    if 'FNumber' in exif_data:
                        template = template.replace("{aperture}", f"f{exif_data['FNumber']}")
                    if 'ExposureTime' in exif_data:
                        template = template.replace("{shutter}", exif_data['ExposureTime'])
                    if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                        template = template.replace("{width}", exif_data['ImageWidth'])
                        template = template.replace("{height}", exif_data['ImageHeight'])
                template = template.replace("{original}", os.path.splitext(os.path.basename(file_path))[0])
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = template
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = template + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)

    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        """生成唯一文件名，避免批量重命名冲突"""
        try:
            # 确保目录路径是绝对路径
            directory = os.path.abspath(os.path.normpath(directory))
            
            # 初始化计数器
            counter = 1
            max_counter = 999  # 最大计数器值
            
            while counter <= max_counter:
                # 根据不同的后缀样式生成后缀
                if suffix_style == "_001":
                    suffix = f"_{counter:03d}"
                elif suffix_style == "-01":
                    suffix = f"-{counter:02d}"
                elif suffix_style == "_1":
                    suffix = f"_{counter}"
                else:
                    suffix = f"_{counter:03d}"
                    
                # 生成新文件名
                new_filename = f"{base_name}{suffix}{ext}"
                
                # 确保文件名不超过系统限制
                if len(new_filename) > 255:
                    # 如果文件名太长，截断基础名称
                    max_base_length = 255 - len(suffix) - len(ext)
                    base_name = base_name[:max_base_length]
                    new_filename = f"{base_name}{suffix}{ext}"
                
                # 检查完整路径是否存在
                full_path = os.path.join(directory, new_filename)
                if not os.path.exists(full_path):
                    return new_filename
                    
                counter += 1
            
            # 如果超过最大计数器，使用时间戳
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            new_filename = f"{base_name}_{timestamp}{ext}"
            
            # 最后一次检查文件名长度
            if len(new_filename) > 255:
                max_base_length = 255 - len(timestamp) - len(ext) - 1
                base_name = base_name[:max_base_length]
                new_filename = f"{base_name}_{timestamp}{ext}"
            
            return new_filename
            
        except Exception as e:
            logging.error(f"生成唯一文件名失败: {e}")
            # 发生错误时返回带时间戳的文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            return f"{base_name}_{timestamp}{ext}"

    def update_caches_on_rename(self, old_path, new_path):
        """重命名后同步所有缓存key，保持界面和数据一致"""
        try:
            # 更新 file_info_cache
            info = self.file_info_cache.get(old_path)
            if info:
                # 重新获取文件信息以确保数据是最新的
                new_info = self.cache_file_info(new_path)
                if new_info:
                    self.file_info_cache.set(new_path, new_info)
                self.file_info_cache.remove(old_path)
            
            # 更新 exif_cache
            exif = self.exif_cache.get(old_path)
            if exif is not None:
                self.exif_cache.put(new_path, exif)
                self.exif_cache.put(old_path, None)
            
            # 更新 status_cache
            status = self.status_cache.get(old_path)
            if status is not None:
                self.status_cache.put(new_path, status)
                self.status_cache.put(old_path, None)
            
            # 更新 file_hash_cache
            old_hash = self.get_file_hash(old_path)
            new_hash = self.get_file_hash(new_path)
            if old_hash:
                val = self.file_hash_cache.get(old_hash)
                if val is not None:
                    self.file_hash_cache.put(new_hash, val)
                    self.file_hash_cache.put(old_hash, None)
        except Exception as e:
            logging.error(f"更新缓存失败: {old_path} -> {new_path}, 错误: {e}")

    def safe_rename_file(self, source_path: str, target_path: str) -> bool:
        """安全地重命名文件，保留原始文件的创建日期和修改日期"""
        try:
            import shutil
            
            # 使用shutil.copy2来复制文件，这会保留所有元数据
            shutil.copy2(source_path, target_path)
            
            # 删除原始文件
            os.remove(source_path)
            
            return True
            
        except Exception as e:
            logging.error(f"重命名文件失败: {source_path} -> {target_path}, 错误: {e}")
            return False

    def rename_photo(self, file_path: str, item: str) -> tuple:
        try:
            # 获取文件信息
            exif_data = self.get_exif_data(file_path)
            date_basis = self.date_basis_var.get()
            date_obj = None

            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        return True, os.path.basename(file_path)
                    elif alternate == "修改日期":
                        date_obj = self.get_cached_or_real_modification_date(file_path)
                        if not date_obj:
                            date_obj = self.get_cached_or_real_creation_date(file_path)
                    elif alternate == "创建日期":
                        date_obj = self.get_cached_or_real_creation_date(file_path)
                        if not date_obj:
                            date_obj = self.get_cached_or_real_modification_date(file_path)
                    
                    if not date_obj:
                        return True, os.path.basename(file_path)
            elif date_basis == "修改日期":
                date_obj = self.get_cached_or_real_modification_date(file_path)
                if not date_obj:
                    date_obj = self.get_cached_or_real_creation_date(file_path)
                if not date_obj:
                    return False, self.lang["rename_skipped_no_date"]
            elif date_basis == "创建日期":
                date_obj = self.get_cached_or_real_creation_date(file_path)
                if not date_obj:
                    date_obj = self.get_cached_or_real_modification_date(file_path)
                if not date_obj:
                    return False, self.lang["rename_skipped_no_date"]

            # 生成新名称
            new_name = self.generate_new_name(file_path, exif_data)
            if not new_name:
                return False, self.lang["rename_skipped_no_name"]

            # 重命名文件
            directory = os.path.dirname(file_path)
            new_path = os.path.join(directory, new_name)
            
            # 检查目标文件是否已存在
            if os.path.exists(new_path):
                return False, self.lang["rename_skipped_exists"]
            
            # 执行重命名
            if self.safe_rename_file(file_path, new_path):
                # 更新缓存
                self.update_caches_on_rename(file_path, new_path)
                return True, new_path
            else:
                return False, self.lang["rename_failed"]
                
        except Exception as e:
            logging.error(f"重命名文件失败: {file_path}, 错误: {e}")
            return False, str(e)

    def get_heic_data(self, file_path):
        """获取 HEIC 文件的 EXIF 信息，并缓存结果"""
        # 检查缓存
        cached_data = self.exif_cache.get(file_path)
        if cached_data:
            return cached_data

        # 优化：对于HEIC文件，也先检查文件名是否已包含日期格式
        filename = os.path.basename(file_path)
        for date_format in COMMON_DATE_FORMATS:
            try:
                date_pattern = date_format.replace('%Y', r'(\d{4})').replace('%m', r'(\d{2})').replace('%d', r'(\d{2})')
                date_pattern = date_pattern.replace('%H', r'(\d{2})').replace('%M', r'(\d{2})').replace('%S', r'(\d{2})')
                
                if re.match(date_pattern, os.path.splitext(filename)[0]):
                    return None
            except:
                pass

        try:
            heif_file = pillow_heif.read_heif(file_path)
            if 'exif' not in heif_file.info:
                # 如果没有EXIF信息，缓存空结果并返回
                self.exif_cache.put(file_path, {})
                return {}
                
            exif_dict = piexif.load(heif_file.info['exif'])
            exif_data = {}
            if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                try:
                    date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                    
                    # 修复：处理包含"上午"/"下午"等中文时间格式的情况
                    date_str = date_str.replace("上午", "").replace("下午", "").strip()
                    
                    # 尝试多种日期格式
                    try:
                        exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        # 尝试其他可能的格式
                        formats = ['%Y:%m:%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M']
                        for fmt in formats:
                            try:
                                exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                    
                    # 获取到拍摄日期后就缓存并返回
                    self.exif_cache.put(file_path, exif_data)
                    return exif_data
                except Exception as e:
                    logging.error(f"解析HEIC日期格式失败: {file_path}, 原始日期字符串: {date_str}, 错误: {e}")
                    # 尝试从文件名获取日期
                    try:
                        # 从文件名提取日期信息
                        match = re.search(r'(\d{4})(\d{2})(\d{2})[-_]?(\d{2})(\d{2})(\d{2})', filename)
                        if match:
                            year, month, day, hour, minute, second = map(int, match.groups())
                            date_obj = datetime.datetime(year, month, day, hour, minute, second)
                            exif_data['DateTimeOriginalParsed'] = date_obj
                            self.exif_cache.put(file_path, exif_data)
                            return exif_data
                    except Exception:
                        pass
            
            # 如果没有拍摄日期，缓存空结果
            self.exif_cache.put(file_path, {})
            return {}
        except Exception as e:
            logging.error(f"读取HEIC数据失败: {file_path}, 错误: {e}")
            self.handle_error(e, f"读取HEIC数据: {file_path}")
            # 发生错误时，缓存空结果避免重复尝试读取
            self.exif_cache.put(file_path, {})
        return {}

    def create_tooltip(self, widget, text):
        """创建工具提示，鼠标移出或点击时关闭"""
        # 如果已经存在工具提示窗口，则销毁它
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            widget.tooltip_window.destroy()

        # 创建提示框
        tooltip = Toplevel(widget)
        tooltip.wm_overrideredirect(True)  # 去掉窗口边框
        x = widget.winfo_pointerx() + 10
        y = widget.winfo_pointery() + 10
        tooltip.geometry(f"+{x}+{y}")

        # 添加提示内容
        label = Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, anchor='w', justify='left')
        label.pack(fill='both', expand=True)

        # 绑定点击事件以关闭提示框
        label.bind("<Button-1>", lambda e: tooltip.destroy())

        # 绑定鼠标移出事件以关闭提示框
        tooltip.bind("<Leave>", lambda e: tooltip.destroy())

        # 将提示框保存到 widget 属性中
        widget.tooltip_window = tooltip

    def show_exif_info(self, event):
        """显示文件的 EXIF 信息"""
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
        file_path = self.files_tree.item(item, 'values')[0]
        # 直接使用file_path，无需original_to_new_mapping
        def process_info():
            try:
                exif_data = None
                if file_path.lower().endswith('.heic'):
                    exif_data = self.get_heic_data(file_path)
                else:
                    exif_data = self.get_exif_data(file_path)
                exif_info = self.extract_exif_info(file_path, exif_data)
                self.root.after(0, lambda: self.create_tooltip(event.widget, exif_info))
            except Exception as e:
                logging.error(f"显示EXIF信息出错: {e}")
                self.handle_error(e, "显示EXIF信息")
        Thread(target=process_info, daemon=True).start()

    def extract_exif_info(self, file_path, exif_data):
        """提取 EXIF 信息并生成字符串"""
        exif_info = ""
        
        # 原文件名
        original_name = os.path.basename(file_path)
        exif_info += f"旧名称: {original_name}\n"

        # 新名称
        new_name = self.generate_new_name(file_path, exif_data)
        exif_info += f"新名称: {new_name}\n"

        # 修改日期
        mod_date = self.get_file_modification_date(file_path)
        if mod_date:
            exif_info += f"修改日期: {mod_date.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # 创建日期
        create_date = self.get_file_creation_date(file_path)
        if create_date:
            exif_info += f"创建日期: {create_date.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # 如果存在 EXIF 信息，则显示更多详细信息
        if exif_data:
            # 拍摄日期
            if 'DateTimeOriginalParsed' in exif_data:
                exif_info += f"拍摄日期: {exif_data['DateTimeOriginalParsed'].strftime('%Y-%m-%d %H:%M:%S')}\n"

            # 设备
            if 'Model' in exif_data:
                exif_info += f"拍摄设备: {exif_data['Model']}"

            # 镜头
            if 'LensModel' in exif_data:
                exif_info += f"镜头: {exif_data['LensModel']}\n"

            # ISO
            if 'ISOSpeedRatings' in exif_data:
                exif_info += f"ISO: {exif_data['ISOSpeedRatings']}\n"

            # 光圈
            if 'FNumber' in exif_data:
                exif_info += f"光圈: f/{exif_data['FNumber']}\n"

            # 快门速度
            if 'ExposureTime' in exif_data:
                exif_info += f"快门速度: {exif_data['ExposureTime']} 秒\n"

            # 分辨率
            if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                exif_info += f"分辨率: {exif_data['ImageWidth']}x{exif_data['ImageHeight']}\n"

        return exif_info

    def get_file_modification_date(self, file_path: str) -> Optional[datetime.datetime]:
        """获取文件修改日期"""
        try:
            # 规范化文件路径
            file_path = os.path.normpath(file_path)
            # 确保路径使用正确的斜杠
            if sys.platform == 'win32':
                file_path = file_path.replace('/', '\\')
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None
                
            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                logging.error(f"无法访问文件: {file_path}，权限不足")
                return None
                
            modification_time = os.path.getmtime(file_path)
            return datetime.datetime.fromtimestamp(modification_time)
        except PermissionError as e:
            logging.error(f"权限错误: {file_path}, 错误: {e}")
            return None
        except OSError as e:
            logging.error(f"系统错误: {file_path}, 错误: {e}")
            return None
        except Exception as e:
            logging.error(f"获取文件修改日期失败: {file_path}, 错误: {e}")
            return None

    def get_file_creation_date(self, file_path: str) -> Optional[datetime.datetime]:
        """获取文件创建日期"""
        try:
            # 规范化文件路径
            file_path = os.path.normpath(file_path)
            # 确保路径使用正确的斜杠
            if sys.platform == 'win32':
                file_path = file_path.replace('/', '\\')
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None
                
            # 检查文件权限
            if not os.access(file_path, os.R_OK):
                logging.error(f"无法访问文件: {file_path}，权限不足")
                return None
                
            if sys.platform == 'win32':
                creation_time = os.path.getctime(file_path)
                return datetime.datetime.fromtimestamp(creation_time)
            else:
                stat = os.stat(file_path)
                try:
                    birth_time = stat.st_birthtime
                    return datetime.datetime.fromtimestamp(birth_time)
                except AttributeError:
                    return datetime.datetime.fromtimestamp(stat.st_ctime)
        except PermissionError as e:
            logging.error(f"权限错误: {file_path}, 错误: {e}")
            return None
        except OSError as e:
            logging.error(f"系统错误: {file_path}, 错误: {e}")
            return None
        except Exception as e:
            logging.error(f"获取文件创建日期失败: {file_path}, 错误: {e}")
            return None

    def remove_file(self, event):
        selected_items = self.files_tree.selection()
        for item in selected_items:
            self.files_tree.delete(item)
        self.update_file_count()  # 更新文件总数

    def stop_renaming(self):
        self.stop_event.set()

    def clear_file_list(self):
        self.files_tree.delete(*self.files_tree.get_children())
        self.update_file_count()  # 更新文件总数

    def open_file(self, event):
        item = self.files_tree.identify_row(event.y)
        if item:
            file_path = self.files_tree.item(item, 'values')[0]
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, file_path])
            except Exception as e:
                logging.error(f"打开文件失败: {file_path}, 错误: {e}")

    def update_status_bar(self, message_key, *args):
        """更新状态栏消息"""
        if message_key in self.lang:
            message = self.lang[message_key].format(*args)
            self.status_label.config(text=message)
        else:
            self.status_label.config(text=message_key)

    def show_help(self):
        help_window = Toplevel(self.root)
        help_window.title(self.lang["help"])
        help_text = self.lang["help_text"]
        help_label = Label(help_window, text=help_text, justify='left')
        help_label.pack(padx=10, pady=10)

    def load_language(self):
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("language", "简体中文")
        return "简体中文"

    def open_update_link(self):
        webbrowser.open("https://github.com/Qwejay/QphotoRenamer")

    def detect_file_status(self, file_path: str, exif_data: Optional[Dict] = None) -> str:
        """检测文件状态，使用缓存机制"""
        try:
            # 获取日期基准
            date_basis = self.date_basis_var.get()
            used_basis = None
            date_obj = None

            # 获取日期对象的通用函数
            def get_date_by_basis(basis):
                if basis == "拍摄日期":
                    if exif_data and 'DateTimeOriginalParsed' in exif_data:
                        return "拍摄日期", exif_data['DateTimeOriginalParsed']
                    return None, None
                elif basis == "修改日期":
                    date = self.get_cached_or_real_modification_date(file_path)
                    if date:
                        return "修改日期", date
                    date = self.get_cached_or_real_creation_date(file_path)
                    if date:
                        return "创建日期", date
                    return None, None
                elif basis == "创建日期":
                    date = self.get_cached_or_real_creation_date(file_path)
                    if date:
                        return "创建日期", date
                    date = self.get_cached_or_real_modification_date(file_path)
                    if date:
                        return "修改日期", date
                    return None, None
                return None, None

            # 首先尝试使用第一下拉框的选择
            used_basis, date_obj = get_date_by_basis(date_basis)

            # 如果是拍摄日期但没有日期，则使用第二下拉框的选择
            if date_basis == "拍摄日期" and not date_obj:
                alternate = self.alternate_date_var.get()
                if alternate == "保留原文件名":
                    return self.lang["prepare_rename_keep_name"]
                used_basis, date_obj = get_date_by_basis(alternate)
                if not date_obj:
                    return self.lang["prepare_rename_keep_name"]

            if used_basis:
                return self.lang["prepare_rename_by"].format(used_basis)
            return self.lang["ready_to_rename"]

        except Exception as e:
            logging.error(f"检测文件状态失败: {file_path}, 错误: {e}")
            return self.lang["prepare_rename_keep_name"]

    def get_video_creation_date(self, file_path):
        """获取视频文件的媒体创建日期"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format_tags=creation_time',
                '-of', 'default=noprint_wrappers=1:nokey=1', file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                creation_time = result.stdout.strip()
                if creation_time:
                    return datetime.datetime.strptime(creation_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        except Exception as e:
            logging.error(f"获取视频文件创建日期失败: {file_path}, 错误: {e}")
        return None

    def show_omitted_info(self, event):
        """点击某一行时显示快速添加模式所省略的内容"""
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
            
        file_path = self.files_tree.item(item, 'values')[0]
        new_name = self.files_tree.item(item, 'values')[1]

        # 开始一个新线程来处理
        def process_info():
            try:
                # 如果新名称为空（快速添加模式跳过），则动态生成新名称
                if not new_name:
                    exif_data = None
                    if file_path.lower().endswith('.heic'):
                        exif_data = self.get_heic_data(file_path)
                    else:
                        exif_data = self.get_exif_data(file_path)
                    generated_name = self.generate_new_name(file_path, exif_data)  # 动态生成新名称
                    self.root.after(0, lambda: self.files_tree.set(item, 'renamed_name', generated_name))
                    # 显示文件信息
                    info = self.extract_omitted_info(file_path, exif_data, generated_name)
                    self.root.after(0, lambda: self.create_tooltip(event.widget, info))
                else:
                    # 已有新名称，直接显示信息
                    exif_data = None
                    if file_path.lower().endswith('.heic'):
                        exif_data = self.get_heic_data(file_path)
                    else:
                        exif_data = self.get_exif_data(file_path)
                    info = self.extract_omitted_info(file_path, exif_data, new_name)
                    self.root.after(0, lambda: self.create_tooltip(event.widget, info))
            except Exception as e:
                logging.error(f"显示文件信息出错: {e}")
                self.handle_error(e, "显示文件信息")
                
        Thread(target=process_info, daemon=True).start()

    def extract_omitted_info(self, file_path, exif_data, new_name):
        """提取快速添加模式所省略的信息"""
        # 原文件名
        original_name = os.path.basename(file_path)
        info = f"旧名称: {original_name}\n"
        info += f"新名称: {new_name}\n"  # 添加新名称

        # 拍摄日期
        if exif_data and 'DateTimeOriginalParsed' in exif_data:
            info += f"拍摄日期: {exif_data['DateTimeOriginalParsed'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            info += "拍摄日期: 无\n"

        # 修改日期
        mod_date = self.get_file_modification_date(file_path)
        if mod_date:
            info += f"修改日期: {mod_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            info += "修改日期: 无\n"

        # 创建日期
        create_date = self.get_file_creation_date(file_path)
        if create_date:
            info += f"创建日期: {create_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            info += "创建日期: 无\n"

        # 其他 EXIF 信息
        if exif_data:
            if 'Model' in exif_data:
                info += f"拍摄设备: {exif_data['Model']}"
            if 'LensModel' in exif_data:
                info += f"镜头: {exif_data['LensModel']}\n"
            if 'ISOSpeedRatings' in exif_data:
                info += f"ISO: {exif_data['ISOSpeedRatings']}\n"
            if 'FNumber' in exif_data:
                info += f"光圈: f/{exif_data['FNumber']}\n"
            if 'ExposureTime' in exif_data:
                info += f"快门速度: {exif_data['ExposureTime']} 秒\n"
            if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                info += f"分辨率: {exif_data['ImageWidth']}x{exif_data['ImageHeight']}\n"

        return info

    # 添加新方法
    def stop_all_operations(self):
        """停止所有操作，包括文件加载、重命名等"""
        try:
            # 设置停止标志
            self.stop_event.set()
            
            # 停止更新线程
            self.stop_update_event.set()
            
            # 等待所有线程完成
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=1.0)
            
            # 清空更新队列
            while not self.update_queue.empty():
                try:
                    self.update_queue.get_nowait()
                    self.update_queue.task_done()
                except queue.Empty:
                    break
            
            # 重置停止标志
            self.reset_stop_event()
            
        except Exception as e:
            logging.error(f"停止操作时发生错误: {e}")

    def reset_stop_event(self):
        """重置停止事件"""
        self.stop_event.clear()
        self.stop_update_event.clear()

    def rename_photo_with_name(self, file_path, item, new_name):
        try:
            file_path = os.path.normpath(file_path)
            directory = os.path.normpath(os.path.dirname(file_path))
            new_file_path = os.path.normpath(os.path.join(directory, new_name))
            if os.path.exists(new_file_path):
                if os.path.samefile(file_path, new_file_path):
                    with self.lock:
                        self.files_tree.set(item, 'status', '已重命名')
                        self.files_tree.item(item, tags=('renamed',))
                    return True, new_file_path
                with self.lock:
                    self.files_tree.set(item, 'status', '目标文件已存在')
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
            try:
                os.rename(file_path, new_file_path)
            except PermissionError:
                with self.lock:
                    error_msg = "无权限重命名文件"
                    self.files_tree.set(item, 'status', f'错误: {error_msg}')
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
            with self.lock:
                # 更新文件路径列
                self.files_tree.set(item, 'filename', new_file_path)
                # 更新新名称列
                self.files_tree.set(item, 'renamed_name', new_name)
                self.files_tree.set(item, 'status', '已重命名')
                self.files_tree.item(item, tags=('renamed',))
            return True, new_file_path
        except Exception as e:
            logging.error(f"重命名失败: {str(e)}")
            with self.lock:
                self.files_tree.set(item, 'status', f'错误: {e}')
                self.files_tree.item(item, tags=('failed',))
                self.unrenamed_files += 1
            return False, None

    def cache_file_info(self, file_path):
        """缓存文件的所有必要信息"""
        try:
            info = {
                'modification_date': self.get_file_modification_date(file_path),
                'creation_date': self.get_file_creation_date(file_path),
                'exif_data': None,
                'video_date': None
            }
            
            # 根据文件类型获取额外信息
            if file_path.lower().endswith('.heic'):
                info['exif_data'] = self.get_heic_data(file_path)
            elif file_path.lower().endswith(SUPPORTED_IMAGE_FORMATS):
                info['exif_data'] = self.get_exif_data(file_path)
            elif file_path.lower().endswith(('.mov', '.mp4', '.avi', '.mkv')):
                info['video_date'] = self.get_video_creation_date(file_path)
            
            self.file_info_cache.set(file_path, info)
            return info
        except Exception as e:
            logging.error(f"缓存文件信息失败: {file_path}, 错误: {e}")
            return None

    def start_update_thread(self):
        """启动更新线程"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.stop_update_event.clear()
            self.update_thread = threading.Thread(target=self._process_updates)
            self.update_thread.daemon = True
            self.update_thread.start()

    def stop_update_thread(self):
        """停止更新线程"""
        self.stop_update_event.set()
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join()

    def _process_updates(self):
        """处理更新队列中的任务"""
        while not self.stop_update_event.is_set():
            try:
                task = self.update_queue.get(timeout=0.1)
                if task is None:
                    continue
                
                file_path, date_basis, alternate = task
                self._update_single_file(file_path, date_basis, alternate)
                self.update_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"处理更新任务失败: {e}")

    def _update_single_file(self, file_path, date_basis, alternate):
        """更新单个文件的新名称"""
        try:
            info = self.file_info_cache.get(file_path)
            if not info:
                info = self.cache_file_info(file_path)
            
            if not info:
                return
            
            # 根据日期基准获取日期
            date_obj = None
            if date_basis == "拍摄日期":
                if info['exif_data'] and 'DateTimeOriginalParsed' in info['exif_data']:
                    date_obj = info['exif_data']['DateTimeOriginalParsed']
                elif info['video_date']:
                    date_obj = info['video_date']
            elif date_basis == "修改日期":
                date_obj = info['modification_date']
            elif date_basis == "创建日期":
                date_obj = info['creation_date']
            
            if date_obj:
                exif_data = {'DateTimeOriginalParsed': date_obj}
                new_name = self.generate_new_name(file_path, exif_data)
                if new_name:
                    self.root.after(0, lambda: self._update_ui(file_path, new_name))
        except Exception as e:
            logging.error(f"更新文件新名称失败: {file_path}, 错误: {e}")

    def _update_ui(self, file_path, new_name):
        """更新UI显示"""
        for item in self.files_tree.get_children():
            if self.files_tree.item(item)['values'][0] == file_path:
                self.files_tree.set(item, 'renamed_name', new_name)
                self.files_tree.update_idletasks()
                break

    def on_closing(self):
        """程序关闭时的清理工作"""
        try:
            # 停止所有操作
            self.stop_all_operations()
            
            # 清理缓存
            try:
                self.cleanup_cache()
            except Exception as e:
                logging.error(f"清理缓存失败: {e}")
            
            # 关闭所有子窗口
            for window in self.toplevel_windows:
                try:
                    window.destroy()
                except:
                    pass
            
            # 销毁主窗口
            self.root.destroy()
            
        except Exception as e:
            logging.error(f"关闭程序时出错: {e}")
            self.root.destroy()

    def get_cached_or_real_modification_date(self, file_path):
        info = self.file_info_cache.get(file_path)
        if info and info.get('modification_date'):
            return info['modification_date']
        return self.get_file_modification_date(file_path)

    def get_cached_or_real_creation_date(self, file_path):
        info = self.file_info_cache.get(file_path)
        if info and info.get('creation_date'):
            return info['creation_date']
        return self.get_file_creation_date(file_path)

    def generate_new_name(self, file_path, exif_data, add_suffix=True):
        try:
            file_path = os.path.abspath(os.path.normpath(file_path))
            directory = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            template = self.template_var.get()
            if not template:
                try:
                    if os.path.exists('QphotoRenamer.ini'):
                        config = configparser.ConfigParser()
                        config.read('QphotoRenamer.ini', encoding='utf-8')
                        if config.has_option('Template', 'default_template'):
                            template = config.get('Template', 'default_template')
                except Exception as e:
                    logging.error(f"加载默认模板失败: {e}")
            if not template:
                template = "{date}_{time}"
            date_basis = self.date_basis_var.get()
            date_obj = None
            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    alternate = self.alternate_date_var.get()
                    if alternate == "保留原文件名":
                        return os.path.basename(file_path)
                    elif alternate == "修改日期":
                        date_obj = self.get_cached_or_real_modification_date(file_path)
                        if not date_obj:
                            date_obj = self.get_cached_or_real_creation_date(file_path)
                    elif alternate == "创建日期":
                        date_obj = self.get_cached_or_real_creation_date(file_path)
                        if not date_obj:
                            date_obj = self.get_cached_or_real_modification_date(file_path)
                    if not date_obj:
                        return os.path.basename(file_path)
            elif date_basis == "修改日期":
                date_obj = self.get_cached_or_real_modification_date(file_path)
                if not date_obj:
                    date_obj = self.get_cached_or_real_creation_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            elif date_basis == "创建日期":
                date_obj = self.get_cached_or_real_creation_date(file_path)
                if not date_obj:
                    date_obj = self.get_cached_or_real_modification_date(file_path)
                if not date_obj:
                    return os.path.basename(file_path)
            if date_obj:
                template = template.replace("{date}", date_obj.strftime("%Y%m%d"))
                template = template.replace("{time}", date_obj.strftime("%H%M%S"))
                if exif_data:
                    if 'Model' in exif_data:
                        template = template.replace("{camera}", exif_data['Model'])
                    if 'LensModel' in exif_data:
                        template = template.replace("{lens}", exif_data['LensModel'])
                    if 'ISOSpeedRatings' in exif_data:
                        template = template.replace("{iso}", exif_data['ISOSpeedRatings'])
                    if 'FNumber' in exif_data:
                        template = template.replace("{aperture}", f"f{exif_data['FNumber']}")
                    if 'ExposureTime' in exif_data:
                        template = template.replace("{shutter}", exif_data['ExposureTime'])
                    if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                        template = template.replace("{width}", exif_data['ImageWidth'])
                        template = template.replace("{height}", exif_data['ImageHeight'])
                template = template.replace("{original}", os.path.splitext(os.path.basename(file_path))[0])
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = template
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = template + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)

class TemplateEditor(ttk.Frame):
    def __init__(self, parent, template_var, prefix_var=None, suffix_var=None, lang=None, main_app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.template_var = template_var  # 使用主程序传入的 template_var
        self.prefix_var = prefix_var
        self.suffix_var = suffix_var
        self.lang = lang or LANGUAGES["简体中文"]  # 默认使用简体中文
        self.config = configparser.ConfigParser()
        self.config_file = 'QphotoRenamer.ini'
        self.main_app = main_app
        self.is_modified = False  # 标记是否有未保存的修改
        self.last_saved_content = ""  # 记录上次保存的内容，用于判断是否真正修改
        
        # 初始化变量列表
        self.variables = [
            ("{date}", "日期"),
            ("{time}", "时间"),
            ("{camera}", "相机型号"),
            ("{lens}", "镜头型号"),
            ("{iso}", "ISO"),
            ("{focal}", "焦距"),
            ("{aperture}", "光圈"),
            ("{shutter}", "快门")
        ]
        
        # 初始化模板列表
        self.templates = [
            "{date}_{time}",
            "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}",
            "{date}_{time}_{camera}",
            "{camera}_{lens}_{iso}_{focal}_{aperture}",
            "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}_{shutter}"
        ]
        self.default_template = None
        
        # 设置UI
        self.setup_ui()
        
        # 加载模板
        self.load_templates()
        
        # 设置默认模板
        if self.default_template:
            self.set_template(self.default_template)
            self.template_combobox.set(self.default_template)
        elif self.template_var.get():
            self.set_template(self.template_var.get())
            self.template_combobox.set(self.template_var.get())
        else:
            # 如果没有默认模板，使用第一个预设模板
            self.set_template(self.templates[0])
            self.template_combobox.set(self.templates[0])
            
        # 初始化完成后立即更新预览
        self.update_preview()

    def setup_ui(self):
        """设置UI界面"""
        # 创建上下分栏
        top_frame = ttk.Frame(self)
        top_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        middle_frame = ttk.Frame(self)
        middle_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 上部分：预设模板和模板编辑
        # 预设模板区域
        preset_frame = ttk.LabelFrame(top_frame, text="选择模板")
        preset_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建预设模板的顶部框架
        preset_top_frame = ttk.Frame(preset_frame)
        preset_top_frame.pack(fill=ttk.X, padx=5, pady=5)
        
        # 创建下拉框，增加宽度
        self.template_combobox = ttk.Combobox(preset_top_frame, values=self.templates, state="readonly", width=50)
        self.template_combobox.pack(side=ttk.LEFT, padx=5, pady=5, fill=ttk.X, expand=True)
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)
        
        # 创建按钮容器框架，用于右对齐按钮
        button_frame = ttk.Frame(preset_top_frame)
        button_frame.pack(side=ttk.RIGHT, padx=5)
        
        # 添加保存和删除按钮，放在右侧
        save_button = ttk.Button(button_frame, text=self.lang["save_template"], command=self.save_current_template, width=8)
        save_button.pack(side=ttk.LEFT, padx=2)
        save_button.text_key = "save_template"
        
        delete_button = ttk.Button(button_frame, text=self.lang["delete_template"], command=self.delete_current_template, width=8)
        delete_button.pack(side=ttk.LEFT, padx=2)
        delete_button.text_key = "delete_template"
        
        # 模板编辑区域
        edit_frame = ttk.LabelFrame(top_frame, text="编辑模板")
        edit_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 模板文本框
        self.template_text = tk.Text(edit_frame, height=3, wrap=tk.WORD)
        self.template_text.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定所有可能改变文本的事件
        def on_text_change(event=None):
            template = self.template_text.get("1.0", END).strip()
            self.template_var.set(template)  # 直接更新主程序的模板变量
            self.update_preview()  # 立即更新预览
            return True
            
        self.template_text.bind('<KeyRelease>', on_text_change)
        self.template_text.bind('<KeyPress>', on_text_change)
        self.template_text.bind('<<Paste>>', on_text_change)
        self.template_text.bind('<<Cut>>', on_text_change)
        self.template_text.bind('<Delete>', on_text_change)
        self.template_text.bind('<BackSpace>', on_text_change)
        
        # 中部分：变量按钮
        variables_frame = ttk.LabelFrame(middle_frame, text="变量")
        variables_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        self.create_variable_buttons(variables_frame, self.variables)
        
        # 下部分：预览区域
        preview_frame = ttk.LabelFrame(bottom_frame, text="预览")
        preview_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 使用Label替代Text控件来显示预览
        self.preview_label = ttk.Label(preview_frame, text="", anchor='w', wraplength=0)
        self.preview_label.pack(fill=ttk.X, padx=5, pady=5)
        
        # 找到父窗口并绑定关闭事件
        parent = self.winfo_toplevel()
        original_close_handler = getattr(parent, 'protocol', lambda *args: None)('WM_DELETE_WINDOW')
        
        def on_parent_close():
            """父窗口关闭时检查是否有未保存的修改"""
            if self.has_unsaved_changes():
                if messagebox.askyesno("未保存的修改", "模板编辑器中有未保存的修改，是否保存？"):
                    self.save_current_template()
            
            # 调用原始的关闭处理函数
            if callable(original_close_handler):
                original_close_handler()
            else:
                parent.destroy()
                
        parent.protocol("WM_DELETE_WINDOW", on_parent_close)

    def update_preview(self, event=None):
        """更新预览"""
        template = self.template_text.get("1.0", END).strip()
        
        # 只有当内容真正变化时才标记为已修改
        if template != self.last_saved_content:
            self.is_modified = True
            
            # 检查当前模板是否为新模板（与所有已有模板都不同）
            is_new_template = template not in self.templates
            
            # 如果是新模板，更新下拉框提示用户
            if is_new_template and template:
                current_values = list(self.template_combobox['values'])
                if "(新模板)" not in current_values:
                    new_values = current_values + ["(新模板)"]
                    self.template_combobox['values'] = new_values
                    self.template_combobox.set("(新模板)")
        
        # 创建预览文本
        preview = template
        preview = preview.replace("{date}", "20240315")
        preview = preview.replace("{time}", "143022")
        preview = preview.replace("{camera}", "Canon EOS R5")
        preview = preview.replace("{lens}", "RF 24-70mm F2.8L")
        preview = preview.replace("{iso}", "100")
        preview = preview.replace("{focal}", "50mm")
        preview = preview.replace("{aperture}", "f2.8")
        preview = preview.replace("{shutter}", "1/125")
        preview = preview.replace("{width}", "8192")
        preview = preview.replace("{height}", "5464")
        preview = preview.replace("{original}", "IMG_1234")
        preview = preview.replace("{counter}", "001")
        
        # 更新预览标签
        self.preview_label.config(text=preview)
        
        # 如果有主程序实例，更新文件列表中的预览
        if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
            self.main_app.update_renamed_name_column()
            
        # 返回 True 以允许事件继续传播
        return True

    def clear_template(self):
        """清除模板内容"""
        self.template_text.delete("1.0", END)
        # 清除后内容与保存的内容不同，标记为已修改
        self.update_preview()
        # 强制设置为已修改，因为清空是明确的修改操作
        self.is_modified = True
        
    def on_drop(self, event):
        """处理拖放事件"""
        current_content = self.template_text.get("1.0", END).strip()
        self.template_text.insert(INSERT, event.data)
        # 拖放后检查内容是否有变化
        self.update_preview()
        # 明确标记为已修改，因为拖放是明确的修改操作
        self.is_modified = True
        
    def create_variable_buttons(self, parent, variables):
        """创建变量按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # 使用网格布局，每行4个按钮
        for i, (var, desc) in enumerate(variables):
            row = i // 4
            col = i % 4
            
            # 创建按钮容器
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            
            # 创建按钮
            btn = ttk.Button(btn_frame, text=desc, width=8,
                           command=lambda v=var: self.insert_variable(v))
            btn.pack(side=ttk.LEFT, padx=2)
            
            # 显示变量名称的标签
            lbl = ttk.Label(btn_frame, text=var, foreground="gray", width=8)
            lbl.pack(side=ttk.LEFT, padx=2)
            
        # 使按钮水平方向填充
        for i in range(4):
            frame.columnconfigure(i, weight=1)

    def has_unsaved_changes(self):
        """检查是否有未保存的修改"""
        current_content = self.template_text.get("1.0", tk.END).strip()
        return current_content != self.last_saved_content
        
    def delete_current_template(self):
        """删除当前选中的模板"""
        # 检查是否有未保存的修改
        if self.has_unsaved_changes():
            if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                self.save_current_template()
                
        current_template = self.template_combobox.get()
        if current_template in self.templates:
            # 从列表中移除当前模板
            self.templates.remove(current_template)
            # 确保从配置文件中也移除
            try:
                if os.path.exists(self.config_file):
                    self.config.read(self.config_file, encoding='utf-8')
                    if 'Template' in self.config:
                        # 遍历所有模板项，找到并删除匹配的值
                        for key in list(self.config['Template']):
                            if key.startswith('template') and self.config['Template'][key] == current_template:
                                del self.config['Template'][key]
                        # 写入配置文件
                        with open(self.config_file, 'w', encoding='utf-8') as f:
                            self.config.write(f)
            except Exception as e:
                logging.error(f"从配置文件删除模板失败: {e}")
            
            # 刷新下拉框
            self.update_template_combobox()
            
            # 如果还有其他模板，选择第一个
            if self.templates:
                self.template_combobox.set(self.templates[0])
                self.set_template(self.templates[0])
            else:
                # 如果没有模板了，清空文本框和下拉框
                self.clear_template()
                self.template_combobox['values'] = []
                self.template_combobox.set("")
            
            # 通知用户
            self.update_status_bar(f"已删除模板: {current_template}")
            
    def load_templates(self):
        """从配置文件加载模板"""
        try:
            # 尝试从配置文件加载模板
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                
                # 加载默认模板
                if self.config.has_option('Template', 'default_template'):
                    self.default_template = self.config.get('Template', 'default_template')
                    self.last_saved_content = self.default_template  # 更新保存的内容
                
                # 加载模板列表
                if self.config.has_section('Template'):
                    templates = []
                    for i in range(1, 6):
                        template_key = f'template{i}'
                        if self.config.has_option('Template', template_key):
                            template = self.config.get('Template', template_key)
                            if template not in templates:
                                templates.append(template)
                    
                    # 如果找到了保存的模板，使用它们
                    if templates:
                        self.templates = templates
                        
        except Exception as e:
            logging.error(f"加载模板失败: {e}")
        
        # 如果没有找到模板，使用默认模板
        if not self.templates:
            self.templates = [
                "{date}_{time}",
                "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}",
                "{date}_{time}_{camera}",
                "{camera}_{lens}_{iso}_{focal}_{aperture}",
                "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}_{shutter}"
            ]
            
        # 更新下拉框的值
        self.update_template_combobox()
        
    def save_templates(self):
        """保存模板记录到配置文件"""
        try:
            # 读取现有配置
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
            
            # 确保 Template 部分存在
            if 'Template' not in self.config:
                self.config['Template'] = {}
            
            # 获取当前模板内容
            current_template = self.template_text.get("1.0", END).strip()
            if not current_template:
                self.update_status_bar("模板内容不能为空")
                return
            
            # 保存当前模板为默认模板
            self.config['Template']['default_template'] = current_template
            self.default_template = current_template
            
            # 保存模板列表
            # 首先清除所有现有的模板
            for key in list(self.config['Template'].keys()):
                if key.startswith('template'):
                    del self.config['Template'][key]
            
            # 确保当前模板在列表中
            if current_template not in self.templates:
                self.templates.append(current_template)
            
            # 保存所有模板
            for i, template in enumerate(self.templates, 1):
                if template and template != "(新模板)":  # 只保存有效的模板
                    self.config['Template'][f'template{i}'] = template
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            # 同时更新主程序的模板变量
            if self.template_var:
                self.template_var.set(current_template)
            
            # 更新下拉框
            self.update_template_combobox()
            self.template_combobox.set(current_template)
            
            self.update_status_bar("模板已保存")
            
        except Exception as e:
            logging.error(f"保存模板记录时出错: {e}")
            self.update_status_bar(f"保存模板失败: {str(e)}")

    def save_current_template(self):
        """保存当前模板"""
        try:
            # 获取当前模板内容
            template = self.template_text.get("1.0", tk.END).strip()
            if not template:
                self.update_status_bar("模板内容不能为空")
                return
            
            # 检查当前模板是否为新模板
            is_new_template = template not in self.templates
            
            # 如果模板不在列表中，添加到列表
            if is_new_template:
                self.templates.append(template)
                self.update_status_bar("新模板已创建并保存")
            else:
                self.update_status_bar("模板已更新")
            
            # 设置为当前模板
            self.default_template = template
            
            # 保存到文件
            self.save_templates()
            
            # 更新下拉框
            self.update_template_combobox()
            self.template_combobox.set(template)
            
            # 重置修改标志并更新保存的内容
            self.is_modified = False
            self.last_saved_content = template
            
            # 如果有主程序实例，更新文件列表中的预览
            if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
                self.main_app.update_renamed_name_column()
            
        except Exception as e:
            error_msg = f"保存模板失败: {str(e)}"
            logging.error(error_msg)
            self.update_status_bar(error_msg)
    
    def update_status_bar(self, message):
        """更新状态栏消息"""
        try:
            if self.main_app and hasattr(self.main_app, 'status_label'):
                self.main_app.status_label.config(text=message)
            else:
                logging.info(message)
        except Exception as e:
            logging.error(f"更新状态栏失败: {str(e)}")
            logging.info(message)  # 至少记录到日志
            
    def on_template_selected(self, event=None):
        """当选择模板时更新编辑器内容"""
        try:
            selected_template = self.template_combobox.get()
            current_template = self.template_text.get("1.0", tk.END).strip()
            
            # 如果选择的不是当前正在编辑的模板
            if selected_template != "(新模板)" and selected_template != current_template:
                # 检查是否有未保存的修改
                if self.is_modified:
                    if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                        # 如果当前是新模板且用户希望保存
                        if "(新模板)" in self.template_combobox['values'] and self.template_combobox.get() == "(新模板)":
                            # 保存新模板内容
                            if current_template and current_template not in self.templates:
                                self.templates.append(current_template)
                                # 通知用户新模板已保存
                                self.update_status_bar("新模板已保存")
                        self.save_current_template()
                
                # 现在获取并显示选择的模板
                if selected_template in self.templates:
                    self.template_text.delete("1.0", tk.END)
                    self.template_text.insert("1.0", selected_template)
                    
                    # 更新默认模板
                    self.default_template = selected_template
                    
                    # 保存到配置文件
                    self.save_templates()
                    
                    # 更新状态
                    self.update_status_bar(f"已加载模板: {selected_template}")
                    
                    # 重置修改标志并更新保存的内容
                    self.is_modified = False
                    self.last_saved_content = selected_template
                    
                    # 更新主程序的模板变量
                    if self.template_var:
                        self.template_var.set(selected_template)
                    
                    # 更新主程序的文件列表预览
                    if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
                        self.main_app.update_renamed_name_column()
                
        except Exception as e:
            error_msg = f"加载模板失败: {str(e)}"
            logging.error(error_msg)
            self.update_status_bar(error_msg)
            
    def update_template_combobox(self):
        """更新下拉框的选项"""
        # 获取当前编辑器中的内容
        current_content = self.template_text.get("1.0", tk.END).strip()
        
        # 确保self.templates不包含重复项
        unique_templates = []
        for t in self.templates:
            if t != "(新模板)" and t not in unique_templates:
                unique_templates.append(t)
        self.templates = unique_templates
        
        # 创建下拉框值列表
        values = self.templates.copy()
        
        # 确保当前编辑的模板内容在值列表中（如果不是空的且与已保存内容不同）
        if current_content and current_content not in values and current_content != self.last_saved_content:
            # 将当前内容视为一个潜在的新模板
            values.append("(新模板)")
            
        # 更新下拉框
        self.template_combobox['values'] = values
        
    def set_template(self, template):
        """设置模板内容"""
        self.template_text.delete("1.0", END)
        self.template_text.insert("1.0", template)
        self.last_saved_content = template  # 更新保存的内容
        self.is_modified = False  # 重置修改标志
        
        # 更新主程序的模板变量
        if self.template_var:
            self.template_var.set(template)
            
        # 立即更新预览
        self.update_preview()
        
        # 更新主程序的文件列表预览
        if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
            self.main_app.update_renamed_name_column()

    def insert_variable(self, variable):
        """插入变量到模板"""
        current_content = self.template_text.get("1.0", END).strip()
        self.template_text.insert(INSERT, variable)
        # 更新 template_var 以触发预览更新
        self.template_var.set(self.template_text.get("1.0", END).strip())
        # 明确标记为已修改，因为插入变量是明确的修改操作
        self.is_modified = True
        
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    try:
        renamer = PhotoRenamer(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序遇到严重错误: {str(e)}")
        os._exit(1)