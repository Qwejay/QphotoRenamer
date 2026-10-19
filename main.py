import os
import sys
import errno
import ctypes
import datetime
import json
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
import tempfile
import threading

base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'icon.ico')
LEGACY_CONFIG_PATH = os.path.join(base_path, 'QphotoRenamer.ini')


def _resolve_config_path():
    # Keep the historical INI location when writable, but support read-only install folders.
    if os.access(base_path, os.W_OK) and (
        not os.path.exists(LEGACY_CONFIG_PATH) or os.access(LEGACY_CONFIG_PATH, os.W_OK)
    ):
        return LEGACY_CONFIG_PATH
    if os.name == 'nt':
        config_dir = os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'QphotoRenamer')
    elif sys.platform == 'darwin':
        config_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'QphotoRenamer')
    else:
        config_dir = os.path.join(os.environ.get('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config'), 'QphotoRenamer')
    return os.path.join(config_dir, 'QphotoRenamer.ini')


CONFIG_PATH = _resolve_config_path()
LOG_PATH = os.path.join(base_path, 'QphotoRenamer.log')
_LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
try:
    _file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
except OSError:
    # Installed application folders may be read-only; keep diagnostics in a writable location.
    LOG_PATH = os.path.join(os.path.expanduser('~'), 'QphotoRenamer.log')
    try:
        _file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
    except OSError:
        LOG_PATH = os.path.join(tempfile.gettempdir(), 'QphotoRenamer.log')
        _file_handler = logging.FileHandler(LOG_PATH, encoding='utf-8')
_file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
logging.basicConfig(level=logging.INFO, handlers=[_file_handler])


def _atomic_write_config(config, destination):
    """Write settings without clobbering a pre-existing temporary/user file."""
    destination = os.path.abspath(destination)
    directory = os.path.dirname(destination)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(destination) + '.', suffix='.tmp', dir=directory
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            config.write(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, destination)
        tmp_path = ''
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
            except OSError:
                logging.warning('清理配置临时文件失败: %s', tmp_path, exc_info=True)


SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.heic'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.m4v'}

