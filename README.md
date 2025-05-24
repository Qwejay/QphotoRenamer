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

## 📥 安装与运行

### 环境要求
- Python 3.6+
- Windows/macOS/Linux

### 使用源码运行

1. 克隆仓库或下载源码
```bash
git clone https://github.com/Qwejay/QphotoRenamer.git
cd QphotoRenamer
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python QphotoRenamer.py
```

### 使用预编译版本

直接[下载最新版本](https://github.com/Qwejay/QphotoRenamer/releases)的可执行文件，无需安装，双击运行即可。

## 🎯 使用方法

### 基本操作

1. **添加文件**：
   - 点击"添加文件"按钮选择文件
   - 或直接将文件/文件夹拖放到程序界面

2. **设置重命名格式**：
   - 点击"设置"按钮打开设置窗口
   - 在"重命名模板"标签页中自定义命名格式

3. **开始重命名**：
   - 点击"开始重命名"按钮执行重命名
   - 状态栏会显示进度和结果

<p align="center">
  <img src="https://github.com/user-attachments/assets/48b9365a-c6b3-426a-9fe1-57f08d71f548" alt="设置界面" width="600">
</p>

### 高级功能

#### 自定义命名模板

在设置中的"重命名模板"中，可以使用以下变量组合命名格式：
- `{date}` - 日期（如20240101）
- `{time}` - 时间（如120530）
- `{camera}` - 相机型号
- `{lens}` - 镜头型号
- `{iso}` - ISO值
- `{focal}` - 焦距
- `{aperture}` - 光圈
- `{shutter}` - 快门速度

也可以使用标准的日期格式化字符：
- `%Y` - 年份（四位数）
- `%m` - 月份（两位数）
- `%d` - 日期（两位数）
- `%H` - 小时（24小时制）
- `%M` - 分钟
- `%S` - 秒数

#### 快速添加模式

当需要处理大量文件时，建议启用"快速添加模式"：

1. 在设置中勾选"启用快速添加模式"
2. 设置合适的文件数量阈值（默认10）
3. 超过阈值的文件将快速添加而不立即读取EXIF数据

#### 文件名冲突处理

在设置中配置文件名冲突的处理方式：

- **增加后缀**：自动添加数字后缀（如 "_001"、"_1"或" (1)"）
- **保留原文件名**：不重命名已存在相同名称的文件

#### 文件信息查看

- 单击文件选中后右键可查看详细EXIF信息
- 双击文件可直接打开源文件

## ⚙️ 设置选项详解

### 重命名模板
自定义文件重命名的格式，支持日期、时间和EXIF信息变量。

### 日期设置
- **首选日期**：优先使用的日期类型（拍摄日期/修改日期/创建日期）
- **备选日期**：当无法获取首选日期时使用的替代日期类型

### 文件处理
- **文件过滤**：设置需要跳过的文件扩展名
- **名称冲突处理**：配置同名文件的处理方式
- **性能优化**：快速添加模式设置

### 界面设置
- **语言选择**：简体中文/English
- **其他设置**：自动滚动、错误显示等选项

## 🔗 快捷操作

- **文件列表右键菜单**：
  - 查看文件EXIF信息
  - 移除所选文件
  - 打开文件位置

- **快捷键**：
  - `Delete`：从列表移除选中文件
  - `双击`：打开选中文件

## 📋 版本历史

### 版本 2.4 (2024-05-24)
- 修复后缀超过数量报错问题 感谢@kk43
- 此版本修复BUG为主，未增加新功能

### 版本 2.3 (2024-04-15)
- 修复命名模板无法自定义问题 感谢@kk43
- 完善命名模板逻辑，更加人性化
- 修复配置保存失败问题
- 移除命名撤销功能
- 优化性能以及错误处理机制
- 补全部分英文语言缺失

### 版本 2.2 (2024-03-31)
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
