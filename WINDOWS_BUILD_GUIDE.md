# 车辆档案批处理系统 - Windows版打包指南

## 系统要求

### 开发环境（打包机器）
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 - 3.11 推荐
- **内存**: 至少 8GB RAM
- **磁盘空间**: 至少 5GB 可用空间

### 目标环境（用户机器）
- **操作系统**: Windows 10/11 (64位)
- **内存**: 至少 4GB RAM
- **无需安装Python**（独立运行）

---

## 打包步骤

### 1. 准备打包环境

#### 在Windows上克隆代码并安装依赖

```bash
# 1. 克隆或下载代码到Windows机器
git clone <repository_url>
cd id_card_ocr

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\activate

# 4. 升级pip
python -m pip install --upgrade pip

# 5. 安装运行依赖
pip install -r requirements.txt

# 6. 安装打包工具
pip install pyinstaller>=6.0.0
```

### 2. 测试功能

在打包前，先测试程序是否正常运行：

```bash
# 测试命令行工具
python vehicle_cli.py --version
python vehicle_cli.py --help

# 测试处理单个档案（如果有测试数据）
python vehicle_cli.py test_archive.zip
```

### 3. 执行打包

```bash
# 运行打包脚本
python build_vehicle_exe.py
```

打包脚本会自动：
1. ✅ 清理旧的构建文件
2. ✅ 检查依赖是否完整
3. ✅ 创建PyInstaller配置文件
4. ✅ 编译生成EXE文件
5. ✅ 复制必要的配置文件和文档
6. ✅ 创建用户友好的启动脚本

### 4. 验证打包结果

打包完成后，会在 `dist/VehicleArchiveProcessor/` 目录生成以下文件：

```
dist/VehicleArchiveProcessor/
├── VehicleArchiveProcessor.exe    # 主程序
├── 启动-拖放文件.bat              # GUI启动脚本
├── 批量处理.bat                   # 批量处理脚本
├── 使用说明.txt                   # 中文使用说明
├── README.md                      # 详细文档
├── config.yaml                    # 配置文件
├── archives/                      # 测试输入文件夹
├── _internal/                     # 依赖库和资源（PyInstaller生成）
│   ├── opencv_python*.dll
│   ├── paddle*.dll
│   ├── onnxruntime*.dll
│   └── ... (其他依赖)
```

### 5. 测试打包的EXE

```bash
# 进入打包目录
cd dist\VehicleArchiveProcessor

# 测试命令
VehicleArchiveProcessor.exe --version
VehicleArchiveProcessor.exe --help

# 测试处理（如果有测试档案）
VehicleArchiveProcessor.exe test_archive.zip
```

---

## 打包选项说明

### PyInstaller配置选项

在 `build_vehicle_exe.py` 中可以调整以下选项：

```python
# 1. 单文件模式 vs 文件夹模式
# 当前使用文件夹模式（推荐，启动更快）
exclude_binaries=True

# 改为单文件模式（体积更大，但只有一个exe）
# exclude_binaries=False
# onefile=True

# 2. 控制台窗口
console=True          # 显示命令行窗口（推荐，可以看到输出）
# console=False       # 隐藏窗口（GUI应用）

# 3. 图标（可选）
icon=None             # 不设置图标
# icon='icon.ico'     # 使用自定义图标

# 4. UPX压缩
upx=True              # 启用压缩（减小体积）
# upx=False           # 禁用压缩（如果UPX出问题）
```

### 排除不必要的包（减小体积）

在 `get_hidden_imports()` 函数中的 `excludes` 列表：

```python
excludes=[
    'matplotlib',     # 不需要绘图
    'scipy',          # 不需要科学计算
    'pandas',         # 不需要数据分析
    'jupyter',        # 不需要Jupyter
    'notebook',       # 不需要Notebook
    'tkinter',        # 不需要GUI框架
]
```

---

## 常见问题

### Q1: 打包时报错 "ModuleNotFoundError"

**原因**: 缺少某个依赖包

**解决**:
```bash
# 检查缺少哪个包
pip list

# 安装缺失的包
pip install <package_name>
```

### Q2: 打包后EXE无法运行

**原因**: 可能是杀毒软件误报或依赖缺失

