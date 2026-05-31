# QphotoRenamer

QphotoRenamer 是一个简单易用的文件与照片批量重命名工具，支持根据拍摄日期、修改日期或创建日期重命名文件。它专为摄影爱好者和需要管理大量照片的用户设计，帮助您轻松整理各种文件，特别是照片和视频文件。

<p align="center">
  <img src="https://github.com/user-attachments/assets/23af7394-725e-41ba-b416-737c47f231e8" alt="主界面" width="600">
</p>

## 🌟 主要功能

- **拖放支持**：支持直接从文件管理器拖拽文件或文件夹到程序界面。
- **多格式兼容**：处理常见图片格式（JPG、PNG、HEIC等）和视频文件（MOV、MP4、AVI等）。
- **EXIF 数据利用**：自动读取照片拍摄信息（相机型号、镜头、ISO、光圈等）用于重命名。
- **自定义命名模板**：高度自定义重命名格式，支持多种日期及变量组合。
- **高效批处理**：优化的多线程处理，支持“快速添加模式”以应对海量文件。
- **智能冲突处理**：自动处理重名文件，支持添加后缀或保留原文件名。
- **持久化配置**：所有的自定义设置与模板均保存至配置文件，重启后自动加载。

---

## 📋 更新日志

### 版本 2.5 (2026-05-10)
- **性能优化**：优化了海量照片读取 EXIF 信息的并发效率，降低了运行期间的内存占用。
- **界面改进**：微调了 UI 布局与提示文本，提升了在高 DPI 屏幕下的兼容性与显示效果。
- **兼容性增强**：改进了对部分特定型号相机 RAW 格式及新型 HEIC 格式的元数据解析。
- **问题修复**：修正了特定异常路径下可能导致的程序退出问题，提升了批量处理时的稳定性。

### 版本 2.3 (2026-03-15)
- **代码精简**：代码从3000多行精简至1000多行，保持原有大部分功能同时移除了多语言的支持等。
- **配置修复**：彻底修复了设置界面保存逻辑，确保参数持久化有效，修改后实时生效。
- **稳定性修复**：解决 `Labelframe` 拼写报错及部分常量属性丢失问题，大幅提升代码鲁棒性。
- **交互升级**：优化多线程处理，解决批量重命名时的界面假死与 UI 同步问题。
- **格式优化**：重构了命名模板解析逻辑，支持缺失变量的智能剔除，避免文件名出现多余空格或下划线。

### 版本 2.2 (2025-03-31)
- **代码重构**：将全局变量整合至类属性，减少运行状态冲突。
- **性能优化**：引入类型注解增强可维护性。
- **功能修复**：修正停止按钮逻辑，确保操作可即时中断。

### 版本 2.0 (2024-12-29)
- 新增快速添加模式（针对大量文件性能优化）。
- 新增自定义冲突处理选项。
- 增强 EXIF 信息读取与缓存机制。
---

## 🛠️ 安装与构建

### 依赖安装

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --add-data "QPhotoRenamer.ini;." --add-data "icon.ico;." --add-data "C:\Path\To\Python\Lib\site-packages\tkinterdnd2\tkdnd;tkdnd" --add-data "C:\Path\To\Python\Lib\site-packages\tkinterdnd2;tkinterdnd2" --name QPhotoRenamer QphotoRenamer.py
```

### Nuitka 打包

```bash
pip install nuitka
nuitka --standalone --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=exifread --include-package=piexif --include-package=pillow_heif --include-package=ttkbootstrap --include-package=tkinterdnd2 --include-data-file=QphotoRenamer.ini=QphotoRenamer.ini --include-data-file=icon.ico=icon.ico --windows-icon-from-ico=icon.ico QphotoRenamer.py
```
## 下载
[查看所有版本](https://github.com/Qwejay/QphotoRenamer/releases)

## 🔗 相关链接

- [GitHub仓库](https://github.com/Qwejay/QphotoRenamer)
- [问题反馈](https://github.com/Qwejay/QphotoRenamer/issues)
- [最新版本](https://github.com/Qwejay/QphotoRenamer/releases)

## 📄 许可证

GPL License © QwejayHuang

## 🌟 致谢

感谢所有使用和支持QphotoRenamer的用户，您的反馈和建议是我们不断改进的动力！
