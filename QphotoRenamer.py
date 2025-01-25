import os
import sys
import datetime
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

# 获取当前脚本所在的目录路径
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'icon.ico')

# 全局变量
DATE_FORMAT = "%Y%m%d_%H%M%S"
stop_event = Event()  # 全局停止事件
renaming_in_progress = False
original_to_new_mapping = {}
processed_files = set()
unrenamed_files = 0
current_renaming_file = None

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
        "help_text": "使用说明:\n\
1. 将文件或文件夹拖放到列表中，或点击“添加文件”按钮选择文件。\n\
2. 点击“开始重命名”按钮，程序将根据设置的日期格式重命名文件。\n\
3. 若无法获取拍摄日期，程序将根据设置的备用日期（修改日期、创建日期或保留原文件名）进行处理。\n\
4. 双击列表中的文件名可打开文件。\n\
5. 右键点击列表中的文件名可移除文件。\n\
6. 点击“撤销重命名”按钮可将文件恢复为原始名称。\n\
7. 点击“设置”按钮可调整日期格式、前缀、后缀等设置。\n\
8. 勾选“自动滚动”选项，列表将自动滚动至最新添加的文件。\n\
9. 点击“清空列表”按钮可清空文件列表。\n\
10. 点击“停止重命名”按钮可停止当前的重命名操作。\n\
11. 重命名完成后，已重命名的文件项将显示为绿色，重命名失败的文件项将显示为红色。\n\
12. 点击文件名可查看文件的EXIF信息。",
        "settings_window_title": "设置",
        "prefix": "前缀:",
        "suffix": "后缀:",
        "skip_extensions": "跳过重命名的文件类型（空格分隔）:",
        "file_count": "总数量: {}",
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
        "help_text": "Usage Instructions:\n\
1. Drag and drop files or folders into the list, or click the 'Add Files' button to select files.\n\
2. Click the 'Start Renaming' button to rename files based on the specified date format.\n\
3. If the shooting date is unavailable, the program will use the alternate date (modified date, created date, or keep the original name).\n\
4. Double-click a file name in the list to open the file.\n\
5. Right-click a file name in the list to remove it.\n\
6. Click the 'Undo Renaming' button to restore files to their original names.\n\
7. Click the 'Settings' button to adjust the date format, prefix, suffix, and other settings.\n\
8. Enable the 'Auto Scroll' option to automatically scroll to the latest added file.\n\
9. Click the 'Clear List' button to clear the file list.\n\
10. Click the 'Stop Renaming' button to stop the current renaming operation.\n\
11. After renaming, successfully renamed files will be highlighted in green, while failed files will be highlighted in red.\n\
12. Click on a file name to view its EXIF information.",
        "settings_window_title": "Settings",
        "prefix": "Prefix:",
        "suffix": "Suffix:",
        "skip_extensions": "File extensions to skip renaming (space-separated):",
        "file_count": "Total Files: {}",
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

# 跳过重命名的文件扩展名
SKIP_EXTENSIONS = []

