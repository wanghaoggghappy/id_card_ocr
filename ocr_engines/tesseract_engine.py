"""
Tesseract OCR引擎
Google开源的经典OCR引擎
优点：
- 完全开源免费
- 支持100+语言
- 历史悠久，社区活跃
- 可训练自定义模型
缺点：
- 需要单独安装Tesseract
- 中文识别效果一般
- 处理速度较慢
- 需要预处理才能获得好效果

安装Tesseract:
- Mac: brew install tesseract tesseract-lang
- Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-chi-sim
"""

import numpy as np
from typing import List
from .base_engine import BaseOCREngine, OCRResult


class TesseractEngine(BaseOCREngine):
    """Tesseract OCR引擎"""
    
    def __init__(self, use_gpu: bool = False, 
                 lang: str = "chi_sim+eng", 
                 config: str = "--psm 6", **kwargs):
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "tesseract"
        self.lang = lang
        self.tesseract_config = config
        self._init_model()
        
    def _init_model(self):
        """初始化Tesseract"""
        try:
            import pytesseract
            
            # 检查Tesseract是否安装
            version = pytesseract.get_tesseract_version()
            self._model = pytesseract
            print(f"✓ Tesseract 初始化成功 (版本: {version})")
            
        except ImportError:
            raise ImportError("请安装pytesseract: pip install pytesseract")
        except Exception as e:
            raise RuntimeError(
                f"Tesseract初始化失败: {e}\n"
                "请确保已安装Tesseract:\n"
                "  Mac: brew install tesseract tesseract-lang\n"
                "  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
            )
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # 使用image_to_data获取详细信息
        import cv2
        from PIL import Image
        
        # 转换为PIL Image
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        pil_image = Image.fromarray(image_rgb)
        
        # 获取详细的OCR数据
        data = self._model.image_to_data(
            pil_image,
            lang=self.lang,
            config=self.tesseract_config,
            output_type=self._model.Output.DICT
        )
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                conf = int(data['conf'][i])
                if conf > 0:  # 过滤无效结果
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    # 构建box坐标
                    box = [
                        [x, y],
                        [x + w, y],
                        [x + w, y + h],
                        [x, y + h]
                    ]
                    
                    results.append(OCRResult(
                        text=text,
                        confidence=conf / 100.0,  # 转换为0-1范围
                        box=box
                    ))
                    
        return results
    
    def recognize_simple(self, image: np.ndarray) -> str:
        """简单识别，只返回文本"""
        import cv2
        from PIL import Image
        
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        pil_image = Image.fromarray(image_rgb)
        
        text = self._model.image_to_string(
            pil_image,
            lang=self.lang,
            config=self.tesseract_config
        )
        return text.strip()
