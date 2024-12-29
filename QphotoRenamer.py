import os
import sys
import datetime
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, Entry, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread, Event
import logging
import re
import json
import subprocess
import webbrowser
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

# 获取当前脚本所在的目录路径
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'logo.ico')

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
        "window_title": "文件&照片批量重命名 QphotoRenamer 2.0 —— QwejayHuang",
        "description_base": "拖动文件&照片，即将按照",
        "description_suffix": "重命名文件，如无拍摄日期(或者不是媒体文件)，则使用",
        "start_renaming": "开始重命名",
        "undo_renaming": "撤销重命名",
        "stop_renaming": "停止重命名",
        "settings": "设置",
        "clear_list": "清空列表",
        "add_files": "添加文件",
        "help": "帮助",
        "auto_scroll": "自动滚动",
        "check_for_updates": "反馈&更新",
        "ready": "准备就绪",
        "rename_pattern": "重命名样式:",
        "language": "语言",
        "save_settings": "保存设置",
        "formats_explanation": "常用日期格式示例:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "正在重命名，请稍后...",
        "renaming_stopped": "重命名操作已停止。",
        "renaming_success": "成功重命名 {0} 个文件，未重命名 {1} 个文件。",
        "all_files_restored": "所有文件已恢复到原始名称。",
        "filename": "文件路径",
        "status": "状态",
        "renamed_name": "新名称",
        "prepare_rename_by": "准备以 {} 重命名",
        "prepare_rename_keep_name": "准备保留原名",
        "already_rename_by": "已按 {} 命名",
        "ready_to_rename": "待重命名",
        "help_text": "使用说明:\n\
1. 拖拽文件或文件夹到列表中，或点击“添加文件”按钮选择文件。\n\
2. 点击“开始重命名”按钮，程序将根据设置的日期格式重命名文件。\n\
3. 如果无法找到拍摄日期，程序将根据设置的备用日期（修改日期、创建日期或保留原名）进行处理。\n\
4. 双击列表中的文件名可打开文件。\n\
5. 右键点击列表中的文件名可移除文件。\n\
6. 点击“撤销重命名”按钮可恢复文件到原始名称。\n\
7. 点击“设置”按钮可更改日期格式、前缀、后缀等设置。\n\
8. 勾选“自动滚动”选项，列表会自动滚动到最新添加的文件。\n\
9. 点击“清空列表”按钮可清空文件列表。\n\
10. 点击“停止重命名”按钮可停止当前的重命名操作。\n\
11. 重命名完成后，已重命名的文件项会显示为绿色，重命名失败的文件项会显示为红色。\n\
12. 点击文件名可显示文件的EXIF信息。",
        "settings_window_title": "设置",
        "prefix": "前缀:",
        "suffix": "后缀:",
        "skip_extensions": "跳过重命名的文件类型（空格分隔）:",
        "file_count": "文件总数: {}",
        "fast_add_mode": "启用快速添加模式（一次性添加文件超过）:",
        "name_conflict_prompt": "当命名后文件名相同时:",
        "add_suffix_option": "增加后缀（_+数字）",
        "keep_original_option": "保留原文件名",
        "other_settings": "其他设置",
        "file_handling_settings": "文件处理设置",
        "rename_pattern_settings": "重命名样式设置",
        "date_bases": [
            {"display": "拍摄日期", "value": "拍摄日期"},
            {"display": "修改日期", "value": "修改日期"},
            {"display": "创建日期", "value": "创建日期"}
        ],
        "alternate_dates": [
            {"display": "修改日期", "value": "修改日期"},
            {"display": "创建日期", "value": "创建日期"},
            {"display": "保留原名", "value": "保留原名"}
        ]
    },
    "English": {
        "window_title": "QphotoRenamer 2.0 —— QwejayHuang",
        "description_base": "Drag and drop photos to begin renaming by ",
        "description_suffix": ",If the shooting date cannot be found, use",
        "start_renaming": "Start",
        "undo_renaming": "Undo",
        "stop_renaming": "Stop",
        "settings": "Settings",
        "clear_list": "Clear List",
        "add_files": "Add Files",
        "help": "Help",
        "auto_scroll": "Auto Scroll",
        "check_for_updates": "Feedback&Check Updates",
        "ready": "Ready",
        "rename_pattern": "Rename Pattern:",
        "language": "Language",
        "save_settings": "Save Settings",
        "formats_explanation": "Common Date Formats Examples:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "Renaming operation is already in progress, please try again later.",
        "renaming_stopped": "Renaming operation has been stopped.",
        "renaming_success": "Successfully renamed {0} files, {1} files not renamed.",
        "all_files_restored": "All files have been restored to their original names.",
        "filename": "Filename",
        "status": "Status",
        "renamed_name": "Renamed Name",
        "prepare_rename_by": "Ready to rename by {}",
        "prepare_rename_keep_name": "Ready to keep original name",
        "already_rename_by": "Already renamed by {}",
        "ready_to_rename": "Ready to rename",
        "help_text": "Usage Instructions:\n\
1. Drag files or folders into the list or click the 'Add Files' button to select files.\n\
2. Click the 'Start' button to begin renaming files.\n\
3. If the shooting date cannot be found, the program will use the alternate date (modified date, created date, or keep original name).\n\
4. Double-click on a file name in the list to open the image.\n\
5. Right-click on a file name in the list to remove the file.\n\
6. Click the 'Undo' button to restore files to their original names.\n\
7. Click the 'Settings' button to change the date format, prefix, suffix, etc.\n\
8. Check the 'Auto Scroll' option to automatically scroll to the latest added file.\n\
9. Click the 'Clear List' button to clear the file list.\n\
10. Click the 'Stop' button to stop the renaming operation.\n\
11. After renaming, successfully renamed files will be marked green, and failed files will be marked red.\n\
12. Click on a file name to display EXIF information.",
        "settings_window_title": "Settings",
        "prefix": "Prefix:",
        "suffix": "Suffix:",
        "skip_extensions": "File extensions to skip renaming (space-separated):",
        "file_count": "Total Files: {}",
        "fast_add_mode": "Enable Fast Add Mode (when adding more than):",
        "name_conflict_prompt": "When file names conflict after renaming:",
        "add_suffix_option": "Add suffix (_+number)",
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
            {"display": "Original Name", "value": "保留原名"}
        ]
    }
}

