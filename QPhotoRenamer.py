import os
import sys
import datetime
import exifread
import piexif
import pillow_heif
import ttkbootstrap as ttk
from tkinter import filedialog, Toplevel, Label, Checkbutton
from tkinterdnd2 import DND_FILES, TkinterDnD
from threading import Thread
import logging
import re
import json
import locale
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='rename_tool.log')

DATE_FORMAT = "%Y%m%d_%H%M%S"
stop_requested = False
renaming_in_progress = False
original_to_new_mapping = {}
processed_files = set()
unrenamed_files = 0

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
        "window_title": "照片批量重命名 QphotoRenamer 1.0.1 —— QwejayHuang",
        "description": "只需将照片拖入列表即可快速添加；点击“开始”按钮批量重命名您的照片；双击查看文件；右键点击移除文件；单击文件显示EXIF信息。",
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
        "formats_explanation": "常用日期格式示例:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023"
    },
    "English": {
        "window_title": "QphotoRenamer 1.0.1 —— QwejayHuang",
        "description": "Just drop photos into the list to quickly add them; click the 'Start' button to rename your photos; double-click to view files; right-click to remove files; click on the file to display EXIF information.",
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
        "formats_explanation": "Common Date Formats Examples:\n%Y%m%d_%H%M%S -> 20230729_141530\n%Y-%m-%d %H:%M:%S -> 2023-07-29 14:15:30\n%d-%m-%Y %H:%M:%S -> 29-07-2023 14:15:30\n%Y%m%d -> 20230729\n%H%M%S -> 141530\n%Y-%m-%d -> 2023-07-29\n%d-%m-%Y -> 29-07-2023"
    }
}

def set_language(language):
    if language in LANGUAGES:
        lang = LANGUAGES[language]
        root.title(lang["window_title"])
        label_description.config(text=lang["description"])
        start_button.config(text=lang["start_renaming"])
        undo_button.config(text=lang["undo_renaming"])
        stop_button.config(text=lang["stop_renaming"])
        settings_button.config(text=lang["settings"])
        clear_button.config(text=lang["clear_list"])
        select_files_button.config(text=lang["add_files"])
        help_button.config(text=lang["help"])
        auto_scroll_checkbox.config(text=lang["auto_scroll"])
        status_bar.config(text=lang["ready"])  # 更新状态栏文本

def save_language(language):
    config = {}
    if os.path.exists("QPhotoRenamer.ini"):
        with open("QPhotoRenamer.ini", "r") as f:
            config = json.load(f)
    config["language"] = language
    with open("QPhotoRenamer.ini", "w") as f:
        json.dump(config, f)

def load_language():
    if os.path.exists("QPhotoRenamer.ini"):
        with open("QPhotoRenamer.ini", "r") as f:
            config = json.load(f)
            return config.get("language", "简体中文")
    return "简体中文"

def get_exif_data(file_path):
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

def get_heic_data(file_path):
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

def get_file_modification_date(file_path):
    try:
        modification_time = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(modification_time)
    except Exception as e:
        logging.error(f"获取文件修改日期失败: {file_path}, 错误: {e}")
    return None

def generate_unique_filename(directory, base_name, ext, original_filename):
    new_filename = f"{base_name}{ext}"
    new_file_path = os.path.join(directory, new_filename)
    counter = 1
    while os.path.exists(new_file_path):
        new_filename = f"{base_name}_{counter}{ext}"
        new_file_path = os.path.join(directory, new_filename)
        counter += 1
    return new_file_path

def rename_photos(files_listbox, progress_var):
    global stop_requested, renaming_in_progress, processed_files, unrenamed_files

    if renaming_in_progress:
        update_status_bar("重命名操作已在进行中，请稍后再试。")
        return

    renaming_in_progress = True
    start_button.config(state=ttk.DISABLED)
    stop_button.config(state=ttk.NORMAL)

    # 清空上一次重命名的列表
    processed_files.clear()
    unrenamed_files = 0

    total_files = files_listbox.size()
    for i in range(total_files):
        if stop_requested:
            stop_requested = False
            update_status_bar("重命名操作已停止。")
            break

        file_path = files_listbox.get(i).strip('"')
        if file_path not in processed_files:
            update_status_bar(f"正在重命名: {os.path.basename(file_path)}")
            renamed = rename_photo(file_path, files_listbox, progress_var, total_files, i)
            if renamed:
                processed_files.add(file_path)
                # 删除原始文件路径
                files_listbox.delete(i)
                # 插入新的重命名文件路径
                files_listbox.insert(i, f'"{renamed}"')
                # 更新进度变量
                progress_var.set((i + 1) * 100 / total_files)
                # 自动滚动到最新处理的文件
                if auto_scroll_var.get():
                    files_listbox.see(i)
            else:
                # 如果重命名失败，确保循环能够继续处理下一个文件
                continue

    update_status_bar(f"成功重命名 {len(processed_files)} 个文件，未重命名 {unrenamed_files} 个文件。")

    undo_button.config(state=ttk.NORMAL)
    renaming_in_progress = False
    start_button.config(state=ttk.NORMAL)
    stop_button.config(state=ttk.DISABLED)

