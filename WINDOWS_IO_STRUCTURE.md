# Windows版本 - 输入输出目录说明

## 📁 目录结构

打包后的Windows程序文件夹结构如下：

```
VehicleArchiveProcessor/        # 主程序文件夹
│
├── VehicleArchiveProcessor.exe # 主程序（可执行文件）
├── 启动-拖放文件.bat            # 图形界面启动脚本
├── 批量处理.bat                 # 批量处理脚本
├── 使用说明.txt                 # 中文使用手册
│
├── archives/                    # 【输入】压缩包放这里
│   ├── README.txt              #   使用说明
│   ├── 档案1.zip               #   ← 用户把压缩包放这里
│   ├── 档案2.zip               #   ← 用户把压缩包放这里
│   └── ...                     #   支持多个
│
├── output/                      # 【输出】处理结果保存在这里
│   ├── vehicle_info.xlsx       #   ← Excel汇总表（自动生成）
│   │
│   ├── LSVNF60C8NN097361/      #   ← 按车架号整理的文件夹
│   │   ├── 行驶证.jpg
│   │   ├── 登记证.jpg
│   │   └── 发票.jpg
│   │
│   └── LSVNP68C0PN046761/      #   ← 另一个车架号
│       └── ...
│
├── config.yaml                  # 配置文件（可选）
├── README.md                    # 英文说明文档
└── _internal/                   # 依赖库（不要删除）
    └── ...

```

## 📥 输入目录：archives/

### 用途
存放待处理的车辆档案压缩包

### 支持格式
- ✅ `.zip` 格式

### 使用方法

**方法1：手动放置**
```
1. 打开 archives 文件夹
2. 将压缩包文件复制进去
3. 双击运行 "批量处理.bat"
```

**方法2：拖放（推荐）**
```
1. 双击运行 "启动-拖放文件.bat"
2. 将压缩包拖放到弹出的窗口
3. 按回车键开始处理
```

**方法3：命令行**
```cmd
# 不需要放在archives文件夹
VehicleArchiveProcessor.exe C:\路径\档案.zip
VehicleArchiveProcessor.exe *.zip
```

### 示例压缩包结构
```
LSVNF60C8NN097361.zip
├── 行驶证-01.jpg
├── 行驶证-02.jpg  
├── 登记证-01.jpg
├── 发票.jpg
└── ...
```

## 📤 输出目录：output/

### 用途
存放所有处理结果

### 输出内容

#### 1. Excel汇总表
**文件名**: `vehicle_info.xlsx`

| 列名 | 说明 | 示例 |
|------|------|------|
| 序号 | 自动编号 | 1, 2, 3... |
| 档案名 | ZIP文件名 | LSVNF60C8NN097361.zip |
| 行驶证-车架号 | 行驶证中的VIN | LSVNF60C8NN097361 |
| 登记证-车架号 | 登记证中的VIN | LSVNF60C8NN097361 |
| 发票-车架号 | 发票中的VIN | LSVNF60C8NN097361 |
| 车主 | 行驶证车主 | 张三 |
| 新车主 | 登记证新车主 | 李四 |
| 交易金额 | 发票金额 | 150000.00 |

**特殊标记**：
- 🔴 **红色标记**：车架号不一致时会标红
- 📏 **列宽优化**：车主列自动加宽（30字符）
- 📝 **自动换行**：长公司名自动换行显示

#### 2. 按车架号整理的文件夹

```
output/
├── LSVNF60C8NN097361/    # 按VIN命名的文件夹
│   ├── 行驶证-正页.jpg
│   ├── 行驶证-副页.jpg
│   ├── 登记证-注册登记.jpg
│   └── 发票.jpg
│
└── LSVNP68C0PN046761/
    └── ...
```

**文件命名规则**：
- 行驶证: `行驶证-正页.jpg`, `行驶证-副页.jpg`
- 登记证: `登记证-注册登记.jpg`, `登记证-转移登记.jpg`
- 发票: `发票.jpg`, `发票-1.jpg`, `发票-2.jpg`

### 自定义输出目录

**命令行方式**：
```cmd
VehicleArchiveProcessor.exe 档案.zip -o D:\我的输出目录
VehicleArchiveProcessor.exe 档案.zip --output C:\结果
```

**只导出Excel不整理文件**：
```cmd
VehicleArchiveProcessor.exe 档案.zip --no-organize
```

## 🚀 三种使用模式

### 模式1：拖放式（最简单）

```
【适用场景】：处理少量文件，不熟悉命令行

1. 双击 "启动-拖放文件.bat"
2. 拖放压缩包到窗口（可多选）
3. 按回车
4. 到 output 文件夹查看结果
```

### 模式2：批量处理

```
【适用场景】：一次处理大量文件

1. 把所有压缩包复制到 archives 文件夹
2. 双击 "批量处理.bat"
3. 等待完成
4. 到 output 文件夹查看结果
```

