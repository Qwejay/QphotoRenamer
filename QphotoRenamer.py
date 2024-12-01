import os
import sys
import datetime
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, Checkbutton, Entry, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread, Event
import logging
import re
import json
import locale
import subprocess

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
    "%Y%m%d_%H%M%S",    # 20230729_141530
    "%Y-%m-%d %H:%M:%S",  # 2023-07-29 14:15:30
    "%d-%m-%Y %H:%M:%S",  # 29-07-2023 14:15:30
    "%Y%m%d",            # 20230729
    "%H%M%S",            # 141530
    "%Y-%m-%d",          # 2023-07-29
    "%d-%m-%Y"           # 29-07-2023
]

LANGUAGES = {
    "简体中文": {
        "window_title": "照片批量重命名 QphotoRenamer 1.0.5 —— QwejayHuang",
        "description": "即将按照拍摄日期重命名照片。只需将照片拖入列表即可快速添加；点击“开始重命名”按钮批量重命名您的照片。",
        "start_renaming": "开始重命名",
        "undo_renaming": "撤销重命名",
        "stop_renaming": "停止重命名",
        "settings": "设置",
        "clear_list": "清空列表",
        "add_files": "添加文件",
        "help": "帮助",
        "auto_scroll": "自动滚动",
        "ready": "准备就绪",
        "rename_pattern": "重命名样式:",
        "use_modification_date": "使用修改日期重命名",
        "language": "语言",
        "save_settings": "保存设置",
        "formats_explanation": "常用日期格式示例:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "正在重命名，请稍后...",
        "renaming_stopped": "重命名操作已停止。",
        "renaming_success": "成功重命名 {0} 个文件，未重命名 {1} 个文件。",
        "all_files_restored": "所有文件已恢复到原始名称。",
        "help_text": "使用说明:\n1. 拖拽文件进列表，或点击“添加文件”按钮选择文件。\n2. 点击“开始重命名”按钮开始重命名文件。\n3. 双击列表中的文件名打开图片。\n4. 右键点击列表中的文件名移除文件。\n5. 点击“撤销重命名”按钮恢复到原始名称。\n6. 点击“设置”按钮更改日期格式。\n7. 勾选“自动滚动”选项，列表会自动滚动到最新添加的文件。\n8. 点击“清空列表”按钮清空文件列表。\n9. 点击“停止重命名”按钮停止重命名操作。\n10. 点击文件名显示EXIF信息。",
        "settings_window_title": "设置",
        "prefix": "前缀:",
        "suffix": "后缀:",
        "rename_videos": "重命名视频文件",
        "video_date_basis": "视频文件重命名依据:",
        "modification_date": "修改日期",
        "creation_date": "创建日期",
        "supported_extensions": "支持的文件类型（空格分隔）:",
    },
    "English": {
        "window_title": "QphotoRenamer 1.0.5 —— QwejayHuang",
        "description": "Drag and drop photos into the list for quick addition, and then click ‘Start’ to begin renaming the photos.",
        "start_renaming": "Start",
        "undo_renaming": "Undo",
        "stop_renaming": "Stop",
        "settings": "Settings",
        "clear_list": "Clear List",
        "add_files": "Add Files",
        "help": "Help",
        "auto_scroll": "Auto Scroll",
        "ready": "Ready",
        "rename_pattern": "Rename Pattern:",
        "use_modification_date": "Use Modification Date for Renaming",
        "language": "Language",
        "save_settings": "Save Settings",
        "formats_explanation": "Common Date Formats Examples:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023",
        "renaming_in_progress": "Renaming operation is already in progress, please try again later.",
        "renaming_stopped": "Renaming operation has been stopped.",
        "renaming_success": "Successfully renamed {0} files, {1} files not renamed.",
        "all_files_restored": "All files have been restored to their original names.",
        "help_text": "Usage Instructions:\n1. Drag files into the list or click the 'Add Files' button to select files.\n2. Click the 'Start' button to begin renaming files.\n3. Double-click on a file name in the list to open the image.\n4. Right-click on a file name in the list to remove the file.\n5. Click the 'Undo' button to restore files to their original names.\n6. Click the 'Settings' button to change the date format.\n7. Check the 'Auto Scroll' option to automatically scroll to the latest added file.\n8. Click the 'Clear List' button to clear the file list.\n9. Click the 'Stop' button to stop the renaming operation.\n10. Click on a file name to display EXIF information.",
        "settings_window_title": "Settings",
        "prefix": "Prefix:",
        "suffix": "Suffix:",
        "rename_videos": "Rename video files",
        "video_date_basis": "Video file renaming basis:",
        "modification_date": "Modification date",
        "creation_date": "Creation date",
        "supported_extensions": "Supported file extensions (space-separated):",
    }
}