def rename_photo(file_path, files_listbox, progress_var, total_files, current_index):
    global unrenamed_files
    filename = os.path.basename(file_path)
    # 检查文件名是否已经是重命名后的名字
    if re.match(r'\d{8}_\d{6}\.\w+', filename):
        update_status_bar(f'跳过重命名: "{file_path}" 已是重命名后的名字')
        progress_var.set((current_index + 1) * 100 / total_files)
        return False

    exif_data = get_heic_data(file_path) if filename.lower().endswith('.heic') else get_exif_data(file_path)
    date_time = exif_data['DateTimeOriginalParsed'] if exif_data and 'DateTimeOriginalParsed' in exif_data else None
    if not date_time and use_modification_date_var.get():
        date_time = get_file_modification_date(file_path)
    if date_time:
        base_name = date_time.strftime(DATE_FORMAT)
        ext = os.path.splitext(filename)[1]
        directory = os.path.dirname(file_path)
        new_file_path = generate_unique_filename(directory, base_name, ext, file_path)
        # 检查文件名是否已经是重命名后的名字
        if new_file_path != file_path and not os.path.exists(new_file_path):
            try:
                os.rename(file_path, new_file_path)
                logging.info(f'重命名成功: "{file_path}" 重命名为 "{new_file_path}"')
                original_to_new_mapping[file_path] = new_file_path
                progress_var.set((current_index + 1) * 100 / total_files)
                return new_file_path
            except Exception as e:
                logging.error(f"重命名失败: {file_path}, 错误: {e}")
        else:
            # 如果文件名已经是重命名后的名字，则跳过重命名
            logging.info(f'跳过重命名: "{file_path}" 已经是重命名后的名字')
    else:
        unrenamed_files += 1
        files_listbox.itemconfig(current_index, fg="red")  # 将未重命名的文件显示为红色
    progress_var.set((current_index + 1) * 100 / total_files)
    return False

def undo_rename():
    global original_to_new_mapping
    for original, new in original_to_new_mapping.items():
        try:
            os.rename(new, original)
            logging.info(f'撤销重命名成功: "{new}" 恢复为 "{original}"')
        except Exception as e:
            logging.error(f'撤销重命名失败: {new}, 错误: {e}')
    original_to_new_mapping.clear()
    update_status_bar("所有文件已恢复到原始名称。")
    # 撤销操作完成后，禁用撤销按钮
    undo_button.config(state=ttk.DISABLED)

def on_drop(event, files_listbox):
    paths = re.findall(r'(?<=\{)[^{}]*(?=\})|[^{}\s]+', event.data)
    current_files = set(files_listbox.get(0, ttk.END))
    for path in paths:
        path = path.strip().strip('{}')
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if (file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic', '.webp', '.raw')) and 
                        file_path not in current_files):
                        files_listbox.insert(ttk.END, file_path)
                        if auto_scroll_var.get():
                            files_listbox.see(ttk.END)
        elif (path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.heic', '.webp', '.raw')) and 
              path not in current_files):
            files_listbox.insert(ttk.END, path)
            if auto_scroll_var.get():
                files_listbox.see(ttk.END)

def remove_file(event):
    selected_indices = files_listbox.curselection()
    for index in selected_indices[::-1]:
        files_listbox.delete(index)

def stop_renaming():
    global stop_requested
    stop_requested = True