LANG = {
    "window_title": "文件与照片批量重命名工具 QphotoRenamer 2.7 —— QwejayHuang",
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
        self._queue_lock = Lock()
        self._state_lock = Lock()
        self._active_operation = None
        self._closing = False
        self.ui_queue = Queue()
        self._skip_extensions_snapshot = ''

        self.exif_cache = LRUCache(2000)
        self.added_files_set = set()
        self._path_by_key = {}
        # Identity snapshot prevents stale previews from renaming a different/replaced file.
        self._file_fingerprints = {}
        self._detached_items = set()
        self._preview_generation = 0

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
        self._job_config_snapshot = self._get_config_snapshot()
        self.remove_invalid_files()

        self.root.after(50, self._drain_ui_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._refresh_date_basis_widgets()

    def safe_update_ui(self, func):
        try:
            func()
        except Exception:
            logging.debug("UI update failed", exc_info=True)

    def post_ui(self, func):
        """Queue UI work; worker threads never call Tk APIs directly."""
        if not self._closing:
            self.ui_queue.put(func)

    def _drain_ui_queue(self):
        if self._closing:
            return
        for _ in range(500):
            try:
                callback = self.ui_queue.get_nowait()
            except Exception:
                break
            self.safe_update_ui(callback)
        try:
            self.root.after(50, self._drain_ui_queue)
        except Exception:
            pass

    def remove_invalid_files(self):
        invalid_items = []
        all_items = list(self.files_tree.get_children()) + list(self._detached_items)
        for item in all_items:
            values = self.files_tree.item(item)['values']
            if values:
                if not os.path.exists(values[0]):
                    invalid_items.append(item)
        for item in invalid_items:
            vals = self.files_tree.item(item)['values']
            if vals:
                self.added_files_set.discard(vals[0])
                key = os.path.normcase(os.path.realpath(vals[0]))
                self._path_by_key.pop(key, None)
                self._file_fingerprints.pop(key, None)
            self.files_tree.delete(item)
            self._detached_items.discard(item)
        if invalid_items:
            self.update_file_count()

    def on_closing(self):
        self._closing = True
        self.stop_event.set()
        try:
            for window in list(self.toplevel_windows):
                try:
                    window.destroy()
                except Exception:
                    pass
            self.root.destroy()
        except Exception:
            logging.exception("关闭程序出错")

    def load_or_create_settings(self):
        if not os.path.exists(CONFIG_PATH) and not os.path.exists(LEGACY_CONFIG_PATH):
            config = configparser.ConfigParser()
            config['General'] = {
                'date_basis': '拍摄日期', 'alternate_date': '修改日期',
                'skip_extensions': '', 'name_conflict': '增加后缀',
                'suffix_option': '_001', 'auto_scroll': 'True',
                'fast_add_mode': 'True', 'fast_add_threshold': '100',
                'show_errors_only': 'False'
            }
            config['Template'] = {'default': '{date}_{time}', 'template1': '{date}_{time}'}
            self._write_config_atomically(config)
        self.load_settings()

    def _write_config_atomically(self, config):
        _atomic_write_config(config, CONFIG_PATH)

    def load_settings(self):
        config = configparser.ConfigParser()
        try:
            config.read([LEGACY_CONFIG_PATH, CONFIG_PATH], encoding='utf-8')
        except Exception:
            logging.exception("读取设置文件失败，将使用默认设置")

        def read_string(key, default):
            try:
                value = config.get('General', key, fallback=default)
                return value if value is not None else default
            except Exception:
                logging.warning("设置项 %s 无效，使用默认值", key, exc_info=True)
                return default

        def read_boolean(key, default):
            try:
                return config.getboolean('General', key, fallback=default)
            except Exception:
                logging.warning("布尔设置项 %s 无效，使用默认值", key, exc_info=True)
                return default

        def read_integer(key, default):
            try:
                return max(1, config.getint('General', key, fallback=default))
            except Exception:
                logging.warning("整数设置项 %s 无效，使用默认值", key, exc_info=True)
                return default

        date_basis = read_string('date_basis', '拍摄日期')
        if date_basis not in {item['display'] for item in self.lang['date_bases']}:
            date_basis = '拍摄日期'
        alternate = read_string('alternate_date', '修改日期')
        if alternate not in {item['display'] for item in self.lang['alternate_dates']}:
            alternate = '修改日期'
        conflict = read_string('name_conflict', '增加后缀')
        if conflict not in {item['display'] for item in self.lang['name_conflicts']}:
            conflict = '增加后缀'
        suffix = read_string('suffix_option', '_001')
        if suffix not in {'_001', '-01', '_1'}:
            suffix = '_001'

        self.date_basis_var.set(date_basis)
        self.alternate_date_var.set(alternate)
        self.skip_extensions_var.set(read_string('skip_extensions', ''))
        self.name_conflict_var.set(conflict)
        self.suffix_option_var.set(suffix)
        self.auto_scroll_var.set(read_boolean('auto_scroll', True))
        self.fast_add_mode_var.set(read_boolean('fast_add_mode', True))
        self.fast_add_threshold_var.set(read_integer('fast_add_threshold', 100))
        self.show_errors_only_var.set(read_boolean('show_errors_only', False))
        try:
            self.template_var.set(config.get('Template', 'default', fallback='{date}_{time}') or '{date}_{time}')
        except Exception:
            self.template_var.set('{date}_{time}')
            logging.warning("模板设置无效，使用默认模板", exc_info=True)

    def save_settings(self, settings_window):
        try:
            if hasattr(self, 'template_editor') and self.template_editor.has_unsaved_changes():
                if not self.template_editor.save_current_template():
                    return
            config = configparser.ConfigParser()
            config.read([LEGACY_CONFIG_PATH, CONFIG_PATH], encoding='utf-8')
            if not config.has_section('General'):
                config.add_section('General')
            values = {
                'date_basis': self.date_basis_var.get(),
                'alternate_date': self.alternate_date_var.get(),
                'skip_extensions': self.skip_extensions_var.get(),
                'name_conflict': self.name_conflict_var.get(),
                'suffix_option': self.suffix_option_var.get(),
                'auto_scroll': str(self.auto_scroll_var.get()),
                'fast_add_mode': str(self.fast_add_mode_var.get()),
                'fast_add_threshold': str(max(1, int(self.fast_add_threshold_var.get()))),
                'show_errors_only': str(self.show_errors_only_var.get()),
            }
            for key, value in values.items():
                config.set('General', key, value)
            self._write_config_atomically(config)
            self.update_renamed_name_column()
            self._refresh_date_basis_widgets()
            settings_window.destroy()
        except Exception as e:
            logging.exception("保存设置失败")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def _cache_key(self, file_path):
        try:
            real_path = os.path.normcase(os.path.realpath(file_path))
            st = os.stat(file_path)
            return (
                real_path, st.st_dev, st.st_ino, st.st_size,
                getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9)),
                getattr(st, 'st_ctime_ns', int(st.st_ctime * 1e9)),
            )
        except OSError:
            return (os.path.normcase(os.path.abspath(file_path)), None, None)

    def get_media_data(self, file_path: str, ext: str) -> Optional[Dict]:
        key = self._cache_key(file_path)
        cached = self.exif_cache.get(key)
        if cached is not None:
            return cached
        ext = ext.lower()
        try:
            if ext == '.heic':
                data = self.get_heic_data(file_path)
            elif ext in SUPPORTED_IMAGE_FORMATS:
                data = self.get_exif_data(file_path)
            elif ext in SUPPORTED_VIDEO_FORMATS:
                video_date = self.get_video_creation_date(file_path)
                data = {'DateTimeOriginalParsed': video_date} if video_date else {}
            else:
                data = {}
        except Exception as exc:
            logging.exception("读取媒体元数据失败: %s", file_path)
            data = {'_metadata_error': f'媒体元数据读取失败: {exc}'}
        self.exif_cache.put(key, data if data is not None else {})
        return data if data is not None else {}

    @staticmethod
    def _parse_exif_datetime(value):
        value = str(value or '').strip().strip('\x00 ')
        if not value or '0000:00:00' in value or '0000/00/00' in value:
            return None
        for fmt in ('%Y:%m:%d %H:%M:%S', '%Y:%m:%d %H:%M',
                    '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M'):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _tag_text(value, field=''):
        if value is None:
            return ''
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace').strip('\x00 ')
        numerator = getattr(value, 'num', None)
        denominator = getattr(value, 'den', None)
        if numerator is None and isinstance(value, (tuple, list)) and len(value) == 2:
            numerator, denominator = value
        try:
            if numerator is not None and denominator not in (None, 0):
                n, d = float(numerator), float(denominator)
                if field == 'ExposureTime':
                    return f'{int(numerator)}/{int(denominator)}' if d != 1 else str(int(n))
                number = n / d
                rendered = str(int(number)) if number.is_integer() else f'{number:.4g}'
                return rendered + ('mm' if field == 'FocalLength' else '')
        except (TypeError, ValueError, OverflowError):
            pass
        text = str(value).strip().strip('\x00 ')
        if field == 'FocalLength' and text and not re.search(r'(?i)mm$', text):
            match = re.fullmatch(r'(\d+(?:\.\d+)?)', text)
            if match:
                text += 'mm'
        return text

    def get_exif_data(self, file_path: str) -> Optional[Dict]:
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            if not tags:
                return {}
            date_value = (tags.get('EXIF DateTimeOriginal') or
                          tags.get('EXIF DateTimeDigitized') or tags.get('Image DateTime'))
            date_obj = self._parse_exif_datetime(date_value)
            data = {'DateTimeOriginalParsed': date_obj} if date_obj else {}
            aliases = {
                'Model': ('Image Model', 'EXIF Model'),
                'LensModel': ('EXIF LensModel', 'EXIF Lens Model'),
                'ISOSpeedRatings': ('EXIF ISOSpeedRatings', 'EXIF ISO'),
                'FNumber': ('EXIF FNumber',),
                'ExposureTime': ('EXIF ExposureTime',),
                'FocalLength': ('EXIF FocalLength',),
            }
            for target, keys in aliases.items():
                for key in keys:
                    if tags.get(key) is not None:
                        data[target] = self._tag_text(tags[key], target)
                        break
            return data
        except Exception as exc:
            logging.warning("EXIF读取失败: %s", file_path, exc_info=True)
            return {'_metadata_error': f'EXIF读取失败: {exc}'}

    def get_heic_data(self, file_path):
        try:
            heif_file = pillow_heif.read_heif(file_path, decode_image=False)
            exif_blob = heif_file.info.get('exif')
            if not exif_blob:
                return {}
            exif_dict = piexif.load(exif_blob)
            data = {}
            exif_ifd = exif_dict.get('Exif', {})
            date_bytes = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal) or exif_ifd.get(piexif.ExifIFD.DateTimeDigitized)
            if date_bytes:
                if isinstance(date_bytes, bytes):
                    date_bytes = date_bytes.decode('utf-8', errors='replace')
                parsed = self._parse_exif_datetime(date_bytes)
                if parsed:
                    data['DateTimeOriginalParsed'] = parsed
            if exif_dict.get('0th', {}).get(piexif.ImageIFD.Model):
                data['Model'] = exif_dict['0th'][piexif.ImageIFD.Model].decode('utf-8', errors='replace').strip('\x00 ')
            mappings = {
                'LensModel': (piexif.ExifIFD.LensModel, 'LensModel'),
                'ISOSpeedRatings': (piexif.ExifIFD.ISOSpeedRatings, 'ISOSpeedRatings'),
                'FNumber': (piexif.ExifIFD.FNumber, 'FNumber'),
                'ExposureTime': (piexif.ExifIFD.ExposureTime, 'ExposureTime'),
                'FocalLength': (piexif.ExifIFD.FocalLength, 'FocalLength'),
            }
            for key, (tag_id, _) in mappings.items():
                value = exif_ifd.get(tag_id)
                if value is not None:
                    data[key] = self._tag_text(value, key)
            return data
        except Exception as exc:
            logging.warning("HEIC元数据读取失败: %s", file_path, exc_info=True)
            return {'_metadata_error': f'HEIC元数据读取失败: {exc}'}

    @staticmethod
    def _parse_video_datetime(value, preserve_wall_time=False):
        """Parse ISO/QuickTime dates; preserve a camera-tag's written wall time when requested."""
        if not value:
            return None
        text = str(value).strip().strip('"')
        if not text:
            return None
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        try:
            dt = datetime.datetime.fromisoformat(text.replace(' ', 'T', 1) if 'T' not in text and ' ' in text else text)
        except ValueError:
            dt = None
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
                try:
                    dt = datetime.datetime.strptime(text, fmt)
                    break
                except ValueError:
                    pass
        if dt is None:
            return None
        if dt.year < 1970 or dt.year > 2100:
            return None
        if dt.tzinfo is not None:
            if preserve_wall_time:
                dt = dt.replace(tzinfo=None)
            else:
                dt = dt.astimezone().replace(tzinfo=None)
        return dt.replace(microsecond=0)

    def _read_quicktime_mvhd_date(self, file_path):
        """Read the mvhd creation value without imposing the host's timezone on a naive field.

        Some camera-generated QuickTime files encode local wall time in mvhd even though the
        field is specified in UTC. Preserve the stored clock value here to avoid host-dependent
        8-hour shifts. Prefer an explicit Apple capture-date tag when available.
        """
        epoch = datetime.datetime(1904, 1, 1)
        try:
            with open(file_path, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                limit = file_size

                def read_atom_header(pos, parent_end):
                    if pos + 8 > parent_end:
                        return None
                    f.seek(pos)
                    header = f.read(8)
                    if len(header) != 8:
                        return None
                    size = int.from_bytes(header[:4], 'big')
                    atom_type = header[4:8]
                    header_len = 8
                    if size == 1:
                        ext = f.read(8)
                        if len(ext) != 8:
                            return None
                        size = int.from_bytes(ext, 'big')
                        header_len = 16
                    elif size == 0:
                        size = parent_end - pos
                    if size < header_len or pos + size > parent_end:
                        return None
                    return size, atom_type, header_len

                pos = 0
                while pos + 8 <= limit:
                    atom = read_atom_header(pos, limit)
                    if not atom:
                        break
                    size, atom_type, header_len = atom
                    if atom_type == b'moov':
                        child_pos = pos + header_len
                        end = pos + size
                        while child_pos + 8 <= end:
                            child = read_atom_header(child_pos, end)
                            if not child:
                                break
                            child_size, child_type, child_header_len = child
                            if child_type == b'mvhd':
                                payload = child_pos + child_header_len
                                f.seek(payload)
                                full_header = f.read(4)
                                if len(full_header) != 4:
                                    return None
                                version = full_header[0]
                                width = 4 if version == 0 else 8 if version == 1 else 0
                                if not width:
                                    return None
                                raw = f.read(width)
                                if len(raw) != width:
                                    return None
                                seconds = int.from_bytes(raw, 'big')
                                if seconds <= 0:
                                    return None
                                dt = epoch + datetime.timedelta(seconds=seconds)
                                return dt.replace(microsecond=0) if 1970 <= dt.year <= 2100 else None
                            child_pos += child_size
                        return None
                    pos += size
        except (OSError, OverflowError, ValueError):
            logging.debug("读取mvhd失败: %s", file_path, exc_info=True)
        return None

    def get_video_creation_date(self, file_path):
        # Explicit Apple metadata is a capture wall-time; do not convert it through the PC timezone.
        generic_creation_time = None
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=15, creationflags=flags, check=False)
            if result.returncode == 0 and result.stdout.strip():
                payload = json.loads(result.stdout)
                tag_groups = []
                fmt_tags = payload.get('format', {}).get('tags', {})
                if fmt_tags:
                    tag_groups.append(fmt_tags)
                for stream in payload.get('streams', []):
                    if stream.get('tags'):
                        tag_groups.append(stream['tags'])
                normalized = {}
                for group in tag_groups:
                    for key, value in group.items():
                        normalized[str(key).lower()] = value
                generic_creation_time = normalized.get('creation_time')
                for key in ('com.apple.quicktime.creationdate', 'com.apple.quicktime.creation_date', 'date'):
                    parsed = self._parse_video_datetime(normalized.get(key), preserve_wall_time=True)
                    if parsed:
                        return parsed
        except FileNotFoundError:
            logging.info("未安装ffprobe，将使用QuickTime元数据备用解析: %s", file_path)
        except subprocess.TimeoutExpired:
            logging.warning("ffprobe读取视频元数据超时: %s", file_path)
        except Exception:
            logging.debug("ffprobe读取失败: %s", file_path, exc_info=True)

        # Use the raw mvhd clock field before FFprobe's generic UTC-normalized creation_time.
        parsed = self._read_quicktime_mvhd_date(file_path)
        if parsed:
            return parsed
        parsed = self._parse_video_datetime(generic_creation_time, preserve_wall_time=False)
        if parsed:
            return parsed

        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format_tags=creation_time',
                   '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, timeout=15, creationflags=flags, check=False)
            if result.returncode == 0:
                return self._parse_video_datetime(result.stdout.strip(), preserve_wall_time=False)
        except Exception:
            logging.debug("ffprobe备用日期读取失败: %s", file_path, exc_info=True)
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
        ttk.Checkbutton(button_frame, text=self.lang["show_errors_only"], variable=self.show_errors_only_var, command=self.apply_error_filter).pack(side='left', padx=5)

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
                        if not self.template_editor.save_current_template():
                            return
                    else:
                        # Discard the edited template so Start cannot use an unpreviewed value.
                        self.template_var.set(self.template_editor.last_saved_content)
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
            self.settings_date_basis_combobox = date_basis_select_frame.winfo_children()[-1]
            self.settings_date_basis_combobox.bind('<<ComboboxSelected>>', self.on_date_basis_selected)

            alternate_date_select_frame = ttk.Frame(date_basis_frame)
            alternate_date_select_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(alternate_date_select_frame, text="备选日期:").pack(side='left')
            self.settings_alternate_date_combobox = ttk.Combobox(alternate_date_select_frame, textvariable=self.alternate_date_var, values=[item['display'] for item in self.lang["alternate_dates"]], state="readonly")
            self.settings_alternate_date_combobox.pack(side='left', fill='x', expand=True, padx=5)
            self.settings_alternate_date_combobox.bind('<<ComboboxSelected>>', lambda e: self.update_renamed_name_column())

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
            def on_conflict_selected(event=None):
                suffix_option_combobox.config(state="normal" if self.name_conflict_var.get() == "增加后缀" else "disabled")
                self.update_renamed_name_column()

            name_conflict_combobox.bind("<<ComboboxSelected>>", on_conflict_selected)
            suffix_option_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_renamed_name_column())

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
                "QphotoRenamer 2.7\n\n"
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

            self._refresh_date_basis_widgets()
            ttk.Button(settings_window, text="保存设置", command=lambda: self.save_settings(settings_window)).pack(pady=10)

        except Exception as e:
            logging.error(f"打开设置窗口时出错: {e}")

    def _refresh_date_basis_widgets(self):
        basis = self.date_basis_var.get()
        state = 'disabled' if basis in ('创建日期', '修改日期') else 'readonly'
        for widget_name in ('alternate_date_combobox', 'settings_alternate_date_combobox'):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                try:
                    widget.configure(state=state)
                except Exception:
                    pass

    def on_date_basis_selected(self, event=None):
        self._refresh_date_basis_widgets()
        self.update_renamed_name_column()

    @staticmethod
    def _file_identity(file_path):
        """Identity + change fingerprint for detecting path replacement or edits."""
        st = os.stat(file_path)
        return (
            st.st_dev, st.st_ino, st.st_size,
            getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9)),
            getattr(st, 'st_ctime_ns', int(st.st_ctime * 1e9)),
        )

    def get_cached_or_real_modification_date(self, file_path):
        try:
            return datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).replace(microsecond=0)
        except (OSError, ValueError, OverflowError):
            return None

    def get_cached_or_real_creation_date(self, file_path):
        try:
            stat_result = os.stat(file_path)
            birthtime = getattr(stat_result, 'st_birthtime', None)
            if birthtime is None and os.name == 'nt':
                birthtime = stat_result.st_ctime
            # On Linux, st_ctime is inode-change time, not creation time. Do not mislabel it.
            if birthtime is None:
                return None
            return datetime.datetime.fromtimestamp(birthtime).replace(microsecond=0)
        except (OSError, ValueError, OverflowError):
            return None

    def _safe_threshold_value(self):
        try:
            return max(1, int(self.fast_add_threshold_var.get()))
        except (TypeError, ValueError):
            return 100

    def _get_config_snapshot(self):
        """Read Tk variables only on the main thread; pass plain values to workers."""
        return {
            'template': self.template_var.get() or '{date}_{time}',
            'date_basis': self.date_basis_var.get(),
            'alternate_date': self.alternate_date_var.get(),
            'name_conflict': self.name_conflict_var.get(),
            'suffix_option': self.suffix_option_var.get(),
            'show_errors_only': bool(self.show_errors_only_var.get()),
            'auto_scroll': bool(self.auto_scroll_var.get()),
            'fast_add_mode': bool(self.fast_add_mode_var.get()),
            'fast_add_threshold': self._safe_threshold_value(),
        }



    @staticmethod
    def _sanitize_filename_component(value):
        value = str(value or '')
        value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value)
        value = value.strip().rstrip('. ')
        value = re.sub(r'\s+', ' ', value)
        value = re.sub(r'_+', '_', value).strip('_ ')
        if not value:
            value = 'Untitled'
        stem = value.split('.')[0].upper()
        if stem in {'CON', 'PRN', 'AUX', 'NUL'} or re.fullmatch(r'(COM|LPT)[1-9]', stem):
            value = '_' + value
        return value

    def _resolve_date_obj(self, file_path, exif_data, config):
        data = exif_data or {}
        basis = config.get('date_basis', '拍摄日期')
        if basis == '拍摄日期':
            capture_date = data.get('DateTimeOriginalParsed')
            if capture_date:
                return capture_date
            alternate = config.get('alternate_date', '修改日期')
            if alternate == '修改日期':
                return self.get_cached_or_real_modification_date(file_path)
            if alternate == '创建日期':
                return self.get_cached_or_real_creation_date(file_path)
            return None
        if basis == '修改日期':
            return self.get_cached_or_real_modification_date(file_path)
        if basis == '创建日期':
            return self.get_cached_or_real_creation_date(file_path)
        return None

    def generate_new_name(self, file_path, exif_data, add_suffix=True, config=None):
        """Return the desired basename; suffix conflict resolution is performed at execution time."""
        try:
            file_path = os.path.abspath(file_path)
            basename = os.path.basename(file_path)
            directory, ext = os.path.dirname(file_path), os.path.splitext(basename)[1]
            cfg = config or self._get_config_snapshot()
            exif_data = exif_data or {}
            date_obj = self._resolve_date_obj(file_path, exif_data, cfg)
            if not date_obj:
                return basename

            def text(key):
                value = exif_data.get(key, '')
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='replace')
                return str(value).strip()

            fnumber = text('FNumber')
            if fnumber and not fnumber.startswith('f'):
                fnumber = 'f' + fnumber
            variables = {
                '{date}': date_obj.strftime('%Y%m%d'),
                '{time}': date_obj.strftime('%H%M%S'),
                '{original}': os.path.splitext(basename)[0],
                '{camera}': text('Model'), '{lens}': text('LensModel'),
                '{iso}': text('ISOSpeedRatings'), '{focal}': text('FocalLength'),
                '{aperture}': fnumber, '{shutter}': text('ExposureTime'),
            }
            new_stem = cfg.get('template', '{date}_{time}')
            for variable, value in variables.items():
                new_stem = new_stem.replace(variable, value)
            # Unknown template placeholders are rejected, not written into filenames silently.
            new_stem = re.sub(r'\{[^{}]+\}', '', new_stem)
            new_stem = self._sanitize_filename_component(new_stem)
            return new_stem + ext
        except Exception:
            logging.exception("生成新文件名失败: %s", file_path)
            return os.path.basename(file_path)

    @staticmethod
    def _same_path(path_a, path_b):
        try:
            if os.path.exists(path_a) and os.path.exists(path_b):
                return os.path.samefile(path_a, path_b)
        except OSError:
            pass
        return os.path.normcase(os.path.abspath(path_a)) == os.path.normcase(os.path.abspath(path_b))

    def generate_unique_filename(self, directory, base_name, ext, suffix_style, source_path=None):
        """Find an unoccupied candidate. Return None on exhaustion; never return a known collision."""
        candidate = f'{base_name}{ext}'
        candidate_path = os.path.join(directory, candidate)
        if not os.path.lexists(candidate_path) or (source_path and self._same_path(source_path, candidate_path)):
            return candidate
        for counter in range(1, 100000):
            if suffix_style == '_001':
                suffix = f'_{counter:03d}'
            elif suffix_style == '-01':
                suffix = f'-{counter:02d}'
            else:
                suffix = f'_{counter}'
            candidate = f'{base_name}{suffix}{ext}'
            candidate_path = os.path.join(directory, candidate)
            if not os.path.lexists(candidate_path) or (source_path and self._same_path(source_path, candidate_path)):
                return candidate
        return None

    def _preview_new_name(self, file_path, exif_data, config):
        original = os.path.basename(file_path)
        data = exif_data or {}
        date_obj = self._resolve_date_obj(file_path, data, config)
        if not date_obj:
            if data.get('_metadata_error'):
                return original, '元数据读取失败，已保留原名'
            if config.get('date_basis') == '创建日期' or (
                config.get('date_basis') == '拍摄日期' and config.get('alternate_date') == '创建日期'
            ):
                return original, '系统未提供可靠创建日期，已保留原名'
            if config.get('date_basis') == '拍摄日期' and config.get('alternate_date') == '保留原文件名':
                return original, '缺少拍摄日期，已保留原名'
            return original, '未找到可用日期，已保留原名'

        desired = self.generate_new_name(file_path, data, config=config)
        if not desired or desired == original:
            return original, '无需重命名'
        directory = os.path.dirname(os.path.abspath(file_path))
        target = os.path.join(directory, desired)
        if not os.path.lexists(target) or self._same_path(file_path, target):
            return desired, '待重命名'
        if config.get('name_conflict', '增加后缀') != '增加后缀':
            return original, '目标冲突，将保留原名'
        stem, ext = os.path.splitext(desired)
        candidate = self.generate_unique_filename(directory, stem, ext,
                                                  config.get('suffix_option', '_001'),
                                                  source_path=file_path)
        if not candidate:
            return original, '冲突过多，无法生成名称'
        return candidate, '待重命名（冲突已加后缀）'

    @staticmethod
    def _rename_no_overwrite(source, target):
        """Atomically rename without replacing any existing destination."""
        if os.path.islink(source):
            raise OSError('不支持重命名符号链接，已安全跳过')
        if os.name == 'nt':
            # Windows os.rename fails atomically when the destination already exists.
            os.rename(source, target)
            return

        # Prefer native exclusive rename to avoid the link/unlink visibility window.
        if sys.platform.startswith('linux'):
            try:
                libc = ctypes.CDLL(None, use_errno=True)
                renameat2 = getattr(libc, 'renameat2', None)
            except OSError:
                renameat2 = None
            if renameat2 is not None:
                renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                      ctypes.c_char_p, ctypes.c_uint]
                renameat2.restype = ctypes.c_int
                result = renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # RENAME_NOREPLACE
                if result == 0:
                    return
                error = ctypes.get_errno()
                if error == errno.EEXIST:
                    raise FileExistsError(error, os.strerror(error), target)
                unsupported = {errno.ENOSYS, errno.EINVAL, getattr(errno, 'ENOTSUP', errno.EINVAL),
                               getattr(errno, 'EOPNOTSUPP', errno.EINVAL)}
                if error not in unsupported:
                    raise OSError(error, os.strerror(error), target)

        elif sys.platform == 'darwin':
            try:
                libc = ctypes.CDLL(None, use_errno=True)
                renamex_np = getattr(libc, 'renamex_np', None)
            except OSError:
                renamex_np = None
            if renamex_np is not None:
                renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
                renamex_np.restype = ctypes.c_int
                result = renamex_np(os.fsencode(source), os.fsencode(target), 0x00000004)  # RENAME_EXCL
                if result == 0:
                    return
                error = ctypes.get_errno()
                if error == errno.EEXIST:
                    raise FileExistsError(error, os.strerror(error), target)
                unsupported = {errno.ENOSYS, errno.EINVAL, getattr(errno, 'ENOTSUP', errno.EINVAL),
                               getattr(errno, 'EOPNOTSUPP', errno.EINVAL)}
                if error not in unsupported:
                    raise OSError(error, os.strerror(error), target)

        # Fail closed: a link/unlink fallback has a source-path race that can delete
        # a concurrent replacement. If atomic no-replace rename is unavailable,
        # preserve both paths and ask the user to move to a supported filesystem.
        raise OSError(
            getattr(errno, 'ENOTSUP', getattr(errno, 'EOPNOTSUPP', errno.EINVAL)),
            '当前平台或文件系统不支持原子且不覆盖目标的重命名；为保护文件，已拒绝执行',
            target,
        )


    def _detach_tree_item(self, item):
        try:
            if self.files_tree.exists(item) and item not in self._detached_items:
                self.files_tree.detach(item)
                self._detached_items.add(item)
        except Exception:
            logging.debug("隐藏列表项失败", exc_info=True)

    def apply_error_filter(self):
        try:
            if self.show_errors_only_var.get():
                for item in list(self.files_tree.get_children()):
                    tags = self.files_tree.item(item, 'tags') or ()
                    if 'failed' not in tags:
                        self._detach_tree_item(item)
            else:
                for item in list(self._detached_items):
                    if self.files_tree.exists(item):
                        self.files_tree.reattach(item, '', 'end')
                    self._detached_items.discard(item)
            self.update_file_count()
        except Exception:
            logging.exception("应用错误筛选失败")

    def update_file_count(self):
        try:
            count = len(self.files_tree.get_children()) + len(self._detached_items)
            self.file_count_label.config(text=self.lang['file_count'].format(count))
        except Exception:
            logging.debug("更新文件计数失败", exc_info=True)

    def select_files(self):
        paths = filedialog.askopenfilenames()
        if paths: self.add_files_to_queue(paths)

    def on_drop(self, event):
        try:
            paths = [os.path.normpath(str(p).strip()) for p in self.root.tk.splitlist(event.data)]
            self.add_files_to_queue(paths)
        except Exception:
            logging.warning("处理拖放文件失败", exc_info=True)

    def add_files_to_queue(self, paths):
        if self.processing_thread and self.processing_thread.is_alive() and self.stop_event.is_set():
            messagebox.showinfo('请稍候', '正在停止当前任务，请结束后再添加文件。')
            return
        if self.renaming_in_progress or self._active_operation == 'renaming':
            messagebox.showinfo('请稍候', '重命名操作仍在运行，结束后再添加文件。')
            return
        valid = []
        for path in paths:
            path = os.path.normpath(os.path.abspath(str(path)))
            if os.path.exists(path):
                valid.append(path)
        if not valid:
            return
        with self._queue_lock:
            for path in valid:
                self.file_queue.put((path, 'file' if os.path.isfile(path) else 'directory'))
            if not self.processing_thread or not self.processing_thread.is_alive():
                # Freeze settings for this discovery run; adding more inputs does not mutate a live job.
                self._skip_extensions_snapshot = self.skip_extensions_var.get()
                self._job_config_snapshot = self._get_config_snapshot()
                self.stop_event.clear()
                self._active_operation = 'adding'
                self.processing_thread = Thread(target=self.process_files_from_queue, daemon=True, name='QphotoAddWorker')
                self.processing_thread.start()
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.update_status_bar('正在扫描和读取媒体信息…')

    def process_files_from_queue(self):
        """Single queue consumer with a lock-protected empty check to avoid lost wakeups."""
        reserved_keys = {}
        try:
            while not self.stop_event.is_set():
                paths = []
                with self._queue_lock:
                    while True:
                        try:
                            paths.append(self.file_queue.get_nowait())
                        except Exception:
                            break
                    if not paths:
                        return
                skip_ext_str = self._skip_extensions_snapshot.strip().lower()
                skipped = {x if x.startswith('.') else '.' + x
                           for x in re.split(r'[\s,;]+', skip_ext_str) if x.strip()}
                files = []
                for path, kind in paths:
                    if self.stop_event.is_set():
                        break
                    if kind == 'file':
                        if self._is_supported(path, skipped):
                            files.append(path)
                    else:
                        for root_dir, dirs, names in os.walk(path):
                            dirs.sort()
                            if self.stop_event.is_set():
                                break
                            for name in names:
                                if self.stop_event.is_set():
                                    break
                                candidate = os.path.join(root_dir, name)
                                if self._is_supported(candidate, skipped):
                                    files.append(candidate)
                if self.stop_event.is_set():
                    break
                # Dedupe by normalized absolute path (case-insensitive on Windows).
                new_files = []
                for path in files:
                    canonical = os.path.normcase(os.path.realpath(path))
                    with self._state_lock:
                        if canonical in self._path_by_key:
                            continue
                        self._path_by_key[canonical] = path
                        self.added_files_set.add(path)
                        try:
                            self._file_fingerprints[canonical] = self._file_identity(path)
                        except OSError:
                            self._file_fingerprints.pop(canonical, None)
                    reserved_keys[canonical] = path
                    new_files.append(path)
                cfg = dict(self._job_config_snapshot)
                use_fast_add = cfg.get('fast_add_mode', True) and len(new_files) >= cfg.get('fast_add_threshold', 100)
                chunk_size = 200 if use_fast_add else 100
                worker_limit = 8 if use_fast_add else 4
                for start in range(0, len(new_files), chunk_size):
                    if self.stop_event.is_set():
                        break
                    chunk = new_files[start:start + chunk_size]
                    batch = []
                    workers = min(worker_limit, max(1, os.cpu_count() or 1), len(chunk))
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = {executor.submit(self._process_single_file, path, cfg): path for path in chunk}
                        for future in as_completed(futures):
                            if self.stop_event.is_set():
                                break
                            path = futures[future]
                            try:
                                row = future.result()
                                if row is not None:
                                    batch.append(row)
                            except Exception as exc:
                                logging.exception("读取文件失败: %s", path)
                                batch.append((path, os.path.basename(path), f'读取失败: {exc}'))
                            if len(batch) >= 50 and not self.stop_event.is_set():
                                self.flush_batch_to_ui(batch)
                                for row in batch:
                                    reserved_keys.pop(os.path.normcase(os.path.realpath(row[0])), None)
                                batch = []
                    if batch and not self.stop_event.is_set():
                        self.flush_batch_to_ui(batch)
                        for row in batch:
                            reserved_keys.pop(os.path.normcase(os.path.realpath(row[0])), None)
        except Exception:
            logging.exception("批量添加线程发生异常")
        finally:
            # If stop/error interrupted a batch, allow those paths to be added again.
            if reserved_keys:
                with self._state_lock:
                    for key, path in reserved_keys.items():
                        if self._path_by_key.get(key) == path:
                            self._path_by_key.pop(key, None)
                        self._file_fingerprints.pop(key, None)
                        self.added_files_set.discard(path)
            with self._queue_lock:
                current_thread = threading.current_thread()
                if self.processing_thread is current_thread:
                    self.processing_thread = None
                    if self._active_operation == 'adding':
                        self._active_operation = None
                # Enqueue and shutdown use the same lock, so no task can be lost here.
                has_pending = not self.file_queue.empty() and not self.stop_event.is_set()
                if has_pending and not self._closing and not (self.processing_thread and self.processing_thread.is_alive()):
                    self._active_operation = 'adding'
                    self.processing_thread = Thread(target=self.process_files_from_queue, daemon=True, name='QphotoAddWorker')
                    self.processing_thread.start()
                    has_pending = False
                elif self.processing_thread is not None and self.processing_thread is not current_thread:
                    # A newly started consumer owns the pending queue.
                    has_pending = False
            if not has_pending:
                self.post_ui(self._finish_processing)

    @staticmethod
    def _is_supported(path, skipped):
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_IMAGE_FORMATS.union(SUPPORTED_VIDEO_FORMATS) and ext not in skipped

    def _get_config_snapshot_threadsafe(self):
        # Workers consume a plain immutable-at-start job snapshot, never Tk variables.
        return dict(getattr(self, '_job_config_snapshot', {}))

    def _process_single_file(self, path, config=None):
        if self.stop_event.is_set() or self._closing:
            return None
        ext = os.path.splitext(path)[1].lower()
        exif_data = self.get_media_data(path, ext) or {}
        new_name, status = self._preview_new_name(path, exif_data, config)
        return (path, new_name, status)



    @staticmethod
    def _is_error_status(status):
        text = str(status or '')
        return text.startswith((
            '读取失败', '错误', '重命名失败', '元数据读取失败', '冲突过多',
            '文件不存在', '文件在预览后发生变化', '文件在读取期间发生变化',
            '系统未提供可靠创建日期', '未找到可用日期', '目标冲突',
            '目标名称冲突', '冲突后缀耗尽',
        ))

    def flush_batch_to_ui(self, batch):
        def update():
            for row in batch:
                item_id = self.files_tree.insert('', 'end', values=row)
                if self._is_error_status(row[2]):
                    self.files_tree.item(item_id, tags=('failed',))
            if self.show_errors_only_var.get():
                self.apply_error_filter()
            if self.auto_scroll_var.get() and self.files_tree.get_children():
                self.files_tree.see(self.files_tree.get_children()[-1])
            self.update_file_count()
        self.post_ui(update)

    def _finish_processing(self):
        if self._closing:
            return
        # If an add worker has restarted itself, do not enable execution prematurely.
        worker_alive = self.processing_thread is not None and self.processing_thread.is_alive()
        if worker_alive:
            return
        self.update_status_bar('已停止' if self.stop_event.is_set() else self.lang['ready'])
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')


    def update_renamed_name_column(self):
        try:
            config = self._get_config_snapshot()
            items = [(item, self.files_tree.item(item, 'values')[0])
                     for item in list(self.files_tree.get_children()) + list(self._detached_items)
                     if self.files_tree.item(item, 'values')]
            self._preview_generation += 1
            generation = self._preview_generation
        except Exception:
            return

        def apply_preview(item, name, status):
            if generation != self._preview_generation or not self.files_tree.exists(item):
                return
            self.files_tree.set(item, 'renamed_name', name)
            self.files_tree.set(item, 'status', status)
            if self._is_error_status(status):
                self.files_tree.item(item, tags=('failed',))
                if item in self._detached_items:
                    self.files_tree.reattach(item, '', 'end')
                    self._detached_items.discard(item)
            elif self.show_errors_only_var.get():
                self._detach_tree_item(item)
            elif item in self._detached_items:
                self.files_tree.reattach(item, '', 'end')
                self._detached_items.discard(item)
            self.update_file_count()

        def worker():
            for item, path in items:
                if self._closing or generation != self._preview_generation:
                    return
                try:
                    if os.path.isfile(path):
                        data = self.get_media_data(path, os.path.splitext(path)[1].lower())
                        name, status = self._preview_new_name(path, data, config)
                        self.post_ui(lambda i=item, n=name, st=status: apply_preview(i, n, st))
                except Exception:
                    logging.debug("刷新预览失败: %s", path, exc_info=True)
        Thread(target=worker, daemon=True, name='QphotoPreviewWorker').start()

    def rename_photos(self):
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showinfo('请稍候', '文件扫描或添加任务仍在运行，请完成后再开始重命名。')
            return
        rows = []
        all_items = list(self.files_tree.get_children()) + list(self._detached_items)
        for item in all_items:
            values = self.files_tree.item(item, 'values')
            if values:
                rows.append((item, values[0]))
        if not rows:
            return
        config = self._get_config_snapshot()
        self._preview_generation += 1  # Invalidate any delayed preview callbacks before mutating files.
        self.stop_event.clear()
        self.renaming_in_progress = True
        self._active_operation = 'renaming'
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        Thread(target=self.rename_photos_thread, args=(rows, config), daemon=True, name='QphotoRenameWorker').start()

    def rename_photos_thread(self, items_data, config=None):
        renamed = errors = skipped = 0
        try:
            config = dict(self._job_config_snapshot) if config is None else config
            for item, path in items_data:
                if self.stop_event.is_set() or self._closing:
                    break
                result = self.rename_photo(path, item, config)
                if result['status'] == 'renamed':
                    renamed += 1
                    self.exif_cache.clear()
                elif result['status'] == 'error':
                    errors += 1
                else:
                    skipped += 1
            summary = f'重命名结束：成功 {renamed} 个，跳过 {skipped} 个，失败 {errors} 个。'
            if self.stop_event.is_set():
                summary = '已请求停止。' + summary
            self.post_ui(lambda msg=summary: self.status_label.config(text=msg))
        except Exception:
            logging.exception("重命名线程发生异常")
            self.post_ui(lambda: self.status_label.config(text='重命名过程中发生异常，详情见日志。'))
        finally:
            self.renaming_in_progress = False
            self._active_operation = None
            self.post_ui(self._finish_renaming) 

    def _finish_renaming(self):
        if self._closing:
            return
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.update_file_count()

    def rename_photo(self, file_path, item, config=None):
        config = self._get_config_snapshot() if config is None else config
        try:
            if not os.path.isfile(file_path):
                self.post_ui(lambda: self._mark_rename_result(item, '文件不存在', failed=True))
                return {'status': 'error', 'message': '文件不存在'}

            source_key = os.path.normcase(os.path.realpath(file_path))
            expected_identity = getattr(self, '_file_fingerprints', {}).get(source_key)

            def source_unchanged():
                if expected_identity is None:
                    return True  # Legacy/manually inserted rows have no scan-time snapshot.
                try:
                    return self._file_identity(file_path) == expected_identity
                except OSError:
                    return False

            if not source_unchanged():
                message = '文件在预览后发生变化，已跳过；请移除后重新添加'
                self.post_ui(lambda msg=message: self._mark_rename_result(item, msg, failed=True))
                return {'status': 'error', 'message': message}

            ext = os.path.splitext(file_path)[1]
            exif_data = self.get_media_data(file_path, ext.lower()) or {}
            if not source_unchanged():
                message = '文件在读取期间发生变化，已跳过；请移除后重新添加'
                self.post_ui(lambda msg=message: self._mark_rename_result(item, msg, failed=True))
                return {'status': 'error', 'message': message}

            desired_name = self.generate_new_name(file_path, exif_data, config=config)
            original_name = os.path.basename(file_path)
            if not desired_name or desired_name == original_name:
                _, reason = self._preview_new_name(file_path, exif_data, config)
                self.post_ui(lambda msg=reason: self._mark_rename_result(item, msg))
                return {'status': 'skipped', 'message': reason}

            directory = os.path.dirname(os.path.abspath(file_path))
            desired_stem, desired_ext = os.path.splitext(desired_name)
            candidate = desired_name
            strategy = config.get('name_conflict', '增加后缀')
            suffix_style = config.get('suffix_option', '_001')
            while True:
                target = os.path.join(directory, candidate)
                if self._same_path(file_path, target):
                    return {'status': 'skipped', 'message': '目标与源文件相同'}
                if os.path.lexists(target):
                    if strategy != '增加后缀':
                        self.post_ui(lambda: self._mark_rename_result(item, '目标名称冲突，已保留原文件名'))
                        return {'status': 'skipped', 'message': '目标名称冲突'}
                    candidate = self.generate_unique_filename(directory, desired_stem, desired_ext, suffix_style, source_path=file_path)
                    if not candidate:
                        self.post_ui(lambda: self._mark_rename_result(item, '冲突后缀耗尽', failed=True))
                        return {'status': 'error', 'message': '冲突后缀耗尽'}
                    target = os.path.join(directory, candidate)
                if self.stop_event.is_set() or self._closing:
                    message = '已停止，未执行本次重命名'
                    self.post_ui(lambda msg=message: self._mark_rename_result(item, msg))
                    return {'status': 'skipped', 'message': message}
                if not source_unchanged():
                    message = '文件在预览后发生变化，已跳过；请移除后重新添加'
                    self.post_ui(lambda msg=message: self._mark_rename_result(item, msg, failed=True))
                    return {'status': 'error', 'message': message}
                logging.info('RENAME_INTENT source=%r target=%r', file_path, target)
                try:
                    self._rename_no_overwrite(file_path, target)
                    logging.info('RENAME_DONE source=%r target=%r', file_path, target)
                    break
                except FileExistsError:
                    # Another process won the race. Retry only under the suffix policy.
                    if strategy != '增加后缀':
                        self.post_ui(lambda: self._mark_rename_result(item, '目标名称冲突，已保留原文件名'))
                        return {'status': 'skipped', 'message': '目标名称冲突'}
                    candidate = self.generate_unique_filename(directory, desired_stem, desired_ext, suffix_style, source_path=file_path)
                    if not candidate:
                        self.post_ui(lambda: self._mark_rename_result(item, '冲突后缀耗尽', failed=True))
                        return {'status': 'error', 'message': '冲突后缀耗尽'}
                except OSError as exc:
                    logging.warning("安全重命名失败: %s -> %s", file_path, target, exc_info=True)
                    self.post_ui(lambda msg=str(exc): self._mark_rename_result(item, f'重命名失败: {msg}', failed=True))
                    return {'status': 'error', 'message': str(exc)}

            self.exif_cache.clear()
            self.post_ui(lambda: self._apply_rename_success(item, file_path, target))
            return {'status': 'renamed', 'message': target}
        except Exception as exc:
            logging.exception("重命名失败: %s", file_path)
            self.post_ui(lambda msg=str(exc): self._mark_rename_result(item, f'重命名失败: {msg}', failed=True))
            return {'status': 'error', 'message': str(exc)}

    def _mark_rename_result(self, item, message, failed=False):
        try:
            if not self.files_tree.exists(item):
                return
            if failed:
                if item in self._detached_items:
                    self.files_tree.reattach(item, '', 'end')
                    self._detached_items.discard(item)
                self.files_tree.set(item, 'status', message)
                self.files_tree.item(item, tags=('failed',))
            elif self.show_errors_only_var.get():
                self.files_tree.set(item, 'status', message)
                self._detach_tree_item(item)
            else:
                if item in self._detached_items:
                    self.files_tree.reattach(item, '', 'end')
                    self._detached_items.discard(item)
                self.files_tree.set(item, 'status', message)
            self.update_file_count()
        except Exception:
            logging.debug("更新重命名结果失败", exc_info=True)

    def _apply_rename_success(self, item, source, target):
        try:
            old_key = os.path.normcase(os.path.realpath(source))
            new_key = os.path.normcase(os.path.realpath(target))
            with self._state_lock:
                self._path_by_key.pop(old_key, None)
                self._path_by_key[new_key] = target
                self._file_fingerprints.pop(old_key, None)
                try:
                    self._file_fingerprints[new_key] = self._file_identity(target)
                except OSError:
                    self._file_fingerprints.pop(new_key, None)
                self.added_files_set.discard(source)
                self.added_files_set.add(target)
            if not self.files_tree.exists(item):
                return
            self.files_tree.set(item, 'filename', target)
            self.files_tree.set(item, 'renamed_name', os.path.basename(target))
            self.files_tree.set(item, 'status', '已重命名')
            self.files_tree.item(item, tags=('renamed',))
            if self.show_errors_only_var.get():
                self._detach_tree_item(item)
            elif item in self._detached_items:
                self.files_tree.reattach(item, '', 'end')
                self._detached_items.discard(item)
            self.update_file_count()
        except Exception:
            logging.debug("更新重命名后的列表失败", exc_info=True)

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
        if self._active_operation is not None:
            return
        for item in self.files_tree.selection():
            vals = self.files_tree.item(item)['values']
            if vals:
                self.added_files_set.discard(vals[0])
                key = os.path.normcase(os.path.realpath(vals[0]))
                self._path_by_key.pop(key, None)
                self._file_fingerprints.pop(key, None)
            self.files_tree.delete(item)
        self.update_file_count()

    def clear_file_list(self):
        if self._active_operation is not None:
            messagebox.showinfo('请稍候', '任务运行期间不能清空列表。')
            return
        all_items = list(self.files_tree.get_children()) + list(self._detached_items)
        for item in all_items:
            try:
                self.files_tree.delete(item)
            except Exception:
                pass
        self._detached_items.clear()
        self.added_files_set.clear()
        self._path_by_key.clear()
        self._file_fingerprints.clear()
        self.update_file_count()

    def open_file(self, event):
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
        values = self.files_tree.item(item, 'values')
        if not values or not os.path.exists(values[0]):
            return
        path = values[0]
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception:
            logging.exception("打开文件失败: %s", path)
            messagebox.showerror('打开失败', f'无法打开文件：\n{path}')

    def update_status_bar(self, msg_key, *args):
        message = self.lang.get(msg_key, msg_key)
        try:
            message = message.format(*args)
        except Exception:
            pass
        self.post_ui(lambda text=message: self.status_label.config(text=text))

    def show_help(self):
        w = Toplevel(self.root)
        w.title("帮助")
        Label(w, text=self.lang["help_text"], justify='left').pack(padx=20, pady=20)

    def open_update_link(self):
        try: webbrowser.open("https://github.com/Qwejay/QphotoRenamer")
        except Exception: pass

    def stop_all_operations(self):
        self.stop_event.set()
        # Drop pending discovery inputs. The in-flight file operation checks the stop flag.
        with self._queue_lock:
            while True:
                try:
                    self.file_queue.get_nowait()
                except Exception:
                    break
        self.update_status_bar('正在停止…')

