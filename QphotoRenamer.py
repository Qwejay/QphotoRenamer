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

# 获取当前脚本所在的目录路径
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'logo.ico')

DATE_FORMAT = "%Y%m%d_%H%M%S"
stop_event = Event()
renaming_in_progress = False
original_to_new_mapping = {}
processed_files = set()
unrenamed_files = 0
current_renaming_file = None

COMMON_DATE_FORMATS = [
    "%Y%m%d_%H%M%S",    # 20240729_141530
    "%Y-%m-%d %H:%M:%S",  # 2024-07-29 14:15:30
    "%d-%m-%Y %H:%M:%S",  # 29-07-2024 14:15:30
    "%Y%m%d",            # 20240729
    "%H%M%S",            # 141530
    "%Y-%m-%d",          # 2024-07-29
    "%d-%m-%Y"           # 29-07-2024
]

LANGUAGES = {
    "简体中文": {
        "window_title": "文件&照片批量重命名 QphotoRenamer 1.0.8 —— QwejayHuang",
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
        "window_title": "QphotoRenamer 1.0.8 —— QwejayHuang",
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

SKIP_EXTENSIONS = []
USE_ALTERNATE_DATE = False
ALTERNATE_DATE_BASIS = "modification"

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("文件&照片批量重命名 QphotoRenamer 1.0.8 —— QwejayHuang")
        self.root.geometry("900x600")
        self.root.iconbitmap(icon_path)

        self.style = ttk.Style('litera')

        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.language_var = ttk.StringVar(value=self.load_language())
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.skip_extensions_var = ttk.StringVar(value="")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")

        # 初始化 self.lang
        self.lang = LANGUAGES[self.language_var.get()]

        # 初始化 exif_cache
        self.exif_cache = {}

        self.initialize_ui()
        self.load_settings()
        self.set_language(self.language_var.get())

    def initialize_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True)

        # 修改描述部分
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

        # 在初始化UI时绑定下拉框的选项变化事件
        self.date_basis_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_renamed_name_column())
        self.alternate_date_combobox.bind('<<ComboboxSelected>>', lambda event: self.update_renamed_name_column())

        # 列表排序
        columns = ('filename', 'renamed_name', 'status')

        self.files_tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        # 设置列标题
        self.files_tree.heading('filename', text=self.lang["filename"], anchor='w')
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"], anchor='w')
        self.files_tree.heading('status', text=self.lang["status"], anchor='w')

        # 设置列宽度
        self.files_tree.column('filename', anchor='w', stretch=True, width=400)
        self.files_tree.column('renamed_name', anchor='w', stretch=True, width=200)
        self.files_tree.column('status', anchor='w', width=100, minwidth=100)

        self.files_tree.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        self.files_tree.drop_target_register(DND_FILES)
        self.files_tree.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_tree.bind('<Button-3>', self.remove_file)
        self.files_tree.bind('<Double-1>', self.open_file)
        self.files_tree.bind('<Button-1>', self.show_exif_info)

        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=ttk.X, padx=10, pady=10)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=ttk.X, padx=10, pady=10)

        # 开始重命名按钮
        self.start_button = ttk.Button(button_frame, text=self.lang["start_renaming"], command=lambda: self.rename_photos())
        self.start_button.pack(side=ttk.LEFT, padx=5)
        self.start_button.text_key = "start_renaming"

        # 撤销重命名按钮
        self.undo_button = ttk.Button(button_frame, text=self.lang["undo_renaming"], command=self.undo_rename)
        self.undo_button.pack(side=ttk.LEFT, padx=5)
        self.undo_button.text_key = "undo_renaming"

        # 停止重命名按钮
        self.stop_button = ttk.Button(button_frame, text=self.lang["stop_renaming"], command=self.stop_renaming)
        self.stop_button.pack(side=ttk.LEFT, padx=5)
        self.stop_button.text_key = "stop_renaming"

        # 设置按钮
        self.settings_button = ttk.Button(button_frame, text=self.lang["settings"], command=self.open_settings)
        self.settings_button.pack(side=ttk.LEFT, padx=5)
        self.settings_button.text_key = "settings"

        # 清空列表按钮
        self.clear_button = ttk.Button(button_frame, text=self.lang["clear_list"], command=lambda: self.clear_file_list())
        self.clear_button.pack(side=ttk.LEFT, padx=5)
        self.clear_button.text_key = "clear_list"

        # 添加文件按钮
        self.select_files_button = ttk.Button(button_frame, text=self.lang["add_files"], command=lambda: self.select_files())
        self.select_files_button.pack(side=ttk.LEFT, padx=5)
        self.select_files_button.text_key = "add_files"

        # 帮助按钮
        self.help_button = ttk.Button(button_frame, text=self.lang["help"], command=self.show_help)
        self.help_button.pack(side=ttk.LEFT, padx=5)
        self.help_button.text_key = "help"

        # 自动滚动复选框
        self.auto_scroll_checkbox = ttk.Checkbutton(button_frame, text=self.lang["auto_scroll"], variable=self.auto_scroll_var)
        self.auto_scroll_checkbox.pack(side=ttk.LEFT, padx=5)
        self.auto_scroll_checkbox.text_key = "auto_scroll"

        # 检查更新超链接
        self.update_link = ttk.Label(button_frame, text=self.lang.get("check_for_updates", "反馈&检查更新"), foreground="blue", cursor="hand2")
        self.update_link.pack(side=ttk.RIGHT, padx=5)
        self.update_link.bind("<Button-1>", lambda e: self.open_update_link())
        self.update_link.text_key = "check_for_updates"

        # 状态栏
        self.status_bar = ttk.Label(self.root, text=self.lang["ready"], relief=ttk.SUNKEN, anchor=ttk.W)
        self.status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)
        self.status_bar.text_key = "ready"

    def select_files(self):
        file_paths = filedialog.askopenfilenames()
        for file_path in file_paths:
            if any(file_path == self.files_tree.item(item, 'values')[0] for item in self.files_tree.get_children()):
                logging.info(f"跳过重复添加的文件: {file_path}")
                continue
            status = self.detect_file_status(file_path)
            self.files_tree.insert('', 'end', values=(file_path, '', status))  # 初始化 renamed_name 列为空
            self.update_renamed_name_column()  # 更新名称预览列

    def on_drop(self, event):
        paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
        for path in paths:
            path = path.strip().strip('{}')
            if os.path.isfile(path):
                if not any(path == self.files_tree.item(item, 'values')[0] for item in self.files_tree.get_children()):
                    status = self.detect_file_status(path)
                    self.files_tree.insert('', 'end', values=(path, '', status))
                    self.update_renamed_name_column()
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not any(file_path == self.files_tree.item(item, 'values')[0] for item in self.files_tree.get_children()):
                            status = self.detect_file_status(file_path)
                            self.files_tree.insert('', 'end', values=(file_path, '', status))
                            self.update_renamed_name_column()

    def update_renamed_name_column(self):
        # 清除所有项的背景颜色
        for item in self.files_tree.get_children():
            self.files_tree.item(item, tags=())  # 清除所有标签

        for item in self.files_tree.get_children():
            file_path = self.files_tree.item(item, 'values')[0]
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
            new_name = self.generate_new_name(file_path, exif_data)
            status = self.detect_file_status(file_path)
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
                self.skip_extensions_var.set(" ".join(config.get("skip_extensions", [])))
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
            self.status_bar.config(text=self.lang["ready"])

            # 更新 Treeview 的列标题
            self.files_tree.heading('filename', text=self.lang["filename"])
            self.files_tree.heading('status', text=self.lang["status"])
            self.files_tree.heading('renamed_name', text=self.lang["renamed_name"])

    def save_settings(self, date_format, language, prefix, suffix, skip_extensions_input, settings_window):
        global DATE_FORMAT, SKIP_EXTENSIONS
        DATE_FORMAT = date_format
        skip_ext_input = skip_extensions_input.strip().lower()
        SKIP_EXTENSIONS = [ext for ext in skip_ext_input.split() if ext.startswith('.')]
        if not all(ext.startswith('.') for ext in SKIP_EXTENSIONS):
            messagebox.showerror("错误", "跳过重命名的扩展名必须以点号开头，例如 .jpg")
            return
        # 获取内部值
        date_basis_internal = next(item['value'] for item in self.lang["date_bases"] if item['display'] == self.date_basis_var.get())
        alternate_date_basis_internal = next(item['value'] for item in self.lang["alternate_dates"] if item['display'] == self.alternate_date_var.get())
        config = {
            "date_format": DATE_FORMAT,
            "language": language,
            "prefix": prefix,
            "suffix": suffix,
            "skip_extensions": SKIP_EXTENSIONS,
            "date_basis": date_basis_internal,
            "alternate_date_basis": alternate_date_basis_internal,
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

        settings_frame = ttk.Frame(settings_window)
        settings_frame.pack(padx=10, pady=10)

        ttk.Label(settings_frame, text=self.lang["rename_pattern"], anchor='w').grid(row=0, column=0, padx=10, pady=10)
        date_format_var = ttk.StringVar(value=DATE_FORMAT)
        date_format_combobox = ttk.Combobox(settings_frame, textvariable=date_format_var, values=COMMON_DATE_FORMATS, state="readonly")
        date_format_combobox.grid(row=0, column=1, padx=10, pady=10)
        date_format_combobox.set(DATE_FORMAT)

        ttk.Label(settings_frame, text=self.lang["language"], anchor='w').grid(row=1, column=0, padx=10, pady=10)
        language_combobox = ttk.Combobox(settings_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
        language_combobox.grid(row=1, column=1, padx=10, pady=10)
        language_combobox.bind('<<ComboboxSelected>>', lambda event: self.set_language(language_combobox.get()))

        ttk.Label(settings_frame, text=self.lang["prefix"], anchor='w').grid(row=2, column=0, padx=10, pady=10)
        prefix_entry = Entry(settings_frame, textvariable=self.prefix_var)
        prefix_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=self.lang["suffix"], anchor='w').grid(row=3, column=0, padx=10, pady=10)
        suffix_entry = Entry(settings_frame, textvariable=self.suffix_var)
        suffix_entry.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=self.lang["skip_extensions"], anchor='w').grid(row=4, column=0, padx=10, pady=10)
        skip_ext_entry = Entry(settings_frame, textvariable=self.skip_extensions_var)
        skip_ext_entry.grid(row=4, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=self.lang["formats_explanation"], anchor='w').grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        save_button = ttk.Button(settings_frame, text=self.lang["save_settings"], command=lambda: self.save_settings(date_format_var.get(), self.language_var.get(), self.prefix_var.get(), self.suffix_var.get(), skip_ext_entry.get(), settings_window))
        save_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

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

        for item in self.files_tree.get_children():
            if stop_event.is_set():
                stop_event.clear()
                self.update_status_bar("renaming_stopped")
                break

            file_path = self.files_tree.item(item, 'values')[0]
            if file_path not in processed_files:
                current_renaming_file = file_path
                self.update_status_bar("renaming_in_progress", os.path.basename(file_path))
                renamed = self.rename_photo(file_path, item)
                if renamed:
                    processed_files.add(file_path)
                    self.files_tree.set(item, 'status', '已重命名')
                    self.files_tree.item(item, tags=('renamed',))  # 标记为已重命名
                    renamed_files_count += 1
                else:
                    self.files_tree.set(item, 'status', '未重命名')
                    self.files_tree.item(item, tags=('failed',))  # 标记为重命名失败
                    unrenamed_files += 1

                self.progress_var.set((renamed_files_count + unrenamed_files) * 100 / total_files)
                if self.auto_scroll_var.get():
                    self.files_tree.see(item)

        self.update_status_bar("renaming_success", renamed_files_count, unrenamed_files)

        # 设置样式：已重命名的文件项为绿色，重命名失败的文件项为红色
        self.files_tree.tag_configure('renamed', background='lightgreen')
        self.files_tree.tag_configure('failed', background='lightcoral')

        self.undo_button.config(state=ttk.NORMAL)
        renaming_in_progress = False
        self.start_button.config(state=ttk.NORMAL)
        self.stop_button.config(state=ttk.DISABLED)
        current_renaming_file = None

        # 重命名完成后清理缓存
        self.exif_cache.clear()

    def rename_photo(self, file_path, item):
        global unrenamed_files
        filename = os.path.basename(file_path)
        logging.info(f"处理文件: {file_path}")

        # 检查文件是否已经被重命名过
        original_file_path = file_path
        if file_path in original_to_new_mapping:
            # 如果已经被重命名过，则使用原始文件路径
            original_file_path = original_to_new_mapping[file_path]
            file_path = original_file_path
            filename = os.path.basename(file_path)

        if filename.lower().endswith(tuple(SKIP_EXTENSIONS)):
            logging.info(f"跳过文件: {filename}")
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
        new_file_path = self.generate_unique_filename(directory, new_file_name, ext)

        if new_file_path != file_path and not os.path.exists(new_file_path):
            try:
                os.rename(file_path, new_file_path)
                logging.info(f'重命名成功: "{file_path}" 重命名为 "{new_file_path}"')
                # 更新映射关系
                original_to_new_mapping[original_file_path] = new_file_path
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
        except FileNotFoundError as e:
            logging.error(f"文件不存在: {file_path}, 错误: {e}")
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
            if 'Exif' in exif_dict and piexif.ExifIFD.ISOSpeedRatings in exif_dict['Exif']:
                exif_data['ISOSpeedRatings'] = exif_dict['Exif'][piexif.ExifIFD.ISOSpeedRatings]
            if 'Exif' in exif_dict and piexif.ExifIFD.FNumber in exif_dict['Exif']:
                exif_data['FNumber'] = exif_dict['Exif'][piexif.ExifIFD.FNumber]
            if 'Exif' in exif_dict and piexif.ExifIFD.ExposureTime in exif_dict['Exif']:
                exif_data['ExposureTime'] = exif_dict['Exif'][piexif.ExifIFD.ExposureTime]
            if 'Exif' in exif_dict and piexif.ExifIFD.LensModel in exif_dict['Exif']:
                exif_data['LensModel'] = exif_dict['Exif'][piexif.ExifIFD.LensModel].decode('utf-8')
            if 'Exif' in exif_dict and piexif.ImageIFD.Model in exif_dict['0th']:
                exif_data['Model'] = exif_dict['0th'][piexif.ImageIFD.Model].decode('utf-8')
            if 'Exif' in exif_dict and piexif.ImageIFD.ImageWidth in exif_dict['0th']:
                exif_data['ImageWidth'] = exif_dict['0th'][piexif.ImageIFD.ImageWidth]
            if 'Exif' in exif_dict and piexif.ImageIFD.ImageLength in exif_dict['0th']:
                exif_data['ImageHeight'] = exif_dict['0th'][piexif.ImageIFD.ImageLength]
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
            
            # 使用 after 方法延迟显示提示框
            self.root.after(100, self.delayed_show_exif_info, file_path, event.widget)

    def delayed_show_exif_info(self, file_path, widget):
        """延迟显示 EXIF 信息"""
        exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
        exif_info = self.extract_exif_info(file_path, exif_data)
        self.create_tooltip(widget, exif_info)

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

    def stop_renaming(self):
        stop_event.set()

    def clear_file_list(self):
        self.files_tree.delete(*self.files_tree.get_children())

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
            self.status_bar.config(text=self.lang[message_key].format(*args))
        else:
            self.status_bar.config(text=message_key)

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

    def detect_file_status(self, file_path):
        filename = os.path.basename(file_path)
        status = ""

        date_basis_display = self.date_basis_var.get()
        alternate_date_display = self.alternate_date_var.get()

        if date_basis_display == "拍摄日期":
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
            exif_data = self.get_heic_data(file_path) if file_path.lower().endswith('.heic') else self.get_exif_data(file_path)
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