def open_settings():
    settings_window = ttk.Toplevel(root)
    settings_window.title("设置")

    settings_frame = ttk.Frame(settings_window)
    settings_frame.pack(padx=10, pady=10)

    lang = LANGUAGES[language_var.get()]

    ttk.Label(settings_frame, text=lang["rename_pattern"], anchor='w').grid(row=0, column=0, padx=10, pady=10)
    date_format_var = ttk.StringVar(value=DATE_FORMAT)
    date_format_combobox = ttk.Combobox(settings_frame, textvariable=date_format_var, values=COMMON_DATE_FORMATS, state="readonly")
    date_format_combobox.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(settings_frame, text=lang["use_modification_date"], anchor='w').grid(row=1, column=0, padx=10, pady=10)
    use_modification_date_checkbox = Checkbutton(settings_frame, variable=use_modification_date_var)
    use_modification_date_checkbox.grid(row=1, column=1, padx=10, pady=10)

    ttk.Label(settings_frame, text=lang["language"], anchor='w').grid(row=2, column=0, padx=10, pady=10)
    language_combobox = ttk.Combobox(settings_frame, textvariable=language_var, values=list(LANGUAGES.keys()), state="readonly")
    language_combobox.grid(row=2, column=1, padx=10, pady=10)

    ttk.Label(settings_frame, text=lang["formats_explanation"], anchor='w').grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    save_button = ttk.Button(settings_frame, text=lang["save_settings"], command=lambda: save_settings(date_format_var.get(), language_var.get(), settings_window))
    save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

def save_settings(date_format, language, settings_window):
    global DATE_FORMAT
    DATE_FORMAT = date_format
    config = {
        "date_format": DATE_FORMAT,
        "use_modification_date": use_modification_date_var.get(),
        "language": language
    }
    with open("QPhotoRenamer.ini", "w") as f:
        json.dump(config, f)
    set_language(language)
    update_status_bar("设置已保存")
    settings_window.destroy()  # 关闭设置界面

def load_settings():
    global DATE_FORMAT
    if os.path.exists("QPhotoRenamer.ini"):
        with open("QPhotoRenamer.ini", "r") as f:
            config = json.load(f)
            DATE_FORMAT = config.get("date_format", "%Y%m%d_%H%M%S")
            use_modification_date_var.set(config.get("use_modification_date", True))
            language_var.set(config.get("language", locale.getdefaultlocale()[0]))

def select_files(files_listbox):
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png *.jpg *.jpeg *.tiff *.bmp *.gif *.heic")])
    current_files = set(files_listbox.get(0, ttk.END))
    for file_path in file_paths:
        if file_path not in current_files:
            files_listbox.insert(ttk.END, file_path)
            if auto_scroll_var.get():
                files_listbox.see(ttk.END)

def show_exif_info(event):
    widget = event.widget
    index = widget.curselection()
    if index:
        file_path = widget.get(index[0]).strip('"')
        Thread(target=display_exif_info, args=(widget, file_path)).start()

def display_exif_info(widget, file_path):
    filename = os.path.basename(file_path)
    exif_data = get_heic_data(file_path) if filename.lower().endswith('.heic') else get_exif_data(file_path)
    date_time = exif_data['DateTimeOriginalParsed'] if exif_data and 'DateTimeOriginalParsed' in exif_data else None
    if not date_time:
        date_time = get_file_modification_date(file_path)
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

        widget.after(0, create_tooltip, widget, exif_info)

def create_tooltip(widget, exif_info):
    if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
        widget.tooltip_window.destroy()
    widget.tooltip_window = Toplevel(widget)
    widget.tooltip_window.wm_overrideredirect(True)
    x, y, _, _ = widget.bbox(widget.curselection()[0])
    x = widget.winfo_rootx() + x + 20
    y = widget.winfo_rooty() + y + 20
    widget.tooltip_window.geometry(f"+{x}+{y}")
    Label(widget.tooltip_window, text=exif_info, background="lightyellow", relief="solid", borderwidth=1, anchor='w', justify='left').pack(fill='both', expand=True)

def on_leave(event):
    widget = event.widget
    if hasattr(widget, 'tooltip_window') and widget.tooltip_window:
        widget.tooltip_window.destroy()
        widget.tooltip_window = None

def open_file(event):
    index = files_listbox.index("@%s,%s" % (event.x, event.y))
    # 检查双击的是不是列表中的文件项
    if index >= 0 and index < files_listbox.size():
        # 双击的是文件项，尝试打开文件
        file_path = files_listbox.get(index).strip('"')
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, file_path])
        except Exception as e:
            logging.error(f"打开文件失败: {file_path}, 错误: {e}")
    else:
        # 双击的是空白处，打开添加文件框
        select_files(files_listbox)

def update_status_bar(message):
    status_bar.config(text=message)