SUPPORTED_EXTENSIONS = [
    '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic',
    '.mp4', '.avi', '.mkv', '.mov'
]

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("照片批量重命名 QphotoRenamer 1.0.5 —— QwejayHuang")
        self.root.geometry("800x600")
        self.root.iconbitmap(icon_path)

        self.style = ttk.Style('litera')  # 使用ttkbootstrap主题

        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.use_modification_date_var = ttk.BooleanVar(value=True)  # 默认勾选
        self.language_var = ttk.StringVar(value=self.load_language())
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.rename_videos_var = ttk.BooleanVar(value=False)
        self.video_date_var = ttk.StringVar(value="modification")  # 默认使用修改日期

        self.initialize_ui()
        self.load_settings()
        self.set_language(self.language_var.get())

    def initialize_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=ttk.BOTH, expand=True)

        self.label_description = ttk.Label(main_frame, text="只需将照片拖入列表即可快速添加；点击“开始”按钮批量重命名您的照片；双击查看文件；右键点击移除文件；单击文件显示EXIF信息。")
        self.label_description.pack(fill=ttk.X, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(main_frame)
        scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)

        self.files_listbox = ttk.tk.Listbox(main_frame, width=100, height=15, yscrollcommand=scrollbar.set)
        self.files_listbox.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
        self.files_listbox.drop_target_register(DND_FILES)
        self.files_listbox.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_listbox.bind('<Button-3>', self.remove_file)
        self.files_listbox.bind('<Double-1>', self.open_file)
        self.files_listbox.bind('<Button-1>', self.show_exif_info)
        self.files_listbox.bind('<Leave>', self.on_leave)

        scrollbar.config(command=self.files_listbox.yview)

        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=ttk.X, padx=10, pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=ttk.X, padx=10, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始重命名", command=lambda: self.rename_photos())
        self.start_button.pack(side=ttk.LEFT, padx=5)
        self.start_button.config(state=ttk.NORMAL)

        self.undo_button = ttk.Button(button_frame, text="撤销重命名", command=self.undo_rename)
        self.undo_button.pack(side=ttk.LEFT, padx=5)
        self.undo_button.config(state=ttk.DISABLED)

        self.stop_button = ttk.Button(button_frame, text="停止重命名", command=self.stop_renaming)
        self.stop_button.pack(side=ttk.LEFT, padx=5)
        self.stop_button.config(state=ttk.DISABLED)

        self.settings_button = ttk.Button(button_frame, text="设置", command=self.open_settings)
        self.settings_button.pack(side=ttk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="清空列表", command=lambda: self.files_listbox.delete(0, ttk.END))
        self.clear_button.pack(side=ttk.LEFT, padx=5)

        self.select_files_button = ttk.Button(button_frame, text="添加文件", command=lambda: self.select_files())
        self.select_files_button.pack(side=ttk.LEFT, padx=5)

        self.help_button = ttk.Button(button_frame, text="帮助", command=self.show_help)
        self.help_button.pack(side=ttk.LEFT, padx=5)

        self.auto_scroll_checkbox = ttk.Checkbutton(button_frame, text="自动滚动", variable=self.auto_scroll_var)
        self.auto_scroll_checkbox.pack(side=ttk.LEFT, padx=5)

        self.status_bar = ttk.Label(self.root, text="准备就绪", relief=ttk.SUNKEN, anchor=ttk.W)
        self.status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)

    def load_settings(self):
        global DATE_FORMAT, SUPPORTED_EXTENSIONS
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r") as f:
                config = json.load(f)
                DATE_FORMAT = config.get("date_format", "%Y%m%d_%H%M%S")
                self.use_modification_date_var.set(config.get("use_modification_date", True))
                self.language_var.set(config.get("language", locale.getlocale()[0]))
                self.prefix_var.set(config.get("prefix", ""))
                self.suffix_var.set(config.get("suffix", ""))
                self.rename_videos_var.set(config.get("rename_videos", False))
                self.video_date_var.set(config.get("video_date", "modification"))
                SUPPORTED_EXTENSIONS = config.get("supported_extensions", [
                    '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic',
                    '.mp4', '.avi', '.mkv', '.mov'
                ])
        else:
            # 如果配置文件不存在，使用默认值
            DATE_FORMAT = "%Y%m%d_%H%M%S"
            SUPPORTED_EXTENSIONS = [
                '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic',
                '.mp4', '.avi', '.mkv', '.mov'
            ]

    def set_language(self, language):
        if language in LANGUAGES:
            lang = LANGUAGES[language]
            self.root.title(lang["window_title"])
            self.label_description.config(text=lang["description"])
            self.start_button.config(text=lang["start_renaming"])
            self.undo_button.config(text=lang["undo_renaming"])
            self.stop_button.config(text=lang["stop_renaming"])
            self.settings_button.config(text=lang["settings"])
            self.clear_button.config(text=lang["clear_list"])
            self.select_files_button.config(text=lang["add_files"])
            self.help_button.config(text=lang["help"])
            self.auto_scroll_checkbox.config(text=lang["auto_scroll"])
            self.status_bar.config(text=lang["ready"])  # 更新状态栏文本

    def save_language(self, language):
        config = {}
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r") as f:
                config = json.load(f)
        config["language"] = language
        with open("QphotoRenamer.ini", "w") as f:
            json.dump(config, f)

    def load_language(self):
        if os.path.exists("QphotoRenamer.ini"):
            with open("QphotoRenamer.ini", "r") as f:
                config = json.load(f)
                return config.get("language", "简体中文")
        return "简体中文"

    def get_exif_data(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                exif_data = {}
                if 'EXIF DateTimeOriginal' in tags:
                    date_str = str(tags['EXIF DateTimeOriginal'])
                    exif_data['DateTimeOriginal'] = date_str
                    exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                if 'Image Make' in tags:
                    exif_data['Make'] = str(tags['Image Make'])
                if 'Image Model' in tags:
                    exif_data['Model'] = str(tags['Image Model'])
                if 'EXIF ISOSpeedRatings' in tags:
                    exif_data['ISO'] = str(tags['EXIF ISOSpeedRatings'])
                if 'EXIF FNumber' in tags:
                    exif_data['Aperture'] = str(tags['EXIF FNumber'])
                if 'EXIF ExposureTime' in tags:
                    exif_data['ShutterSpeed'] = str(tags['EXIF ExposureTime'])
                if 'EXIF LensModel' in tags:
                    exif_data['LensModel'] = str(tags['EXIF LensModel'])
                if 'EXIF ExifImageWidth' in tags:
                    exif_data['Width'] = str(tags['EXIF ExifImageWidth'])
                if 'EXIF ExifImageLength' in tags:
                    exif_data['Height'] = str(tags['EXIF ExifImageLength'])
                return exif_data
        except Exception as e:
            logging.error(f"读取EXIF数据失败: {file_path}, 错误: {e}")
        return None

    def get_heic_data(self, file_path):
        try:
            heif_file = pillow_heif.read_heif(file_path)
            exif_dict = piexif.load(heif_file.info['exif'])
            exif_data = {}
            if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                exif_data['DateTimeOriginal'] = date_str
                exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            if '0th' in exif_dict:
                if piexif.ImageIFD.Make in exif_dict['0th']:
                    exif_data['Make'] = exif_dict['0th'][piexif.ImageIFD.Make].decode('utf-8')
                if piexif.ImageIFD.Model in exif_dict['0th']:
                    exif_data['Model'] = exif_dict['0th'][piexif.ImageIFD.Model].decode('utf-8')
                if piexif.ExifIFD.ISOSpeedRatings in exif_dict['Exif']:
                    exif_data['ISO'] = str(exif_dict['Exif'][piexif.ExifIFD.ISOSpeedRatings])
                if piexif.ExifIFD.FNumber in exif_dict['Exif']:
                    exif_data['Aperture'] = str(exif_dict['Exif'][piexif.ExifIFD.FNumber])
                if piexif.ExifIFD.ExposureTime in exif_dict['Exif']:
                    exif_data['ShutterSpeed'] = str(exif_dict['Exif'][piexif.ExifIFD.ExposureTime])
                if piexif.ExifIFD.LensModel in exif_dict['Exif']:
                    exif_data['LensModel'] = exif_dict['Exif'][piexif.ExifIFD.LensModel].decode('utf-8')
                if piexif.ExifIFD.PixelXDimension in exif_dict['Exif']:
                    exif_data['Width'] = str(exif_dict['Exif'][piexif.ExifIFD.PixelXDimension])
                if piexif.ExifIFD.PixelYDimension in exif_dict['Exif']:
                    exif_data['Height'] = str(exif_dict['Exif'][piexif.ExifIFD.PixelYDimension])
            return exif_data
        except Exception as e:
            logging.error(f"读取HEIC数据失败: {file_path}, 错误: {e}")
        return None

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
                # Windows 使用 ctime 作为创建日期
                creation_time = os.path.getctime(file_path)
                return datetime.datetime.fromtimestamp(creation_time)
            else:
                # macOS 和 Linux 使用_birthtime_
                stat = os.stat(file_path)
                try:
                    birth_time = stat.st_birthtime
                    return datetime.datetime.fromtimestamp(birth_time)
                except AttributeError:
                    # 如果没有 st_birthtime，使用 ctime
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

        processed_files.clear()
        unrenamed_files = 0

        total_files = self.files_listbox.size()
        batch_size = 100  # 每次处理100个文件
        for start in range(0, total_files, batch_size):
            if stop_event.is_set():
                stop_event.clear()
                self.update_status_bar("renaming_stopped")
                break

            end = min(start + batch_size, total_files)
            for i in range(start, end):
                if stop_event.is_set():
                    stop_event.clear()
                    self.update_status_bar("renaming_stopped")
                    break

                file_path = self.files_listbox.get(i).strip('"')
                if file_path not in processed_files:
                    current_renaming_file = file_path
                    self.update_status_bar("renaming_in_progress", os.path.basename(file_path))
                    renamed = self.rename_photo(file_path, i)
                    if renamed:
                        processed_files.add(file_path)
                        self.files_listbox.delete(i)
                        self.files_listbox.insert(i, f'"{renamed}"')
                        self.progress_var.set((i + 1) * 100 / total_files)
                        if self.auto_scroll_var.get():
                            self.files_listbox.see(i)
                    else:
                        continue

                if stop_event.is_set():
                    stop_event.clear()
                    self.update_status_bar("renaming_stopped")
                    break

            self.root.update_idletasks()

        self.update_status_bar("renaming_success", len(processed_files), unrenamed_files)

        self.undo_button.config(state=ttk.NORMAL)
        renaming_in_progress = False
        self.start_button.config(state=ttk.NORMAL)
        self.stop_button.config(state=ttk.DISABLED)
        current_renaming_file = None

    def rename_photo(self, file_path, current_index):
        global unrenamed_files
        filename = os.path.basename(file_path)
        if re.match(r'\d{8}_\d{6}\.\w+', filename):
            self.update_status_bar("renaming_in_progress", os.path.basename(file_path))
            self.progress_var.set((current_index + 1) * 100 / self.files_listbox.size())
            return False

        # 检查是否是视频文件
        is_video = filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov'))
        if is_video:
            if not self.rename_videos_var.get():
                # 跳过视频文件
                return False
            # 获取视频文件的日期
            if self.video_date_var.get() == "modification":
                date_time = self.get_file_modification_date(file_path)
            else:
                date_time = self.get_file_creation_date(file_path)
        else:
            exif_data = self.get_heic_data(file_path) if filename.lower().endswith('.heic') else self.get_exif_data(file_path)
            date_time = exif_data['DateTimeOriginalParsed'] if exif_data and 'DateTimeOriginalParsed' in exif_data else None
            if not date_time and self.use_modification_date_var.get():
                date_time = self.get_file_modification_date(file_path)

        if date_time:
            base_name = date_time.strftime(DATE_FORMAT)
            prefix = self.prefix_var.get()
            suffix = self.suffix_var.get()
            ext = os.path.splitext(filename)[1]  # 获取原始文件的扩展名
            directory = os.path.dirname(file_path)
            new_file_name = f"{prefix}{base_name}{suffix}"  # 确保只添加一次扩展名
            new_file_path = self.generate_unique_filename(directory, new_file_name, ext)
            if new_file_path != file_path and not os.path.exists(new_file_path):
                try:
                    os.rename(file_path, new_file_path)
                    logging.info(f'重命名成功: "{file_path}" 重命名为 "{new_file_path}"')
                    original_to_new_mapping[file_path] = new_file_path
                    self.progress_var.set((current_index + 1) * 100 / self.files_listbox.size())
                    return new_file_path
                except Exception as e:
                    logging.error(f"重命名失败: {file_path}, 错误: {e}")
            else:
                logging.info(f'跳过重命名: "{file_path}" 已经是重命名后的名字')
        else:
            unrenamed_files += 1
            self.files_listbox.itemconfig(current_index, fg="red")  # 将未重命名的文件显示为红色
        self.progress_var.set((current_index + 1) * 100 / self.files_listbox.size())
        return False

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

    def on_drop(self, event):
        paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
        current_files = set(self.files_listbox.get(0, ttk.END))
        for path in paths:
            path = path.strip().strip('{}')
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if (file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)) and 
                            file_path not in current_files):
                            self.files_listbox.insert(ttk.END, file_path)
                            if self.auto_scroll_var.get():
                                self.files_listbox.see(ttk.END)
            elif (path.lower().endswith(tuple(SUPPORTED_EXTENSIONS)) and 
                  path not in current_files):
                self.files_listbox.insert(ttk.END, path)
                if self.auto_scroll_var.get():
                    self.files_listbox.see(ttk.END)

    def remove_file(self, event):
        selected_indices = self.files_listbox.curselection()
        for index in selected_indices[::-1]:
            self.files_listbox.delete(index)

    def stop_renaming(self):
        stop_event.set()

    def open_settings(self):
        settings_window = ttk.Toplevel(self.root)
        lang = LANGUAGES[self.language_var.get()]
        settings_window.title(lang["settings_window_title"])

        settings_frame = ttk.Frame(settings_window)
        settings_frame.pack(padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["rename_pattern"], anchor='w').grid(row=0, column=0, padx=10, pady=10)
        date_format_var = ttk.StringVar(value=DATE_FORMAT)
        date_format_combobox = ttk.Combobox(settings_frame, textvariable=date_format_var, values=COMMON_DATE_FORMATS, state="readonly")
        date_format_combobox.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["use_modification_date"], anchor='w').grid(row=1, column=0, padx=10, pady=10)
        use_modification_date_checkbox = ttk.Checkbutton(settings_frame, variable=self.use_modification_date_var)
        use_modification_date_checkbox.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["language"], anchor='w').grid(row=2, column=0, padx=10, pady=10)
        language_combobox = ttk.Combobox(settings_frame, textvariable=self.language_var, values=list(LANGUAGES.keys()), state="readonly")
        language_combobox.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["prefix"], anchor='w').grid(row=3, column=0, padx=10, pady=10)
        prefix_entry = Entry(settings_frame, textvariable=self.prefix_var)
        prefix_entry.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["suffix"], anchor='w').grid(row=4, column=0, padx=10, pady=10)
        suffix_entry = Entry(settings_frame, textvariable=self.suffix_var)
        suffix_entry.grid(row=4, column=1, padx=10, pady=10)

        # 新增控件：重命名视频文件选项
        ttk.Checkbutton(settings_frame, text=lang["rename_videos"], variable=self.rename_videos_var).grid(row=5, column=0, columnspan=2, pady=10)

        # 新增控件：选择视频文件重命名依据
        ttk.Label(settings_frame, text=lang["video_date_basis"], anchor='w').grid(row=6, column=0, padx=10, pady=10)
        ttk.Radiobutton(settings_frame, text=lang["modification_date"], variable=self.video_date_var, value="modification").grid(row=6, column=1, sticky='w', padx=10, pady=10)
        ttk.Radiobutton(settings_frame, text=lang["creation_date"], variable=self.video_date_var, value="creation").grid(row=7, column=1, sticky='w', padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["supported_extensions"], anchor='w').grid(row=8, column=0, padx=10, pady=10)
        supported_ext_var = ttk.StringVar(value=" ".join(SUPPORTED_EXTENSIONS))
        supported_ext_entry = Entry(settings_frame, textvariable=supported_ext_var)
        supported_ext_entry.grid(row=8, column=1, padx=10, pady=10)

        ttk.Label(settings_frame, text=lang["formats_explanation"], anchor='w').grid(row=9, column=0, columnspan=2, padx=10, pady=10)

        save_button = ttk.Button(settings_frame, text=lang["save_settings"], command=lambda: self.save_settings(date_format_var.get(), self.language_var.get(), self.prefix_var.get(), self.suffix_var.get(), self.rename_videos_var.get(), self.video_date_var.get(), settings_window, supported_ext_var.get()))
        save_button.grid(row=10, column=0, columnspan=2, padx=10, pady=10)

    def save_settings(self, date_format, language, prefix, suffix, rename_videos, video_date, settings_window, supported_extensions_input):
        global DATE_FORMAT, SUPPORTED_EXTENSIONS
        DATE_FORMAT = date_format
        supported_ext_input = supported_extensions_input.strip().lower()
        SUPPORTED_EXTENSIONS = [ext for ext in supported_ext_input.split() if ext.startswith('.')]
        if not all(ext.startswith('.') for ext in SUPPORTED_EXTENSIONS):
            messagebox.showerror("错误", "扩展名必须以点号开头，例如 .jpg")
            return
        config = {
            "date_format": DATE_FORMAT,
            "use_modification_date": self.use_modification_date_var.get(),
            "language": language,
            "prefix": prefix,
            "suffix": suffix,
            "rename_videos": rename_videos,
            "video_date": video_date,
            "supported_extensions": SUPPORTED_EXTENSIONS
        }
        with open("QphotoRenamer.ini", "w") as f:
            json.dump(config, f)
        self.set_language(language)
        self.update_status_bar("save_settings")
        settings_window.destroy()  # 关闭设置界面

    def select_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("支持的文件", " ".join(SUPPORTED_EXTENSIONS))])
        current_files = set(self.files_listbox.get(0, ttk.END))
        for file_path in file_paths:
            if file_path not in current_files:
                self.files_listbox.insert(ttk.END, file_path)
                if self.auto_scroll_var.get():
                    self.files_listbox.see(ttk.END)

    def show_exif_info(self, event):
        widget = event.widget
        index = widget.curselection()
        if index:
            file_path = widget.get(index[0]).strip('"')
            Thread(target=self.display_exif_info, args=(widget, file_path)).start()

    def display_exif_info(self, widget, file_path):
        filename = os.path.basename(file_path)
        exif_data = self.get_heic_data(file_path) if filename.lower().endswith('.heic') else self.get_exif_data(file_path)
        date_time = exif_data['DateTimeOriginalParsed'] if exif_data and 'DateTimeOriginalParsed' in exif_data else None
        if not date_time:
            date_time = self.get_file_modification_date(file_path)
            exif_data = {'DateTimeOriginalParsed': date_time}
        
        if date_time:
            base_name = date_time.strftime(DATE_FORMAT)
            ext = os.path.splitext(filename)[1]
            new_file_name = f"{base_name}{ext}"
            exif_info = f"新名称: {new_file_name}\n"
            if exif_data:
                exif_info += f"拍摄日期: {exif_data.get('DateTimeOriginal', '未知')}\n"
                exif_info += f"设备: {exif_data.get('Make', '未知')} {exif_data.get('Model', '')}\n"
                exif_info += f"镜头: {exif_data.get('LensModel', '未知')}\n"
                exif_info += f"ISO: {exif_data.get('ISO', '未知')}\n"
                exif_info += f"光圈: {exif_data.get('Aperture', '未知')}\n"
                exif_info += f"快门速度: {exif_data.get('ShutterSpeed', '未知')}\n"
                exif_info += f"分辨率: {exif_data.get('Width', '未知')} x {exif_data.get('Height', '未知')}"

            widget.after(0, self.create_tooltip, widget, exif_info)

    def create_tooltip(self, widget, exif_info):
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            widget.tooltip_window.destroy()
        widget.tooltip_window = Toplevel(widget)
        widget.tooltip_window.wm_overrideredirect(True)
        x, y, _, _ = widget.bbox(widget.curselection()[0])
        x = widget.winfo_rootx() + x + 20
        y = widget.winfo_rooty() + y + 20
        widget.tooltip_window.geometry(f"+{x}+{y}")
        Label(widget.tooltip_window, text=exif_info, background="lightyellow", relief="solid", borderwidth=1, anchor='w', justify='left').pack(fill='both', expand=True)

    def on_leave(self, event):
        widget = event.widget
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            widget.tooltip_window.destroy()
            widget.tooltip_window = None

    def open_file(self, event):
        index = self.files_listbox.index("@%s,%s" % (event.x, event.y))
        if index >= 0 and index < self.files_listbox.size():
            file_path = self.files_listbox.get(index).strip('"')
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, file_path])
            except Exception as e:
                logging.error(f"打开文件失败: {file_path}, 错误: {e}")
        else:
            self.select_files()

    def update_status_bar(self, message_key, *args):
        lang = LANGUAGES[self.language_var.get()]
        if message_key in lang:
            self.status_bar.config(text=lang[message_key].format(*args))
        else:
            self.status_bar.config(text=message_key)

    def show_help(self):
        lang = LANGUAGES[self.language_var.get()]
        help_window = Toplevel(self.root)
        help_window.title(lang["help"])
        help_text = lang["help_text"]
        help_label = Label(help_window, text=help_text, justify='left')
        help_label.pack(padx=10, pady=10)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    renamer = PhotoRenamer(root)
    root.mainloop()