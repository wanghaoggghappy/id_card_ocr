# 快速打包指南

## 在Windows上打包可执行文件（5分钟）

### 第一步：准备环境（首次）

```cmd
# 1. 确保已安装Python 3.8-3.11
python --version

# 2. 进入项目目录
cd path\to\id_card_ocr

# 3. 创建虚拟环境
python -m venv venv

# 4. 激活虚拟环境
venv\Scripts\activate

# 5. 安装所有依赖
pip install -r requirements.txt
pip install pyinstaller
```

### 第二步：执行打包（1分钟）

```cmd
# 确保虚拟环境已激活
venv\Scripts\activate

# 运行打包脚本
python build_vehicle_exe.py
```

等待3-10分钟（取决于电脑性能）。

### 第三步：测试（1分钟）

```cmd
# 进入打包目录
cd dist\VehicleArchiveProcessor

# 测试运行
VehicleArchiveProcessor.exe --version
VehicleArchiveProcessor.exe --help
```

### 第四步：分发

将整个 `dist\VehicleArchiveProcessor` 文件夹打包成zip发给用户：

```
VehicleArchiveProcessor_v1.0.0.zip
```

---

## 用户使用方法

用户解压后：

1. **简单使用**：双击 `启动-拖放文件.bat`，拖放压缩包
2. **批量处理**：将文件放入 `archives` 文件夹，双击 `批量处理.bat`
3. **命令行**：`VehicleArchiveProcessor.exe archive.zip`

---

## 常见问题速查

| 问题 | 解决方案 |
|------|---------|
| ModuleNotFoundError | `pip install <缺失的包>` |
| 打包体积太大 | 使用轻量级OCR引擎（见完整指南） |
| EXE无法运行 | 检查杀毒软件，安装VC++运行库 |
| 首次运行很慢 | 正常，正在下载OCR模型（需联网） |

完整指南请查看 [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md)
