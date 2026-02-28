"""
OCR引擎基类
定义统一的OCR接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str                           # 识别的文本
    confidence: float                   # 置信度 0-1
    box: Optional[List[List[int]]]     # 文本框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    def __repr__(self):
        return f"OCRResult(text='{self.text}', confidence={self.confidence:.3f})"


class BaseOCREngine(ABC):
    """OCR引擎基类"""
    
    def __init__(self, use_gpu: bool = False, **kwargs):
        self.use_gpu = use_gpu
        self.config = kwargs
        self._model = None
        self.engine_name = "base"
        
    @abstractmethod
    def _init_model(self):
        """初始化模型"""
        pass
    
    @abstractmethod
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """
        识别图像中的文字
        
        Args:
            image: BGR格式的图像数组
            
        Returns:
            识别结果列表
        """
        pass
    
    def recognize_batch(self, images: List[np.ndarray]) -> List[List[OCRResult]]:
        """
        批量识别图像
        
        Args:
            images: 图像列表
            
        Returns:
            识别结果列表的列表
        """
        return [self.recognize(img) for img in images]
    
    def get_text_only(self, image: np.ndarray) -> List[str]:
        """只返回识别的文本"""
        results = self.recognize(image)
        return [r.text for r in results]
    
    def get_full_text(self, image: np.ndarray, separator: str = "\n") -> str:
        """返回完整的识别文本"""
        texts = self.get_text_only(image)
        return separator.join(texts)
    
    @property
    def is_initialized(self) -> bool:
        """检查模型是否已初始化"""
        return self._model is not None
    
    def __repr__(self):
        return f"{self.__class__.__name__}(use_gpu={self.use_gpu})"
