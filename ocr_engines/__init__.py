"""
OCR引擎模块
提供多种OCR引擎的统一接口
"""

from .base_engine import BaseOCREngine
from .paddleocr_engine import PaddleOCREngine
from .easyocr_engine import EasyOCREngine
from .tesseract_engine import TesseractEngine
from .rapidocr_engine import RapidOCREngine
from .cnocr_engine import CnOCREngine
from .deepseek_ocr_engine import DeepSeekOCREngine
from .deepseek_gguf_engine import DeepSeekGGUFEngine

# 引擎注册表
ENGINE_REGISTRY = {
    "paddleocr": PaddleOCREngine,
    "easyocr": EasyOCREngine,
    "tesseract": TesseractEngine,
    "rapidocr": RapidOCREngine,
    "cnocr": CnOCREngine,
    "deepseek": DeepSeekOCREngine,
    "deepseek-ocr": DeepSeekOCREngine,
    "deepseek-ocr-2": DeepSeekOCREngine,
    "deepseek-gguf": DeepSeekGGUFEngine,
    "deepseek-cpu": DeepSeekGGUFEngine,
}


def get_engine(engine_name: str, **kwargs):
    """获取OCR引擎实例"""
    if engine_name not in ENGINE_REGISTRY:
        raise ValueError(f"未知的OCR引擎: {engine_name}. 可用引擎: {list(ENGINE_REGISTRY.keys())}")
    return ENGINE_REGISTRY[engine_name](**kwargs)


def list_engines():
    """列出所有可用的OCR引擎"""
    return list(ENGINE_REGISTRY.keys())