### 模式3：命令行（高级）

```cmd
【适用场景】：自动化脚本、自定义参数

# 基本使用
VehicleArchiveProcessor.exe 档案.zip

# 批量处理（通配符）
VehicleArchiveProcessor.exe *.zip
VehicleArchiveProcessor.exe D:\车辆档案\*.zip

# 自定义输出目录
VehicleArchiveProcessor.exe 档案.zip -o D:\输出

# 只导出Excel
VehicleArchiveProcessor.exe 档案.zip --no-organize

# 详细日志
VehicleArchiveProcessor.exe 档案.zip -v

# 查看帮助
VehicleArchiveProcessor.exe --help
```

## 📝 实际使用示例

### 示例1：处理单个档案

```
操作步骤：
1. 双击 "启动-拖放文件.bat"
2. 将 "LSVNF60C8NN097361.zip" 拖到窗口
3. 按回车

结果：
output/
├── vehicle_info.xlsx           # 生成汇总表
└── LSVNF60C8NN097361/         # 整理的文件
    ├── 行驶证-正页.jpg
    └── ...
```

### 示例2：批量处理10个档案

```
操作步骤：
1. 把10个zip文件复制到 archives 文件夹
2. 双击 "批量处理.bat"
3. 等待进度条完成

结果：
output/
├── vehicle_info.xlsx           # 包含10行数据
├── LSVNF60C8NN097361/         # 10个车架号文件夹
├── LSVNP68C0PN046761/
├── ...
└── (共10个文件夹)
```

### 示例3：VIN不匹配检测

```
档案：LSVNF60C8NN097361.zip
  行驶证VIN: LSVNF60C8NN097361
  登记证VIN: LSVNF60C8NN097361
  发票VIN:   LSVNP68C0PN046761  ❌ 不一致！

Excel输出：
序号 | 档案名              | 行驶证-车架号      | 登记证-车架号      | 发票-车架号        
-----|--------------------|--------------------|--------------------|-----------------
1    | LSVNF60C...zip     | LSVNF60C8NN097361  | LSVNF60C8NN097361  | LSVNP68C0PN046761 🔴
     |                    |                    |                    | ↑ 标红提示
```

## ⚙️ 配置文件（可选）

### config.yaml

```yaml
# OCR引擎选择
ocr_engine: paddleocr  # 可选: paddleocr, rapidocr, easyocr

# 输出选项
output:
  organize_files: true      # 是否整理文件到车架号文件夹
  export_excel: true        # 是否导出Excel
  excel_filename: vehicle_info.xlsx
  
# Excel格式
excel:
  column_widths:
    - 6   # 序号
    - 20  # 档案名
    - 22  # 行驶证车架号
    - 22  # 登记证车架号
    - 22  # 发票车架号
    - 30  # 车主（加宽）
    - 30  # 新车主（加宽）
    - 15  # 交易金额
```

## 🔧 常见问题

### 问：为什么output文件夹是空的？

**答**：检查以下几点：
1. 确认压缩包格式是 `.zip`
2. 确认压缩包内有图片文件
3. 查看命令窗口是否有错误提示
4. 尝试用 `-v` 参数查看详细日志

### 问：可以不使用archives文件夹吗？

**答**：可以！
- 方法1：拖放式不需要archives文件夹
- 方法2：命令行直接指定路径
- archives文件夹只是方便批量处理时使用

### 问：output文件夹可以改名吗？

**答**：可以用 `-o` 参数自定义：
```cmd
VehicleArchiveProcessor.exe 档案.zip -o 我的结果
```

### 问：Excel文件被占用怎么办？

**答**：关闭已打开的Excel文件，或者：
```cmd
# 指定新的Excel文件名（修改config.yaml）
excel_filename: vehicle_info_新.xlsx
```

## 📊 处理流程图

```
┌─────────────┐
│  压缩包文件  │ (archives/*.zip 或 拖放)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  解压ZIP    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  OCR识别    │ (PaddleOCR)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  信息提取   │ (VIN/车主/金额)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  VIN验证    │ (格式检查/一致性)
└──────┬──────┘
       │
       ├──────────────────┐
       │                  │
       ↓                  ↓
┌─────────────┐    ┌──────────────┐
│ 导出Excel   │    │ 文件整理     │
│ (汇总表)    │    │ (按VIN分类)  │
└──────┬──────┘    └──────┬───────┘
       │                  │
       ↓                  ↓
┌─────────────────────────────┐
│      output/               │
│  ├── vehicle_info.xlsx     │
│  └── LSVNF.../             │
└─────────────────────────────┘
```

## 📞 技术支持

如遇问题，请检查：
1. [使用说明.txt](使用说明.txt) - 快速上手指南
2. [QUICKSTART_BUILD.md](QUICKSTART_BUILD.md) - 打包快速指南  
3. [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md) - 完整技术文档