# 跳过重命名的文件扩展名
SKIP_EXTENSIONS = []

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("文件&照片批量重命名 QphotoRenamer 2.0 —— QwejayHuang")
        self.root.geometry("900x600")
        self.root.iconbitmap(icon_path)

        self.style = ttk.Style('litera')

        # 初始化变量
        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.language_var = ttk.StringVar(value=self.load_language())
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.skip_extensions_var = ttk.StringVar(value="")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")
        self.file_threshold_var = ttk.IntVar(value=50)  # 默认文件数量阈值为50
        self.name_conflict_var = ttk.StringVar(value="add_suffix")  # 默认选项为增加后缀

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
        self.files_tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        self.files_tree.heading('filename', text=self.lang["filename"], anchor='w')
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"], anchor='w')
        self.files_tree.heading('status', text=self.lang["status"], anchor='w')
        self.files_tree.column('filename', anchor='w', stretch=True, width=400)
        self.files_tree.column('renamed_name', anchor='w', stretch=True, width=200)
        self.files_tree.column('status', anchor='w', width=100, minwidth=100)
        self.files_tree.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        self.files_tree.drop_target_register(DND_FILES)
        self.files_tree.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_tree.bind('<Button-3>', self.remove_file)
        self.files_tree.bind('<Double-1>', self.open_file)
        self.files_tree.bind('<Button-1>', self.show_exif_info)
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

        # 如果文件数量超过阈值，则跳过EXIF读取和状态检测
        if file_count >= self.file_threshold_var.get():
            status = self.lang["ready_to_rename"]  # 直接标记为“待重命名”
            new_name = os.path.basename(file_path)  # 保留原文件名
        else:
            # 正常模式，读取EXIF信息
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            status = self.detect_file_status(file_path, exif_data)
            new_name = self.generate_new_name(file_path, exif_data)

        # 添加文件到列表
        self.files_tree.insert('', 'end', values=(file_path, new_name, status))
        if self.auto_scroll_var.get():
            self.files_tree.see(self.files_tree.get_children()[-1])
        self.update_file_count()  # 更新文件总数
        self.root.update_idletasks()

    def process_file_in_background(self, file_path):
        """在后台处理文件，读取EXIF信息并更新状态"""
        exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
        status = self.detect_file_status(file_path, exif_data)
        new_name = self.generate_new_name(file_path, exif_data)
        
        # 在主线程中更新UI
        self.root.after(0, self.update_file_list, file_path, new_name, status)

    def update_file_list(self, file_path, new_name, status):
        """在主线程中更新文件列表"""
        self.files_tree.insert('', 'end', values=(file_path, new_name, status))
        if self.auto_scroll_var.get():
            self.files_tree.see(self.files_tree.get_children()[-1])
        self.update_file_count()  # 更新文件总数

    def update_renamed_name_column(self):
        for item in self.files_tree.get_children():
            file_path = self.files_tree.item(item, 'values')[0]
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            new_name = self.generate_new_name(file_path, exif_data)
            status = self.detect_file_status(file_path, exif_data)
            self.files_tree.set(item, 'renamed_name', new_name)
            self.files_tree.set(item, 'status', status)

    def load_settings(self):
        global DATE_FORMAT, SKIP_EXTENSIONS
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r") as f:
                config = json.load(f)
                DATE_FORMAT = config.get("date_format", "%Y%m%d_%H%M%S")
                self.language_var.set(config.get("language", "简体中文"))
                self.prefix_var.set(config.get("prefix", ""))
                self.suffix_var.set(config.get("suffix", ""))
                # 去掉扩展名前的点号显示
                self.skip_extensions_var.set(" ".join(ext[1:] for ext in config.get("skip_extensions", [])))
                self.file_threshold_var.set(config.get("fast_add_mode_threshold", 50))  # 加载文件数量阈值，默认值为50
                self.name_conflict_var.set(config.get("name_conflict", "add_suffix"))  # 默认选项为增加后缀
                # 先设置语言
                self.set_language(self.language_var.get())
                # 然后设置下拉框的值
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
            DATE_FORMAT = "%Y%m%d_%H%M%S"
            self.skip_extensions_var.set("")
            self.file_threshold_var.set(50)  # 默认文件数量阈值为50
            self.name_conflict_var.set("add_suffix")  # 默认选项为增加后缀

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
                    with open("QphotoRenamer.ini", "r") as f:
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
                    with open("QphotoRenamer.ini", "r") as f:
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

    def save_settings(self, date_format, language, prefix, suffix, skip_extensions_input, settings_window):
        global DATE_FORMAT, SKIP_EXTENSIONS
        DATE_FORMAT = date_format
        skip_ext_input = skip_extensions_input.strip().lower()
        SKIP_EXTENSIONS = ['.' + ext for ext in skip_ext_input.split()]

        # 保存文件数量阈值
        try:
            file_threshold = int(self.file_threshold_var.get())
            if file_threshold < 0:
                raise ValueError("文件数量阈值必须为正整数")
        except ValueError as e:
            messagebox.showerror("错误", "文件数量阈值必须为正整数")
            return
        
        config = {
            "date_format": DATE_FORMAT,
            "language": language,
            "prefix": prefix,
            "suffix": suffix,
            "skip_extensions": SKIP_EXTENSIONS,
            "date_basis": next(item['value'] for item in self.lang["date_bases"] if item['display'] == self.date_basis_var.get()),
            "alternate_date_basis": next(item['value'] for item in self.lang["alternate_dates"] if item['display'] == self.alternate_date_var.get()),
            "fast_add_mode_threshold": self.file_threshold_var.get(),  # 保存文件数量阈值
            "name_conflict": self.name_conflict_var.get()  # 保存文件名冲突处理方式
        }
        with open("QphotoRenamer.ini", "w") as f:
            json.dump(config, f)
        self.set_language(language)
        self.update_renamed_name_column()
        self.update_status_bar("save_settings")
        settings_window.destroy()

    def open_settings(self):
        settings_window = ttk.Toplevel(self.root)
        settings_window.title(self.lang["settings_window_title"])
        settings_window.geometry("530x540")

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

        # 快速添加模式设置
        ttk.Label(file_handling_frame, text=self.lang["fast_add_mode"], anchor='w').grid(row=1, column=0, padx=5, pady=5, sticky='w')
        file_threshold_entry = Entry(file_handling_frame, textvariable=self.file_threshold_var)
        file_threshold_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(file_handling_frame, text=self.lang["name_conflict_prompt"], anchor='w').grid(row=2, column=0, padx=5, pady=5, sticky='w')
        ttk.Radiobutton(file_handling_frame, text=self.lang["add_suffix_option"], variable=self.name_conflict_var, value="add_suffix").grid(row=2, column=1, padx=5, pady=5, sticky='w')
        ttk.Radiobutton(file_handling_frame, text=self.lang["keep_original_option"], variable=self.name_conflict_var, value="keep_original").grid(row=3, column=1, padx=5, pady=5, sticky='w')

        # 分割线
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=10)

        # 其他设置
        other_settings_frame = ttk.LabelFrame(main_frame, text=self.lang["other_settings"], padding=10)
        other_settings_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(other_settings_frame, text=self.lang["language"], anchor='w').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        language_combobox = ttk.Combobox(other_settings_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
        language_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        language_combobox.bind('<<ComboboxSelected>>', lambda event: self.set_language(language_combobox.get()))

        # 保存设置按钮
        save_button = ttk.Button(main_frame, text=self.lang["save_settings"], command=lambda: self.save_settings(date_format_var.get(), self.language_var.get(), self.prefix_var.get(), self.suffix_var.get(), skip_ext_entry.get(), settings_window))
        save_button.grid(row=5, column=0, sticky="ew", padx=5, pady=10)

        # 调整列权重，使内容居中
        main_frame.columnconfigure(0, weight=1)
        rename_pattern_frame.columnconfigure(1, weight=1)
        file_handling_frame.columnconfigure(1, weight=1)
        other_settings_frame.columnconfigure(1, weight=1)

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

        # 清除旧的重命名记录
        original_to_new_mapping.clear()

        processed_files.clear()
        unrenamed_files = 0
        renamed_files_count = 0

        total_files = len(self.files_tree.get_children())

        # 如果没有文件需要处理，提示用户
        if total_files == 0:
            self.update_status_bar("ready")
            messagebox.showinfo("提示", "没有文件需要重命名。")
            renaming_in_progress = False
            self.start_button.config(state=ttk.NORMAL)
            self.stop_button.config(state=ttk.DISABLED)
            return

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(self.rename_photo, self.files_tree.item(item, 'values')[0], item): item for item in self.files_tree.get_children()}
            for future in as_completed(futures):
                if stop_event.is_set():  # 检查是否停止
                    executor.shutdown(wait=False)  # 立即停止线程池
                    break
                item = futures[future]
                try:
                    renamed = future.result()
                    if renamed:
                        renamed_files_count += 1
                    else:
                        unrenamed_files += 1
                except Exception as e:
                    logging.error(f"处理文件时出错: {e}")
                    unrenamed_files += 1

                self.progress_var.set((renamed_files_count + unrenamed_files) * 100 / total_files)
                if self.auto_scroll_var.get():
                    self.files_tree.see(item)

        if not stop_event.is_set():  # 如果没有停止，则更新状态
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
        stop_event.clear()  # 重置停止事件

    def rename_photo(self, file_path, item):
        global unrenamed_files
        filename = os.path.basename(file_path)
        logging.info(f"处理文件: {file_path}")

        # 检查文件是否已经被重命名过
        if file_path in original_to_new_mapping:
            return False

        # 检查文件类型是否在跳过列表中
        ext = os.path.splitext(filename)[1].lower()
        if ext in SKIP_EXTENSIONS:
            logging.info(f"跳过文件: {filename}，文件类型被跳过")
            self.files_tree.set(item, 'status', '此文件类型被跳过')
            unrenamed_files += 1
            return False

        date_basis = self.date_basis_var.get()
        if date_basis == "拍摄日期":
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                # 如果是视频文件，获取媒体创建日期
                shot_date = self.get_video_creation_date(file_path)
                if not shot_date:
                    if self.alternate_date_var.get() == "修改日期":
                        shot_date = self.get_file_modification_date(file_path)
                    elif self.alternate_date_var.get() == "创建日期":
                        shot_date = self.get_file_creation_date(file_path)
                    elif self.alternate_date_var.get() == "保留原名":
                        self.files_tree.set(item, 'status', '保留原名')
                        unrenamed_files += 1
                        return False
            else:
                # 如果是图片文件，获取EXIF信息
                exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
                shot_date = exif_data.get('DateTimeOriginalParsed') if exif_data else None
                if not shot_date:
                    if self.alternate_date_var.get() == "修改日期":
                        shot_date = self.get_file_modification_date(file_path)
                    elif self.alternate_date_var.get() == "创建日期":
                        shot_date = self.get_file_creation_date(file_path)
                    elif self.alternate_date_var.get() == "保留原名":
                        self.files_tree.set(item, 'status', '保留原名')
                        unrenamed_files += 1
                        return False
        elif date_basis == "修改日期":
            shot_date = self.get_file_modification_date(file_path)
        elif date_basis == "创建日期":
            shot_date = self.get_file_creation_date(file_path)

        if shot_date:
            base_name = shot_date.strftime(DATE_FORMAT)
        else:
            self.files_tree.set(item, 'status', '无法获取日期')
            unrenamed_files += 1
            return False

        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()
        ext = os.path.splitext(filename)[1]
        directory = os.path.dirname(file_path)
        new_file_name = f"{prefix}{base_name}{suffix}"

        # 根据用户选择的选项处理文件名冲突
        if self.name_conflict_var.get() == "add_suffix":
            new_file_path = self.generate_unique_filename(directory, new_file_name, ext)
        else:
            new_file_path = os.path.join(directory, f"{new_file_name}{ext}")
            if os.path.exists(new_file_path):
                self.files_tree.set(item, 'status', '保留原文件名')
                return False

        if new_file_path != file_path and not os.path.exists(new_file_path):
            try:
                os.rename(file_path, new_file_path)
                logging.info(f'重命名成功: "{file_path}" 重命名为 "{new_file_path}"')
                # 更新映射关系
                original_to_new_mapping[file_path] = new_file_path
                # 更新列表中的文件名和状态
                self.files_tree.set(item, 'filename', new_file_path)
                self.files_tree.set(item, 'status', '已重命名')
                self.files_tree.item(item, tags=('renamed',))  # 标记为已重命名
                return True
            except Exception as e:
                logging.error(f"重命名失败: {file_path}, 错误: {e}")
                self.files_tree.set(item, 'status', f'错误: {e}')
                self.files_tree.item(item, tags=('failed',))  # 标记为重命名失败
        else:
            logging.info(f'跳过重命名: "{file_path}" 已经是重命名后的名字')
            self.files_tree.set(item, 'status', '已重命名')
            self.files_tree.item(item, tags=('renamed',))  # 标记为已重命名

        return False

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

    def create_tooltip(self, widget, exif_info):
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            widget.tooltip_window.destroy()
        
        # 创建提示框
        tooltip = Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        x = widget.winfo_pointerx() + 10
        y = widget.winfo_pointery() + 10
        tooltip.geometry(f"+{x}+{y}")
        label = Label(tooltip, text=exif_info, background="lightyellow", relief="solid", borderwidth=1, anchor='w', justify='left')
        label.pack(fill='both', expand=True)
        widget.tooltip_window = tooltip

        # 设置提示框在10秒后自动销毁
        def destroy_tooltip():
            if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
                widget.tooltip_window.destroy()
                widget.tooltip_window = None

        widget.after(10000, destroy_tooltip)

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

    def generate_unique_filename(self, directory, base_name, ext):
        new_filename = f"{base_name}{ext}"
        new_file_path = os.path.join(directory, new_filename)
        counter = 1
        while os.path.exists(new_file_path):
            new_filename = f"{base_name}_{counter}{ext}"
            new_file_path = os.path.join(directory, new_filename)
            counter += 1
        return new_file_path

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

    def generate_new_name(self, file_path, exif_data):
        # 根据用户选择的日期格式或备用日期生成新名称
        if self.date_basis_var.get() == "拍摄日期":
            if exif_data and 'DateTimeOriginalParsed' in exif_data:
                base_name = exif_data['DateTimeOriginalParsed'].strftime(DATE_FORMAT)
            else:
                # 如果没有EXIF信息，使用备用日期
                if self.alternate_date_var.get() == "修改日期":
                    mod_date = self.get_file_modification_date(file_path)
                    if mod_date:
                        base_name = mod_date.strftime(DATE_FORMAT)
                    else:
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                elif self.alternate_date_var.get() == "创建日期":
                    create_date = self.get_file_creation_date(file_path)
                    if create_date:
                        base_name = create_date.strftime(DATE_FORMAT)
                    else:
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                else:
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
        elif self.date_basis_var.get() == "修改日期":
            mod_date = self.get_file_modification_date(file_path)
            if mod_date:
                base_name = mod_date.strftime(DATE_FORMAT)
            else:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
        elif self.date_basis_var.get() == "创建日期":
            create_date = self.get_file_creation_date(file_path)
            if create_date:
                base_name = create_date.strftime(DATE_FORMAT)
            else:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            # 默认情况，使用文件名（不含扩展名）
            base_name = os.path.splitext(os.path.basename(file_path))[0]

        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()
        ext = os.path.splitext(file_path)[1]
        new_name = f"{prefix}{base_name}{suffix}{ext}"
        return new_name

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
            self.status_label.config(text=self.lang[message_key].format(*args))
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
            with open("QphotoRenamer.ini", "r") as f:
                config = json.load(f)
                return config.get("language", "简体中文")
        return "简体中文"

    def open_update_link(self):
        webbrowser.open("https://github.com/Qwejay/QphotoRenamer")

    def detect_file_status(self, file_path, exif_data=None):
        filename = os.path.basename(file_path)
        status = ""

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

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    renamer = PhotoRenamer(root)
    root.mainloop()