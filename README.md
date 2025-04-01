# QphotoRenamer

QphotoRenamer 是一个简单易用的文件与照片批量重命名工具，支持根据拍摄日期、修改日期或创建日期重命名文件。

## 主要功能

- 支持拖放文件和文件夹
- 支持多种日期格式重命名
- 支持 HEIC 格式照片
- 支持多语言（简体中文/English）
- 支持快速添加模式
- 支持文件名冲突处理
- 支持撤销重命名
- 支持查看文件 EXIF 信息
- 支持自定义前缀和后缀

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：`python QphotoRenamer.py`
2. 拖放文件或点击"添加文件"选择文件
3. 在设置中配置重命名格式
4. 点击"开始重命名"执行重命名操作

## 设置选项

- 重命名格式：支持多种日期格式
- 日期基准：拍摄日期/修改日期/创建日期
- 备用日期：当无法获取拍摄日期时的替代方案
- 前缀/后缀：可自定义文件名前缀和后缀
- 快速添加模式：批量添加文件时提高效率
- 文件名冲突处理：自动添加后缀或保留原文件名

## 快捷键

- 双击文件：打开文件
- 右键文件：移除文件
- 点击文件名：查看 EXIF 信息

## 许可证

MIT License

## 功能特性

- 自动根据照片的拍摄日期和视频文件的媒体创建日期对文件重命名
- 非媒体文件支持通过文件的修改日期和创建日期重命名
- 自定义重命名格式、可添加命名前缀和后缀
- 程序美观简洁易用

![image](https://github.com/user-attachments/assets/23af7394-725e-41ba-b416-737c47f231e8)
![image](https://github.com/user-attachments/assets/48b9365a-c6b3-426a-9fe1-57f08d71f548)

## 下载
[查看所有版本](https://github.com/Qwejay/QphotoRenamer/releases)

## QphotoRenamer 更新日志

### 版本 2.2 (2025-03-31)
- 代码优化，将全局变量重构为类变量，减少全局状态带来的问题，添加类型注解，提高代码可读性和可维护性
- 停止按钮逻辑调整，修复无法停止操作的问题

### 版本 2.0 (2024-12-29)
- 新增快速添加模式，文件数量超过阈值时跳过文件状态的读取，提升加载速度
- 新增文件名冲突处理选项，支持"增加后缀"或"保留原文件名"
- 优化多线程处理功能，提升重命名效率，支持中途停止
- 新增文件总数显示，状态栏实时更新文件数量
- 新增文件处理队列，支持批量添加文件，后台逐步处理
- 优化EXIF信息缓存，减少重复读取，提升性能
- 优化状态栏显示，实时反馈文件加载状态
- 修复文件重复添加、EXIF读取失败、文件名冲突处理等问题
- 优化代码结构，提升可读性和可维护性
- 修复排除拓展名不生效需要加"."才生效的问题

### 版本 1.0.8 (2024-12-18)
- 增加对视频文件的媒体创建日期的读取，以便更好的服务按"拍摄日期"重命名功能
- 增加新名称的预览列显示

### 版本 1.0.7 (2024-12-17)
- 增加了对文件状态的检测，确保在选择不同的日期来源时，程序能够正确地更新文件的状态
- 修复部分文字的英文语言支持
- 修复文件可以重复添加的BUG
- 程序能够正确处理多次重命名操作
    
### 版本 1.0.6 (2024-12-13)
- 支持无拍摄日期则保留原文件名
- 增加新名称实时预览
- 列表增加颜色提示
- 修复重命名提示计数错误

### 版本 1.0.5 (2024-12-3)
- 支持所有文件的重命名，自动查找拍摄日期重命名
- 无拍摄日期则可供用户选择其他参考日期（文件创建日期、修改日期）
- 支持输入不重命名的拓展名
- 界面优化

### 版本 1.0.4 (2024-10-3)
- 添加了重命名前缀和后缀的自定义功能
- 修复了修改部分设置后无法再次重命名已命名文件的问题

### 版本 1.0.2 (2024-08-1)
- 增加了多语言支持，现在用户可以选择简体中文或英文界面。添加了自动滚动功能，当新文件添加到列表时，列表会自动滚动到最新添加的文件
- 使用多线程和异步处理，优化了重命名过程，现在重命名操作更加稳定和高效。改进了状态栏的显示，现在状态栏会根据当前操作显示相应的提示信息。更新了帮助文档，提供了更详细的使用说明
- 修复了在某些情况下无法正确读取 HEIC 格式图片的 EXIF 数据的问题。修复了在重命名过程中偶尔出现的文件名冲突问题。修复了在撤销重命名操作时可能出现的文件恢复失败的问题

### 版本 1.0.1 (2024-07-26)
- 增加了对 HEIC 格式图片的支持，现在可以读取和重命名 HEIC 格式的图片。添加了撤销重命名功能，用户可以恢复到重命名前的文件名
- 优化了文件拖放功能，现在可以更方便地将文件和文件夹拖入列表。改进了设置界面，现在用户可以更方便地更改日期格式和语言设置
- 修复了在某些情况下无法正确读取图片 EXIF 数据的问题。修复了在重命名大量文件时可能出现的性能问题

### 版本 1.0.0 (2024-07-15)
- 首次发布 QphotoRenamer，支持批量重命名图片文件。支持读取和使用图片的 EXIF 数据进行重命名。提供了基本的设置选项，如日期格式和使用修改日期重命名

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
pyinstaller --onefile --windowed --icon=logo.ico --add-data "QphotoRenamer.ini;." --add-data icon.ico;." --add-data "tkdnd;tkdnd" QphotoRenamer.py
pyinstaller --onefile --windowed --icon=icon.ico --add-data "QPhotoRenamer.ini;." --add-data "icon.ico;." --add-data "C:\Users\dkm38\AppData\Local\Programs\Python\Python313\Lib\site-packages\tkinterdnd2\tkdnd;tkdnd" --add-data "C:\Users\dkm38\AppData\Local\Programs\Python\Python313\Lib\site-packages\tkinterdnd2;tkinterdnd2" --name QPhotoRenamer QphotoRenamer.py
nuitk打包参数：
安装打包工具：pip install nuitka
打包：
nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=exifread --include-package=piexif --include-package=pillow_heif --include-package=ttkbootstrap --include-package=tkinterdnd2 --include-data-file=QphotoRenamer.ini=QphotoRenamer.ini --include-data-file=icon.ico=icon.ico --windows-icon-from-ico=icon.ico QphotoRenamer.py
