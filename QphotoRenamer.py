import os
import sys
import datetime
from typing import Dict, Optional, Any
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, messagebox, Text
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread, Event, Lock
import logging
import re
import subprocess
import webbrowser
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
import configparser
import gc
import time
import threading

base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'icon.ico')

SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v'}

LANG = {
    "window_title": "文件与照片批量重命名工具 QphotoRenamer 2.4 —— QwejayHuang",
    "drag_hint": "拖入文件，优先使用",
    "rename_hint": "重命名，如无拍摄日期则使用",
    "rename_end_hint": "重命名。",
    "start_renaming": "开始重命名",
    "stop_renaming": "停止重命名",
    "settings": "设置",
    "clear_list": "清空列表",
    "add_files": "添加文件",
    "help": "帮助",
    "auto_scroll": "自动滚动",
    "show_errors_only": "仅显示错误",
    "check_for_updates": "反馈&检查更新",
    "ready": "准备就绪",
    "renaming_in_progress": "正在重命名，请稍候...",
    "renaming_success": "成功重命名 {0} 个文件，未重命名 {1} 个文件。",
    "renaming_complete": "重命名完成: 成功 {0} 个，已跳过 {1} 个。",
    "filename": "文件路径",
    "status": "命名依据",
    "renamed_name": "新名称",
    "ready_to_rename": "待重命名",
    "file_count": "文件总数: {0}",
    "date_bases": [{"display": "拍摄日期"}, {"display": "修改日期"}, {"display": "创建日期"}],
    "alternate_dates": [{"display": "修改日期"}, {"display": "创建日期"}, {"display": "保留原文件名"}],
    "name_conflicts": [{"display": "增加后缀"}, {"display": "保留原文件名"}],
    "help_text": "使用说明:\n1. 拖放文件或点击添加。\n2. 设定格式并点击开始。\n3. 重命名成功显示绿色，失败红色。\n4. 双击打开，右键移除。"
}


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache: return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache: self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity: self.cache.popitem(last=False)

    def clear(self) -> None:
        with self.lock: self.cache.clear()


