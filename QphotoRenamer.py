import os
import sys
import datetime
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, Entry, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread, Event, Lock
import logging
import re
import json
import subprocess
import webbrowser
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from collections import OrderedDict
from functools import lru_cache

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
        "window_title": "文件与照片批量重命名工具 QphotoRenamer 2.2 —— QwejayHuang",
        "description_base": "拖放文件或照片，将按照",
        "description_suffix": "重命名文件。若无法获取拍摄日期（或非媒体文件），则使用",
        "start_renaming": "开始重命名",
        "undo_renaming": "撤销重命名",
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
        "formats_explanation": "常用日期格式示例:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "正在重命名，请稍候...",
        "renaming_stopped": "重命名操作已停止。",
        "renaming_success": "成功重命名 {0} 个文件，未重命名 {1} 个文件。",
        "all_files_restored": "所有文件已恢复为原始名称。",
        "filename": "文件路径",
        "status": "状态",
        "renamed_name": "新名称",
        "prepare_rename_by": "准备以 {} 重命名",
        "prepare_rename_keep_name": "准备保留原文件名",
        "already_rename_by": "已按 {} 命名",
        "ready_to_rename": "待重命名",
        "help_text": """使用说明:
1. 将文件或文件夹拖放到列表中，或点击"添加文件"按钮选择文件。
2. 点击"开始重命名"按钮，程序将根据设置的日期格式重命名文件。
3. 若无法获取拍摄日期，程序将根据设置的备用日期（修改日期、创建日期或保留原文件名）进行处理。
4. 双击列表中的文件名可打开文件。
5. 右键点击列表中的文件名可移除文件。
6. 点击"撤销重命名"按钮可将文件恢复为原始名称。
7. 点击"设置"按钮可调整日期格式、前缀、后缀等设置。
8. 勾选"自动滚动"选项，列表将自动滚动至最新添加的文件。
9. 点击"清空列表"按钮可清空文件列表。
10. 点击"停止重命名"按钮可停止当前的重命名操作。
11. 重命名完成后，已重命名的文件项将显示为绿色，重命名失败的文件项将显示为红色。
12. 点击文件名可查看文件的EXIF信息。""",
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
        "show_errors_only": "仅显示错误"
    },
    "English": {
        "window_title": "QphotoRenamer 2.2 —— QwejayHuang",
        "description_base": "Drag and drop files or photos to rename them based on ",
        "description_suffix": ". If the shooting date is unavailable, use ",
        "start_renaming": "Start Renaming",
        "undo_renaming": "Undo Renaming",
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
        "formats_explanation": "Common Date Format Examples:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "Renaming is in progress, please wait...",
        "renaming_stopped": "Renaming operation has been stopped.",
        "renaming_success": "Successfully renamed {0} files, {1} files were not renamed.",
        "all_files_restored": "All files have been restored to their original names.",
        "filename": "File Path",
        "status": "Status",
        "renamed_name": "New Name",
        "prepare_rename_by": "Ready to rename by {}",
        "prepare_rename_keep_name": "Ready to keep original name",
        "already_rename_by": "Already renamed by {}",
        "ready_to_rename": "Ready to rename",
        "help_text": """Usage Instructions:
1. Drag and drop files or folders into the list, or click the 'Add Files' button to select files.
2. Click the 'Start Renaming' button to rename files based on the specified date format.
3. If the shooting date is unavailable, the program will use the alternate date (modified date, created date, or keep the original name).
4. Double-click a file name in the list to open the file.
5. Right-click a file name in the list to remove it.
6. Click the 'Undo Renaming' button to restore files to their original names.
7. Click the 'Settings' button to adjust the date format, prefix, suffix, and other settings.
8. Enable the 'Auto Scroll' option to automatically scroll to the latest added file.
9. Click the 'Clear List' button to clear the file list.
10. Click the 'Stop Renaming' button to stop the current renaming operation.
11. After renaming, successfully renamed files will be highlighted in green, while failed files will be highlighted in red.
12. Click on a file name to view its EXIF information.""",
        "settings_window_title": "Settings",
        "prefix": "Prefix:",
        "suffix": "Suffix:",
        "skip_extensions": "File extensions to skip renaming (space-separated):",
        "file_count": "Total Files: {0}",
        "fast_add_mode": "Enable Fast Add Mode:",
        "name_conflict_prompt": "When file names conflict after renaming:",
        "add_suffix_option": "Add suffix",
        "keep_original_option": "Keep original name",
        "other_settings": "Other Settings",
        "file_handling_settings": "File Handling Settings",
        "rename_pattern_settings": "Rename Pattern Settings",
        "date_bases": [
            {"display": "Taken Date", "value": "拍摄日期"},
            {"display": "Modified Date", "value": "修改日期"},
            {"display": "Created Date", "value": "创建日期"}
        ],
        "alternate_dates": [
            {"display": "Modified Date", "value": "修改日期"},
            {"display": "Created Date", "value": "创建日期"},
            {"display": "Original Name", "value": "保留原文件名"}
        ],
        "suffix_options": ["_001", "-01", "Custom"],
        "suffix_edit_label": "Edit Suffix Name:",
        "show_errors_only": "Only Errors"
    }
}

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

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

