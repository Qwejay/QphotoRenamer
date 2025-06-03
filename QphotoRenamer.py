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
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'icon.ico')
COMMON_DATE_FORMATS = [
    "%Y%m%d_%H%M%S",    
    "%Y-%m-%d %H:%M:%S",  
    "%d-%m-%Y %H:%M:%S",  
    "%Y%m%d",            
    "%H%M%S",            
    "%Y-%m-%d",          
    "%d-%m-%Y"           
]
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic'}
LANGUAGES = {
    "简体中文": {
        "window_title": "文件与照片批量重命名工具 QphotoRenamer 2.5 —— QwejayHuang",
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
        "rename_skipped_exists": "目标文件已存在",
        "file_not_found": "文件不存在"
    },
    "English": {
        "window_title": "QphotoRenamer 2.5 —— QwejayHuang",
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
        "rename_skipped_exists": "Target file already exists",
        "file_not_found": "File not found"
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
        self.template_var = ttk.StringVar(value="%Y%m%d_%H%M%S") 
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.language_var = ttk.StringVar(value="简体中文")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")
        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.show_errors_only_var = ttk.BooleanVar(value=False)
        self.fast_add_mode_var = ttk.BooleanVar(value=True)
        self.fast_add_threshold_var = ttk.IntVar(value=100)
        self.date_format = "%Y%m%d_%H%M%S"
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
        self.batch_size = 50  
        self.processing_batch = False
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 300
        self.root.title("文件&照片批量重命名 QphotoRenamer 2.5 —— QwejayHuang")
        self.root.geometry("850x600")
        self.root.iconbitmap(icon_path)
        self.style = ttk.Style('litera')
        self.lock = Lock()
        self.initialize_ui()
        self.load_or_create_settings()
        self.remove_invalid_files()  
        self.root.after(300000, self.cleanup_cache)
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
            self.stop_all_operations()
            try:
                self.cleanup_cache()
            except Exception as e:
                logging.error(f"清理缓存失败: {e}")
            for window in self.toplevel_windows:
                try:
                    window.destroy()
                except:
                    pass
            self.root.destroy()
        except Exception as e:
            logging.error(f"关闭程序时出错: {e}")
            self.root.destroy()
    def load_or_create_settings(self):
        """加载或创建设置"""
        try:
            if not os.path.exists('QphotoRenamer.ini'):
                config = configparser.ConfigParser()
                config['General'] = {
                    'language': '简体中文',
                    'prefix': '',
                    'suffix': '',
                    'skip_extensions': '',
                    'auto_scroll': 'True',
                    'fast_add_mode': 'False',
                    'fast_add_threshold': '100'
                }
                config['Template'] = {
                    'default': '{date}_{time}',
                    'template1': '{date}_{time}_{camera}',
                    'template2': '{date}_{time}_{camera}_{lens}',
                    'template3': '{date}_{time}_{camera}_{lens}_{iso}',
                    'template4': '{date}_{time}_{camera}_{lens}_{iso}_{focal}',
                    'template5': '{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}'
                }
                with open('QphotoRenamer.ini', 'w', encoding='utf-8') as f:
                    config.write(f)
            self.load_settings()
        except Exception as e:
            logging.error(f"加载或创建设置失败: {e}")
            self.template_var.set("{date}_{time}")
            self.language_var.set("简体中文")
            self.prefix_var.set("")
            self.suffix_var.set("")
            self.skip_extensions_var.set("")
            self.auto_scroll_var.set(True)
            self.fast_add_mode_var.set(False)
            self.fast_add_threshold_var.set(100)
            self.update_status_bar("ready")  
    def load_settings(self):
        """加载设置"""
        try:
            config = configparser.ConfigParser()
            config.read('QphotoRenamer.ini', encoding='utf-8')
            if not config.has_section('General'):
                config.add_section('General')
            if not config.has_section('Template'):
                config.add_section('Template')
            self.language_var.set(config.get('General', 'language', fallback='简体中文'))
            self.prefix_var.set(config.get('General', 'prefix', fallback=''))
            self.suffix_var.set(config.get('General', 'suffix', fallback=''))
            self.skip_extensions_var.set(config.get('General', 'skip_extensions', fallback=''))
            self.auto_scroll_var.set(config.getboolean('General', 'auto_scroll', fallback=True))
            self.fast_add_mode_var.set(config.getboolean('General', 'fast_add_mode', fallback=False))
            self.fast_add_threshold_var.set(config.getint('General', 'fast_add_threshold', fallback=100))
            default_template = config.get('Template', 'default', fallback='{date}_{time}')
            self.template_var.set(default_template)
            self.templates = []
            for i in range(1, 6):
                template = config.get('Template', f'template{i}', fallback='')
                if template:
                    self.templates.append(template)
            if not self.templates:
                self.templates = [
                    '{date}_{time}',
                    '{date}_{time}_{camera}',
                    '{date}_{time}_{camera}_{lens}',
                    '{date}_{time}_{camera}_{lens}_{iso}',
                    '{date}_{time}_{camera}_{lens}_{iso}_{focal}'
                ]
            self.set_language(self.language_var.get())
        except Exception as e:
            logging.error(f"加载设置失败: {e}")
            self.handle_error(e, "加载设置")
    def get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        try:
            file_path = os.path.abspath(file_path)
            file_path = os.path.normpath(file_path)
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return ""
            if not os.access(file_path, os.R_OK):
                logging.error(f"无法访问文件: {file_path}，权限不足")
                return ""
            with open(file_path, 'rb') as f:
                data = f.read(8192)  
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
            expired_errors = [
                error_id for error_id, data in self.error_cache.items()
                if (current_time - data['last_time']) > 3600  
            ]
            for error_id in expired_errors:
                del self.error_cache[error_id]
            if self._settings_cache and (current_time - self._settings_cache['timestamp']) > 300:  
                self._settings_cache = None
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache = LRUCache(1000)
            if hasattr(self, 'exif_cache'):
                self.exif_cache = LRUCache(1000)
            if hasattr(self, 'status_cache'):
                self.status_cache = LRUCache(1000)
            gc.collect()
        except Exception as e:
            logging.error(f"清理缓存时出错: {e}")
        finally:
            self.root.after(300000, self.cleanup_cache) 
    @lru_cache(maxsize=1000)
    def get_exif_data(self, file_path: str) -> Optional[Dict]:
        try:
            current_time = time.time()
            if current_time - self.last_cleanup_time > self.cleanup_interval:
                self.cleanup_cache()
                self.last_cleanup_time = current_time
            if file_path.lower().endswith('.heic'):
                return self.get_heic_data(file_path)
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if not tags:
                    return None
                exif_data = {}
                date_time_original = None
                if 'EXIF DateTimeOriginal' in tags:
                    date_time_original = str(tags['EXIF DateTimeOriginal'])
                elif 'Image DateTime' in tags:
                    date_time_original = str(tags['Image DateTime'])
                if date_time_original:
                    try:
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
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        date_basis_frame = ttk.Frame(main_frame)
        date_basis_frame.pack(fill=ttk.X, pady=5)
        self.drag_hint_label = ttk.Label(date_basis_frame, text=self.lang["drag_hint"])
        self.drag_hint_label.pack(side=ttk.LEFT)
        self.date_basis_var = ttk.StringVar(value=self.lang["date_bases"][0]["display"])
        self.date_basis_combobox = ttk.Combobox(
            date_basis_frame,
            textvariable=self.date_basis_var,
            values=[item["display"] for item in self.lang["date_bases"]],
            state="readonly", width=15)  
        self.date_basis_combobox.pack(side=ttk.LEFT, padx=5)
        self.date_basis_combobox.bind("<<ComboboxSelected>>", self.on_date_basis_selected)
        self.rename_hint_label = ttk.Label(date_basis_frame, text=self.lang["rename_hint"])
        self.rename_hint_label.pack(side=ttk.LEFT, padx=5)
        self.alternate_date_var = ttk.StringVar(value=self.lang["alternate_dates"][0]["display"])
        self.alternate_date_combobox = ttk.Combobox(
            date_basis_frame,
            textvariable=self.alternate_date_var,
            values=[item["display"] for item in self.lang["alternate_dates"]],
            state="readonly", width=15)  
        self.alternate_date_combobox.pack(side=ttk.LEFT, padx=5)
        self.alternate_date_combobox.bind("<<ComboboxSelected>>", self.on_alternate_date_selected)  
        self.rename_end_hint_label = ttk.Label(date_basis_frame, text=self.lang["rename_end_hint"])
        self.rename_end_hint_label.pack(side=ttk.LEFT, padx=5)
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
        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=ttk.X, padx=10, pady=10)
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
            date_basis = self.date_basis_var.get()
            if date_basis in ["创建日期", "修改日期"]:
                self.alternate_date_combobox.configure(state="disabled")
                self.alternate_date_var.set("保留原文件名")
            else:
                self.alternate_date_combobox.configure(state="readonly")
            if hasattr(self, 'status_cache'):
                self.status_cache.clear()
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache.clear()
            for item in self.files_tree.get_children():
                try:
                    values = self.files_tree.item(item)['values']
                    if not values or len(values) < 3:
                        continue
                    file_path = str(values[0])  
                    if not file_path:
                        continue
                    if not os.path.exists(file_path):
                        new_name = str(values[1]) if values[1] else ""  
                        if new_name and new_name != self.lang["ready_to_rename"]:
                            directory = os.path.dirname(file_path)
                            new_path = os.path.join(directory, new_name)
                            if os.path.exists(new_path):
                                self.files_tree.item(item, values=(new_path, new_name, values[2]))
                                file_path = new_path
                            else:
                                self.files_tree.set(item, 'status', self.lang["file_not_found"])
                                continue
                    exif_data = self.get_exif_data(file_path)
                    has_shooting_date = exif_data and 'DateTimeOriginalParsed' in exif_data
                    if date_basis == "拍摄日期":
                        if has_shooting_date:
                            status = self.lang["prepare_rename_by"].format("拍摄日期")
                        else:
                            alternate = self.alternate_date_var.get()
                            if alternate == "保留原文件名":
                                status = self.lang["prepare_rename_keep_name"]
                            else:
                                status = self.lang["prepare_rename_by"].format(alternate)
                    else:
                        status = self.lang["prepare_rename_by"].format(date_basis)
                    self.files_tree.set(item, 'status', status)
                    new_name = self.generate_new_name(file_path, exif_data)
                    if new_name:  
                        self.files_tree.set(item, 'renamed_name', new_name)
                except Exception as e:
                    logging.error(f"处理文件项时出错: {e}")
                    continue
            self.update_renamed_name_column()
            self.root.update_idletasks()  
        except Exception as e:
            logging.error(f"更新日期基准选择时出错: {e}")
            self.handle_error(e, "更新日期基准选择")
    def on_alternate_date_selected(self, event):
        """当备选日期选择改变时，更新文件列表"""
        try:
            if hasattr(self, 'status_cache'):
                self.status_cache.clear()
            if hasattr(self, 'file_hash_cache'):
                self.file_hash_cache.clear()
            date_basis = self.date_basis_var.get()
            alternate = self.alternate_date_var.get()
            for item in self.files_tree.get_children():
                try:
                    values = self.files_tree.item(item)['values']
                    if not values or len(values) < 3:
                        continue
                    file_path = str(values[0])  
                    if not file_path:
                        continue
                    if not os.path.exists(file_path):
                        new_name = str(values[1]) if values[1] else ""  
                        if new_name and new_name != self.lang["ready_to_rename"]:
                            directory = os.path.dirname(file_path)
                            new_path = os.path.join(directory, new_name)
                            if os.path.exists(new_path):
                                self.files_tree.item(item, values=(new_path, new_name, values[2]))
                                file_path = new_path
                            else:
                                self.files_tree.set(item, 'status', self.lang["file_not_found"])
                                continue
                    exif_data = self.get_exif_data(file_path)
                    has_shooting_date = exif_data and 'DateTimeOriginalParsed' in exif_data
                    if date_basis == "拍摄日期":
                        if has_shooting_date:
                            status = self.lang["prepare_rename_by"].format("拍摄日期")
                        else:
                            if alternate == "保留原文件名":
                                status = self.lang["prepare_rename_keep_name"]
                            else:
                                status = self.lang["prepare_rename_by"].format(alternate)
                    else:
                        status = self.lang["prepare_rename_by"].format(date_basis)
                    self.files_tree.set(item, 'status', status)
                    new_name = self.generate_new_name(file_path, exif_data)
                    if new_name:  
                        self.files_tree.set(item, 'renamed_name', new_name)
                except Exception as e:
                    logging.error(f"处理文件项时出错: {e}")
                    continue
            self.update_renamed_name_column()
            self.root.update_idletasks()  
        except Exception as e:
            logging.error(f"更新备选日期选择时出错: {e}")
            self.handle_error(e, "更新备选日期选择")
    def on_template_selected(self, event=None):
        """当选择模板时更新编辑器内容"""
        try:
            selected_template = self.template_combobox.get()
            current_template = self.template_text.get("1.0", tk.END).strip()
            if selected_template != "(新模板)" and selected_template != current_template:
                if self.is_modified:
                    if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                        if "(新模板)" in self.template_combobox['values'] and self.template_combobox.get() == "(新模板)":
                            if current_template and current_template not in self.templates:
                                self.templates.append(current_template)
                                self.update_status_bar("新模板已保存")
                        self.save_current_template()
                if selected_template in self.templates:
                    self.template_text.delete("1.0", tk.END)
                    self.template_text.insert("1.0", selected_template)
                    self.default_template = selected_template
                    if self.template_var:
                        self.template_var.set(selected_template)
                    self.is_modified = False
                    self.last_saved_content = selected_template
                    self.update_preview()
                    if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
                        self.main_app.update_renamed_name_column()
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
                    date_obj = date_obj.replace(microsecond=0)
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
                # 使用字典来存储所有可能的变量值
                variables = {
                    "{date}": date_obj.strftime("%Y%m%d"),
                    "{time}": date_obj.strftime("%H%M%S"),
                    "{original}": os.path.splitext(os.path.basename(file_path))[0]
                }
                
                # 添加 EXIF 数据变量
                if exif_data:
                    if 'Model' in exif_data:
                        variables["{camera}"] = exif_data['Model']
                    if 'LensModel' in exif_data:
                        variables["{lens}"] = exif_data['LensModel']
                    if 'ISOSpeedRatings' in exif_data:
                        variables["{iso}"] = exif_data['ISOSpeedRatings']
                    if 'FNumber' in exif_data:
                        variables["{aperture}"] = f"f{exif_data['FNumber']}"
                    if 'ExposureTime' in exif_data:
                        variables["{shutter}"] = exif_data['ExposureTime']
                    if 'ImageWidth' in exif_data:
                        variables["{width}"] = exif_data['ImageWidth']
                    if 'ImageHeight' in exif_data:
                        variables["{height}"] = exif_data['ImageHeight']
                
                # 按变量长度降序排序，避免部分替换问题
                sorted_vars = sorted(variables.keys(), key=len, reverse=True)
                
                # 替换所有变量
                new_name = template
                for var in sorted_vars:
                    new_name = new_name.replace(var, variables[var])
                
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = new_name
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = new_name + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)
    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        """生成唯一文件名，避免批量重命名冲突"""
        try:
            directory = os.path.abspath(os.path.normpath(directory))
            
            # 检查日期时间格式
            date_time_match = re.match(r"(\d{8})_(\d{6})", base_name)
            if not date_time_match:
                logging.info(f"文件名 {base_name} 不符合日期时间格式，直接返回")
                return base_name + ext
                
            date_part = date_time_match.group(1)
            time_part = date_time_match.group(2)
            logging.info(f"处理文件: {base_name}, 日期: {date_part}, 时间: {time_part}")
            
            # 获取所有可能的后缀模式
            suffix_patterns = [
                r"_\d{3}$",  # _001
                r"-\d{2}$",  # -01
                r"_\d+$"     # _1
            ]
            
            # 检查文件是否已经包含任何后缀
            has_suffix = any(re.search(pattern, base_name) for pattern in suffix_patterns)
            if has_suffix:
                logging.info(f"文件名 {base_name} 已包含后缀，直接返回")
                return base_name + ext
                
            existing_files = []
            for file in os.listdir(directory):
                if file.endswith(ext):
                    file_base = os.path.splitext(file)[0]
                    # 移除任何现有的后缀
                    for pattern in suffix_patterns:
                        file_base = re.sub(pattern, '', file_base)
                    
                    file_match = re.match(r"(\d{8})_(\d{6})", file_base)
                    if file_match:
                        file_date = file_match.group(1)
                        file_time = file_match.group(2)
                        if file_date == date_part and file_time == time_part:
                            if os.path.join(directory, file) != os.path.join(directory, base_name + ext):
                                existing_files.append(file)
                                logging.info(f"找到相同时间点的文件: {file}")
            
            if not existing_files:
                logging.info(f"没有找到相同时间点的文件，使用原始名称: {base_name}{ext}")
                return base_name + ext
                
            counter = 1
            max_counter = 999
            while counter <= max_counter:
                if suffix_style == "_001":
                    suffix = f"_{counter:03d}"
                elif suffix_style == "-01":
                    suffix = f"-{counter:02d}"
                elif suffix_style == "_1":
                    suffix = f"_{counter}"
                else:
                    suffix = f"_{counter:03d}"
                new_filename = f"{base_name}{suffix}{ext}"
                if not os.path.exists(os.path.join(directory, new_filename)):
                    logging.info(f"生成新文件名: {new_filename}")
                    return new_filename
                counter += 1
                
            logging.info(f"达到最大计数，使用原始名称: {base_name}{ext}")
            return base_name + ext
        except Exception as e:
            logging.error(f"生成唯一文件名失败: {e}")
            return base_name + ext
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
                if hasattr(self, 'template_editor') and self.template_editor.has_unsaved_changes():
                    if messagebox.askyesno("未保存的修改", "模板编辑器中有未保存的修改，是否保存？"):
                        self.template_editor.save_current_template()
                if settings_window in self.toplevel_windows:
                    self.toplevel_windows.remove(settings_window)
                settings_window.destroy()
            settings_window.protocol("WM_DELETE_WINDOW", on_close)
            notebook = ttk.Notebook(settings_window)
            notebook.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            template_frame = ttk.Frame(notebook)
            notebook.add(template_frame, text=self.lang.get("rename_pattern_settings", "重命名格式设置"))
            template_editor = TemplateEditor(template_frame, self.template_var, lang=self.lang, main_app=self)
            template_editor.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            self.template_editor = template_editor  
            date_frame = ttk.Frame(notebook)
            notebook.add(date_frame, text=self.lang.get("date_settings", "日期设置"))
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
            file_frame = ttk.Frame(notebook)
            notebook.add(file_frame, text=self.lang.get("file_handling_settings", "文件处理设置"))
            filter_frame = ttk.LabelFrame(file_frame, text=self.lang.get("file_filter", "文件过滤"))
            filter_frame.pack(fill=ttk.X, padx=10, pady=5)
            skip_extensions_frame = ttk.Frame(filter_frame)
            skip_extensions_frame.pack(fill=ttk.X, padx=5, pady=5)
            ttk.Label(skip_extensions_frame, text=self.lang.get("skip_extensions", "跳过的扩展名:")).pack(side=ttk.LEFT)
            skip_extensions_entry = ttk.Entry(skip_extensions_frame, textvariable=self.skip_extensions_var)
            skip_extensions_entry.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
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
            ui_frame = ttk.Frame(notebook)
            notebook.add(ui_frame, text=self.lang.get("ui_settings", "界面设置"))
            language_frame = ttk.LabelFrame(ui_frame, text=self.lang.get("language_settings", "语言设置"))
            language_frame.pack(fill=ttk.X, padx=10, pady=5)
            ttk.Label(language_frame, text=self.lang.get("interface_language", "界面语言:")).pack(side=ttk.LEFT, padx=5)
            language_combobox = ttk.Combobox(language_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
            language_combobox.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=5)
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
            about_frame = ttk.Frame(notebook)
            notebook.add(about_frame, text=self.lang.get("about", "关于"))
            about_text = """
QphotoRenamer 2.5
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
"""
            about_label = ttk.Label(about_frame, text=about_text, justify=ttk.LEFT)
            about_label.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
            save_button = ttk.Button(settings_window, text=self.lang["save_settings"], 
            command=lambda: self.save_settings(self.template_var.get(), 
            self.language_var.get(),
            self.prefix_var.get(),  
            self.suffix_var.get(),  
            self.skip_extensions_var.get(),
            settings_window))
            save_button.pack(pady=10)
            save_button.text_key = "save_settings"
            template_frame.columnconfigure(0, weight=1)
            date_frame.columnconfigure(0, weight=1)
            file_frame.columnconfigure(0, weight=1)
            ui_frame.columnconfigure(0, weight=1)
            about_frame.columnconfigure(0, weight=1)
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
            return 1 <= int(value) <= 1000  
        return False
    def save_settings(self, template, language, prefix, suffix, skip_extensions_input, settings_window):
        """保存设置到配置文件"""
        try:
            config = configparser.ConfigParser(interpolation=None)
            if os.path.exists("QphotoRenamer.ini"):
                config.read("QphotoRenamer.ini", encoding="utf-8")
            if 'General' not in config:
                config['General'] = {}
            config['General']['language'] = language
            config['General']['template'] = template
            config['General']['prefix'] = prefix
            config['General']['suffix'] = suffix
            config['General']['skip_extensions'] = skip_extensions_input
            with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
                config.write(f)
            self._apply_settings(config)
            settings_window.destroy()
        except Exception as e:
            logging.error(f"保存设置失败: {e}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")
    def fix_config_encoding(self, config: Dict):
        """修复配置文件中的编码问题（只支持INI格式）"""
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
            normalized_paths = []
            for path in paths:
                try:
                    abs_path = os.path.abspath(path)
                    norm_path = os.path.normpath(abs_path)
                    if os.path.exists(norm_path):
                        normalized_paths.append(norm_path)
                    else:
                        logging.warning(f"文件不存在，已跳过: {norm_path}")
                except Exception as e:
                    logging.error(f"处理文件路径时出错: {path}, 错误: {e}")
                    continue
            if not normalized_paths:
                self.update_status_bar("no_valid_files")
                return
            self.start_button.config(state=ttk.DISABLED)
            self.stop_button.config(state=ttk.NORMAL)
            self.stop_event.clear()
            while not self.file_queue.empty():
                self.file_queue.get()
            for path in normalized_paths:
                if os.path.isfile(path):
                    self.file_queue.put((path, 'file'))
                elif os.path.isdir(path):
                    self.file_queue.put((path, 'directory'))
            if not self.processing_thread or not self.processing_thread.is_alive():
                self.processing_thread = Thread(target=self.process_files_from_queue)
                self.processing_thread.start()
            self.update_status_bar("processing_in_progress")
        except Exception as e:
            logging.error(f"添加文件到队列时出错: {e}")
            self.handle_error(e, "添加文件到队列")
            self.start_button.config(state=ttk.NORMAL)
            self.stop_button.config(state=ttk.DISABLED)
    def process_files_from_queue(self):
        """处理文件队列中的文件"""
        try:
            processed_count = 0
            total_files = self.file_queue.qsize()
            while not self.file_queue.empty() and not self.stop_event.is_set():
                try:
                    path, path_type = self.file_queue.get_nowait()
                    if path_type == 'file':
                        is_duplicate = False
                        for item in self.files_tree.get_children():
                            current_path = self.files_tree.item(item)['values'][0]
                            if path == current_path:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            self.add_file_to_list(path)
                            processed_count += 1
                    elif path_type == 'directory':
                        self.process_directory(path)
                    self.root.after(0, lambda: self.update_status_bar("processing_files", 
                        self.file_queue.qsize(), processed_count, total_files))
                except queue.Empty:
                    break
                except Exception as e:
                    logging.error(f"处理文件时出错: {path}, 错误: {e}")
                    continue
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.update_status_bar("files_ready"))
                self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
                self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))
        except Exception as e:
            logging.error(f"处理文件队列时出错: {e}")
            self.handle_error(e, "处理文件队列")
            self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))
    def process_directory(self, dir_path: str):
        """处理目录，使用生成器减少内存使用"""
        try:
            file_count = 0
            file_batch = []
            for root, _, files in os.walk(dir_path):
                if self.stop_event.is_set():
                    return
                for file in files:
                    if self.stop_event.is_set():
                        return
                    file_path = os.path.join(root, file)
                    self.file_queue.put((file_path, 'file'))
                    file_count += 1
                    self.root.after(0, lambda count=file_count: self.update_status_bar("added_files_to_queue", count))
                    self.root.update_idletasks()
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
            for item in self.files_tree.get_children():
                if file_path == self.files_tree.item(item, 'values')[0]:
                    logging.info(f"文件已存在，跳过添加: {file_path}")
                    return
            file_count = len(self.files_tree.get_children())
            ext = os.path.splitext(file_path)[1].lower()
            status = ""
            new_name = ""
            try:
                exif_data = None
                if ext in SUPPORTED_IMAGE_FORMATS:
                    if ext == '.heic':
                        exif_data = self.get_heic_data(file_path) 
                    else:
                        exif_data = self.get_exif_data(file_path)
                elif ext in ['.mov', '.mp4', '.avi', '.mkv']:
                    date_obj = self.get_video_creation_date(file_path)
                    if date_obj:
                        exif_data = {'DateTimeOriginalParsed': date_obj}
                if exif_data:
                    status = self.detect_file_status(file_path, exif_data)
                    new_name = self.generate_new_name(file_path, exif_data)
                else:
                    status = self.lang["ready_to_rename"]
                    new_name = self.generate_new_name(file_path, None)
            except Exception as e:
                logging.error(f"读取文件信息失败: {file_path}, 错误: {e}")
                self.handle_error(e, f"读取文件信息: {file_path}")
                status = self.lang["ready_to_rename"]
                new_name = os.path.basename(file_path)
            values = (file_path, new_name, status)
            basename = os.path.basename(file_path)
            def update_ui():
                try:
                    self.status_label.config(text=f"正在加载: {basename}")
                    self.files_tree.insert('', 'end', values=values)
                    if self.auto_scroll_var.get() and self.files_tree.get_children():
                        self.files_tree.see(self.files_tree.get_children()[-1])
                    self.update_file_count()  
                except Exception as e:
                    logging.error(f"更新UI时出错: {e}")
                    self.handle_error(e, "更新UI")
            self.root.after(0, update_ui)
        except Exception as e:
            logging.error(f"添加文件到列表时出错: {file_path}, 错误: {e}")
            self.handle_error(e, f"添加文件到列表: {file_path}")
    def update_renamed_name_column(self):
        """更新重命名后的文件名列"""
        self.remove_invalid_files()  
        for item in self.files_tree.get_children():
            try:
                values = self.files_tree.item(item)['values']
                if not values or len(values) < 3:
                    continue
                file_path = str(values[0])  
                if not file_path:
                    continue
                if not os.path.exists(file_path):
                    new_name = str(values[1]) if values[1] else ""  
                    if new_name and new_name != self.lang["ready_to_rename"]:
                        directory = os.path.dirname(file_path)
                        new_path = os.path.join(directory, new_name)
                        if os.path.exists(new_path):
                            self.files_tree.item(item, values=(new_path, new_name, values[2]))
                            file_path = new_path
                        else:
                            continue
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
                if new_name:  
                    self.files_tree.set(item, 'renamed_name', new_name)
            except Exception as e:
                logging.error(f"更新重命名列时出错: {e}")
                continue
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
        self.stop_event.clear()
        self.renaming_in_progress = True
        self.start_button.config(state=ttk.DISABLED)
        self.stop_button.config(state=ttk.NORMAL)
        Thread(target=self.rename_photos_thread).start()
    def is_already_renamed(self, filename, template, suffix_style, file_path):
        """判断文件名是否已经符合当前模板+后缀规则，并检查日期基准"""
        try:
            current_date_basis = self.date_basis_var.get()
            date_match = re.match(r"(\d{8})_(\d{6})", filename)
            if not date_match:
                return False
            file_date = date_match.group(1)
            file_time = date_match.group(2)
            exif_data = self.get_exif_data(file_path)
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
                    date_obj = date_obj.replace(microsecond=0)
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
                # 使用字典来存储所有可能的变量值
                variables = {
                    "{date}": date_obj.strftime("%Y%m%d"),
                    "{time}": date_obj.strftime("%H%M%S"),
                    "{original}": os.path.splitext(os.path.basename(file_path))[0]
                }
                
                # 添加 EXIF 数据变量
                if exif_data:
                    if 'Model' in exif_data:
                        variables["{camera}"] = exif_data['Model']
                    if 'LensModel' in exif_data:
                        variables["{lens}"] = exif_data['LensModel']
                    if 'ISOSpeedRatings' in exif_data:
                        variables["{iso}"] = exif_data['ISOSpeedRatings']
                    if 'FNumber' in exif_data:
                        variables["{aperture}"] = f"f{exif_data['FNumber']}"
                    if 'ExposureTime' in exif_data:
                        variables["{shutter}"] = exif_data['ExposureTime']
                    if 'ImageWidth' in exif_data:
                        variables["{width}"] = exif_data['ImageWidth']
                    if 'ImageHeight' in exif_data:
                        variables["{height}"] = exif_data['ImageHeight']
                
                # 按变量长度降序排序，避免部分替换问题
                sorted_vars = sorted(variables.keys(), key=len, reverse=True)
                
                # 替换所有变量
                new_name = template
                for var in sorted_vars:
                    new_name = new_name.replace(var, variables[var])
                
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = new_name
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = new_name + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)
    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        """生成唯一文件名，避免批量重命名冲突"""
        try:
            directory = os.path.abspath(os.path.normpath(directory))
            
            # 检查日期时间格式
            date_time_match = re.match(r"(\d{8})_(\d{6})", base_name)
            if not date_time_match:
                logging.info(f"文件名 {base_name} 不符合日期时间格式，直接返回")
                return base_name + ext
                
            date_part = date_time_match.group(1)
            time_part = date_time_match.group(2)
            logging.info(f"处理文件: {base_name}, 日期: {date_part}, 时间: {time_part}")
            
            # 获取所有可能的后缀模式
            suffix_patterns = [
                r"_\d{3}$",  # _001
                r"-\d{2}$",  # -01
                r"_\d+$"     # _1
            ]
            
            # 检查文件是否已经包含任何后缀
            has_suffix = any(re.search(pattern, base_name) for pattern in suffix_patterns)
            if has_suffix:
                logging.info(f"文件名 {base_name} 已包含后缀，直接返回")
                return base_name + ext
                
            existing_files = []
            for file in os.listdir(directory):
                if file.endswith(ext):
                    file_base = os.path.splitext(file)[0]
                    # 移除任何现有的后缀
                    for pattern in suffix_patterns:
                        file_base = re.sub(pattern, '', file_base)
                    
                    file_match = re.match(r"(\d{8})_(\d{6})", file_base)
                    if file_match:
                        file_date = file_match.group(1)
                        file_time = file_match.group(2)
                        if file_date == date_part and file_time == time_part:
                            if os.path.join(directory, file) != os.path.join(directory, base_name + ext):
                                existing_files.append(file)
                                logging.info(f"找到相同时间点的文件: {file}")
            
            if not existing_files:
                logging.info(f"没有找到相同时间点的文件，使用原始名称: {base_name}{ext}")
                return base_name + ext
                
            counter = 1
            max_counter = 999
            while counter <= max_counter:
                if suffix_style == "_001":
                    suffix = f"_{counter:03d}"
                elif suffix_style == "-01":
                    suffix = f"-{counter:02d}"
                elif suffix_style == "_1":
                    suffix = f"_{counter}"
                else:
                    suffix = f"_{counter:03d}"
                new_filename = f"{base_name}{suffix}{ext}"
                if not os.path.exists(os.path.join(directory, new_filename)):
                    logging.info(f"生成新文件名: {new_filename}")
                    return new_filename
                counter += 1
                
            logging.info(f"达到最大计数，使用原始名称: {base_name}{ext}")
            return base_name + ext
        except Exception as e:
            logging.error(f"生成唯一文件名失败: {e}")
            return base_name + ext
    def update_caches_on_rename(self, old_path, new_path):
        """重命名后同步所有缓存key，保持界面和数据一致"""
        try:
            info = self.file_info_cache.get(old_path)
            if info:
                new_info = self.cache_file_info(new_path)
                if new_info:
                    self.file_info_cache.set(new_path, new_info)
                self.file_info_cache.remove(old_path)
            exif = self.exif_cache.get(old_path)
            if exif is not None:
                self.exif_cache.put(new_path, exif)
                self.exif_cache.put(old_path, None)
            status = self.status_cache.get(old_path)
            if status is not None:
                self.status_cache.put(new_path, status)
                self.status_cache.put(old_path, None)
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
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                logging.error(f"源文件不存在: {source_path}")
                return False
                
            # 检查源文件是否可读
            if not os.access(source_path, os.R_OK):
                logging.error(f"源文件不可读: {source_path}")
                return False
                
            # 检查目标目录是否可写
            target_dir = os.path.dirname(target_path)
            if not os.access(target_dir, os.W_OK):
                logging.error(f"目标目录不可写: {target_dir}")
                return False
                
            # 检查磁盘空间
            source_size = os.path.getsize(source_path)
            free_space = shutil.disk_usage(target_dir).free
            if free_space < source_size:
                logging.error(f"目标磁盘空间不足: {target_dir}")
                return False
                
            # 如果源文件和目标文件是同一个文件，直接返回成功
            if os.path.exists(target_path) and os.path.samefile(source_path, target_path):
                return True
                
            # 创建临时文件
            temp_path = target_path + '.tmp'
            backup_path = source_path + '.bak'
            
            try:
                # 先备份源文件
                shutil.copy2(source_path, backup_path)
                
                # 验证备份文件
                if not os.path.exists(backup_path) or os.path.getsize(backup_path) != source_size:
                    raise Exception("备份文件验证失败")
                    
                # 复制到临时文件
                shutil.copy2(source_path, temp_path)
                
                # 验证临时文件
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) != source_size:
                    raise Exception("临时文件验证失败")
                    
                # 如果目标文件存在，先备份
                target_backup = None
                if os.path.exists(target_path):
                    target_backup = target_path + '.bak'
                    os.rename(target_path, target_backup)
                    
                try:
                    # 重命名临时文件为目标文件
                    os.rename(temp_path, target_path)
                    
                    # 验证目标文件
                    if not os.path.exists(target_path) or os.path.getsize(target_path) != source_size:
                        raise Exception("目标文件验证失败")
                        
                    # 删除源文件
                    os.remove(source_path)
                    
                    # 清理备份文件
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    if target_backup and os.path.exists(target_backup):
                        os.remove(target_backup)
                        
                    return True
                    
                except Exception as e:
                    # 如果重命名失败，尝试恢复
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    if target_backup and os.path.exists(target_backup):
                        try:
                            os.rename(target_backup, target_path)
                        except:
                            pass
                    # 恢复源文件
                    if os.path.exists(backup_path):
                        try:
                            shutil.copy2(backup_path, source_path)
                        except:
                            pass
                    raise e
                    
            except Exception as e:
                # 清理所有临时文件
                for path in [temp_path, backup_path]:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass
                raise e
                
        except Exception as e:
            logging.error(f"重命名文件失败: {source_path} -> {target_path}, 错误: {e}")
            return False
    def rename_photo(self, file_path: str, item: str) -> tuple:
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, self.lang["file_not_found"]
                
            # 检查文件是否可读
            if not os.access(file_path, os.R_OK):
                return False, self.lang["file_not_readable"]
                
            # 检查文件是否被其他程序占用
            try:
                with open(file_path, 'a+b') as f:
                    pass
            except PermissionError:
                return False, self.lang["file_in_use"]
                
            # 获取文件信息
            exif_data = self.get_exif_data(file_path)
            date_basis = self.date_basis_var.get()
            date_obj = None
            
            # 根据日期基准获取日期
            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                    date_obj = date_obj.replace(microsecond=0)
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
                    
            # 生成新文件名
            new_name = self.generate_new_name(file_path, exif_data)
            if not new_name:
                return False, self.lang["rename_skipped_no_name"]
                
            # 检查新文件名是否合法
            if not self.sanitize_filename(new_name):
                return False, self.lang["invalid_filename"]
                
            directory = os.path.dirname(file_path)
            target_path = os.path.join(directory, new_name)
            
            # 检查目标文件是否存在
            if os.path.exists(target_path):
                if os.path.samefile(file_path, target_path):
                    # 如果是同一个文件，直接返回成功
                    return True, new_name
                else:
                    # 如果目标文件存在但不是同一个文件，生成新的唯一文件名
                    ext = os.path.splitext(new_name)[1]
                    base_name = os.path.splitext(new_name)[0]
                    suffix_style = self.suffix_option_var.get()
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                    target_path = os.path.join(directory, new_name)
                    
            # 检查目标目录是否可写
            if not os.access(directory, os.W_OK):
                return False, self.lang["directory_not_writable"]
                
            # 检查磁盘空间
            source_size = os.path.getsize(file_path)
            free_space = shutil.disk_usage(directory).free
            if free_space < source_size:
                return False, self.lang["insufficient_disk_space"]
                
            # 执行重命名
            if self.safe_rename_file(file_path, target_path):
                # 更新缓存
                self.update_caches_on_rename(file_path, target_path)
                return True, new_name
            else:
                return False, self.lang["rename_failed"]
                
        except Exception as e:
            logging.error(f"重命名文件失败: {file_path}, 错误: {e}")
            return False, str(e)
    def get_heic_data(self, file_path):
        """获取 HEIC 文件的 EXIF 信息，并缓存结果"""
        cached_data = self.exif_cache.get(file_path)
        if cached_data:
            return cached_data
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
                self.exif_cache.put(file_path, {})
                return {}
            exif_dict = piexif.load(heif_file.info['exif'])
            exif_data = {}
            if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                try:
                    date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                    date_str = date_str.replace("上午", "").replace("下午", "").strip()
                    try:
                        exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        formats = ['%Y:%m:%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M']
                        for fmt in formats:
                            try:
                                exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                    self.exif_cache.put(file_path, exif_data)
                    return exif_data
                except Exception as e:
                    logging.error(f"解析HEIC日期格式失败: {file_path}, 原始日期字符串: {date_str}, 错误: {e}")
                    try:
                        match = re.search(r'(\d{4})(\d{2})(\d{2})[-_]?(\d{2})(\d{2})(\d{2})', filename)
                        if match:
                            year, month, day, hour, minute, second = map(int, match.groups())
                            date_obj = datetime.datetime(year, month, day, hour, minute, second)
                            exif_data['DateTimeOriginalParsed'] = date_obj
                            self.exif_cache.put(file_path, exif_data)
                            return exif_data
                    except Exception:
                        pass
            self.exif_cache.put(file_path, {})
            return {}
        except Exception as e:
            logging.error(f"读取HEIC数据失败: {file_path}, 错误: {e}")
            self.handle_error(e, f"读取HEIC数据: {file_path}")
            self.exif_cache.put(file_path, {})
        return {}
    def create_tooltip(self, widget, text):
        """创建工具提示，鼠标移出或点击时关闭"""
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            widget.tooltip_window.destroy()
        tooltip = Toplevel(widget)
        tooltip.wm_overrideredirect(True)  
        x = widget.winfo_pointerx() + 10
        y = widget.winfo_pointery() + 10
        tooltip.geometry(f"+{x}+{y}")
        label = Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, anchor='w', justify='left')
        label.pack(fill='both', expand=True)
        label.bind("<Button-1>", lambda e: tooltip.destroy())
        tooltip.bind("<Leave>", lambda e: tooltip.destroy())
        widget.tooltip_window = tooltip
    def show_exif_info(self, event):
        """显示文件的 EXIF 信息"""
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
        file_path = self.files_tree.item(item, 'values')[0]
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
        original_name = os.path.basename(file_path)
        exif_info += f"旧名称: {original_name}\n"
        new_name = self.generate_new_name(file_path, exif_data)
        exif_info += f"新名称: {new_name}\n"
        mod_date = self.get_file_modification_date(file_path)
        if mod_date:
            exif_info += f"修改日期: {mod_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        create_date = self.get_file_creation_date(file_path)
        if create_date:
            exif_info += f"创建日期: {create_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        if exif_data:
            if 'DateTimeOriginalParsed' in exif_data:
                exif_info += f"拍摄日期: {exif_data['DateTimeOriginalParsed'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            if 'Model' in exif_data:
                exif_info += f"拍摄设备: {exif_data['Model']}"
            if 'LensModel' in exif_data:
                exif_info += f"镜头: {exif_data['LensModel']}\n"
            if 'ISOSpeedRatings' in exif_data:
                exif_info += f"ISO: {exif_data['ISOSpeedRatings']}\n"
            if 'FNumber' in exif_data:
                exif_info += f"光圈: f/{exif_data['FNumber']}\n"
            if 'ExposureTime' in exif_data:
                exif_info += f"快门速度: {exif_data['ExposureTime']} 秒\n"
            if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                exif_info += f"分辨率: {exif_data['ImageWidth']}x{exif_data['ImageHeight']}\n"
        return exif_info
    def get_file_modification_date(self, file_path: str) -> Optional[datetime.datetime]:
        """获取文件修改日期"""
        try:
            file_path = os.path.normpath(file_path)
            if sys.platform == 'win32':
                file_path = file_path.replace('/', '\\')
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None
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
            file_path = os.path.normpath(file_path)
            if sys.platform == 'win32':
                file_path = file_path.replace('/', '\\')
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None
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
        self.update_file_count()  
    def stop_renaming(self):
        self.stop_event.set()
    def clear_file_list(self):
        self.files_tree.delete(*self.files_tree.get_children())
        self.update_file_count()  
    def open_file(self, event):
        """双击打开文件"""
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
        file_path = self.files_tree.item(item, 'values')[0]
        new_name = self.files_tree.item(item, 'values')[1]
        if not os.path.exists(file_path):
            directory = os.path.dirname(file_path)
            if new_name and new_name != self.lang["ready_to_rename"]:
                new_path = os.path.join(directory, new_name)
                if os.path.exists(new_path):
                    file_path = new_path
                else:
                    self.update_status_bar("file_not_found", file_path)
                    return
            else:
                self.update_status_bar("file_not_found", file_path)
                return
        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  
                subprocess.run(['open', file_path])
            else:  
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            logging.error(f"打开文件失败: {file_path}, 错误: {e}")
            self.handle_error(e, "打开文件")
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
            date_basis = self.date_basis_var.get()
            used_basis = None
            date_obj = None
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
            used_basis, date_obj = get_date_by_basis(date_basis)
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
        if not os.path.exists(file_path):
            directory = os.path.dirname(file_path)
            if new_name and new_name != self.lang["ready_to_rename"]:
                new_path = os.path.join(directory, new_name)
                if os.path.exists(new_path):
                    file_path = new_path
                else:
                    self.create_tooltip(event.widget, f"文件不存在: {file_path}")
                    return
            else:
                self.create_tooltip(event.widget, f"文件不存在: {file_path}")
                return
        def process_info():
            try:
                try:
                    stat = os.stat(file_path)
                    modification_date = datetime.datetime.fromtimestamp(stat.st_mtime)
                    if hasattr(stat, 'st_birthtime'):  
                        creation_date = datetime.datetime.fromtimestamp(stat.st_birthtime)
                    elif hasattr(stat, 'st_ctime'):    
                        creation_date = datetime.datetime.fromtimestamp(stat.st_ctime)
                    else:                              
                        creation_date = datetime.datetime.fromtimestamp(stat.st_ctime)
                except (OSError, AttributeError) as e:
                    logging.error(f"获取文件状态失败: {file_path}, 错误: {e}")
                    self.root.after(0, lambda: self.create_tooltip(event.widget, f"获取文件状态失败: {str(e)}"))
                    return
                exif_data = None
                try:
                    if file_path.lower().endswith('.heic'):
                        exif_data = self.get_heic_data(file_path)
                    else:
                        exif_data = self.get_exif_data(file_path)
                except Exception as e:
                    logging.error(f"获取EXIF数据失败: {file_path}, 错误: {e}")
                    exif_data = None
                if not new_name:
                    generated_name = self.generate_new_name(file_path, exif_data)
                    self.root.after(0, lambda: self.files_tree.set(item, 'renamed_name', generated_name))
                    info = self.extract_omitted_info(file_path, exif_data, generated_name)
                else:
                    info = self.extract_omitted_info(file_path, exif_data, new_name)
                self.root.after(0, lambda: self.create_tooltip(event.widget, info))
            except Exception as e:
                logging.error(f"显示文件信息出错: {e}")
                self.handle_error(e, "显示文件信息")
        Thread(target=process_info, daemon=True).start()
    def extract_omitted_info(self, file_path, exif_data, new_name):
        """提取被省略的信息"""
        try:
            info = []
            try:
                stat = os.stat(file_path)
                try:
                    mtime = stat.st_mtime
                    modification_date = datetime.datetime.fromtimestamp(mtime)
                    info.append(f"修改日期: {modification_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except (AttributeError, OSError):
                    pass
                try:
                    if hasattr(stat, 'st_birthtime'):  
                        birth_time = stat.st_birthtime
                    elif hasattr(stat, 'st_ctime'):    
                        birth_time = stat.st_ctime
                    else:                              
                        birth_time = stat.st_ctime
                    creation_date = datetime.datetime.fromtimestamp(birth_time)
                    info.append(f"创建日期: {creation_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except (AttributeError, OSError):
                    pass
            except (OSError, AttributeError):
                pass
            if exif_data:
                if 'DateTimeOriginalParsed' in exif_data:
                    info.append(f"拍摄日期: {exif_data['DateTimeOriginalParsed'].strftime('%Y-%m-%d %H:%M:%S')}")
                if 'Make' in exif_data:
                    info.append(f"相机品牌: {exif_data['Make']}")
                if 'Model' in exif_data:
                    info.append(f"相机型号: {exif_data['Model']}")
                if 'LensModel' in exif_data:
                    info.append(f"镜头型号: {exif_data['LensModel']}")
                if 'FNumber' in exif_data:
                    info.append(f"光圈: f/{exif_data['FNumber']}")
                if 'ExposureTime' in exif_data:
                    info.append(f"快门速度: {exif_data['ExposureTime']}")
                if 'ISOSpeedRatings' in exif_data:
                    info.append(f"ISO: {exif_data['ISOSpeedRatings']}")
                if 'FocalLength' in exif_data:
                    info.append(f"焦距: {exif_data['FocalLength']}mm")
            if new_name and new_name != self.lang["ready_to_rename"]:
                info.append(f"新名称: {new_name}")
            return "\n".join(info)
        except Exception as e:
            logging.error(f"提取被省略信息失败: {file_path}, 错误: {e}")
            return f"提取信息失败: {str(e)}"
    def stop_all_operations(self):
        """停止所有操作，包括文件加载、重命名等"""
        try:
            self.stop_event.set()
            self.stop_update_event.set()
            if self.update_thread and self.update_thread.is_alive():
                self.update_thread.join(timeout=1.0)
            while not self.update_queue.empty():
                try:
                    self.update_queue.get_nowait()
                    self.update_queue.task_done()
                except queue.Empty:
                    break
            self.reset_stop_event()
        except Exception as e:
            logging.error(f"停止操作时发生错误: {e}")
    def reset_stop_event(self):
        """重置停止事件"""
        self.stop_event.clear()
        self.stop_update_event.clear()
    def rename_photo_with_name(self, file_path, item, new_name):
        try:
            # 规范化路径
            file_path = os.path.normpath(file_path)
            directory = os.path.normpath(os.path.dirname(file_path))
            new_file_path = os.path.normpath(os.path.join(directory, new_name))
            
            # 检查源文件是否存在
            if not os.path.exists(file_path):
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["file_not_found"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            # 检查源文件是否可读
            if not os.access(file_path, os.R_OK):
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["file_not_readable"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            # 检查文件是否被其他程序占用
            try:
                with open(file_path, 'a+b') as f:
                    pass
            except PermissionError:
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["file_in_use"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            # 检查目标目录是否可写
            if not os.access(directory, os.W_OK):
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["directory_not_writable"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            # 检查磁盘空间
            source_size = os.path.getsize(file_path)
            free_space = shutil.disk_usage(directory).free
            if free_space < source_size:
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["insufficient_disk_space"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            # 检查目标文件是否存在
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
                
            # 执行重命名
            if self.safe_rename_file(file_path, new_file_path):
                # 更新缓存
                self.update_caches_on_rename(file_path, new_file_path)
                with self.lock:
                    self.files_tree.set(item, 'filename', new_file_path)
                    self.files_tree.set(item, 'renamed_name', new_name)
                    self.files_tree.set(item, 'status', '已重命名')
                    self.files_tree.item(item, tags=('renamed',))
                return True, new_file_path
            else:
                with self.lock:
                    self.files_tree.set(item, 'status', self.lang["rename_failed"])
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
        except Exception as e:
            logging.error(f"重命名失败: {str(e)}")
            with self.lock:
                self.files_tree.set(item, 'status', f'错误: {e}')
                self.files_tree.item(item, tags=('failed',))
                self.unrenamed_files += 1
            return False, None
    def cache_file_info(self, file_path):
        """缓存文件信息"""
        try:
            file_path = os.path.normpath(file_path)
            if not os.path.exists(file_path):
                return None
            info = {}
            try:
                stat = os.stat(file_path)
                try:
                    mtime = stat.st_mtime
                    info['modification_date'] = datetime.datetime.fromtimestamp(mtime)
                except (AttributeError, OSError) as e:
                    logging.error(f"获取文件修改时间失败: {file_path}, 错误: {e}")
                    info['modification_date'] = None
                try:
                    if hasattr(stat, 'st_birthtime'):  
                        birth_time = stat.st_birthtime
                    elif hasattr(stat, 'st_ctime'):    
                        birth_time = stat.st_ctime
                    else:                              
                        birth_time = stat.st_ctime
                    info['creation_date'] = datetime.datetime.fromtimestamp(birth_time)
                except (AttributeError, OSError) as e:
                    logging.error(f"获取文件创建时间失败: {file_path}, 错误: {e}")
                    info['creation_date'] = None
            except (OSError, AttributeError) as e:
                logging.error(f"获取文件状态失败: {file_path}, 错误: {e}")
                return None
            ext = os.path.splitext(file_path)[1].lower()
            if ext in SUPPORTED_IMAGE_FORMATS:
                if ext == '.heic':
                    info['exif_data'] = self.get_heic_data(file_path)
                else:
                    info['exif_data'] = self.get_exif_data(file_path)
            elif ext in ['.mov', '.mp4', '.avi', '.mkv']:
                info['video_date'] = self.get_video_creation_date(file_path)
            if hasattr(self, 'file_info_cache'):
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
            self.stop_all_operations()
            try:
                self.cleanup_cache()
            except Exception as e:
                logging.error(f"清理缓存失败: {e}")
            for window in self.toplevel_windows:
                try:
                    window.destroy()
                except:
                    pass
            self.root.destroy()
        except Exception as e:
            logging.error(f"关闭程序时出错: {e}")
            self.root.destroy()
    def get_cached_or_real_modification_date(self, file_path):
        """获取文件的修改日期，优先使用缓存"""
        try:
            file_path = os.path.abspath(os.path.normpath(file_path))
            if not os.path.exists(file_path):
                logging.error(f"文件不存在: {file_path}")
                return None
            if not os.access(file_path, os.R_OK):
                logging.error(f"无法访问文件: {file_path}，权限不足")
                return None
            modification_time = os.path.getmtime(file_path)
            date_obj = datetime.datetime.fromtimestamp(modification_time)
            date_obj = date_obj.replace(microsecond=0)
            logging.info(f"文件 {file_path} 的修改时间: {date_obj}")
            return date_obj
        except Exception as e:
            logging.error(f"获取文件修改日期失败: {file_path}, 错误: {e}")
            return None
    def get_cached_or_real_creation_date(self, file_path):
        """获取文件的创建日期，优先使用缓存"""
        try:
            file_path = os.path.normpath(file_path)
            if hasattr(self, 'file_info_cache'):
                info = self.file_info_cache.get(file_path)
                if info and 'creation_date' in info and info['creation_date']:
                    return info['creation_date']
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                try:
                    if hasattr(stat, 'st_birthtime'):  
                        birth_time = stat.st_birthtime
                    elif hasattr(stat, 'st_ctime'):    
                        birth_time = stat.st_ctime
                    else:                              
                        birth_time = stat.st_ctime
                    date_obj = datetime.datetime.fromtimestamp(birth_time)
                    if hasattr(self, 'file_info_cache'):
                        if not info:
                            info = {}
                        info['creation_date'] = date_obj
                        self.file_info_cache.set(file_path, info)
                    return date_obj
                except (AttributeError, OSError) as e:
                    logging.error(f"获取文件创建时间失败: {file_path}, 错误: {e}")
            return None
        except Exception as e:
            logging.error(f"获取文件创建日期失败: {file_path}, 错误: {e}")
            return None
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
                # 使用字典来存储所有可能的变量值
                variables = {
                    "{date}": date_obj.strftime("%Y%m%d"),
                    "{time}": date_obj.strftime("%H%M%S"),
                    "{original}": os.path.splitext(os.path.basename(file_path))[0]
                }
                
                # 添加 EXIF 数据变量
                if exif_data:
                    if 'Model' in exif_data:
                        variables["{camera}"] = exif_data['Model']
                    if 'LensModel' in exif_data:
                        variables["{lens}"] = exif_data['LensModel']
                    if 'ISOSpeedRatings' in exif_data:
                        variables["{iso}"] = exif_data['ISOSpeedRatings']
                    if 'FNumber' in exif_data:
                        variables["{aperture}"] = f"f{exif_data['FNumber']}"
                    if 'ExposureTime' in exif_data:
                        variables["{shutter}"] = exif_data['ExposureTime']
                    if 'ImageWidth' in exif_data:
                        variables["{width}"] = exif_data['ImageWidth']
                    if 'ImageHeight' in exif_data:
                        variables["{height}"] = exif_data['ImageHeight']
                
                # 按变量长度降序排序，避免部分替换问题
                sorted_vars = sorted(variables.keys(), key=len, reverse=True)
                
                # 替换所有变量
                new_name = template
                for var in sorted_vars:
                    new_name = new_name.replace(var, variables[var])
                
                if add_suffix:
                    suffix_style = self.suffix_option_var.get()
                    base_name = new_name
                    new_name = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                else:
                    new_name = new_name + ext
                return new_name
            else:
                return os.path.basename(file_path)
        except Exception as e:
            logging.error(f"生成新名称失败: {file_path}, 错误: {e}")
            return os.path.basename(file_path)
class TemplateEditor(ttk.Frame):
    def __init__(self, parent, template_var, prefix_var=None, suffix_var=None, lang=None, main_app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.template_var = template_var  
        self.prefix_var = prefix_var
        self.suffix_var = suffix_var
        self.lang = lang or LANGUAGES["简体中文"]  
        self.config = configparser.ConfigParser()
        self.config_file = 'QphotoRenamer.ini'
        self.main_app = main_app
        self.is_modified = False  
        self.last_saved_content = ""  
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
        self.templates = [
            "{date}_{time}",
            "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}",
            "{date}_{time}_{camera}",
            "{camera}_{lens}_{iso}_{focal}_{aperture}",
            "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}_{shutter}"
        ]
        self.default_template = None
        self.setup_ui()
        self.load_templates()
        if self.default_template:
            self.set_template(self.default_template)
            self.template_combobox.set(self.default_template)
        elif self.template_var.get():
            self.set_template(self.template_var.get())
            self.template_combobox.set(self.template_var.get())
        else:
            self.set_template(self.templates[0])
            self.template_combobox.set(self.templates[0])
        self.update_preview()
    def setup_ui(self):
        """设置UI界面"""
        top_frame = ttk.Frame(self)
        top_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        middle_frame = ttk.Frame(self)
        middle_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)
        preset_frame = ttk.LabelFrame(top_frame, text="选择模板")
        preset_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        preset_top_frame = ttk.Frame(preset_frame)
        preset_top_frame.pack(fill=ttk.X, padx=5, pady=5)
        self.template_combobox = ttk.Combobox(preset_top_frame, values=self.templates, state="readonly", width=50)
        self.template_combobox.pack(side=ttk.LEFT, padx=5, pady=5, fill=ttk.X, expand=True)
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)
        button_frame = ttk.Frame(preset_top_frame)
        button_frame.pack(side=ttk.RIGHT, padx=5)
        save_button = ttk.Button(button_frame, text=self.lang["save_template"], command=self.save_current_template, width=8)
        save_button.pack(side=ttk.LEFT, padx=2)
        save_button.text_key = "save_template"
        delete_button = ttk.Button(button_frame, text=self.lang["delete_template"], command=self.delete_current_template, width=8)
        delete_button.pack(side=ttk.LEFT, padx=2)
        delete_button.text_key = "delete_template"
        edit_frame = ttk.LabelFrame(top_frame, text="编辑模板")
        edit_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        self.template_text = tk.Text(edit_frame, height=3, wrap=tk.WORD)
        self.template_text.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        def on_text_change(event=None):
            template = self.template_text.get("1.0", END).strip()
            self.template_var.set(template)  
            self.update_preview()  
            return True
        self.template_text.bind('<KeyRelease>', on_text_change)
        self.template_text.bind('<KeyPress>', on_text_change)
        self.template_text.bind('<<Paste>>', on_text_change)
        self.template_text.bind('<<Cut>>', on_text_change)
        self.template_text.bind('<Delete>', on_text_change)
        self.template_text.bind('<BackSpace>', on_text_change)
        variables_frame = ttk.LabelFrame(middle_frame, text="变量")
        variables_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        self.create_variable_buttons(variables_frame, self.variables)
        preview_frame = ttk.LabelFrame(bottom_frame, text="预览")
        preview_frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        self.preview_label = ttk.Label(preview_frame, text="", anchor='w', wraplength=0)
        self.preview_label.pack(fill=ttk.X, padx=5, pady=5)
        parent = self.winfo_toplevel()
        original_close_handler = getattr(parent, 'protocol', lambda *args: None)('WM_DELETE_WINDOW')
        def on_parent_close():
            """父窗口关闭时检查是否有未保存的修改"""
            if self.has_unsaved_changes():
                if messagebox.askyesno("未保存的修改", "模板编辑器中有未保存的修改，是否保存？"):
                    self.save_current_template()
            if callable(original_close_handler):
                original_close_handler()
            else:
                parent.destroy()
        parent.protocol("WM_DELETE_WINDOW", on_parent_close)
    def update_preview(self, event=None):
        """更新预览"""
        template = self.template_text.get("1.0", END).strip()
        if template != self.last_saved_content:
            self.is_modified = True
            is_new_template = template not in self.templates
            if is_new_template and template:
                current_values = list(self.template_combobox['values'])
                if "(新模板)" not in current_values:
                    new_values = current_values + ["(新模板)"]
                    self.template_combobox['values'] = new_values
                    self.template_combobox.set("(新模板)")
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
        self.preview_label.config(text=preview)
        if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
            self.main_app.update_renamed_name_column()
        return True
    def clear_template(self):
        """清除模板内容"""
        self.template_text.delete("1.0", END)
        self.update_preview()
        self.is_modified = True
    def on_drop(self, event):
        """处理拖放事件"""
        current_content = self.template_text.get("1.0", END).strip()
        self.template_text.insert(INSERT, event.data)
        self.update_preview()
        self.is_modified = True
    def create_variable_buttons(self, parent, variables):
        """创建变量按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        for i, (var, desc) in enumerate(variables):
            row = i // 4
            col = i % 4
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            btn = ttk.Button(btn_frame, text=desc, width=8,
                           command=lambda v=var: self.insert_variable(v))
            btn.pack(side=ttk.LEFT, padx=2)
            lbl = ttk.Label(btn_frame, text=var, foreground="gray", width=8)
            lbl.pack(side=ttk.LEFT, padx=2)
        for i in range(4):
            frame.columnconfigure(i, weight=1)
    def has_unsaved_changes(self):
        """检查是否有未保存的修改"""
        current_content = self.template_text.get("1.0", tk.END).strip()
        return current_content != self.last_saved_content
    def delete_current_template(self):
        """删除当前选中的模板"""
        if self.has_unsaved_changes():
            if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                self.save_current_template()
        current_template = self.template_combobox.get()
        if current_template in self.templates:
            self.templates.remove(current_template)
            try:
                if os.path.exists(self.config_file):
                    self.config.read(self.config_file, encoding='utf-8')
                    if 'Template' in self.config:
                        for key in list(self.config['Template']):
                            if key.startswith('template') and self.config['Template'][key] == current_template:
                                del self.config['Template'][key]
                        with open(self.config_file, 'w', encoding='utf-8') as f:
                            self.config.write(f)
            except Exception as e:
                logging.error(f"从配置文件删除模板失败: {e}")
            self.update_template_combobox()
            if self.templates:
                self.template_combobox.set(self.templates[0])
                self.set_template(self.templates[0])
            else:
                self.clear_template()
                self.template_combobox['values'] = []
                self.template_combobox.set("")
            self.update_status_bar(f"已删除模板: {current_template}")
    def load_templates(self):
        """从配置文件加载模板"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                if self.config.has_option('Template', 'default_template'):
                    self.default_template = self.config.get('Template', 'default_template')
                    self.last_saved_content = self.default_template
                if self.config.has_section('Template'):
                    templates = []
                    # 首先添加默认模板
                    if self.default_template and self.default_template not in templates:
                        templates.append(self.default_template)
                    # 然后添加其他模板
                    for i in range(1, 6):
                        template_key = f'template{i}'
                        if self.config.has_option('Template', template_key):
                            template = self.config.get('Template', template_key)
                            if template and template not in templates:
                                templates.append(template)
                    if templates:
                        self.templates = templates
        except Exception as e:
            logging.error(f"加载模板失败: {e}")
        if not self.templates:
            self.templates = [
                "{date}_{time}",
                "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}",
                "{date}_{time}_{camera}",
                "{camera}_{lens}_{iso}_{focal}_{aperture}",
                "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}_{shutter}"
            ]
        self.update_template_combobox()
    def save_templates(self):
        """保存模板记录到配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
            if 'Template' not in self.config:
                self.config['Template'] = {}
            current_template = self.template_text.get("1.0", END).strip()
            if not current_template:
                self.update_status_bar("模板内容不能为空")
                return
            # 保存为默认模板
            self.config['Template']['default_template'] = current_template
            self.default_template = current_template
            
            # 更新模板列表
            if current_template not in self.templates:
                self.templates.append(current_template)
            
            # 保存所有模板
            for i, template in enumerate(self.templates, 1):
                if template and template != "(新模板)":
                    self.config['Template'][f'template{i}'] = template
            
            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            if self.template_var:
                self.template_var.set(current_template)
            self.update_template_combobox()
            self.template_combobox.set(current_template)
            self.update_status_bar("模板已保存")
        except Exception as e:
            logging.error(f"保存模板记录时出错: {e}")
            self.update_status_bar(f"保存模板失败: {str(e)}")
    def save_current_template(self):
        """保存当前模板"""
        try:
            template = self.template_text.get("1.0", tk.END).strip()
            if not template:
                self.update_status_bar("模板内容不能为空")
                return
            is_new_template = template not in self.templates
            if is_new_template:
                self.templates.append(template)
                self.update_status_bar("新模板已创建并保存")
            else:
                self.update_status_bar("模板已更新")
            self.default_template = template
            self.save_templates()
            self.update_template_combobox()
            self.template_combobox.set(template)
            self.is_modified = False
            self.last_saved_content = template
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
            logging.info(message)  
    def on_template_selected(self, event=None):
        """当选择模板时更新编辑器内容"""
        try:
            selected_template = self.template_combobox.get()
            current_template = self.template_text.get("1.0", tk.END).strip()
            if selected_template != "(新模板)" and selected_template != current_template:
                if self.is_modified:
                    if messagebox.askyesno("未保存的修改", "当前模板有未保存的修改，是否保存？"):
                        if "(新模板)" in self.template_combobox['values'] and self.template_combobox.get() == "(新模板)":
                            if current_template and current_template not in self.templates:
                                self.templates.append(current_template)
                                self.update_status_bar("新模板已保存")
                        self.save_current_template()
                if selected_template in self.templates:
                    self.template_text.delete("1.0", tk.END)
                    self.template_text.insert("1.0", selected_template)
                    self.default_template = selected_template
                    self.save_templates()
                    self.update_status_bar(f"已加载模板: {selected_template}")
                    self.is_modified = False
                    self.last_saved_content = selected_template
                    if self.template_var:
                        self.template_var.set(selected_template)
                    if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
                        self.main_app.update_renamed_name_column()
        except Exception as e:
            error_msg = f"加载模板失败: {str(e)}"
            logging.error(error_msg)
            self.update_status_bar(error_msg)
    def update_template_combobox(self):
        """更新下拉框的选项"""
        current_content = self.template_text.get("1.0", tk.END).strip()
        unique_templates = []
        for t in self.templates:
            if t != "(新模板)" and t not in unique_templates:
                unique_templates.append(t)
        self.templates = unique_templates
        values = self.templates.copy()
        if current_content and current_content not in values and current_content != self.last_saved_content:
            values.append("(新模板)")
        self.template_combobox['values'] = values
    def set_template(self, template):
        """设置模板内容"""
        self.template_text.delete("1.0", END)
        self.template_text.insert("1.0", template)
        self.last_saved_content = template  
        self.is_modified = False  
        if self.template_var:
            self.template_var.set(template)
        self.update_preview()
        if self.main_app and hasattr(self.main_app, 'update_renamed_name_column'):
            self.main_app.update_renamed_name_column()
    def insert_variable(self, variable):
        """插入变量到模板"""
        current_content = self.template_text.get("1.0", END).strip()
        self.template_text.insert(INSERT, variable)
        self.template_var.set(self.template_text.get("1.0", END).strip())
        self.is_modified = True
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    try:
        renamer = PhotoRenamer(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序遇到严重错误: {str(e)}")
        os._exit(1)