class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.template_var = ttk.StringVar(value="%Y%m%d_%H%M%S")
        self.prefix_var = ttk.StringVar(value="")
        self.suffix_var = ttk.StringVar(value="")
        self.date_basis_var = ttk.StringVar(value="拍摄日期")
        self.alternate_date_var = ttk.StringVar(value="修改日期")
        self.auto_scroll_var = ttk.BooleanVar(value=True)
        self.show_errors_only_var = ttk.BooleanVar(value=False)
        self.fast_add_mode_var = ttk.BooleanVar(value=True)
        self.fast_add_threshold_var = ttk.IntVar(value=100)
        self.name_conflict_var = ttk.StringVar(value="增加后缀")
        self.suffix_option_var = ttk.StringVar(value="_001")
        self.skip_extensions_var = ttk.StringVar(value="")
        self.stop_event = Event()
        self.renaming_in_progress = False

        self.exif_cache = LRUCache(2000)
        self.error_cache = {}
        self.added_files_set = set()

        self.lang = LANG
        self.file_queue = Queue()
        self.processing_thread = None
        self.toplevel_windows = []

        self.root.title(self.lang["window_title"])
        self.root.geometry("850x600")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        self.style = ttk.Style('litera')
        self.lock = Lock()

        self.initialize_ui()
        self.load_or_create_settings()
        self.remove_invalid_files()

        self.root.after(300000, self.cleanup_cache)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def safe_update_ui(self, func):
        try: func()
        except Exception: pass

    def remove_invalid_files(self):
        invalid_items = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values:
                if not os.path.exists(values[0]):
                    invalid_items.append(item)
        for item in invalid_items:
            vals = self.files_tree.item(item)['values']
            if vals and vals[0] in self.added_files_set:
                self.added_files_set.remove(vals[0])
            self.files_tree.delete(item)
        if invalid_items:
            self.update_file_count()

    def on_closing(self):
        try:
            self.stop_all_operations()
            for window in self.toplevel_windows:
                try: window.destroy()
                except: pass
            self.root.destroy()
        except Exception as e:
            logging.error(f"关闭程序出错: {e}")
            self.root.destroy()

    def load_or_create_settings(self):
        if not os.path.exists('QphotoRenamer.ini'):
            config = configparser.ConfigParser()
            config['General'] = {
                'date_basis': '拍摄日期',
                'alternate_date': '修改日期',
                'skip_extensions': '',
                'name_conflict': '增加后缀',
                'suffix_option': '_001',
                'auto_scroll': 'True',
                'fast_add_mode': 'True',
                'fast_add_threshold': '100',
                'show_errors_only': 'False'
            }
            config['Template'] = {'default': '{date}_{time}'}
            with open('QphotoRenamer.ini', 'w', encoding='utf-8') as f:
                config.write(f)
        self.load_settings()

    def load_settings(self):
        try:
            config = configparser.ConfigParser()
            config.read('QphotoRenamer.ini', encoding='utf-8')
            if not config.has_section('General'): config.add_section('General')

            self.date_basis_var.set(config.get('General', 'date_basis', fallback='拍摄日期'))
            self.alternate_date_var.set(config.get('General', 'alternate_date', fallback='修改日期'))
            self.skip_extensions_var.set(config.get('General', 'skip_extensions', fallback=''))
            self.name_conflict_var.set(config.get('General', 'name_conflict', fallback='增加后缀'))
            self.suffix_option_var.set(config.get('General', 'suffix_option', fallback='_001'))
            self.auto_scroll_var.set(config.getboolean('General', 'auto_scroll', fallback=True))
            self.fast_add_mode_var.set(config.getboolean('General', 'fast_add_mode', fallback=True))
            self.fast_add_threshold_var.set(config.getint('General', 'fast_add_threshold', fallback=100))
            self.show_errors_only_var.set(config.getboolean('General', 'show_errors_only', fallback=False))

            if config.has_section('Template'):
                self.template_var.set(config.get('Template', 'default', fallback='{date}_{time}'))
        except Exception as e:
            logging.error(f"加载设置失败: {e}")

    def save_settings(self, settings_window):
        try:
            if hasattr(self, 'template_editor') and self.template_editor.has_unsaved_changes():
                self.template_editor.save_current_template()

            config = configparser.ConfigParser()
            if os.path.exists("QphotoRenamer.ini"):
                config.read("QphotoRenamer.ini", encoding="utf-8")
            if 'General' not in config:
                config.add_section('General')

            config.set('General', 'date_basis', self.date_basis_var.get())
            config.set('General', 'alternate_date', self.alternate_date_var.get())
            config.set('General', 'skip_extensions', self.skip_extensions_var.get())
            config.set('General', 'name_conflict', self.name_conflict_var.get())
            config.set('General', 'suffix_option', self.suffix_option_var.get())
            config.set('General', 'auto_scroll', str(self.auto_scroll_var.get()))
            config.set('General', 'fast_add_mode', str(self.fast_add_mode_var.get()))
            
            try:
                threshold_val = str(self.fast_add_threshold_var.get())
            except Exception:
                threshold_val = "100"
            config.set('General', 'fast_add_threshold', threshold_val)
            config.set('General', 'show_errors_only', str(self.show_errors_only_var.get()))

            with open("QphotoRenamer.ini", "w", encoding="utf-8") as f:
                config.write(f)

            self.update_renamed_name_column()
            settings_window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def cleanup_cache(self):
        try:
            current_time = time.time()
            expired_errors = [k for k, v in self.error_cache.items() if (current_time - v['last_time']) > 3600]
            for error_id in expired_errors: del self.error_cache[error_id]
            gc.collect()
        except Exception: pass
        finally:
            self.root.after(300000, self.cleanup_cache)

    def get_media_data(self, file_path: str, ext: str) -> Optional[Dict]:
        cached = self.exif_cache.get(file_path)
        if cached is not None:
            return cached

        exif_data = None
        if ext == '.heic':
            exif_data = self.get_heic_data(file_path)
        elif ext in SUPPORTED_IMAGE_FORMATS:
            exif_data = self.get_exif_data(file_path)
        elif ext in SUPPORTED_VIDEO_FORMATS:
            video_date = self.get_video_creation_date(file_path)
            exif_data = {'DateTimeOriginalParsed': video_date} if video_date else {}

        if exif_data is not None:
            self.exif_cache.put(file_path, exif_data)
        return exif_data

    def get_exif_data(self, file_path: str) -> Optional[Dict]:
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                if not tags: return {}

                exif_data = {}
                date_time_original = str(tags.get('EXIF DateTimeOriginal', tags.get('Image DateTime', '')))

                if date_time_original:
                    if "0000:00:00" in date_time_original or "0000/00/00" in date_time_original:
                        return {}
                    formats = ['%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M']
                    for fmt in formats:
                        try:
                            exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_time_original, fmt)
                            break
                        except ValueError: continue

                for tag, value in tags.items():
                    if tag.startswith('EXIF'): exif_data[tag] = str(value)
                    elif tag == 'Image Model': exif_data['Model'] = str(value)
                    elif tag == 'EXIF LensModel': exif_data['LensModel'] = str(value)
                    elif tag == 'EXIF ISOSpeedRatings': exif_data['ISOSpeedRatings'] = str(value)
                    elif tag == 'EXIF FNumber': exif_data['FNumber'] = str(value)
                    elif tag == 'EXIF ExposureTime': exif_data['ExposureTime'] = str(value)
                return exif_data
        except Exception: return {}

    def get_heic_data(self, file_path):
        try:
            # 仅解析元数据，不解码图像像素，速度大幅度提升
            heif_file = pillow_heif.read_heif(file_path, decode_image=False)
            if 'exif' not in heif_file.info: return {}

            exif_dict = piexif.load(heif_file.info['exif'])
            exif_data = {}
            if 'Exif' in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                date_str = date_str.replace("上午", "").replace("下午", "").strip()
                if "0000:00:00" not in date_str:
                    try:
                        exif_data['DateTimeOriginalParsed'] = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError: pass
            return exif_data
        except Exception: return {}

    def get_video_creation_date(self, file_path):
        try:
            with open(file_path, "rb") as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(0)
                offset = 0
                while offset < file_size and offset < 100 * 1024 * 1024:
                    header = f.read(8)
                    if len(header) < 8: break
                    size = int.from_bytes(header[0:4], byteorder='big')
                    atom_type = header[4:8]

                    if size == 1:
                        size_data = f.read(8)
                        if len(size_data) < 8: break
                        size = int.from_bytes(size_data, byteorder='big')
                        header_len = 16
                    else:
                        header_len = 8

                    if size < header_len: break

                    if atom_type == b'moov':
                        offset_moov = f.tell()
                        end_moov = offset_moov + size - header_len
                        while f.tell() < end_moov:
                            h = f.read(8)
                            if len(h) < 8: break
                            s = int.from_bytes(h[0:4], byteorder='big')
                            t = h[4:8]
                            if s == 1:
                                sd = f.read(8)
                                s = int.from_bytes(sd, byteorder='big')
                                hl = 16
                            else: hl = 8
                            if s < hl: break

                            if t == b'mvhd':
                                version = f.read(1)[0]
                                f.read(3)
                                creation_time = int.from_bytes(f.read(4), byteorder='big') if version == 0 else int.from_bytes(f.read(8), byteorder='big')
                                if 0 < creation_time < 20827584000:
                                    try:
                                        dt = datetime.datetime(1904, 1, 1) + datetime.timedelta(seconds=creation_time)
                                        if 1970 < dt.year < 2100: return dt
                                    except (OverflowError, ValueError): pass
                                break
                            else: f.seek(s - hl, 1)
                        break
                    else: f.seek(size - header_len, 1)
                    offset += size
        except Exception: pass

        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format_tags=creation_time', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags)
            if result.returncode == 0 and result.stdout.strip():
                date_str = result.stdout.strip()
                date_str = date_str.replace('T', ' ').replace('Z', '')
                if '.' in date_str:
                    date_str = date_str.split('.')[0]
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
                    try:
                        return datetime.datetime.strptime(date_str.strip(), fmt)
                    except ValueError: continue
        except Exception: pass
        return None

    def initialize_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        date_basis_frame = ttk.Frame(main_frame)
        date_basis_frame.pack(fill='x', pady=5)

        ttk.Label(date_basis_frame, text=self.lang["drag_hint"]).pack(side='left')

        self.date_basis_combobox = ttk.Combobox(date_basis_frame, textvariable=self.date_basis_var, values=[item["display"] for item in self.lang["date_bases"]], state="readonly", width=15)
        self.date_basis_combobox.pack(side='left', padx=5)
        self.date_basis_combobox.bind("<<ComboboxSelected>>", self.on_date_basis_selected)

        ttk.Label(date_basis_frame, text=self.lang["rename_hint"]).pack(side='left', padx=5)

        self.alternate_date_combobox = ttk.Combobox(date_basis_frame, textvariable=self.alternate_date_var, values=[item["display"] for item in self.lang["alternate_dates"]], state="readonly", width=15)
        self.alternate_date_combobox.pack(side='left', padx=5)
        self.alternate_date_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_renamed_name_column())

        ttk.Label(date_basis_frame, text=self.lang["rename_end_hint"]).pack(side='left', padx=5)

        columns = ('filename', 'renamed_name', 'status')
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        self.files_tree.heading('filename', text=self.lang["filename"], anchor='w')
        self.files_tree.heading('renamed_name', text=self.lang["renamed_name"], anchor='w')
        self.files_tree.heading('status', text="命名依据", anchor='w')
        self.files_tree.column('filename', anchor='w', stretch=True, width=400)
        self.files_tree.column('renamed_name', anchor='w', stretch=True, width=200)
        self.files_tree.column('status', anchor='w', width=100, minwidth=100)

        self.files_tree.tag_configure('renamed', foreground='green')
        self.files_tree.tag_configure('failed', foreground='red')

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=vsb.set)
        self.files_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.files_tree.drop_target_register(DND_FILES)
        self.files_tree.dnd_bind('<<Drop>>', lambda e: self.on_drop(e))
        self.files_tree.bind('<Button-3>', self.remove_file)
        self.files_tree.bind('<Double-1>', self.open_file)
        self.files_tree.bind('<Button-1>', self.show_exif_info)

        self.progress_var = ttk.DoubleVar()
        progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill='x', padx=10, pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        self.start_button = ttk.Button(button_frame, text=self.lang["start_renaming"], command=self.rename_photos)
        self.start_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(button_frame, text=self.lang["stop_renaming"], command=self.stop_all_operations, bootstyle="danger")
        self.stop_button.pack(side='left', padx=5)
        self.stop_button.config(state='disabled')

        ttk.Button(button_frame, text=self.lang["settings"], command=self.open_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.lang["clear_list"], command=self.clear_file_list).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.lang["add_files"], command=self.select_files).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.lang["help"], command=self.show_help).pack(side='left', padx=5)

        ttk.Checkbutton(button_frame, text=self.lang["auto_scroll"], variable=self.auto_scroll_var).pack(side='left', padx=5)
        ttk.Checkbutton(button_frame, text=self.lang["show_errors_only"], variable=self.show_errors_only_var).pack(side='left', padx=5)

        self.update_link = ttk.Label(button_frame, text=self.lang["check_for_updates"], foreground="blue", cursor="hand2")
        self.update_link.pack(side='right', padx=5)
        self.update_link.bind("<Button-1>", lambda e: self.open_update_link())

        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_label = ttk.Label(self.status_bar, text=self.lang["ready"], anchor='w')
        self.status_label.pack(side='left', fill='x', expand=True)

        self.file_count_label = ttk.Label(self.status_bar, text="文件总数: 0", anchor='e')
        self.file_count_label.pack(side='right', padx=10)

    def open_settings(self):
        try:
            settings_window = Toplevel(self.root)
            settings_window.title("设置")
            settings_window.geometry("660x660")
            settings_window.resizable(True, True)
            settings_window.transient(self.root)
            settings_window.grab_set()
            self.toplevel_windows.append(settings_window)

            def on_settings_destroy(event):
                if event.widget == settings_window:
                    if settings_window in self.toplevel_windows:
                        self.toplevel_windows.remove(settings_window)
            settings_window.bind("<Destroy>", on_settings_destroy)

            def on_close():
                if hasattr(self, 'template_editor') and self.template_editor.has_unsaved_changes():
                    if messagebox.askyesno("未保存的修改", "模板编辑器中有未保存的修改，是否保存？"):
                        self.template_editor.save_current_template()
                settings_window.destroy()
            settings_window.protocol("WM_DELETE_WINDOW", on_close)

            notebook = ttk.Notebook(settings_window)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)

            # 1. 格式设置
            template_frame = ttk.Frame(notebook)
            notebook.add(template_frame, text="重命名格式设置")
            self.template_editor = TemplateEditor(template_frame, self.template_var, main_app=self)
            self.template_editor.pack(fill='both', expand=True, padx=10, pady=10)

            # 2. 日期设置
            date_frame = ttk.Frame(notebook)
            notebook.add(date_frame, text="日期设置")
            date_basis_frame = ttk.Labelframe(date_frame, text="日期基准")
            date_basis_frame.pack(fill='x', padx=10, pady=5)

            date_basis_select_frame = ttk.Frame(date_basis_frame)
            date_basis_select_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(date_basis_select_frame, text="首选日期:").pack(side='left')
            ttk.Combobox(date_basis_select_frame, textvariable=self.date_basis_var, values=[item['display'] for item in self.lang["date_bases"]], state="readonly").pack(side='left', fill='x', expand=True, padx=5)

            alternate_date_select_frame = ttk.Frame(date_basis_frame)
            alternate_date_select_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(alternate_date_select_frame, text="备选日期:").pack(side='left')
            ttk.Combobox(alternate_date_select_frame, textvariable=self.alternate_date_var, values=[item['display'] for item in self.lang["alternate_dates"]], state="readonly").pack(side='left', fill='x', expand=True, padx=5)

            # 3. 文件处理设置
            file_frame = ttk.Frame(notebook)
            notebook.add(file_frame, text="文件处理设置")

            filter_frame = ttk.Labelframe(file_frame, text="文件过滤")
            filter_frame.pack(fill='x', padx=10, pady=5)
            skip_extensions_frame = ttk.Frame(filter_frame)
            skip_extensions_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(skip_extensions_frame, text="跳过的扩展名 (空格分隔):").pack(side='left')
            ttk.Entry(skip_extensions_frame, textvariable=self.skip_extensions_var).pack(side='left', fill='x', expand=True, padx=5)

            conflict_frame = ttk.Labelframe(file_frame, text="名称冲突处理")
            conflict_frame.pack(fill='x', padx=10, pady=5)
            conflict_select_frame = ttk.Frame(conflict_frame)
            conflict_select_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(conflict_select_frame, text="冲突处理:").pack(side='left')
            name_conflict_combobox = ttk.Combobox(conflict_select_frame, textvariable=self.name_conflict_var, values=[item['display'] for item in self.lang["name_conflicts"]], state="readonly")
            name_conflict_combobox.pack(side='left', fill='x', expand=True, padx=5)

            suffix_option_frame = ttk.Frame(conflict_frame)
            suffix_option_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(suffix_option_frame, text="后缀格式:").pack(side='left')
            suffix_option_combobox = ttk.Combobox(suffix_option_frame, textvariable=self.suffix_option_var, values=["_001", "-01", "_1"], state="readonly" if self.name_conflict_var.get() == "增加后缀" else "disabled")
            suffix_option_combobox.pack(side='left', fill='x', expand=True, padx=5)
            name_conflict_combobox.bind("<<ComboboxSelected>>", lambda e: suffix_option_combobox.config(state="normal" if self.name_conflict_var.get() == "增加后缀" else "disabled"))

            performance_frame = ttk.Labelframe(file_frame, text="性能优化")
            performance_frame.pack(fill='x', padx=10, pady=5)
            fast_add_checkbox = ttk.Checkbutton(performance_frame, text="启用快速添加模式（适用于大量文件）", variable=self.fast_add_mode_var, command=lambda: threshold_entry.config(state="normal" if self.fast_add_mode_var.get() else "disabled"))
            fast_add_checkbox.pack(anchor='w', padx=5, pady=5)
            threshold_frame = ttk.Frame(performance_frame)
            threshold_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(threshold_frame, text="文件数量阈值:").pack(side='left')
            threshold_entry = ttk.Entry(threshold_frame, textvariable=self.fast_add_threshold_var, width=5, state="normal" if self.fast_add_mode_var.get() else "disabled")
            threshold_entry.pack(side='left', padx=5)

            # 4. 关于
            other_frame = ttk.Frame(notebook)
            notebook.add(other_frame, text="关于")

            about_frame = ttk.Labelframe(other_frame, text="关于")
            about_frame.pack(fill='both', expand=True, padx=10, pady=5)
            about_text = (
                "QphotoRenamer 2.4\n\n"
                "是一个简单易用的文件与照片批量重命名工具，支持根据拍摄日期、修改日期或创建日期重命名文件。\n\n"
                "❤拖放支持：直接拖拽极多文件或文件夹到程序界面不卡顿！\n"
                "❤多格式支持：支持常规图片以及视频(mp4/mov等)媒体极速无损解析提取\n"
                "❤EXIF数据利用：自动读取照片EXIF信息用于重命名\n"
                "❤自定义命名格式：支持多种日期格式和变量组合\n"
                "❤高效批处理：优化的多线程架构设计处理超2000个文件轻而易举！\n"
                "❤智能文件名冲突处理：完全无约束的自定义后缀自动递增\n\n"
                "作者：QwejayHuang\n"
                "GitHub：https://github.com/Qwejay/QphotoRenamer"
            )
            ttk.Label(about_frame, text=about_text, justify='left').pack(fill='both', expand=True, padx=10, pady=10)

            ttk.Button(settings_window, text="保存设置", command=lambda: self.save_settings(settings_window)).pack(pady=10)

        except Exception as e:
            logging.error(f"打开设置窗口时出错: {e}")

    def on_date_basis_selected(self, event):
        if self.date_basis_var.get() in ["创建日期", "修改日期"]:
            self.alternate_date_combobox.configure(state="disabled")
            self.alternate_date_var.set("保留原文件名")
        else:
            self.alternate_date_combobox.configure(state="readonly")
        self.update_renamed_name_column()

    def get_cached_or_real_modification_date(self, file_path):
        try: return datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).replace(microsecond=0) if os.path.exists(file_path) else None
        except Exception: return None

    def get_cached_or_real_creation_date(self, file_path):
        try:
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                return datetime.datetime.fromtimestamp(getattr(stat, 'st_birthtime', stat.st_ctime)).replace(microsecond=0)
        except Exception: return None

    def generate_new_name(self, file_path, exif_data, add_suffix=True):
        try:
            file_path = os.path.abspath(file_path)
            directory = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1]
            template = self.template_var.get() or "{date}_{time}"
            date_basis = self.date_basis_var.get()
            date_obj = None

            if date_basis == "拍摄日期":
                if exif_data and 'DateTimeOriginalParsed' in exif_data:
                    date_obj = exif_data['DateTimeOriginalParsed']
                else:
                    alt = self.alternate_date_var.get()
                    if alt == "修改日期": date_obj = self.get_cached_or_real_modification_date(file_path)
                    elif alt == "创建日期": date_obj = self.get_cached_or_real_creation_date(file_path)
            elif date_basis == "修改日期": date_obj = self.get_cached_or_real_modification_date(file_path)
            elif date_basis == "创建日期": date_obj = self.get_cached_or_real_creation_date(file_path)

            if not date_obj: return os.path.basename(file_path)

            variables = {
                "{date}": date_obj.strftime("%Y%m%d"),
                "{time}": date_obj.strftime("%H%M%S"),
                "{original}": os.path.splitext(os.path.basename(file_path))[0],
                "{camera}": exif_data.get('Model', '').strip() if exif_data else '',
                "{lens}": exif_data.get('LensModel', '').strip() if exif_data else '',
                "{iso}": exif_data.get('ISOSpeedRatings', '').strip() if exif_data else '',
                "{focal}": exif_data.get('FocalLength', '').strip() if exif_data else '',
                "{aperture}": f"f{exif_data.get('FNumber', '')}" if exif_data and exif_data.get('FNumber') else '',
                "{shutter}": exif_data.get('ExposureTime', '').strip() if exif_data else ''
            }

            new_name = template
            for var, val in variables.items():
                new_name = new_name.replace(var, val) if val else new_name.replace(var, "")

            new_name = re.sub(r'_+', '_', new_name).strip('_').strip() or "Untitled"

            if add_suffix:
                return self.generate_unique_filename(directory, new_name, ext, self.suffix_option_var.get())
            return new_name + ext
        except Exception: return os.path.basename(file_path)

    def generate_unique_filename(self, directory, base_name, ext, suffix_style):
        new_filename = f"{base_name}{ext}"
        if not os.path.exists(os.path.join(directory, new_filename)):
            return new_filename

        counter = 1
        while counter <= 9999:
            suffix = f"_{counter:03d}" if suffix_style == "_001" else f"-{counter:02d}" if suffix_style == "-01" else f"_{counter}"
            new_filename = f"{base_name}{suffix}{ext}"
            if not os.path.exists(os.path.join(directory, new_filename)):
                return new_filename
            counter += 1
        return base_name + ext

    def update_file_count(self):
        self.root.after(0, lambda: self.file_count_label.config(text=self.lang["file_count"].format(len(self.files_tree.get_children()))))

    def select_files(self):
        paths = filedialog.askopenfilenames()
        if paths: self.add_files_to_queue(paths)

    def on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
            cleaned_paths = []
            for p in paths:
                p_str = str(p).strip()
                if p_str.startswith('{') and p_str.endswith('}'):
                    p_str = p_str[1:-1].strip()
                cleaned_paths.append(p_str)
            self.add_files_to_queue(cleaned_paths)
        except Exception: pass

    def add_files_to_queue(self, paths):
        valid = [os.path.normpath(p) for p in paths if os.path.exists(p)]
        if not valid: return
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.stop_event.clear()
        for path in valid: self.file_queue.put((path, 'file' if os.path.isfile(path) else 'directory'))
        if not self.processing_thread or not self.processing_thread.is_alive():
            self.processing_thread = Thread(target=self.process_files_from_queue, daemon=True)
            self.processing_thread.start()

    def process_files_from_queue(self):
        try:
            all_files = []
            skip_ext_str = self.skip_extensions_var.get().strip().lower()
            skipped_set = set()
            if skip_ext_str:
                skipped_set = {ext if ext.startswith('.') else f".{ext}" for ext in re.split(r'[\s,]+', skip_ext_str) if ext.strip()}

            while not self.file_queue.empty() and not self.stop_event.is_set():
                path, path_type = self.file_queue.get_nowait()
                if path_type == 'file':
                    ext = os.path.splitext(path)[1].lower()
                    if (ext in SUPPORTED_IMAGE_FORMATS or ext in SUPPORTED_VIDEO_FORMATS) and (ext not in skipped_set):
                        all_files.append(os.path.normpath(path))
                elif path_type == 'directory':
                    for root_dir, _, files in os.walk(path):
                        if self.stop_event.is_set(): break
                        for f in files:
                            ext = os.path.splitext(f)[1].lower()
                            if (ext in SUPPORTED_IMAGE_FORMATS or ext in SUPPORTED_VIDEO_FORMATS) and (ext not in skipped_set):
                                all_files.append(os.path.normpath(os.path.join(root_dir, f)))
            if self.stop_event.is_set(): return

            new_files = []
            for path in all_files:
                if path not in self.added_files_set:
                    self.added_files_set.add(path)
                    new_files.append(path)

            if not new_files:
                self.root.after(0, self._finish_processing)
                return

            batch = []
            with ThreadPoolExecutor(max_workers=min(16, os.cpu_count() * 2)) as executor:
                futures = [executor.submit(self._process_single_file, path) for path in new_files]
                for future in as_completed(futures):
                    if self.stop_event.is_set(): break
                    try:
                        res = future.result()
                        if res:
                            batch.append(res)
                            if len(batch) >= 50:
                                self.flush_batch_to_ui(batch)
                                batch = []
                    except Exception: pass

            if batch and not self.stop_event.is_set():
                self.flush_batch_to_ui(batch)

            if not self.stop_event.is_set():
                self.root.after(0, self._finish_processing)
        except Exception: pass

    def _process_single_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        exif_data = self.get_media_data(path, ext)
        status = self.lang["ready_to_rename"] if not exif_data else "待重命名"
        new_name = self.generate_new_name(path, exif_data)
        return (path, new_name, status)

    def flush_batch_to_ui(self, batch):
        def update():
            for item in batch: self.files_tree.insert('', 'end', values=item)
            if self.auto_scroll_var.get() and self.files_tree.get_children():
                self.files_tree.see(self.files_tree.get_children()[-1])
            self.update_file_count()
        self.root.after(0, update)

    def _finish_processing(self):
        self.update_status_bar("ready")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')

    def update_renamed_name_column(self):
        # 主线程一次性读取节点快照，完全避免线程冲突
        items_to_update = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values:
                items_to_update.append((item, values[0]))

        def task():
            for item, path in items_to_update:
                if self.stop_event.is_set(): break
                try:
                    if os.path.exists(path):
                        ext = os.path.splitext(path)[1].lower()
                        exif_data = self.get_media_data(path, ext)
                        new_name = self.generate_new_name(path, exif_data)
                        self.root.after(0, lambda i=item, nn=new_name: self.safe_update_ui(lambda: self.files_tree.set(i, 'renamed_name', nn)))
                except Exception: continue
        Thread(target=task, daemon=True).start()

    def rename_photos(self):
        items = self.files_tree.get_children()
        if not items: return

        # 同样在主线程准备好需要修改的数据快照
        items_data = []
        for item in items:
            vals = self.files_tree.item(item)['values']
            if vals:
                items_data.append((item, vals[0]))

        self.stop_event.clear()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        Thread(target=self.rename_photos_thread, args=(items_data,), daemon=True).start()

    def rename_photos_thread(self, items_data):
        try:
            renamed = errs = skips = 0
            for item, path in items_data:
                if self.stop_event.is_set(): break
                success, result = self.rename_photo(path, item)
                if success:
                    if result == os.path.basename(path): skips += 1
                    else: renamed += 1
                else: errs += 1
            if not self.stop_event.is_set():
                self.update_status_bar("renaming_complete", renamed, skips)
        except Exception: pass
        finally:
            self.stop_event.set()
            self.root.after(0, lambda: self.start_button.config(state='normal'))
            self.root.after(0, lambda: self.stop_button.config(state='disabled'))

    def rename_photo(self, file_path, item):
        try:
            if not os.path.exists(file_path): return False, "Not found"
            ext = os.path.splitext(file_path)[1].lower()
            exif_data = self.get_media_data(file_path, ext)
            new_name = self.generate_new_name(file_path, exif_data)
            if not new_name or new_name == os.path.basename(file_path):
                if self.show_errors_only_var.get():
                    self.root.after(0, lambda: self.safe_update_ui(lambda: self.files_tree.delete(item)))
                else:
                    self.root.after(0, lambda: self.safe_update_ui(lambda: self.files_tree.set(item, 'status', "已跳过")))
                return True, os.path.basename(file_path)

            target = os.path.join(os.path.dirname(file_path), new_name)
            if os.path.exists(target) and not os.path.samefile(file_path, target):
                new_name = self.generate_unique_filename(os.path.dirname(file_path), os.path.splitext(new_name)[0], os.path.splitext(new_name)[1], self.suffix_option_var.get())
                target = os.path.join(os.path.dirname(file_path), new_name)

            os.rename(file_path, target)
            def on_success():
                # 若勾选仅显示错误，将成功的条目直接在列表中删除
                if self.show_errors_only_var.get():
                    self.files_tree.delete(item)
                else:
                    self.files_tree.set(item, 'filename', target)
                    self.files_tree.set(item, 'status', '已重命名')
                    self.files_tree.item(item, tags=('renamed',))
                if file_path in self.added_files_set: self.added_files_set.remove(file_path)
                self.added_files_set.add(target)
            self.root.after(0, lambda: self.safe_update_ui(on_success))
            return True, new_name
        except Exception as e:
            self.root.after(0, lambda: self.safe_update_ui(lambda: self.files_tree.item(item, tags=('failed',))))
            return False, str(e)

    def show_exif_info(self, event):
        item = self.files_tree.identify_row(event.y)
        if not item: return
        try:
            file_path = self.files_tree.item(item, 'values')[0]
            self.create_tooltip(event.widget, f"名称: {os.path.basename(file_path)}")
        except Exception: pass

    def create_tooltip(self, widget, text):
        if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
            try: widget.tooltip_window.destroy()
            except Exception: pass
        tooltip = Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.geometry(f"+{widget.winfo_pointerx()+10}+{widget.winfo_pointery()+10}")
        Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1).pack()
        
        def close_tooltip(e):
            try: tooltip.destroy()
            except Exception: pass
        widget.bind("<Leave>", close_tooltip, add="+")
        tooltip.bind("<Leave>", close_tooltip, add="+")
        widget.tooltip_window = tooltip

    def remove_file(self, event):
        for item in self.files_tree.selection():
            vals = self.files_tree.item(item)['values']
            if vals and vals[0] in self.added_files_set:
                self.added_files_set.remove(vals[0])
            self.files_tree.delete(item)
        self.update_file_count()

    def clear_file_list(self):
        self.files_tree.delete(*self.files_tree.get_children())
        self.added_files_set.clear()
        self.update_file_count()

    def open_file(self, event):
        item = self.files_tree.identify_row(event.y)
        if item and os.path.exists(self.files_tree.item(item, 'values')[0]):
            os.startfile(self.files_tree.item(item, 'values')[0]) if sys.platform == 'win32' else subprocess.run(['open', self.files_tree.item(item, 'values')[0]])

    def update_status_bar(self, msg_key, *args):
        self.root.after(0, lambda: self.status_label.config(text=self.lang.get(msg_key, msg_key).format(*args)))

    def show_help(self):
        w = Toplevel(self.root)
        w.title("帮助")
        Label(w, text=self.lang["help_text"], justify='left').pack(padx=20, pady=20)

    def open_update_link(self):
        try: webbrowser.open("https://github.com/Qwejay/QphotoRenamer")
        except Exception: pass

    def stop_all_operations(self):
        self.stop_event.set()


