# QphotoRenamer

QphotoRenamer 是一个批量重命名工具，支持所有文件格式，如果是图片文件会根据拍摄日期重命名图片。该工具使用Python编写，并使用Tkinter构建用户界面。

## 功能特性

- 自动根据EXIF判断文件并重命名。
- 多线程批量重命名文件。
- 程序简洁易用。

![20241213025306](https://github.com/user-attachments/assets/8c82573c-7f1f-498f-a439-8f01399ca3f8)
![20241213025406](https://github.com/user-attachments/assets/4645554b-8258-4663-9788-2531c7f8ecdf)

## 下载
[查看所有版本](https://github.com/Qwejay/QphotoRenamer/releases)

## 运行&编译
### 依赖项

在运行QphotoRenamer之前，请确保已安装以下依赖项：

- Python 3.6+
- exifread
- piexif
- pillow_heif
- ttkbootstrap
- tkinterdnd2

你可以使用以下命令安装这些依赖项：

```bash
pip install exifread piexif pillow_heif ttkbootstrap tkinterdnd2

pyinstaller打包参数：
安装打包工具：pip install pyinstaller
打包：
pyinstaller --onefile --windowed --icon=logo.ico --add-data "QphotoRenamer.ini;." --add-data "logo.ico;." --add-data "tkdnd;tkdnd" QphotoRenamer.py

nuitk打包参数：
安装打包工具：pip install nuitka
打包：
nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=exifread --include-package=piexif --include-package=pillow_heif --include-package=ttkbootstrap --include-package=tkinterdnd2 --include-data-file=QphotoRenamer.ini=QphotoRenamer.ini --include-data-file=logo.ico=logo.ico --windows-icon-from-ico=logo.ico QphotoRenamer.py
