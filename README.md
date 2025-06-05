# QphotoRenamer

QphotoRenamer 是一个简单易用的文件与照片批量重命名工具，支持根据拍摄日期、修改日期或创建日期重命名文件。它专为摄影爱好者和需要管理大量照片的用户设计，帮助您轻松整理各种文件，特别是照片和视频文件。

<p align="center">
  <img src="https://github.com/user-attachments/assets/23af7394-725e-41ba-b416-737c47f231e8" alt="主界面" width="600">
</p>

## 🌟 主要功能

- **拖放支持**：直接拖拽文件或文件夹到程序界面
- **多格式支持**：处理常见图片格式（JPG、PNG、HEIC等）和视频文件
- **EXIF数据利用**：自动读取照片EXIF信息用于重命名
- **自定义命名格式**：支持多种日期格式和变量组合
- **双语界面**：支持简体中文和英文
- **高效批处理**：优化的多线程处理，支持快速添加模式
- **智能文件名冲突处理**：自动添加后缀或保留原文件名
- **文件信息查看**：查看照片的EXIF信息和详细信息

## 📋 版本历史

### 版本 2.2 (2025-03-31)
- 代码优化，将全局变量重构为类变量，减少全局状态带来的问题
- 添加类型注解，提高代码可读性和可维护性
- 修复停止按钮无法停止操作的问题

### 版本 2.0 (2024-12-29)
- 新增快速添加模式，文件数量超过阈值时跳过文件状态的读取，提升加载速度
- 新增文件名冲突处理选项，支持"增加后缀"或"保留原文件名"
- 优化多线程处理功能，提升重命名效率，支持中途停止
- 新增文件总数显示，状态栏实时更新文件数量
- 新增文件处理队列，支持批量添加文件，后台逐步处理
- 优化EXIF信息缓存，减少重复读取，提升性能
- 优化状态栏显示，实时反馈文件加载状态
- 修复文件重复添加、EXIF读取失败、文件名冲突处理等问题
- 修复排除拓展名需要加"."才生效的问题

[查看所有版本历史](https://github.com/Qwejay/QphotoRenamer/releases)

## 🛠️ 开发构建

### PyInstaller 打包

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --add-data "QPhotoRenamer.ini;." --add-data "icon.ico;." --add-data "C:\Path\To\Python\Lib\site-packages\tkinterdnd2\tkdnd;tkdnd" --add-data "C:\Path\To\Python\Lib\site-packages\tkinterdnd2;tkinterdnd2" --name QPhotoRenamer QphotoRenamer.py
```

### Nuitka 打包

```bash
pip install nuitka
nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=exifread --include-package=piexif --include-package=pillow_heif --include-package=ttkbootstrap --include-package=tkinterdnd2 --include-data-file=QphotoRenamer.ini=QphotoRenamer.ini --include-data-file=icon.ico=icon.ico --windows-icon-from-ico=icon.ico QphotoRenamer.py
```

## 📄 许可证

MIT License © QwejayHuang

## 🌟 致谢

感谢所有使用和支持QphotoRenamer的用户，您的反馈和建议是我们不断改进的动力！

## 🔗 相关链接

- [GitHub仓库](https://github.com/Qwejay/QphotoRenamer)
- [问题反馈](https://github.com/Qwejay/QphotoRenamer/issues)
- [最新版本](https://github.com/Qwejay/QphotoRenamer/releases)

## 功能特性

- 自动根据照片的拍摄日期和视频文件的媒体创建日期对文件重命名
- 非媒体文件支持通过文件的修改日期和创建日期重命名
- 自定义重命名格式、可添加命名前缀和后缀
- 程序美观简洁易用

![image](https://github.com/user-attachments/assets/23af7394-725e-41ba-b416-737c47f231e8)
![image](https://github.com/user-attachments/assets/48b9365a-c6b3-426a-9fe1-57f08d71f548)

## 下载
[查看所有版本](https://github.com/Qwejay/QphotoRenamer/releases)


你可以使用以下命令安装这些依赖项：

```bash
pip install exifread piexif pillow_heif ttkbootstrap tkinterdnd2

pyinstaller打包参数：
安装打包工具：pip install pyinstaller
打包：
pyinstaller --onefile --windowed --icon=logo.ico --add-data "QphotoRenamer.ini;." --add-data icon.ico;." --add-data "tkdnd;tkdnd" QphotoRenamer.py
pyinstaller --onefile --windowed --icon=icon.ico --add-data "QPhotoRenamer.ini;." --add-data "icon.ico;." --add-data "C:\Users\dkm38\AppData\Local\Programs\Python\Python313\Lib\site-packages\tkinterdnd2\tkdnd;tkdnd" --add-data "C:\Users\dkm38\AppData\Local\Programs\Python\Python313\Lib\site-packages\tkinterdnd2;tkinterdnd2" --name QPhotoRenamer QphotoRenamer.py
nuitk打包参数：
安装打包工具：pip install nuitka
打包：
nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=exifread --include-package=piexif --include-package=pillow_heif --include-package=ttkbootstrap --include-package=tkinterdnd2 --include-data-file=QphotoRenamer.ini=QphotoRenamer.ini --include-data-file=icon.ico=icon.ico --windows-icon-from-ico=icon.ico QphotoRenamer.py