class TemplateEditor(ttk.Frame):
    def __init__(self, parent, template_var, main_app=None):
        super().__init__(parent)
        self.template_var = template_var
        self.lang = LANG
        self.main_app = main_app
        self.is_modified = False
        self.last_saved_content = ""
        self.config_file = 'QphotoRenamer.ini'
        self.variables = [
            ("{date}", "日期"), ("{time}", "时间"), ("{camera}", "相机型号"),
            ("{lens}", "镜头型号"), ("{iso}", "ISO"), ("{focal}", "焦距"),
            ("{aperture}", "光圈"), ("{shutter}", "快门")
        ]
        self.templates = [
            "{date}_{time}", "{date}_{time}_{camera}_{lens}_{iso}_{focal}_{aperture}",
            "{date}_{time}_{camera}", "{camera}_{lens}_{iso}_{focal}_{aperture}"
        ]
        self.setup_ui()
        self.load_templates()
        self.set_template(self.template_var.get() or self.templates[0])

    def setup_ui(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        middle_frame = ttk.Frame(self)
        middle_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)

        preset_frame = ttk.Labelframe(top_frame, text="选择模板")
        preset_frame.pack(fill='both', expand=True, padx=5, pady=5)
        preset_top_frame = ttk.Frame(preset_frame)
        preset_top_frame.pack(fill='x', padx=5, pady=5)
        self.template_combobox = ttk.Combobox(preset_top_frame, values=self.templates, state="readonly", width=50)
        self.template_combobox.pack(side='left', padx=5, pady=5, fill='x', expand=True)
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)

        btn_frame = ttk.Frame(preset_top_frame)
        btn_frame.pack(side='right', padx=5)
        ttk.Button(btn_frame, text="保存", command=self.save_current_template, width=8).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="删除", command=self.delete_current_template, width=8).pack(side='left', padx=2)

        edit_frame = ttk.Labelframe(top_frame, text="编辑模板")
        edit_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.template_text = Text(edit_frame, height=3, wrap='word')
        self.template_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.template_text.bind('<KeyRelease>', lambda e: self.on_text_change())

        var_frame = ttk.Labelframe(middle_frame, text="变量")
        var_frame.pack(fill='both', expand=True, padx=5, pady=5)
        f = ttk.Frame(var_frame)
        f.pack(fill='both', expand=True, padx=5, pady=5)
        for i, (var, desc) in enumerate(self.variables):
            bf = ttk.Frame(f)
            bf.grid(row=i//4, column=i%4, sticky="ew", padx=2, pady=2)
            ttk.Button(bf, text=desc, width=8, command=lambda v=var: self.insert_variable(v)).pack(side='left', padx=2)
            ttk.Label(bf, text=var, foreground="gray", width=8).pack(side='left', padx=2)
        for i in range(4): f.columnconfigure(i, weight=1)

        prev_frame = ttk.Labelframe(bottom_frame, text="预览")
        prev_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.preview_label = ttk.Label(prev_frame, text="", anchor='w')
        self.preview_label.pack(fill='x', padx=5, pady=5)

    def on_text_change(self):
        self.template_var.set(self.template_text.get("1.0", 'end').strip())
        self.update_preview()

    def update_preview(self):
        t = self.template_text.get("1.0", 'end').strip()
        self.is_modified = t != self.last_saved_content
        if self.is_modified and t not in self.templates:
            vals = list(self.template_combobox['values'])
            if "(新模板)" not in vals:
                self.template_combobox['values'] = vals + ["(新模板)"]
                self.template_combobox.set("(新模板)")

        prev = t.replace("{date}", "20240315").replace("{time}", "143022").replace("{camera}", "Canon EOS R5").replace("{lens}", "RF 24-70mm F2.8L").replace("{iso}", "100").replace("{focal}", "50mm").replace("{aperture}", "f2.8").replace("{shutter}", "1/125")
        self.preview_label.config(text=prev)

    def insert_variable(self, var):
        self.template_text.insert('insert', var)
        self.on_text_change()

    def has_unsaved_changes(self):
        return self.template_text.get("1.0", 'end').strip() != self.last_saved_content

    def set_template(self, template):
        self.template_text.delete("1.0", 'end')
        self.template_text.insert("1.0", template)
        self.last_saved_content = template
        self.is_modified = False
        self.template_combobox.set(template)
        self.template_var.set(template)
        self.update_preview()

    def on_template_selected(self, event=None):
        sel = self.template_combobox.get()
        if sel != "(新模板)" and sel in self.templates:
            self.set_template(sel)

    def save_current_template(self):
        t = self.template_text.get("1.0", 'end').strip()
        if not t: return
        if t not in self.templates: self.templates.append(t)
        self.last_saved_content = t
        self.is_modified = False

        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.config_file): config.read(self.config_file, encoding='utf-8')
            if 'Template' not in config: config['Template'] = {}
            config['Template']['default'] = t
            for i, tmpl in enumerate(self.templates, 1):
                config['Template'][f'template{i}'] = tmpl
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception: pass

        self.template_combobox['values'] = [x for x in self.templates if x != "(新模板)"]
        self.template_combobox.set(t)

    def load_templates(self):
        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.config_file):
                config.read(self.config_file, encoding='utf-8')
                if config.has_section('Template'):
                    loaded = [config.get('Template', k) for k in config.options('Template') if k.startswith('template')]
                    if loaded: self.templates = list(dict.fromkeys(loaded))
        except Exception: pass
        self.template_combobox['values'] = self.templates

    def delete_current_template(self):
        t = self.template_combobox.get()
        if t in self.templates:
            self.templates.remove(t)
            self.save_current_template()
            if self.templates: self.set_template(self.templates[0])
            else: self.set_template("")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    try:
        renamer = PhotoRenamer(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序遇到严重错误: {str(e)}")
        os._exit(1)