class PhotoRenamer:
    def __init__(self, root):
        # 类变量定义，代替全局变量
        self.date_format = "%Y%m%d_%H%M%S"  # 默认日期格式
        self.stop_event = Event()  # 停止事件
        self.renaming_in_progress = False
        self.original_to_new_mapping = {}
        self.processed_files = set()
        self.unrenamed_files = 0
        self.current_renaming_file = None
        self.skip_extensions = []
        
        # 初始化缓存
        self.exif_cache = LRUCache(1000)  # 最多缓存1000个文件的EXIF信息
        self.status_cache = LRUCache(1000)  # 最多缓存1000个文件的状态
        self.file_hash_cache = LRUCache(1000)  # 最多缓存1000个文件的哈希值
        self.error_cache = {}  # 错误缓存
        self._settings_cache = None  # 设置缓存
        self._update_timer = None  # UI更新定时器
        self._pending_updates = set()  # 待处理的UI更新

        self.root = root
        self.root.title("文件&照片批量重命名 QphotoRenamer 2.2 —— QwejayHuang")
        self.root.geometry("850x600")
        self.root.iconbitmap(icon_path)

        self.style = ttk.Style('litera')
        self.lock = Lock()  # 初始化线程锁

        # 初始化变量
        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.show_errors_only_var = ttk.BooleanVar(value=False)
        self.language_var = ttk.StringVar(value=self.load_language())
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.skip_extensions_var = ttk.StringVar(value="")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")
        self.fast_add_mode_var = ttk.BooleanVar(value=False)
        self.fast_add_threshold_var = ttk.IntVar(value=10)
        self.name_conflict_var = ttk.StringVar(value="add_suffix")
        self.suffix_option_var = ttk.StringVar(value="_001")

        # 初始化语言
        self.lang = LANGUAGES[self.language_var.get()]

        # 初始化文件处理队列
        self.file_queue = Queue()
        self.processing_thread = None

        # 初始化界面
        self.initialize_ui()
        self.load_settings()
        self.set_language(self.language_var.get())
        
        # 设置定期清理缓存
        self.root.after(300000, self.cleanup_cache)  # 每5分钟清理一次缓存

    def get_file_hash(self, file_path: str) -> str:
        """计算文件的MD5哈希值"""
        try:
            # 优化：仅读取文件的前8KB来计算哈希值，而不是整个文件
            # 这对大多数文件来说足够区分，同时显著提高性能
            with open(file_path, 'rb') as f:
                data = f.read(8192)  # 只读取前8KB
                return hashlib.md5(data).hexdigest()
        except Exception as e:
            logging.error(f"计算文件哈希值失败: {file_path}, 错误: {e}")
            return ""

    def cleanup_cache(self):
        """清理过期缓存"""
        try:
            # 清理错误缓存
            current_time = datetime.datetime.now()
            expired_errors = [
                error_id for error_id, data in self.error_cache.items()
                if (current_time - data['last_time']).total_seconds() > 3600  # 1小时后过期
            ]
            for error_id in expired_errors:
                del self.error_cache[error_id]
                
            # 清理设置缓存
            if self._settings_cache and (current_time - self._settings_cache['timestamp']).total_seconds() > 300:  # 5分钟后过期
                self._settings_cache = None
                
            # 清理文件哈希缓存
            self.file_hash_cache = LRUCache(1000)
            
        except Exception as e:
            logging.error(f"清理缓存时出错: {e}")
            
        # 设置下一次清理
        self.root.after(300000, self.cleanup_cache)

    def get_exif_data(self, file_path: str) -> Optional[Dict]:
        """获取文件的 EXIF 信息，并缓存结果"""
        # 检查文件大小
        try:
            if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB
                return None
        except Exception:
            pass

        # 检查文件类型
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_IMAGE_FORMATS:
            return None

        # 检查缓存
        if self.exif_cache.get(file_path):
            return self.exif_cache.get(file_path)

        # 优化：对于很大的照片集，先检查文件名是否已包含日期格式
        # 如果文件名已经是按日期格式命名的，可以跳过EXIF读取
        filename = os.path.basename(file_path)
        for date_format in COMMON_DATE_FORMATS:
            try:
                # 尝试从文件名中解析日期
                date_pattern = date_format.replace('%Y', r'(\d{4})').replace('%m', r'(\d{2})').replace('%d', r'(\d{2})')
                date_pattern = date_pattern.replace('%H', r'(\d{2})').replace('%M', r'(\d{2})').replace('%S', r'(\d{2})')
                
                # 如果文件名与日期模式匹配，则不需要读取EXIF
                if re.match(date_pattern, os.path.splitext(filename)[0]):
                    return None
            except:
                pass

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            with open(file_path, 'rb') as f:
                # 优化：只读取文件前几KB的EXIF数据而不是整个文件
                tags = exifread.process_file(f, details=False, stop_tag='EXIF DateTimeOriginal')
                exif_data = {}
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    # 获取到拍摄日期后就缓存并返回，不再读取其他EXIF信息
                    self.exif_cache.put(file_path, exif_data)
                    return exif_data
                
                # 如果没有拍摄日期，则可能不需要其他EXIF信息
                # 为性能考虑，可以直接返回空字典
                self.exif_cache.put(file_path, {})
                return {}
                
        except Exception as e:
            logging.error(f"读取EXIF数据失败: {file_path}, 错误: {e}")
            self.handle_error(e, f"读取EXIF数据: {file_path}")
        return None

    def handle_error(self, error: Exception, context: str):
        """统一错误处理"""
        error_id = hashlib.md5(str(error).encode()).hexdigest()
        if error_id not in self.error_cache:
            self.error_cache[error_id] = {
                'count': 0,
                'last_time': datetime.datetime.now(),
                'error': str(error),
                'context': context
            }
        
        self.error_cache[error_id]['count'] += 1
        if self.error_cache[error_id]['count'] > 10:
            logging.error(f"频繁错误: {error}, 上下文: {context}")

    def initialize_ui(self):
        # 主界面布局
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True)

        # 描述部分
        self.description_frame = ttk.Frame(main_frame)
        self.description_frame.pack(fill=ttk.X, padx=10, pady=10)

        self.description_label = ttk.Label(self.description_frame, text=self.lang["description_base"])
        self.description_label.pack(side=ttk.LEFT)
        self.description_label.text_key = "description_base"

        self.date_basis_combobox = ttk.Combobox(self.description_frame, textvariable=self.date_basis_var, values=[item['display'] for item in self.lang["date_bases"]], state="readonly", width=10)
        self.date_basis_combobox.pack(side=ttk.LEFT)

        self.description_suffix_label = ttk.Label(self.description_frame, text=self.lang["description_suffix"])
        self.description_suffix_label.pack(side=ttk.LEFT)
        self.description_suffix_label.text_key = "description_suffix"

        self.alternate_date_combobox = ttk.Combobox(self.description_frame, textvariable=self.alternate_date_var, values=[item['display'] for item in self.lang["alternate_dates"]], state="readonly", width=10)
        self.alternate_date_combobox.pack(side=ttk.LEFT)

        # 文件列表
        columns = ('filename', 'renamed_name', 'status')
    
        # 创建一个容器框架来放置 Treeview 和滚动条
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)

        # 创建 Treeview
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        self.files_tree.heading('filename', text=self.lang["filename"], anchor='w')
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"], anchor='w')
        self.files_tree.heading('status', text=self.lang["status"], anchor='w')
        self.files_tree.column('filename', anchor='w', stretch=True, width=400)
        self.files_tree.column('renamed_name', anchor='w', stretch=True, width=200)
        self.files_tree.column('status', anchor='w', width=100, minwidth=100)

        # 创建垂直滚动条
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=vsb.set)

        # 将 Treeview 和滚动条放置在容器框架中
        self.files_tree.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)
        vsb.pack(side=ttk.RIGHT, fill=ttk.Y)

        # 绑定事件
        self.files_tree.drop_target_register(DND_FILES)
        self.files_tree.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_tree.bind('<Button-3>', self.remove_file)
        self.files_tree.bind('<Double-1>', self.open_file)
        self.files_tree.bind('<Button-1>', self.show_exif_info)
        self.files_tree.bind('<ButtonRelease-1>', self.show_omitted_info)

        # 在初始化UI时绑定下拉框的选项变化事件
        self.date_basis_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_renamed_name_column())
        self.alternate_date_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_renamed_name_column())

        # 进度条
        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=ttk.X, padx=10, pady=10)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=ttk.X, padx=10, pady=10)

        # 按钮
        self.start_button = ttk.Button(button_frame, text=self.lang["start_renaming"], command=lambda: self.rename_photos())
        self.start_button.pack(side=ttk.LEFT, padx=5)
        self.start_button.text_key = "start_renaming"

        self.undo_button = ttk.Button(button_frame, text=self.lang["undo_renaming"], command=self.undo_rename)
        self.undo_button.pack(side=ttk.LEFT, padx=5)
        self.undo_button.text_key = "undo_renaming"

        # 修改停止按钮为通用停止按钮
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

    def open_settings(self):
        settings_window = ttk.Toplevel(self.root)
        settings_window.title(self.lang["settings_window_title"])
        settings_window.geometry("500x650")

        # 主框架
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)

        # 重命名样式设置
        rename_pattern_frame = ttk.LabelFrame(main_frame, text=self.lang["rename_pattern_settings"], padding=10)
        rename_pattern_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(rename_pattern_frame, text=self.lang["rename_pattern"], anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        date_format_var = ttk.StringVar(value=self.date_format)
        date_format_combobox = ttk.Combobox(rename_pattern_frame, textvariable=date_format_var, values=COMMON_DATE_FORMATS, state="readonly")
        date_format_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(rename_pattern_frame, text=self.lang["prefix"], anchor='w').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        prefix_entry = Entry(rename_pattern_frame, textvariable=self.prefix_var)
        prefix_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(rename_pattern_frame, text=self.lang["suffix"], anchor='w').grid(row=2, column=0, padx=5, pady=5, sticky='w')
        suffix_entry = Entry(rename_pattern_frame, textvariable=self.suffix_var)
        suffix_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # 分割线
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, sticky="ew", pady=10)

        # 文件处理设置
        file_handling_frame = ttk.LabelFrame(main_frame, text=self.lang["file_handling_settings"], padding=10)
        file_handling_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(file_handling_frame, text=self.lang["skip_extensions"], anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        skip_ext_entry = Entry(file_handling_frame, textvariable=self.skip_extensions_var)
        skip_ext_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # 命名冲突处理设置
        ttk.Label(file_handling_frame, text=self.lang["name_conflict_prompt"], anchor='w').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        name_conflict_combobox = ttk.Combobox(file_handling_frame, textvariable=self.name_conflict_var, values=[self.lang["add_suffix_option"], self.lang["keep_original_option"]], state="readonly")
        name_conflict_combobox.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        # 绑定选项变化事件
        name_conflict_combobox.bind("<<ComboboxSelected>>", lambda event: self.toggle_suffix_option_edit(suffix_option_combobox))

        # 后缀选项设置
        ttk.Label(file_handling_frame, text=self.lang["suffix_edit_label"], anchor='w').grid(row=2, column=0, padx=5, pady=5, sticky='w')
        suffix_option_combobox = ttk.Combobox(file_handling_frame, textvariable=self.suffix_option_var, values=self.lang["suffix_options"], state="normal")
        suffix_option_combobox.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # 初始状态：根据 name_conflict_var 的值设置后缀选项的编辑状态
        self.toggle_suffix_option_edit(suffix_option_combobox)

        # 分割线
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=10)

        # 快速添加模式设置
        fast_add_frame = ttk.LabelFrame(main_frame, text=self.lang["fast_add_mode"], padding=10)
        fast_add_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        # 启用快速添加模式
        fast_add_mode_checkbox = ttk.Checkbutton(
            fast_add_frame,
            text=self.lang["fast_add_mode"],
            variable=self.fast_add_mode_var,
            command=lambda: self.toggle_fast_add_threshold_entry(fast_add_threshold_entry)
        )
        fast_add_mode_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        # 文件数量阈值
        ttk.Label(fast_add_frame, text=self.lang["file_count"].format(""), anchor='w').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        fast_add_threshold_entry = Entry(fast_add_frame, textvariable=self.fast_add_threshold_var, validate="key")
        fast_add_threshold_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        # 限制输入为 1 到 500 的数字
        fast_add_threshold_entry.config(validatecommand=(fast_add_threshold_entry.register(self.validate_threshold_input), "%P"))

        # 初始状态：根据 fast_add_mode_var 的值设置输入框状态
        self.toggle_fast_add_threshold_entry(fast_add_threshold_entry)

        # 分割线
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, sticky="ew", pady=10)

        # 其他设置
        other_settings_frame = ttk.LabelFrame(main_frame, text=self.lang["other_settings"], padding=10)
        other_settings_frame.grid(row=6, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(other_settings_frame, text=self.lang["language"], anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        language_combobox = ttk.Combobox(other_settings_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
        language_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        language_combobox.bind('<<ComboboxSelected>>', lambda event: self.set_language(language_combobox.get()))

        # 保存设置按钮
        save_button = ttk.Button(main_frame, text=self.lang["save_settings"], command=lambda: self.save_settings(date_format_var.get(), self.language_var.get(), self.prefix_var.get(), self.suffix_var.get(), skip_ext_entry.get(), settings_window))
        save_button.grid(row=7, column=0, sticky="ew", padx=5, pady=10)

        # 调整列权重，使内容居中
        main_frame.columnconfigure(0, weight=1)
        rename_pattern_frame.columnconfigure(1, weight=1)
        file_handling_frame.columnconfigure(1, weight=1)
        fast_add_frame.columnconfigure(1, weight=1)
        other_settings_frame.columnconfigure(1, weight=1)

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
        """验证文件数量阈值输入是否为 1 到 500 的数字"""
        if value.isdigit():
            return 1 <= int(value) <= 500
        return False

    def save_settings(self, date_format, language, prefix, suffix, skip_extensions_input, settings_window):
        """保存设置，使用缓存机制"""
        # 验证日期格式
        try:
            datetime.datetime.now().strftime(date_format)
        except ValueError:
            messagebox.showerror("错误", "无效的日期格式！")
            return
        
        # 更新设置
        self.language_var.set(language)
        self.set_language(language)
        self.prefix_var.set(prefix)
        self.suffix_var.set(suffix)
        self.skip_extensions_var.set(skip_extensions_input)
        self.date_format = date_format
        
        skip_ext_input = skip_extensions_input.strip().lower()
        self.skip_extensions = ['.' + ext for ext in skip_ext_input.split()]
        
        # 构建配置字典
        config = {
            "language": language,
            "date_format": date_format,
            "prefix": prefix,
            "suffix": suffix,
            "skip_extensions": self.skip_extensions,
            "date_basis": next(item['value'] for item in self.lang["date_bases"] if item['display'] == self.date_basis_var.get()),
            "alternate_date_basis": next(item['value'] for item in self.lang["alternate_dates"] if item['display'] == self.alternate_date_var.get()),
            "fast_add_mode": self.fast_add_mode_var.get(),
            "fast_add_threshold": self.fast_add_threshold_var.get(),
            "name_conflict": self.name_conflict_var.get(),
            "suffix_option": self.suffix_option_var.get()
        }
        
        # 更新缓存
        self._settings_cache = {
            'data': config,
            'timestamp': datetime.datetime.now()
        }
        
        # 保存到配置文件
        with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        # 更新UI
        self.update_renamed_name_column()
        settings_window.destroy()

    def load_settings(self):
        """加载设置，使用缓存机制"""
        # 检查配置缓存
        if self._settings_cache:
            if datetime.datetime.now() - self._settings_cache['timestamp'] < datetime.timedelta(minutes=5):
                self._apply_settings(self._settings_cache['data'])
                return

        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                    # 检查编码问题
                    self.fix_config_encoding(config)
                    self._settings_cache = {
                        'data': config,
                        'timestamp': datetime.datetime.now()
                    }
                    self._apply_settings(config)
                except Exception as e:
                    logging.error(f"加载配置文件出错: {e}")
                    self.handle_error(e, "加载配置文件")
                    
    def fix_config_encoding(self, config: Dict):
        """修复配置文件中的编码问题"""
        # 检查语言设置是否需要修复
        if "language" in config and config["language"] not in LANGUAGES:
            if "绠€浣撲腑鏂?" in config["language"]:
                config["language"] = "简体中文"
                logging.info("修复语言设置: 将 '绠€浣撲腑鏂?' 更正为 '简体中文'")
                
        # 检查日期基准是否需要修复
        if "date_basis" in config and config["date_basis"] not in ["拍摄日期", "修改日期", "创建日期"]:
            if "鎷嶆憚鏃ユ湡" in config["date_basis"]:
                config["date_basis"] = "拍摄日期"
                logging.info("修复日期基准设置: 将 '鎷嶆憚鏃ユ湡' 更正为 '拍摄日期'")
            elif "淇敼鏃ユ湡" in config["date_basis"]:
                config["date_basis"] = "修改日期"
                logging.info("修复日期基准设置: 将 '淇敼鏃ユ湡' 更正为 '修改日期'")
            elif "鍒涘缓鏃ユ湡" in config["date_basis"]:
                config["date_basis"] = "创建日期"
                logging.info("修复日期基准设置: 将 '鍒涘缓鏃ユ湡' 更正为 '创建日期'")
                
        # 检查备用日期基准是否需要修复
        if "alternate_date_basis" in config and config["alternate_date_basis"] not in ["拍摄日期", "修改日期", "创建日期", "保留原文件名"]:
            if "鎷嶆憚鏃ユ湡" in config["alternate_date_basis"]:
                config["alternate_date_basis"] = "拍摄日期"
                logging.info("修复备用日期基准设置: 将 '鎷嶆憚鏃ユ湡' 更正为 '拍摄日期'")
            elif "淇敼鏃ユ湡" in config["alternate_date_basis"]:
                config["alternate_date_basis"] = "修改日期"
                logging.info("修复备用日期基准设置: 将 '淇敼鏃ユ湡' 更正为 '修改日期'")
            elif "鍒涘缓鏃ユ湡" in config["alternate_date_basis"]:
                config["alternate_date_basis"] = "创建日期"
                logging.info("修复备用日期基准设置: 将 '鍒涘缓鏃ユ湡' 更正为 '创建日期'")
            elif "淇濈暀鍘熸枃浠跺悕" in config["alternate_date_basis"]:
                config["alternate_date_basis"] = "保留原文件名"
                logging.info("修复备用日期基准设置: 将 '淇濈暀鍘熸枃浠跺悕' 更正为 '保留原文件名'")
                
        # 检查命名冲突处理方式是否需要修复
        if "name_conflict" in config and config["name_conflict"] not in ["增加后缀", "保留原文件名"]:
            if "澧炲姞鍚庣紑" in config["name_conflict"]:
                config["name_conflict"] = "增加后缀"
                logging.info("修复命名冲突处理方式: 将 '澧炲姞鍚庣紑' 更正为 '增加后缀'")
            elif "淇濈暀鍘熸枃浠跺悕" in config["name_conflict"]:
                config["name_conflict"] = "保留原文件名"
                logging.info("修复命名冲突处理方式: 将 '淇濈暀鍘熸枃浠跺悕' 更正为 '保留原文件名'")
                
        # 保存修复后的配置
        try:
            with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            logging.info("已保存修复后的配置到文件")
        except Exception as e:
            logging.error(f"保存修复后的配置时出错: {e}")

    def _apply_settings(self, config: Dict):
        """应用设置"""
        try:
            self.language_var.set(config.get("language", "简体中文"))
            self.date_format = config.get("date_format", "%Y%m%d_%H%M%S")
            self.prefix_var.set(config.get("prefix", ""))
            self.suffix_var.set(config.get("suffix", ""))
            self.skip_extensions = config.get("skip_extensions", [])
            self.skip_extensions_var.set(" ".join([ext[1:] for ext in self.skip_extensions]))
            
            # 设置日期基准和备用日期
            date_basis = config.get("date_basis", "拍摄日期")
            alternate_date_basis = config.get("alternate_date_basis", "修改日期")
            self.date_basis_var.set(next(item['display'] for item in self.lang["date_bases"] if item['value'] == date_basis))
            self.alternate_date_var.set(next(item['display'] for item in self.lang["alternate_dates"] if item['value'] == alternate_date_basis))
            
            # 设置快速添加模式
            self.fast_add_mode_var.set(config.get("fast_add_mode", False))
            self.fast_add_threshold_var.set(config.get("fast_add_threshold", 10))
            
            # 设置文件名冲突处理方式
            self.name_conflict_var.set(config.get("name_conflict", "add_suffix"))
            self.suffix_option_var.set(config.get("suffix_option", "_001"))
        except Exception as e:
            logging.error(f"应用设置时出错: {e}")
            self.handle_error(e, "应用设置")

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
        for path in paths:
            path = path.strip().strip('{}')
            if os.path.isfile(path):
                if not any(path == self.files_tree.item(item, 'values')[0] for item in self.files_tree.get_children()):
                    self.file_queue.put((path, 'file'))
            elif os.path.isdir(path):
                self.file_queue.put((path, 'dir'))

        if not self.processing_thread or not self.processing_thread.is_alive():
            self.processing_thread = Thread(target=self.process_files_from_queue, daemon=True)
            self.processing_thread.start()

    def process_files_from_queue(self):
        """处理文件队列，使用批量处理和并行处理"""
        try:
            batch_size = 20  # 增加批处理大小，提高处理效率
            while not self.file_queue.empty():
                # 检查是否设置了停止事件
                if self.stop_event.is_set():
                    # 清空队列
                    while not self.file_queue.empty():
                        try:
                            self.file_queue.get(block=False)
                        except:
                            pass
                    self.root.after(0, lambda: self.update_status_bar("操作已停止"))
                    return

                batch = []
                for _ in range(batch_size):
                    if self.file_queue.empty():
                        break
                    try:
                        path, path_type = self.file_queue.get()
                        batch.append((path, path_type))
                    except Exception as e:
                        logging.error(f"获取队列项出错: {e}")
                        self.handle_error(e, "获取队列项")
                
                # 更新状态栏，显示正在处理
                self.root.after(0, lambda: self.update_status_bar(f"正在处理文件...（队列中还有{self.file_queue.qsize()}个文件待处理）"))
                    
                # 并行处理批次
                with ThreadPoolExecutor(max_workers=8) as executor:  # 增加工作线程数
                    futures = []
                    for path, path_type in batch:
                        if self.stop_event.is_set():
                            break
                        if path_type == 'file':
                            futures.append(executor.submit(self.add_file_to_list, path))
                        elif path_type == 'dir':
                            # 优化：对于目录，先快速获取所有文件路径，再批量处理
                            futures.append(executor.submit(self.process_directory, path))
                            
                    for future in as_completed(futures):
                        if self.stop_event.is_set():
                            executor.shutdown(wait=False)
                            break
                        try:
                            future.result()
                        except Exception as e:
                            logging.error(f"处理文件时出错: {e}")
                            self.handle_error(e, "处理文件队列")
                
                # 检查是否设置了停止事件
                if self.stop_event.is_set():
                    self.root.after(0, lambda: self.update_status_bar("操作已停止"))
                    return

                # 更新UI
                def update_ui():
                    try:
                        # 更新文件计数
                        self.update_file_count()
                        # 更新状态栏
                        self.update_status_bar("正在处理中...")
                    except Exception as e:
                        logging.error(f"更新UI时出错: {e}")
                        self.handle_error(e, "更新UI")
                
                self.root.after(0, update_ui)

            # 所有文件加载完成后更新状态栏
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.update_status_bar("文件已就绪！"))
            else:
                self.root.after(0, lambda: self.update_status_bar("操作已停止"))
        except Exception as e:
            logging.error(f"处理文件队列出错: {e}")
            self.handle_error(e, "处理文件队列")

    def process_directory(self, dir_path: str):
        """处理目录，使用生成器减少内存使用"""
        try:
            for root, _, files in os.walk(dir_path):
                # 检查是否设置了停止事件
                if self.stop_event.is_set():
                    return
                    
                for file in files:
                    # 再次检查是否设置了停止事件
                    if self.stop_event.is_set():
                        return
                        
                    file_path = os.path.join(root, file)
                    # 获取文件状态和名称，然后在主线程中更新UI
                    self.add_file_to_list(file_path)
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
                self.root.after(0, lambda: self.update_status_bar("正在处理文件..."))
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
                    if ext in SUPPORTED_IMAGE_FORMATS:
                        if ext == '.heic':
                            exif_data = self.get_heic_data(file_path) 
                        else:
                            exif_data = self.get_exif_data(file_path)
                        
                        # 只有在获取到EXIF数据时才进行状态检测和新名称生成
                        if exif_data:
                            status = self.detect_file_status(file_path, exif_data)
                            new_name = self.generate_new_name(file_path, exif_data)
                        else:
                            # 如果没有获取到EXIF数据，简化处理
                            status = self.lang["ready_to_rename"]
                            new_name = os.path.basename(file_path)
                    else:
                        # 非图片文件直接设为"待重命名"
                        status = self.lang["ready_to_rename"]
                        new_name = os.path.basename(file_path)
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
        """更新重命名名称列，使用线程安全的方式"""
        def process_updates():
            try:
                files_to_update = []
                # 在工作线程中收集所有需要更新的文件信息
                for item in self.files_tree.get_children():
                    # 检查是否设置了停止事件
                    if self.stop_event.is_set():
                        return
                        
                    file_path = self.files_tree.item(item, 'values')[0]
                    file_count = len(self.files_tree.get_children())

                    if self.fast_add_mode_var.get() and file_count >= self.fast_add_threshold_var.get():
                        status = self.lang["ready_to_rename"]
                        new_name = ""
                    else:
                        exif_data = None
                        if file_path.lower().endswith('.heic'):
                            exif_data = self.get_heic_data(file_path)
                        else:
                            exif_data = self.get_exif_data(file_path)
                        new_name = self.generate_new_name(file_path, exif_data)
                        status = self.detect_file_status(file_path, exif_data)
                    
                    files_to_update.append((item, new_name, status))
                    
                    # 每处理10个文件，检查一次停止事件
                    if len(files_to_update) % 10 == 0 and self.stop_event.is_set():
                        return
                
                # 在主线程中批量更新UI
                def update_ui():
                    if not self.stop_event.is_set():
                        for item, new_name, status in files_to_update:
                            self.files_tree.set(item, 'renamed_name', new_name)
                            self.files_tree.set(item, 'status', status)
                
                self.root.after(0, update_ui)
            except Exception as e:
                logging.error(f"更新文件名列时出错: {e}")
                self.handle_error(e, "更新文件名列")

        # 在工作线程中处理
        Thread(target=process_updates, daemon=True).start()

    def set_language(self, language):
        if language in LANGUAGES:
            self.lang = LANGUAGES[language]
            self.root.title(self.lang["window_title"])

            # 更新带有 text_key 属性的控件的文本
            def update_widget_text(widget):
                if hasattr(widget, 'text_key') and widget.text_key in self.lang:
                    widget.config(text=self.lang[widget.text_key])

            # 递归遍历控件树并更新文本
            def traverse_widgets(widget):
                update_widget_text(widget)
                for child in widget.winfo_children():
                    traverse_widgets(child)

            traverse_widgets(self.root)

            # 更新下拉框的选项和显示值
            if hasattr(self, 'date_basis_combobox'):
                self.date_basis_combobox['values'] = [item['display'] for item in self.lang["date_bases"]]
                # 根据配置文件中的内部值设置显示值
                if os.path.exists("QphotoRenamer.ini"):
                    with open("QphotoRenamer.ini", "r", encoding="utf-8") as f:  # 指定编码为 utf-8
                        config = json.load(f)
                        internal_value = config.get("date_basis", "拍摄日期")
                        for item in self.lang["date_bases"]:
                            if item['value'] == internal_value:
                                self.date_basis_combobox.set(item['display'])
                                break
                else:
                    self.date_basis_combobox.set(self.lang["date_bases"][0]['display'])

            if hasattr(self, 'alternate_date_combobox'):
                self.alternate_date_combobox['values'] = [item['display'] for item in self.lang["alternate_dates"]]
                # 根据配置文件中的内部值设置显示值
                if os.path.exists("QphotoRenamer.ini"):
                    with open("QphotoRenamer.ini", "r", encoding="utf-8") as f:  # 指定编码为 utf-8
                        config = json.load(f)
                        internal_value = config.get("alternate_date_basis", "修改日期")
                        for item in self.lang["alternate_dates"]:
                            if item['value'] == internal_value:
                                self.alternate_date_combobox.set(item['display'])
                                break
                else:
                    self.alternate_date_combobox.set(self.lang["alternate_dates"][0]['display'])

            # 更新状态栏文本
            self.status_label.config(text=self.lang["ready"])

            # 更新 Treeview 的列标题
            self.files_tree.heading('filename', text=self.lang["filename"])
            self.files_tree.heading('status', text=self.lang["status"])
            self.files_tree.heading('renamed_name', text=self.lang["renamed_name"])

    def rename_photos(self):
        Thread(target=self.rename_photos_thread).start()

    def rename_photos_thread(self):
        """重命名照片，使用批量处理和并行处理"""
        if self.renaming_in_progress:
            self.root.after(0, lambda: self.update_status_bar("renaming_in_progress"))
            return

        self.renaming_in_progress = True
        self.root.after(0, lambda: self.start_button.config(state=ttk.DISABLED))
        self.root.after(0, lambda: self.stop_button.config(state=ttk.NORMAL))

        self.original_to_new_mapping.clear()
        self.processed_files.clear()
        self.unrenamed_files = 0
        renamed_files_count = 0

        # 获取文件列表中所有项
        items = self.files_tree.get_children()
        if not items:
            self.root.after(0, lambda: self.update_status_bar("ready"))
            self.root.after(0, lambda: messagebox.showinfo("提示", "没有文件需要重命名。"))
            self.renaming_in_progress = False
            self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))
            return

        total_files = len(items)
        self.root.after(0, lambda: self.progress_var.set(0))

        # 使用批量处理
        batch_size = 5
        for i in range(0, total_files, batch_size):
            if self.stop_event.is_set():
                break
                
            batch = items[i:i + batch_size]
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                for item in batch:
                    file_path = self.files_tree.item(item, 'values')[0]
                    future = executor.submit(self.rename_photo, file_path, item)
                    futures[future] = item

                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        executor.shutdown(wait=False)
                        break
                    try:
                        result, new_path = future.result()
                        with self.lock:
                            if result:
                                renamed_files_count += 1
                            else:
                                self.unrenamed_files += 1
                    except Exception as e:
                        logging.error(f"处理文件时出错: {e}")
                        self.handle_error(e, "重命名文件")
                        with self.lock:
                            self.unrenamed_files += 1

                    progress = (renamed_files_count + self.unrenamed_files) * 100 / total_files
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    if self.auto_scroll_var.get():
                        self.root.after(0, lambda i=item: self.files_tree.see(i))

        if not self.stop_event.is_set():
            self.root.after(0, lambda: self.update_status_bar("renaming_success", renamed_files_count, self.unrenamed_files))
            self.root.after(0, lambda: self.files_tree.tag_configure('renamed', background='lightgreen'))
            self.root.after(0, lambda: self.files_tree.tag_configure('failed', background='lightcoral'))
        else:
            self.root.after(0, lambda: self.update_status_bar("renaming_stopped"))

        self.renaming_in_progress = False
        self.root.after(0, lambda: self.start_button.config(state=ttk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=ttk.DISABLED))
        self.current_renaming_file = None
        self.exif_cache = LRUCache(1000)  # 重置EXIF缓存
        self.stop_event.clear()

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

    def generate_new_name(self, file_path, exif_data):
        """根据文件路径和 EXIF 数据生成新名称"""
        try:
            # 如果配置文件中设置了"保留原文件名"，则直接返回原文件名
            if self.alternate_date_var.get() == "保留原文件名":
                return os.path.basename(file_path)

            ext = os.path.splitext(file_path)[1]  # 获取文件扩展名
            base_name = os.path.splitext(os.path.basename(file_path))[0]  # 默认使用文件名（不含扩展名）

            # 获取用户选择的日期基准
            date_basis = self.date_basis_var.get()
            alternate_date_basis = self.alternate_date_var.get()

            # 根据日期基准获取日期
            date_obj = None
            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    if alternate_date_basis == "修改日期":
                        date_obj = self.get_file_modification_date(file_path)
                    elif alternate_date_basis == "创建日期":
                        date_obj = self.get_file_creation_date(file_path)
                    elif alternate_date_basis == "保留原名":
                        return os.path.basename(file_path)  # 直接返回原文件名
            elif date_basis == "修改日期":
                date_obj = self.get_file_modification_date(file_path)
            elif date_basis == "创建日期":
                date_obj = self.get_file_creation_date(file_path)

            # 如果成功获取日期，则格式化日期并过滤非法字符
            if date_obj:
                try:
                    base_name = date_obj.strftime(self.date_format)
                    base_name = self.sanitize_filename(base_name)  # 关键修复：过滤非法字符
                except Exception as e:
                    logging.error(f"日期格式错误: {self.date_format}, 错误: {str(e)}")
                    base_name = "INVALID_FORMAT"
            else:
                # 如果无法获取日期，则根据备用选项处理
                if alternate_date_basis == "保留原名":
                    return os.path.basename(file_path)  # 直接返回原文件名
                else:
                    base_name = "NO_DATE"

            # 生成最终名称
            return f"{self.prefix_var.get()}{base_name}{self.suffix_var.get()}{ext}"
        except Exception as e:
            logging.error(f"生成新名称时发生错误: {str(e)}")
            return "ERROR_" + os.path.basename(file_path)

    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        """生成唯一文件名"""
        counter = 1
        original_base = base_name
        new_filename = f"{base_name}{ext}"
        new_file_path = os.path.join(directory, new_filename)
        
        logging.info(f"生成唯一文件名，使用的后缀样式: {suffix_style}")

        while os.path.exists(new_file_path):
            if suffix_style == "_001":
                suffix = f"_{counter:03d}"
                logging.info(f"使用后缀样式 '_001', 生成后缀: {suffix}")
            elif suffix_style == "-01":
                suffix = f"-{counter:02d}"
                logging.info(f"使用后缀样式 '-01', 生成后缀: {suffix}")
            elif suffix_style == "_1":
                suffix = f"_{counter}"
                logging.info(f"使用后缀样式 '_1', 生成后缀: {suffix}")
            else:
                suffix = f"_{counter:03d}"
                logging.info(f"使用默认后缀样式, 生成后缀: {suffix}")

            new_filename = f"{original_base}{suffix}{ext}"
            new_file_path = os.path.join(directory, new_filename)
            counter += 1

        return new_file_path

    def rename_photo(self, file_path, item):
        try:
            # 如果配置文件中设置了"保留原文件名"，则直接跳过重命名
            if self.alternate_date_var.get() == "保留原文件名":
                with self.lock:
                    self.files_tree.set(item, 'status', '已跳过（保留原文件名）')
                    self.files_tree.item(item, tags=('skipped',))  # 应用 skipped 样式
                return True, file_path  # 返回原文件名，表示未重命名

            # 否则，继续正常重命名逻辑
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            new_name = self.generate_new_name(file_path, exif_data)
            directory = os.path.dirname(file_path)
            base_name, ext = os.path.splitext(new_name)
            base_name = os.path.basename(base_name)
            
            # 修复：确保目录路径使用正确的斜杠格式
            # 对于网络共享路径，Windows要求使用 \\ 而不是 /
            if sys.platform == 'win32' and directory.startswith('//'):
                # 替换目录分隔符为Windows格式
                directory = directory.replace('/', '\\')
                # 网络共享路径前两个斜杠需要保留
                if directory.startswith('\\\\'):
                    pass  # 已经是正确格式
                else:
                    directory = '\\\\' + directory[2:] 
            
            new_file_path = os.path.join(directory, f"{base_name}{ext}")

            # 检查是否有权限写入目标目录
            if not os.access(directory, os.W_OK):
                with self.lock:
                    error_msg = f"无权限访问目标目录: {directory}"
                    self.files_tree.set(item, 'status', f'错误: {error_msg}')
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None

            # 处理文件名冲突
            if os.path.exists(new_file_path):
                suffix_style = self.suffix_option_var.get()
                logging.info(f"检测到文件名冲突: {new_file_path}")
                logging.info(f"当前设置的name_conflict选项: {self.name_conflict_var.get()}")
                logging.info(f"当前语言的'保留原文件名'对应值: {self.lang['keep_original_option']}")
                logging.info(f"使用的suffix_style选项: {suffix_style}")
                
                # 以下逻辑需要兼容中英文界面以及可能的编码问题
                if (self.name_conflict_var.get() == self.lang["keep_original_option"] or 
                    self.name_conflict_var.get() == "保留原文件名" or 
                    "淇濈暀" in self.name_conflict_var.get()):  # 匹配可能的编码问题
                    logging.info("由于设置了保留原文件名，跳过重命名")
                    with self.lock:
                        self.files_tree.set(item, 'status', '已跳过（文件名冲突）')
                        self.files_tree.item(item, tags=('skipped',))
                    return True, file_path
                else:
                    # 使用后缀方式处理冲突
                    logging.info(f"使用后缀方式处理冲突, 后缀样式: {suffix_style}")
                    new_file_path = self.generate_unique_filename(directory, base_name, ext, suffix_style)
                    logging.info(f"生成的唯一文件名: {new_file_path}")

            # 执行重命名
            try:
                os.rename(file_path, new_file_path)
            except PermissionError:
                # 权限错误时，尝试先复制后删除
                with self.lock:
                    error_msg = f"权限错误: 无法直接重命名文件"
                    self.files_tree.set(item, 'status', f'错误: {error_msg}')
                    self.files_tree.item(item, tags=('failed',))
                    self.unrenamed_files += 1
                return False, None
                
            with self.lock:
                self.original_to_new_mapping[file_path] = new_file_path
                self.files_tree.set(item, 'filename', new_file_path)
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
        """显示文件的 EXIF 信息，如果文件已经被重命名，则使用新文件的路径"""
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
            
        file_path = self.files_tree.item(item, 'values')[0]
        # 如果文件已经被重命名，则使用新文件的路径
        if file_path in self.original_to_new_mapping:
            file_path = self.original_to_new_mapping[file_path]
        
        # 在工作线程中处理
        def process_info():
            try:
                # 动态读取 EXIF 信息
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
                exif_info += f"设备: {exif_data['Model']}\n"

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

    def get_file_modification_date(self, file_path):
        try:
            modification_time = os.path.getmtime(file_path)
            return datetime.datetime.fromtimestamp(modification_time)
        except Exception as e:
            logging.error(f"获取文件修改日期失败: {file_path}, 错误: {e}")
        return None

    def get_file_creation_date(self, file_path):
        try:
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
        except Exception as e:
            logging.error(f"获取文件创建日期失败: {file_path}, 错误: {e}")
        return None

    def undo_rename(self):
        for original, new in self.original_to_new_mapping.items():
            try:
                os.rename(new, original)
                logging.info(f'撤销重命名成功: "{new}" 恢复为 "{original}"')
            except Exception as e:
                logging.error(f'撤销重命名失败: {new}, 错误: {e}')
        self.original_to_new_mapping.clear()
        self.update_status_bar("all_files_restored")
        self.undo_button.config(state=ttk.DISABLED)

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
        if message_key in self.lang:
            status_text = self.lang[message_key].format(*args)
        else:
            status_text = message_key

        # 添加快速添加模式状态
        if self.fast_add_mode_var.get():
            status_text += " | 快速添加模式已启用"
        else:
            status_text += " | 快速添加模式已禁用"

        self.status_label.config(text=status_text)

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
        # 检查状态缓存
        cached_status = self.status_cache.get(file_path)
        if cached_status:
            return cached_status

        filename = os.path.basename(file_path)
        status = ""

        file_count = len(self.files_tree.get_children())

        # 如果启用了快速添加模式且文件数量超过阈值，则直接返回"待重命名"
        if self.fast_add_mode_var.get() and file_count >= self.fast_add_threshold_var.get():
            status = self.lang["ready_to_rename"]
            self.status_cache.put(file_path, status)
            return status

        # 检查文件是否发生变化
        file_hash = self.get_file_hash(file_path)
        cached_hash_status = self.file_hash_cache.get(file_hash)
        if cached_hash_status:
            self.status_cache.put(file_path, cached_hash_status)
            return cached_hash_status

        date_basis_display = self.date_basis_var.get()
        alternate_date_display = self.alternate_date_var.get()

        if date_basis_display == "拍摄日期":
            if exif_data is None:
                exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            if exif_data and 'DateTimeOriginalParsed' in exif_data:
                status = self.lang["prepare_rename_by"].format("拍摄日期")
            else:
                if alternate_date_display == "修改日期":
                    mod_date = self.get_file_modification_date(file_path)
                    if mod_date:
                        status = self.lang["prepare_rename_by"].format("修改日期")
                    else:
                        status = self.lang["prepare_rename_keep_name"]
                elif alternate_date_display == "创建日期":
                    create_date = self.get_file_creation_date(file_path)
                    if create_date:
                        status = self.lang["prepare_rename_by"].format("创建日期")
                    else:
                        status = self.lang["prepare_rename_keep_name"]
                elif alternate_date_display == "保留原名":
                    status = self.lang["prepare_rename_keep_name"]
        elif date_basis_display == "修改日期":
            mod_date = self.get_file_modification_date(file_path)
            if mod_date:
                status = self.lang["prepare_rename_by"].format("修改日期")
            else:
                status = self.lang["prepare_rename_keep_name"]
        elif date_basis_display == "创建日期":
            create_date = self.get_file_creation_date(file_path)
            if create_date:
                status = self.lang["prepare_rename_by"].format("创建日期")
            else:
                status = self.lang["prepare_rename_keep_name"]

        # 如果文件名已经符合命名规则，则显示已按相应的日期命名
        if not status:
            if exif_data and 'DateTimeOriginalParsed' in exif_data:
                shot_date = exif_data['DateTimeOriginalParsed']
                base_name = shot_date.strftime(self.date_format)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("拍摄日期")
                    self.status_cache.put(file_path, status)
                    self.file_hash_cache.put(file_hash, status)
                    return status

            mod_date = self.get_file_modification_date(file_path)
            if mod_date:
                base_name = mod_date.strftime(self.date_format)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("修改日期")
                    self.status_cache.put(file_path, status)
                    self.file_hash_cache.put(file_hash, status)
                    return status

            create_date = self.get_file_creation_date(file_path)
            if create_date:
                base_name = create_date.strftime(self.date_format)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("创建日期")
                    self.status_cache.put(file_path, status)
                    self.file_hash_cache.put(file_hash, status)
                    return status

        if not status:
            status = self.lang["ready_to_rename"]

        # 缓存状态和哈希值
        self.status_cache.put(file_path, status)
        self.file_hash_cache.put(file_hash, status)
        return status

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
        info = f"文件路径: {file_path}\n"
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
                info += f"设备: {exif_data['Model']}\n"
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
        self.stop_event.set()
        
        # 取消所有待处理的UI更新
        if self._update_timer:
            self.root.after_cancel(self._update_timer)
            self._update_timer = None
        
        # 清空文件队列
        while not self.file_queue.empty():
            try:
                self.file_queue.get(block=False)
            except:
                pass
        
        # 更新UI状态
        self.root.after(0, lambda: self.update_status_bar("操作已停止"))
        
        # 如果有正在运行的线程，等待它们结束
        if self.processing_thread and self.processing_thread.is_alive():
            # 不阻塞UI，线程会自行检查 stop_event 并退出
            self.status_label.config(text="正在停止操作，请稍候...")
        
        # 重置停止事件，为下一次操作做准备
        self.root.after(1000, self.reset_stop_event)
    
    def reset_stop_event(self):
        """重置停止事件"""
        self.stop_event.clear()
        self.status_label.config(text="操作已停止")
        
        # 重新启用按钮
        self.start_button.config(state=ttk.NORMAL)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    try:
        renamer = PhotoRenamer(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序遇到严重错误: {str(e)}")