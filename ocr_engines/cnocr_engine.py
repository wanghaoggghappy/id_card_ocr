"""
CnOCR引擎
专门针对中文的轻量级OCR
优点：
- 专注中文识别
- 模型轻量
- 支持多种backbone
- 安装简单
缺点：
- 只做识别，不做检测（需要配合cnstd使用）
- 对复杂场景支持有限
"""

import numpy as np
from typing import List
from .base_engine import BaseOCREngine, OCRResult


class CnOCREngine(BaseOCREngine):
    """CnOCR引擎"""
    
    def __init__(self, use_gpu: bool = False, 
                 model_name: str = "densenet_lite_136-gru", **kwargs):
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "cnocr"
        self.model_name = model_name
        self._det_model = None  # 检测模型
        self._rec_model = None  # 识别模型
        self._init_model()
        
    def _init_model(self):
        """初始化CnOCR模型"""
        try:
            from cnocr import CnOcr
            
            # CnOCR 2.x 版本集成了检测和识别
            self._model = CnOcr(
                rec_model_name=self.model_name,
                det_model_name='ch_PP-OCRv3_det',  # 使用PaddleOCR的检测模型
            )
            print(f"✓ CnOCR 初始化成功 (模型: {self.model_name})")
            
        except ImportError:
            raise ImportError("请安装CnOCR: pip install cnocr")
        except Exception as e:
            raise RuntimeError(f"CnOCR初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # CnOCR ocr方法返回检测+识别结果
        ocr_result = self._model.ocr(image)
        
        for item in ocr_result:
            text = item['text']
            confidence = float(item['score'])
            
            # 获取位置信息
            position = item.get('position')
            if position is not None:
                box_coords = [[int(p[0]), int(p[1])] for p in position]
            else:
                box_coords = None
            
            results.append(OCRResult(
                text=text,
                confidence=confidence,
                box=box_coords
            ))
            
        return results
    
    def recognize_cropped(self, image: np.ndarray) -> List[OCRResult]:
        """识别已裁剪的文本行图像"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # 使用ocr_for_single_line识别单行
        ocr_result = self._model.ocr_for_single_lines([image])
        
        for item in ocr_result:
            text = item['text']
            confidence = float(item['score'])
            
            results.append(OCRResult(
                text=text,
                confidence=confidence,
                box=None
            ))
            
        return results
