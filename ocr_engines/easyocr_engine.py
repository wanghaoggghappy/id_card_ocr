"""
EasyOCR引擎
简单易用的OCR库，支持80+语言
优点：
- 安装简单
- 多语言支持好
- API友好
- 支持GPU加速
缺点：
- 中文识别效果略逊于PaddleOCR
- 首次使用需下载模型
"""

import numpy as np
from typing import List
from .base_engine import BaseOCREngine, OCRResult


class EasyOCREngine(BaseOCREngine):
    """EasyOCR引擎"""
    
    def __init__(self, use_gpu: bool = False, 
                 lang: List[str] = None, **kwargs):
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "easyocr"
        self.lang = lang or ["ch_sim", "en"]  # 默认简体中文和英文
        self._init_model()
        
    def _init_model(self):
        """初始化EasyOCR模型"""
        try:
            import easyocr
            
            # EasyOCR会自动检测CUDA是否可用
            self._model = easyocr.Reader(
                self.lang,
                gpu=self.use_gpu,
                verbose=False
            )
            gpu_status = "GPU" if self.use_gpu else "CPU"
            print(f"✓ EasyOCR 初始化成功 (模式: {gpu_status}, 语言: {self.lang})")
            
        except ImportError:
            raise ImportError("请安装EasyOCR: pip install easyocr")
        except Exception as e:
            raise RuntimeError(f"EasyOCR初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # EasyOCR返回格式: [(box, text, confidence), ...]
        ocr_result = self._model.readtext(image)
        
        for item in ocr_result:
            box = item[0]
            text = item[1]
            confidence = float(item[2])
            
            # 转换box格式为统一格式
            box_coords = [[int(p[0]), int(p[1])] for p in box]
            
            results.append(OCRResult(
                text=text,
                confidence=confidence,
                box=box_coords
            ))
            
        return results