**解决**:
1. 检查杀毒软件，添加例外
2. 在命令行运行查看错误信息：
   ```bash
   VehicleArchiveProcessor.exe --help
   ```
3. 检查是否缺少运行时库（如VC++ Redistributable）

### Q3: 打包后体积太大

**当前体积**: 约 500MB - 1GB（包含PaddleOCR模型）

**优化方法**:
1. 使用单一OCR引擎（删除其他引擎代码）
2. 使用轻量级OCR引擎（RapidOCR约50MB）
3. 启用UPX压缩
4. 使用单文件模式

```python
# 只保留RapidOCR
pip uninstall paddleocr paddlepaddle
pip install rapidocr-onnxruntime
```

### Q4: 首次运行很慢

**原因**: PaddleOCR首次运行会下载模型文件（约100MB）

**解决**:
1. 预下载模型并打包到 `models/` 目录
2. 或在使用说明中提醒用户首次需要联网

### Q5: 在其他Windows电脑上无法运行

**原因**: 缺少VC++运行库

**解决**: 
用户需要安装 [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

或将运行库打包进去：
```python
# 在spec文件中添加
binaries=[
    ('C:\\Windows\\System32\\vcruntime140.dll', '.'),
    ('C:\\Windows\\System32\\msvcp140.dll', '.'),
]
```

---

## 分发打包结果

### 方法1: 直接压缩文件夹

```bash
# 进入dist目录
cd dist

# 压缩整个文件夹
# 使用7-Zip或WinRAR压缩为zip文件
VehicleArchiveProcessor_v1.0.0.zip
```

### 方法2: 制作安装程序（高级）

使用 Inno Setup 或 NSIS 创建安装程序：

```iss
; 示例 Inno Setup 脚本
[Setup]
AppName=车辆档案批处理系统
AppVersion=1.0.0
DefaultDirName={pf}\VehicleArchiveProcessor
DefaultGroupName=车辆档案处理
OutputBaseFilename=VehicleArchiveProcessor_Setup

[Files]
Source: "dist\VehicleArchiveProcessor\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\车辆档案处理"; Filename: "{app}\启动-拖放文件.bat"
Name: "{group}\使用说明"; Filename: "{app}\使用说明.txt"
```

---

## 用户使用指南

将以下内容提供给用户：

### 系统要求
- Windows 10/11 (64位)
- 至少4GB内存
- 首次运行需要联网（下载OCR模型）

### 安装步骤
1. 解压 `VehicleArchiveProcessor_v1.0.0.zip`
2. 进入 `VehicleArchiveProcessor` 文件夹
3. 双击 `启动-拖放文件.bat` 开始使用

### 使用方法
详见 `使用说明.txt`

---

## 版本管理

建议的版本号命名：

```
VehicleArchiveProcessor_v1.0.0_20260228.zip
                           │ │ │  └─ 日期
                           │ │ └─ 修订版本
                           │ └─ 次版本
                           └─ 主版本
```

---

## 技术细节

### 打包后的目录结构

```
VehicleArchiveProcessor/
├── VehicleArchiveProcessor.exe    # 入口程序（约2-5MB）
├── 启动-拖放文件.bat
├── 批量处理.bat
├── 使用说明.txt
├── README.md
├── config.yaml
├── archives/                       # 输入文件夹
└── _internal/                      # 依赖和资源
    ├── base_library.zip            # Python标准库
    ├── python311.dll               # Python运行时
    ├── paddle/                     # PaddleOCR库
    ├── cv2/                        # OpenCV库
    ├── openpyxl/                   # Excel处理库
    ├── PyMuPDF/                    # PDF处理库
    └── ... (其他依赖)
```

### 性能优化建议

1. **使用轻量级OCR**: RapidOCR比PaddleOCR小10倍
2. **延迟加载**: 按需加载OCR引擎
3. **多进程处理**: 利用多核CPU并行处理

---

## 更新日志

### v1.0.0 (2026-02-28)
- ✅ 初始版本
- ✅ 支持ZIP压缩包处理
- ✅ VIN提取（行驶证/登记证/发票）
- ✅ 车主信息提取
- ✅ Excel导出功能
- ✅ VIN不匹配检测

---

## 联系方式

如有问题，请联系技术支持。
