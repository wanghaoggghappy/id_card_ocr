"""
RapidOCR引擎
PaddleOCR的ONNX版本，跨平台部署更方便
优点：
- 使用ONNX Runtime，跨平台兼容性好
- 不依赖PaddlePaddle框架
- 模型效果与PaddleOCR一致
- 支持NVIDIA GPU加速
- 部署简单
缺点：
- 模型更新可能滞后于PaddleOCR

注意：后期部署到NVIDIA芯片时，安装 rapidocr-onnxruntime 并配置GPU
"""

import numpy as np
from typing import List
from .base_engine import BaseOCREngine, OCRResult


class RapidOCREngine(BaseOCREngine):
    """RapidOCR引擎"""
    
    def __init__(self, use_gpu: bool = False, **kwargs):
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "rapidocr"
        self._init_model()
        
    def _init_model(self):
        """初始化RapidOCR模型"""
        try:
            from rapidocr_onnxruntime import RapidOCR
            
            # RapidOCR使用ONNX Runtime，GPU支持需要安装onnxruntime-gpu
            # 它会自动检测可用的执行提供程序（CPU/CUDA/TensorRT等）
            self._model = RapidOCR()
            gpu_status = "GPU" if self.use_gpu else "CPU"
            print(f"✓ RapidOCR 初始化成功 (模式: {gpu_status})")
            
        except ImportError:
            raise ImportError(
                "请安装RapidOCR: pip install rapidocr-onnxruntime"
            )
        except Exception as e:
            raise RuntimeError(f"RapidOCR初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # RapidOCR返回格式: (result, elapse)
        # result: [[box, text, confidence], ...]
        ocr_result, _ = self._model(image)
        
        if ocr_result is None:
            return results
            
        for item in ocr_result:
            box = item[0]
            text = item[1]
            confidence = float(item[2])
            
            # 转换box格式
            box_coords = [[int(p[0]), int(p[1])] for p in box]
            
            results.append(OCRResult(
                text=text,
                confidence=confidence,
                box=box_coords
            ))
            
        return results