def show_help():
    help_window = Toplevel(root)
    help_window.title("帮助")
    help_text = (
        "使用说明:\n"
        "1. 拖拽文件进列表，或点击“添加文件”按钮选择文件。\n"
        "2. 点击“开始重命名”按钮开始重命名文件。\n"
        "3. 双击列表中的文件名打开图片。\n"
        "4. 右键点击列表中的文件名移除文件。\n"
        "5. 点击“撤销重命名”按钮恢复到原始名称。\n"
        "6. 点击“设置”按钮更改日期格式。\n"
        "7. 勾选“自动滚动”选项，列表会自动滚动到最新添加的文件。\n"
        "8. 点击“清空列表”按钮清空文件列表。\n"
        "9. 点击“停止重命名”按钮停止重命名操作。\n"
        "10. 点击文件名显示EXIF信息。"
    )
    help_label = Label(help_window, text=help_text, justify='left')
    help_label.pack(padx=10, pady=10)

root = TkinterDnD.Tk()
root.title("照片批量重命名 QphotoRenamer 1.0.1 —— QwejayHuang")
root.geometry("800x600")

# 设置窗口图标
root.iconbitmap(root, "logo.ico")

style = ttk.Style('litera')  # 使用ttkbootstrap主题

# 在创建主窗口之后再创建变量
auto_scroll_var = ttk.BooleanVar(value=True)
use_modification_date_var = ttk.BooleanVar(value=True)  # 默认勾选
language_var = ttk.StringVar(value=load_language())

main_frame = ttk.Frame(root)
main_frame.pack(fill=ttk.BOTH, expand=True)

label_description = ttk.Label(main_frame, text="只需将照片拖入列表即可快速添加；点击“开始”按钮批量重命名您的照片；双击查看文件；右键点击移除文件；单击文件显示EXIF信息。")
label_description.pack(fill=ttk.X, padx=10, pady=10)

# 创建一个滚动条
scrollbar = ttk.Scrollbar(main_frame)
scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)

files_listbox = ttk.tk.Listbox(main_frame, width=100, height=15, yscrollcommand=scrollbar.set)
files_listbox.pack(fill=ttk.BOTH, expand=True, padx=10, pady=10)
files_listbox.drop_target_register(DND_FILES)
files_listbox.dnd_bind('<<Drop>>', lambda e: on_drop(e, files_listbox))
files_listbox.bind('<Button-3>', remove_file)
files_listbox.bind('<Double-1>', open_file)
files_listbox.bind('<Button-1>', show_exif_info)
files_listbox.bind('<Leave>', on_leave)

scrollbar.config(command=files_listbox.yview)

progress_var = ttk.DoubleVar()
progress = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
progress.pack(fill=ttk.X, padx=10, pady=10)

button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=ttk.X, padx=10, pady=10)

start_button = ttk.Button(button_frame, text="开始重命名", command=lambda: Thread(target=rename_photos, args=(files_listbox, progress_var)).start())
start_button.pack(side=ttk.LEFT, padx=5)
start_button.config(state=ttk.NORMAL)

# 在界面上添加撤销按钮
undo_button = ttk.Button(button_frame, text="撤销重命名", command=undo_rename)
undo_button.pack(side=ttk.LEFT, padx=5)
undo_button.config(state=ttk.DISABLED)

stop_button = ttk.Button(button_frame, text="停止重命名", command=stop_renaming)
stop_button.pack(side=ttk.LEFT, padx=5)
stop_button.config(state=ttk.DISABLED)

settings_button = ttk.Button(button_frame, text="设置", command=open_settings)
settings_button.pack(side=ttk.LEFT, padx=5)

clear_button = ttk.Button(button_frame, text="清空列表", command=lambda: files_listbox.delete(0, ttk.END))
clear_button.pack(side=ttk.LEFT, padx=5)

select_files_button = ttk.Button(button_frame, text="添加文件", command=lambda: select_files(files_listbox))
select_files_button.pack(side=ttk.LEFT, padx=5)

help_button = ttk.Button(button_frame, text="帮助", command=show_help)
help_button.pack(side=ttk.LEFT, padx=5)

auto_scroll_checkbox = ttk.Checkbutton(button_frame, text="自动滚动", variable=auto_scroll_var)
auto_scroll_checkbox.pack(side=ttk.LEFT, padx=5)

# 状态栏
status_bar = ttk.Label(root, text="准备就绪", relief=ttk.SUNKEN, anchor=ttk.W)
status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)

# 加载配置文件
load_settings()
set_language(language_var.get())

root.mainloop()