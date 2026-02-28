"""
身份证识别器
整合OCR引擎和解析器，提供统一的身份证识别接口
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Union
from pathlib import Path
import yaml
import time

from ocr_engines import get_engine, list_engines, BaseOCREngine
from utils import ImageProcessor, IDCardParser
from utils.id_card_parser import IDCardInfo


class IDCardRecognizer:
    """身份证识别器"""
    
    def __init__(self, engine: str = "paddleocr", 
                 config_path: Optional[str] = None,
                 use_gpu: bool = False,
                 **engine_kwargs):
        """
        初始化身份证识别器
        
        Args:
            engine: OCR引擎名称，可选: paddleocr, easyocr, tesseract, rapidocr, cnocr
            config_path: 配置文件路径
            use_gpu: 是否使用GPU
            **engine_kwargs: 传递给OCR引擎的额外参数
        """
        self.engine_name = engine
        self.use_gpu = use_gpu
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.image_processor = ImageProcessor()
        self.parser = IDCardParser()
        
        # 初始化OCR引擎
        engine_config = self.config.get('engines', {}).get(engine, {})
        engine_config.update(engine_kwargs)
        engine_config['use_gpu'] = use_gpu
        
        self.ocr_engine = get_engine(engine, **engine_config)
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
            
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def recognize(self, image: Union[str, np.ndarray, Path],
                  preprocess: bool = True,
                  detect_card_region: bool = False,
                  pdf_page: int = 0) -> IDCardInfo:
        """
        识别身份证
        
        Args:
            image: 图像路径、numpy数组或Path对象
            preprocess: 是否进行预处理
            detect_card_region: 是否自动检测身份证区域
            pdf_page: 如果输入是PDF，指定要识别的页码（0表示第一页，-1表示识别所有页并返回最佳结果）
            
        Returns:
            身份证信息
        """
        # 加载图像
        if isinstance(image, (str, Path)):
            # 检查是否为PDF
            if ImageProcessor.is_pdf(image):
                images = ImageProcessor.pdf_to_images(image)
                
                if not images:
                    raise ValueError(f"PDF文件为空或无法加载: {image}")
                
                # 处理多页PDF
                if pdf_page == -1:
                    # 识别所有页，返回置信度最高的结果
                    best_result = None
                    best_confidence = 0
                    
                    for page_num, page_img in enumerate(images):
                        try:
                            result = self._recognize_single_image(
                                page_img, preprocess, detect_card_region
                            )
                            if result.confidence > best_confidence:
                                best_confidence = result.confidence
                                best_result = result
                        except Exception as e:
                            print(f"警告: 第{page_num + 1}页识别失败: {e}")
                            continue
                    
                    if best_result is None:
                        raise ValueError("所有PDF页面识别均失败")
                    
                    return best_result
                else:
                    # 识别指定页
                    if pdf_page >= len(images):
                        raise ValueError(
                            f"页码{pdf_page}超出范围，PDF共有{len(images)}页"
                        )
                    img = images[pdf_page]
            else:
                # 加载普通图像
                img = cv2.imread(str(image))
                if img is None:
                    raise ValueError(f"无法加载图像: {image}")
        else:
            img = image.copy()
        
        return self._recognize_single_image(img, preprocess, detect_card_region)
    
    def _recognize_single_image(self, img: np.ndarray,
                                preprocess: bool = True,
                                detect_card_region: bool = False) -> IDCardInfo:
        """
        识别单个图像
        
        Args:
            img: 图像数组
            preprocess: 是否预处理
            detect_card_region: 是否检测身份证区域
            
        Returns:
            身份证信息
        """
        # 自动缩放大尺寸图片以优化OCR性能
        img, was_resized = ImageProcessor.resize_for_ocr(img)
        
        # 检测身份证区域
        if detect_card_region:
            card_region = self.image_processor.detect_id_card_region(img)
            if card_region is not None:
                img = card_region
                
        # 预处理
        if preprocess:
            img = self.image_processor.preprocess(
                img,
                denoise=self.config.get('preprocessing', {}).get('denoise', True),
                enhance_contrast=self.config.get('preprocessing', {}).get('enhance_contrast', True),
                deskew=self.config.get('preprocessing', {}).get('deskew', True)
            )
            
        # OCR识别
        ocr_results = self.ocr_engine.recognize(img)
        
        # 解析结果
        id_info = self.parser.parse(ocr_results)
        
        return id_info
    
    def recognize_with_timing(self, image: Union[str, np.ndarray],
                              **kwargs) -> tuple:
        """
        识别身份证并返回耗时
        
        Returns:
            (IDCardInfo, elapsed_time_ms)
        """
        start_time = time.time()
        result = self.recognize(image, **kwargs)
        elapsed_time = (time.time() - start_time) * 1000  # 毫秒
        return result, elapsed_time
    
    def recognize_pdf_all_pages(self, pdf_path: Union[str, Path],
                               preprocess: bool = True,
                               detect_card_region: bool = False) -> List[Dict]:
        """
        识别PDF所有页面
        
        Args:
            pdf_path: PDF文件路径
            preprocess: 是否预处理
            detect_card_region: 是否检测身份证区域
            
        Returns:
            每一页的识别结果列表，格式为: [{"page": 页码, "info": IDCardInfo, "success": bool, "error": str}]
        """
        if not ImageProcessor.is_pdf(pdf_path):
            raise ValueError(f"文件不是PDF格式: {pdf_path}")
        
        images = ImageProcessor.pdf_to_images(pdf_path)
        results = []
        
        for page_num, page_img in enumerate(images):
            try:
                info = self._recognize_single_image(
                    page_img, preprocess, detect_card_region
                )
                results.append({
                    "page": page_num + 1,
                    "info": info,
                    "success": True,
                    "error": None
                })
            except Exception as e:
                results.append({
                    "page": page_num + 1,
                    "info": None,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def switch_engine(self, engine: str, **engine_kwargs):
        """切换OCR引擎"""
        engine_config = self.config.get('engines', {}).get(engine, {})
        engine_config.update(engine_kwargs)
        engine_config['use_gpu'] = self.use_gpu
        
        self.ocr_engine = get_engine(engine, **engine_config)
        self.engine_name = engine
        print(f"已切换到 {engine} 引擎")
        
    @staticmethod
    def available_engines() -> List[str]:
        """获取可用的OCR引擎列表"""
        return list_engines()


class MultiEngineComparator:
    """多引擎比较器"""
    
    def __init__(self, engines: List[str] = None, use_gpu: bool = False):
        """
        初始化比较器
        
        Args:
            engines: 要比较的引擎列表，默认使用所有可用引擎
            use_gpu: 是否使用GPU
        """
        self.engines = engines or list_engines()
        self.use_gpu = use_gpu
        self.recognizers = {}
        
        # 初始化各个引擎
        for engine in self.engines:
            try:
                self.recognizers[engine] = IDCardRecognizer(
                    engine=engine, 
                    use_gpu=use_gpu
                )
                print(f"✓ {engine} 初始化成功")
            except Exception as e:
                print(f"✗ {engine} 初始化失败: {e}")
                
    def compare(self, image: Union[str, np.ndarray],
                preprocess: bool = True) -> Dict:
        """
        使用多个引擎识别并比较结果
        
        Returns:
            比较结果字典
        """
        results = {}
        
        for engine, recognizer in self.recognizers.items():
            try:
                info, elapsed = recognizer.recognize_with_timing(
                    image, preprocess=preprocess
                )
                results[engine] = {
                    "info": info,
                    "time_ms": round(elapsed, 2),
                    "success": True,
                    "error": None
                }
            except Exception as e:
                results[engine] = {
                    "info": None,
                    "time_ms": 0,
                    "success": False,
                    "error": str(e)
                }
                
        return results
    
    def print_comparison(self, results: Dict):
        """打印比较结果"""
        print("\n" + "=" * 80)
        print("OCR引擎比较结果")
        print("=" * 80)
        
        for engine, result in results.items():
            print(f"\n【{engine}】")
            print("-" * 40)
            
            if result["success"]:
                info = result["info"]
                print(f"耗时: {result['time_ms']}ms")
                print(f"置信度: {info.confidence:.3f}")
                print(f"识别结果:")
                for key, value in info.to_dict().items():
                    if value and key not in ["面", "置信度"]:
                        print(f"  {key}: {value}")
            else:
                print(f"识别失败: {result['error']}")
                
        print("\n" + "=" * 80)
