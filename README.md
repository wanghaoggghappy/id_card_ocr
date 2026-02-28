# 智能OCR识别系统

一个支持多种OCR引擎的智能识别系统，支持身份证识别和车辆文档批量处理。

## 📦 主要功能

### 1. 身份证OCR识别
- ✅ 支持5种主流OCR引擎
- ✅ 自动提取身份证正反面信息
- ✅ 图像预处理（去噪、增强、校正）
- ✅ 身份证号码校验
- ✅ 多引擎对比功能
- ✅ 性能基准测试
- ✅ PDF文档支持

### 2. 车辆文档批量处理 ⭐ 新增
- ✅ 自动识别登记证、发票、行驶证
- ✅ 批量提取车架号、金额、车主等信息
- ✅ 智能文件整理和重命名
- ✅ Excel汇总导出
- ✅ 支持多文件夹结构
- ✅ 自动跳过中间文件夹层级
- ✅ ZIP/RAR压缩包支持
- ✅ 4K图片自动缩放优化 ⭐⭐ 新增

## 🚀 快速开始

### 身份证识别
```bash
python main.py id_card.jpg -e paddleocr
```

### 车辆文档批量处理
```bash
./venv/bin/python process_vehicle_archives.py 车辆档案.zip
```

详细文档：
- 身份证识别：继续阅读本文档
- 车辆文档处理：查看 [QUICKSTART.md](QUICKSTART.md)

---

## 身份证识别功能详解

## 支持的OCR引擎

| 引擎 | 中文效果 | 速度 | 部署难度 | GPU支持 | 推荐场景 |
|------|---------|------|---------|---------|---------|
| **PaddleOCR** | ⭐⭐⭐⭐⭐ | 快 | 中 | ✅ | 生产环境首选 |
| **RapidOCR** | ⭐⭐⭐⭐⭐ | 快 | 低 | ✅ | 跨平台部署 |
| **EasyOCR** | ⭐⭐⭐⭐ | 中 | 低 | ✅ | 快速开发 |
| **CnOCR** | ⭐⭐⭐⭐ | 快 | 低 | ✅ | 轻量级部署 |
| **Tesseract** | ⭐⭐⭐ | 慢 | 中 | ❌ | 离线场景 |

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Mac/Linux

# 安装基础依赖
pip install opencv-python numpy Pillow pyyaml tqdm

# 安装OCR引擎（根据需要选择）

# 方案1: PaddleOCR (推荐)
pip install paddlepaddle paddleocr

# 方案2: RapidOCR (ONNX版本，部署更方便)
pip install rapidocr-onnxruntime

# 方案3: EasyOCR
pip install easyocr

# 方案4: CnOCR
pip install cnocr

# 方案5: Tesseract (需要先安装tesseract)
# Mac: brew install tesseract tesseract-lang
pip install pytesseract
```

### 2. 基本使用

```python
from id_card_recognizer import IDCardRecognizer

# 创建识别器
recognizer = IDCardRecognizer(engine="paddleocr")

# 识别身份证
result = recognizer.recognize("id_card.jpg")

# 查看结果
print(f"姓名: {result.name}")
print(f"身份证号: {result.id_number}")
print(f"住址: {result.address}")
```

### 3. 命令行使用

```bash
# 使用默认引擎识别
python main.py id_card.jpg

# 指定引擎
python main.py id_card.jpg -e easyocr

# 多引擎比较
python main.py id_card.jpg -c

# 可视化结果
python main.py id_card.jpg -v

# 列出可用引擎
python main.py --list-engines
```

### 4. 多引擎对比

```python
from id_card_recognizer import MultiEngineComparator

# 创建比较器
comparator = MultiEngineComparator(
    engines=["paddleocr", "rapidocr", "easyocr"]
)

# 比较识别结果
results = comparator.compare("id_card.jpg")
comparator.print_comparison(results)
```

### 5. 性能基准测试

```bash
# 运行基准测试
python benchmark.py image1.jpg image2.jpg -n 5

# 指定引擎
python benchmark.py images/*.jpg -e paddleocr rapidocr
```

## 项目结构

```
id_card_ocr/
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖列表
├── main.py                  # 主程序入口
├── benchmark.py             # 性能测试
├── id_card_recognizer.py    # 身份证识别器
├── ocr_engines/             # OCR引擎模块
│   ├── __init__.py
│   ├── base_engine.py       # 基类
│   ├── paddleocr_engine.py  # PaddleOCR
│   ├── easyocr_engine.py    # EasyOCR
│   ├── tesseract_engine.py  # Tesseract
│   ├── rapidocr_engine.py   # RapidOCR
│   └── cnocr_engine.py      # CnOCR
└── utils/                   # 工具模块
    ├── __init__.py
    ├── image_processor.py   # 图像预处理
    └── id_card_parser.py    # 身份证解析
```

## NVIDIA GPU部署

### 安装GPU版本依赖

```bash
# PaddleOCR GPU版本
pip install paddlepaddle-gpu

# 或使用ONNX Runtime GPU版本
pip install onnxruntime-gpu
pip install rapidocr-onnxruntime

# EasyOCR自动检测CUDA
pip install easyocr torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 启用GPU

```python
# 代码中启用GPU
recognizer = IDCardRecognizer(engine="paddleocr", use_gpu=True)

# 或命令行
python main.py id_card.jpg --gpu
```

## 各引擎详细说明

### 1. PaddleOCR
百度开源的OCR系统，中文识别效果最佳。

**优点：**
- 中文识别准确率高
- 支持检测+识别+方向分类
- 模型丰富，可自定义训练
- 支持PP-OCRv4最新模型

**缺点：**
- 依赖较重（需要PaddlePaddle框架）
- Mac M系列芯片需要特殊配置

### 2. RapidOCR
PaddleOCR的ONNX版本，跨平台部署更方便。

**优点：**
- 使用ONNX Runtime，跨平台兼容性好
- 不依赖PaddlePaddle框架
- 模型效果与PaddleOCR一致
- 部署简单

**缺点：**
- 模型更新可能滞后于PaddleOCR

### 3. EasyOCR
简单易用的OCR库，支持80+语言。

**优点：**
- 安装简单
- API友好
- 多语言支持好

**缺点：**
- 中文识别效果略逊于PaddleOCR
- 首次使用需下载模型

### 4. CnOCR
专门针对中文的轻量级OCR。

**优点：**
- 专注中文识别
- 模型轻量
- 支持多种backbone

**缺点：**
- 对复杂场景支持有限

### 5. Tesseract
Google开源的经典OCR引擎。

**优点：**
- 完全开源免费
- 支持100+语言
- 可训练自定义模型

**缺点：**
- 需要单独安装Tesseract程序
- 中文识别效果一般
- 处理速度较慢

## 选择建议

| 场景 | 推荐引擎 |
|------|---------|
| 生产环境 | PaddleOCR 或 RapidOCR |
| 快速原型开发 | EasyOCR |
| 轻量级部署 | RapidOCR 或 CnOCR |
| 离线环境 | Tesseract |
| NVIDIA GPU加速 | PaddleOCR 或 RapidOCR |

## License

MIT License