class PhotoRenamer:
    def __init__(self, root):
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

        # 初始化 EXIF 缓存
        self.exif_cache = {}

        # 初始化文件处理队列
        self.file_queue = Queue()
        self.processing_thread = None

        # 初始化界面
        self.initialize_ui()
        self.load_settings()
        self.set_language(self.language_var.get())

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

        self.stop_button = ttk.Button(button_frame, text=self.lang["stop_renaming"], command=self.stop_renaming)
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
        self.status_bar = ttk.Frame(self.root, relief=ttk.SUNKEN)
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
        date_format_var = ttk.StringVar(value=DATE_FORMAT)
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
        if self.name_conflict_var.get() == self.lang["add_suffix_option"]:
            suffix_option_combobox.config(state="normal")
        else:
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
        global DATE_FORMAT, SKIP_EXTENSIONS

        # 验证日期格式
        try:
            test_date = datetime.datetime.now()
            test_date.strftime(date_format)
        except ValueError as e:
            messagebox.showerror("格式错误", f"无效的日期格式: {str(e)}")
            return

        # 更新全局变量
        DATE_FORMAT = date_format
        skip_ext_input = skip_extensions_input.strip().lower()
        SKIP_EXTENSIONS = ['.' + ext for ext in skip_ext_input.split()]

        # 构建配置字典
        config = {
            "date_format": DATE_FORMAT,
            "language": language,
            "prefix": prefix,
            "suffix": suffix,
            "skip_extensions": SKIP_EXTENSIONS,
            "date_basis": next(item['value'] for item in self.lang["date_bases"] if item['display'] == self.date_basis_var.get()),
            "alternate_date_basis": next(item['value'] for item in self.lang["alternate_dates"] if item['display'] == self.alternate_date_var.get()),
            "fast_add_mode": self.fast_add_mode_var.get(),
            "fast_add_threshold": self.fast_add_threshold_var.get(),
            "name_conflict": self.name_conflict_var.get(),
            "suffix_option": self.suffix_option_var.get()
        }

        # 将配置写入文件
        with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        # 更新语言和界面
        self.set_language(language)
        self.update_renamed_name_column()
        self.update_status_bar("save_settings")

        # 关闭设置窗口
        settings_window.destroy()

    def load_settings(self):
        global DATE_FORMAT, SKIP_EXTENSIONS
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r", encoding="utf-8") as f:
                config = json.load(f)
                # 读取配置并设置全局变量
                DATE_FORMAT = config.get("date_format", "%Y%m%d_%H%M%S")
                self.language_var.set(config.get("language", "简体中文"))
                self.prefix_var.set(config.get("prefix", ""))
                self.suffix_var.set(config.get("suffix", ""))
                self.skip_extensions_var.set(" ".join(ext[1:] for ext in config.get("skip_extensions", [])))
                self.fast_add_mode_var.set(config.get("fast_add_mode", False))
                self.name_conflict_var.set(config.get("name_conflict", "增加后缀"))
                self.suffix_option_var.set(config.get("suffix_option", "_001"))

                # 设置语言
                self.set_language(self.language_var.get())

                # 设置下拉框的值
                date_basis_internal = config.get("date_basis", "拍摄日期")
                for item in self.lang["date_bases"]:
                    if item['value'] == date_basis_internal:
                        self.date_basis_var.set(item['display'])
                        break

                alternate_date_basis_internal = config.get("alternate_date_basis", "修改日期")
                for item in self.lang["alternate_dates"]:
                    if item['value'] == alternate_date_basis_internal:
                        self.alternate_date_var.set(item['display'])
                        break
        else:
            # 默认配置
            DATE_FORMAT = "%Y%m%d_%H%M%S"
            self.skip_extensions_var.set("")
            self.fast_add_mode_var.set(False)
            self.name_conflict_var.set("增加后缀")
            self.suffix_option_var.set("_001")

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
        while not self.file_queue.empty():
            path, path_type = self.file_queue.get()
            if path_type == 'file':
                self.add_file_to_list(path)
            elif path_type == 'dir':
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self.add_file_to_list(file_path)
            self.file_queue.task_done()

        # 所有文件加载完成后更新状态栏
        self.update_status_bar("文件已就绪！")

    def add_file_to_list(self, file_path):
        self.status_label.config(text=f"正在加载: {os.path.basename(file_path)}")
        file_count = len(self.files_tree.get_children())

        # 如果启用了快速添加模式且文件数量超过阈值
        if self.fast_add_mode_var.get() and file_count >= self.fast_add_threshold_var.get():
            status = self.lang["ready_to_rename"]  # 直接标记为“待重命名”
            new_name = ""  # 在新名称列中显示占位符
        else:
            # 正常模式，读取 EXIF 信息
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            status = self.detect_file_status(file_path, exif_data)
            new_name = self.generate_new_name(file_path, exif_data)

        # 添加文件到列表
        self.files_tree.insert('', 'end', values=(file_path, new_name, status))
        if self.auto_scroll_var.get():
            self.files_tree.see(self.files_tree.get_children()[-1])
        self.update_file_count()  # 更新文件总数
        self.root.update_idletasks()

    def update_renamed_name_column(self):
        for item in self.files_tree.get_children():
            file_path = self.files_tree.item(item, 'values')[0]
            file_count = len(self.files_tree.get_children())

            # 如果启用了快速添加模式且文件数量超过阈值
            if self.fast_add_mode_var.get() and file_count >= self.fast_add_threshold_var.get():
                status = self.lang["ready_to_rename"]  # 直接标记为“待重命名”
                new_name = ""  # 在新名称列中显示占位符
            else:
                # 正常模式，读取 EXIF 信息
                exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
                new_name = self.generate_new_name(file_path, exif_data)
                status = self.detect_file_status(file_path, exif_data)

            self.files_tree.set(item, 'renamed_name', new_name)
            self.files_tree.set(item, 'status', status)

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
        global stop_event, renaming_in_progress, processed_files, unrenamed_files, current_renaming_file

        if renaming_in_progress:
            self.update_status_bar("renaming_in_progress")
            return

        renaming_in_progress = True
        self.start_button.config(state=ttk.DISABLED)
        self.stop_button.config(state=ttk.NORMAL)

        original_to_new_mapping.clear()
        processed_files.clear()
        unrenamed_files = 0
        renamed_files_count = 0

        total_files = len(self.files_tree.get_children())

        if total_files == 0:
            self.update_status_bar("ready")
            messagebox.showinfo("提示", "没有文件需要重命名。")
            renaming_in_progress = False
            self.start_button.config(state=ttk.NORMAL)
            self.stop_button.config(state=ttk.DISABLED)
            return

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for item in self.files_tree.get_children():
                file_path = self.files_tree.item(item, 'values')[0]
                future = executor.submit(self.rename_photo, file_path, item)
                futures[future] = (file_path, item)

            for future in as_completed(futures):
                if stop_event.is_set():
                    executor.shutdown(wait=False)
                    break
                
                file_path, item = futures[future]
                try:
                    success, new_path = future.result()
                    with self.lock:
                        if success:
                            renamed_files_count += 1
                        else:
                            unrenamed_files += 1
                except Exception as e:
                    logging.error(f"处理文件时出错: {e}")
                    with self.lock:
                        unrenamed_files += 1

                self.progress_var.set((renamed_files_count + unrenamed_files) * 100 / total_files)
                if self.auto_scroll_var.get():
                    self.files_tree.see(item)

        if not stop_event.is_set():
            self.update_status_bar("renaming_success", renamed_files_count, unrenamed_files)
            self.files_tree.tag_configure('renamed', background='lightgreen')
            self.files_tree.tag_configure('failed', background='lightcoral')
            self.undo_button.config(state=ttk.NORMAL)
        else:
            self.update_status_bar("renaming_stopped")

        renaming_in_progress = False
        self.start_button.config(state=ttk.NORMAL)
        self.stop_button.config(state=ttk.DISABLED)
        current_renaming_file = None
        self.exif_cache.clear()
        stop_event.clear()

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
            # 如果配置文件中设置了“保留原文件名”，则直接返回原文件名
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
                    base_name = date_obj.strftime(DATE_FORMAT)
                    base_name = self.sanitize_filename(base_name)  # 关键修复：过滤非法字符
                except Exception as e:
                    logging.error(f"日期格式错误: {DATE_FORMAT}, 错误: {str(e)}")
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

        while os.path.exists(new_file_path):
            if suffix_style == "_001":
                suffix = f"_{counter:03d}"
            elif suffix_style == "-01":
                suffix = f"-{counter:02d}"
            elif suffix_style == "_1":
                suffix = f"_{counter}"
            else:
                suffix = f"_{counter:03d}"

            new_filename = f"{original_base}{suffix}{ext}"
            new_file_path = os.path.join(directory, new_filename)
            counter += 1

        return new_file_path

    def rename_photo(self, file_path, item):
        try:
            # 如果配置文件中设置了“保留原文件名”，则直接跳过重命名
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
            new_file_path = os.path.join(directory, f"{base_name}{ext}")

            # 处理文件名冲突
            if os.path.exists(new_file_path):
                suffix_style = self.suffix_option_var.get()
                new_file_path = self.generate_unique_filename(directory, base_name, ext, suffix_style)

            # 执行重命名
            os.rename(file_path, new_file_path)
            with self.lock:
                original_to_new_mapping[file_path] = new_file_path
                self.files_tree.set(item, 'filename', new_file_path)
                self.files_tree.set(item, 'status', '已重命名')
                self.files_tree.item(item, tags=('renamed',))
            return True, new_file_path

        except Exception as e:
            logging.error(f"重命名失败: {str(e)}")
            with self.lock:
                self.files_tree.set(item, 'status', f'错误: {e}')
                self.files_tree.item(item, tags=('failed',))
                unrenamed_files += 1
            return False, None

    def get_exif_data(self, file_path):
        """获取文件的 EXIF 信息，并缓存结果"""
        if file_path in self.exif_cache:
            return self.exif_cache[file_path]

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                exif_data = {}
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                if 'Image Model' in tags:
                    exif_data['Model'] = str(tags['Image Model'])
                if 'EXIF LensModel' in tags:
                    exif_data['LensModel'] = str(tags['EXIF LensModel'])
                if 'EXIF ISOSpeedRatings' in tags:
                    exif_data['ISOSpeedRatings'] = str(tags['EXIF ISOSpeedRatings'])
                if 'EXIF FNumber' in tags:
                    exif_data['FNumber'] = str(tags['EXIF FNumber'])
                if 'EXIF ExposureTime' in tags:
                    exif_data['ExposureTime'] = str(tags['EXIF ExposureTime'])
                if 'Image ImageWidth' in tags:
                    exif_data['ImageWidth'] = str(tags['Image ImageWidth'])
                if 'Image ImageLength' in tags:
                    exif_data['ImageHeight'] = str(tags['Image ImageLength'])
                self.exif_cache[file_path] = exif_data
                return exif_data
        except Exception as e:
            logging.error(f"读取EXIF数据失败: {file_path}, 错误: {e}")
        return None

    def get_heic_data(self, file_path):
        """获取 HEIC 文件的 EXIF 信息，并缓存结果"""
        if file_path in self.exif_cache:
            return self.exif_cache[file_path]

        try:
            heif_file = pillow_heif.read_heif(file_path)
            exif_dict = piexif.load(heif_file.info['exif'])
            exif_data = {}
            if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            # 其他EXIF信息的提取...
            self.exif_cache[file_path] = exif_data
            return exif_data
        except Exception as e:
            logging.error(f"读取HEIC数据失败: {file_path}, 错误: {e}")
        return None

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
        if item:
            file_path = self.files_tree.item(item, 'values')[0]
            # 如果文件已经被重命名，则使用新文件的路径
            if file_path in original_to_new_mapping:
                file_path = original_to_new_mapping[file_path]
        
            # 动态读取 EXIF 信息
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            exif_info = self.extract_exif_info(file_path, exif_data)
            self.create_tooltip(event.widget, exif_info)

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
        global original_to_new_mapping
        for original, new in original_to_new_mapping.items():
            try:
                os.rename(new, original)
                logging.info(f'撤销重命名成功: "{new}" 恢复为 "{original}"')
            except Exception as e:
                logging.error(f'撤销重命名失败: {new}, 错误: {e}')
        original_to_new_mapping.clear()
        self.update_status_bar("all_files_restored")
        self.undo_button.config(state=ttk.DISABLED)

    def remove_file(self, event):
        selected_items = self.files_tree.selection()
        for item in selected_items:
            self.files_tree.delete(item)
        self.update_file_count()  # 更新文件总数

    def stop_renaming(self):
        stop_event.set()

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

    def detect_file_status(self, file_path, exif_data=None):
        filename = os.path.basename(file_path)
        status = ""

        file_count = len(self.files_tree.get_children())

        # 如果启用了快速添加模式且文件数量超过阈值，则直接返回“待重命名”
        if self.fast_add_mode_var.get() and file_count >= self.fast_add_threshold_var.get():
            return self.lang["ready_to_rename"]

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
                base_name = shot_date.strftime(DATE_FORMAT)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("拍摄日期")
                    return status

            mod_date = self.get_file_modification_date(file_path)
            if mod_date:
                base_name = mod_date.strftime(DATE_FORMAT)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("修改日期")
                    return status

            create_date = self.get_file_creation_date(file_path)
            if create_date:
                base_name = create_date.strftime(DATE_FORMAT)
                if filename.startswith(base_name):
                    status = self.lang["already_rename_by"].format("创建日期")
                    return status

        if not status:
            status = self.lang["ready_to_rename"]

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
        if item:
            file_path = self.files_tree.item(item, 'values')[0]
            new_name = self.files_tree.item(item, 'values')[1]

            # 如果新名称为空（快速添加模式跳过），则动态生成新名称
            if not new_name:
                exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
                new_name = self.generate_new_name(file_path, exif_data)  # 动态生成新名称
                self.files_tree.set(item, 'renamed_name', new_name)  # 更新 Treeview 中的新名称列

            # 显示文件信息
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            info = self.extract_omitted_info(file_path, exif_data, new_name)
            self.create_tooltip(event.widget, info)

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

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    try:
        renamer = PhotoRenamer(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序遇到严重错误: {str(e)}")