class TemplateEditor(ttk.Frame):
    def __init__(self, parent, template_var, main_app=None):
        super().__init__(parent)
        self.template_var = template_var
        self.lang = LANG
        self.main_app = main_app
        self.is_modified = False
        self.last_saved_content = ""
        self.config_file = CONFIG_PATH
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
        if sel == "(新模板)" or sel not in self.templates:
            return
        if self.has_unsaved_changes():
            choice = messagebox.askyesnocancel(
                '未保存的修改', '当前模板有未保存的修改。是否先保存再切换？'
            )
            if choice is None:
                self.template_combobox.set(self.last_saved_content)
                return
            if choice and not self.save_current_template():
                self.template_combobox.set(self.last_saved_content)
                return
        self.set_template(sel)
        if self.main_app is not None:
            self.main_app.update_renamed_name_column()

    def save_current_template(self):
        t = self.template_text.get("1.0", 'end').strip()
        if not t:
            return False
        previous_templates = list(self.templates)
        if t not in self.templates:
            self.templates.append(t)
        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.config_file) or os.path.exists(LEGACY_CONFIG_PATH):
                config.read([LEGACY_CONFIG_PATH, self.config_file], encoding='utf-8')
            if 'Template' not in config:
                config['Template'] = {}
            config['Template']['default'] = t
            for i, tmpl in enumerate(self.templates, 1):
                config['Template'][f'template{i}'] = tmpl
            _atomic_write_config(config, self.config_file)
        except Exception as exc:
            self.templates = previous_templates
            logging.exception("保存模板失败")
            messagebox.showerror('保存失败', f'模板未保存，原配置保持不变。\n{exc}')
            return False

        self.last_saved_content = t
        self.is_modified = False
        self.template_combobox['values'] = [x for x in self.templates if x != "(新模板)"]
        self.template_combobox.set(t)
        if self.main_app is not None:
            self.main_app.update_renamed_name_column()
        return True

    def load_templates(self):
        try:
            config = configparser.ConfigParser()
            if os.path.exists(self.config_file) or os.path.exists(LEGACY_CONFIG_PATH):
                config.read([LEGACY_CONFIG_PATH, self.config_file], encoding='utf-8')
                if config.has_section('Template'):
                    loaded = [config.get('Template', k) for k in config.options('Template') if k.startswith('template')]
                    default = config.get('Template', 'default', fallback='')
                    if default and default not in loaded: loaded.insert(0, default)
                    if loaded: self.templates = list(dict.fromkeys(loaded))
        except Exception:
            logging.exception("加载模板失败")
        self.template_combobox['values'] = self.templates

    def delete_current_template(self):
        selected = self.template_combobox.get()
        if selected not in self.templates:
            return
        if len(self.templates) <= 1:
            messagebox.showinfo('提示', '至少保留一个模板。')
            return

        previous_templates = list(self.templates)
        remaining = [template for template in self.templates if template != selected]
        next_template = remaining[0]
        try:
            config = configparser.ConfigParser()
            config.read([LEGACY_CONFIG_PATH, self.config_file], encoding='utf-8')
            if not config.has_section('Template'):
                config.add_section('Template')
            for key in list(config['Template']):
                if key.startswith('template'):
                    del config['Template'][key]
            config['Template']['default'] = next_template
            for index, template in enumerate(remaining, 1):
                config['Template'][f'template{index}'] = template
            _atomic_write_config(config, self.config_file)
        except Exception as exc:
            self.templates = previous_templates
            self.template_combobox['values'] = self.templates
            self.template_combobox.set(selected)
            logging.exception('删除模板失败')
            messagebox.showerror('删除失败', f'模板未删除，原配置保持不变。\n{exc}')
            return

        self.templates = remaining
        self.set_template(next_template)
        self.template_combobox['values'] = self.templates
        if self.main_app is not None:
            self.main_app.update_renamed_name_column()



def main() -> int:
    """Application entry point; keep GUI creation out of import-time execution."""
    root = None
    try:
        root = TkinterDnD.Tk()
        PhotoRenamer(root)
        root.mainloop()
        return 0
    except Exception as exc:
        logging.exception("程序启动或运行时发生致命错误")
        try:
            messagebox.showerror("致命错误", f"程序遇到严重错误: {exc}")
        except Exception:
            print(f"QphotoRenamer 致命错误: {exc}", file=sys.stderr)
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
