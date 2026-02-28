"""
PaddleOCR引擎
百度开源的OCR系统，中文识别效果最佳
优点：
- 中文识别准确率高
- 支持检测+识别+方向分类
- 有丰富的预训练模型
- 支持自定义训练
缺点：
- 依赖较重
- Mac M系列芯片需要特殊处理
"""

import numpy as np
from typing import List
from .base_engine import BaseOCREngine, OCRResult


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR引擎"""
    
    def __init__(self, use_gpu: bool = False, lang: str = "ch", 
                 use_angle_cls: bool = True, **kwargs):
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "paddleocr"
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self._init_model()
        
    def _init_model(self):
        """初始化PaddleOCR模型"""
        try:
            from paddleocr import PaddleOCR
            
            # 配置参数
            # 注意: PaddleOCR 2.7+ 版本GPU通过安装paddlepaddle-gpu来启用，不再使用use_gpu参数
            kwargs = {
                'use_angle_cls': self.use_angle_cls,
                'lang': self.lang,
            }
            
            # 添加可选的模型路径
            if self.config.get('det_model_dir'):
                kwargs['det_model_dir'] = self.config.get('det_model_dir')
            if self.config.get('rec_model_dir'):
                kwargs['rec_model_dir'] = self.config.get('rec_model_dir')
            if self.config.get('cls_model_dir'):
                kwargs['cls_model_dir'] = self.config.get('cls_model_dir')
            
            self._model = PaddleOCR(**kwargs)
            gpu_status = "GPU" if self.use_gpu else "CPU"
            print(f"✓ PaddleOCR 初始化成功 (模式: {gpu_status})")
            
        except ImportError:
            raise ImportError(
                "请安装PaddleOCR: pip install paddlepaddle paddleocr"
            )
        except Exception as e:
            raise RuntimeError(f"PaddleOCR初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None:
            self._init_model()
            
        results = []
        
        # PaddleOCR返回格式: [[[box], (text, confidence)], ...]
        # 注意：cls参数在初始化时设置(use_angle_cls)，ocr()调用时不需要传递
        ocr_result = self._model.ocr(image)
        
        print(f"\n[调试] PaddleOCR原始返回结果类型: {type(ocr_result)}")
        print(f"[调试] PaddleOCR原始返回结果长度: {len(ocr_result) if ocr_result else 0}")
        
        if ocr_result is None or len(ocr_result) == 0:
            print("[调试] OCR结果为空，返回空列表")
            return results
        
        # 检查是否是PaddleX的OCRResult对象
        first_element = ocr_result[0] if len(ocr_result) > 0 else None
        print(f"[调试] 第一个元素类型: {type(first_element)}")
        
        # 如果是PaddleX的OCRResult对象
        if first_element is not None and hasattr(first_element, '__class__') and 'OCRResult' in str(type(first_element)):
            print("[调试] 检测到PaddleX OCRResult对象，使用特殊处理")
            return self._parse_paddlex_result(first_element)
        
        # 标准PaddleOCR格式
        if len(ocr_result) > 0 and ocr_result[0]:
            print(f"[调试] 第一个元素内容(前200字符): {str(ocr_result[0])[:200]}")
        
        return self._parse_standard_result(ocr_result)
    
    def _parse_paddlex_result(self, ocr_result) -> List[OCRResult]:
        """解析PaddleX的OCRResult对象"""
        results = []
        
        try:
            # PaddleX OCRResult是一个类字典对象
            print(f"[调试-PaddleX] OCRResult keys: {list(ocr_result.keys())}")
            
            # 尝试打印完整内容
            if hasattr(ocr_result, 'json'):
                try:
                    import json
                    json_str = ocr_result.json
                    print(f"[调试-PaddleX] JSON内容: {json_str[:500]}")
                    json_data = json.loads(json_str) if isinstance(json_str, str) else json_str
                except:
                    json_data = None
            
            # 尝试直接访问字典键
            for key in ocr_result.keys():
                print(f"[调试-PaddleX] {key}: {type(ocr_result[key])}")
            
            # 尝试多种可能的键名
            possible_keys = [
                ('dt_polys', 'rec_text', 'rec_score'),  # 标准PaddleOCR
                ('boxes', 'texts', 'scores'),  # 可能的变体
                ('det_boxes', 'rec_texts', 'rec_scores'),  # 另一种变体
            ]
            
            boxes = None
            texts = None
            scores = None
            
            # 尝试从字典中获取数据
            for box_key, text_key, score_key in possible_keys:
                if box_key in ocr_result and text_key in ocr_result:
                    boxes = ocr_result[box_key]
                    texts = ocr_result[text_key]
                    scores = ocr_result.get(score_key, [])
                    print(f"[调试-PaddleX] 使用键: {box_key}, {text_key}, {score_key}")
                    break
            
            # 如果还没找到，尝试遍历所有值
            if texts is None:
                for key, value in ocr_result.items():
                    print(f"[调试-PaddleX] 检查 {key}: type={type(value)}, len={len(value) if hasattr(value, '__len__') else 'N/A'}")
                    if isinstance(value, list) and len(value) > 0:
                        # 检查是否是文本列表
                        if isinstance(value[0], str):
                            texts = value
                            print(f"[调试-PaddleX] 找到文本列表: {key}, 示例: {value[0] if value else 'empty'}")
                        # 检查是否是坐标列表
                        elif isinstance(value[0], (list, tuple)) and len(value[0]) > 0:
                            if isinstance(value[0][0], (int, float)):
                                scores = value
                            else:
                                boxes = value
                                print(f"[调试-PaddleX] 找到坐标列表: {key}")
            
            if texts:
                print(f"[调试-PaddleX] 检测到 {len(texts)} 个文本")
                
                for i in range(len(texts)):
                    text = texts[i] if i < len(texts) else ""
                    score = float(scores[i]) if scores and i < len(scores) else 0.9
                    box = boxes[i] if boxes and i < len(boxes) else None
                    
                    print(f"[调试-PaddleX] 文本{i}: '{text}' (置信度: {score:.3f})")
                    
                    # 转换box格式
                    box_coords = None
                    if box is not None:
                        try:
                            if isinstance(box[0], (list, tuple)):
                                box_coords = [[int(float(p[0])), int(float(p[1]))] for p in box]
                            else:
                                # 可能是扁平列表 [x1,y1,x2,y2,...]
                                box_coords = [[int(float(box[j])), int(float(box[j+1]))] for j in range(0, len(box), 2)]
                        except Exception as e:
                            print(f"[警告] 转换坐标失败: {e}")
                    
                    results.append(OCRResult(
                        text=text,
                        confidence=score,
                        box=box_coords
                    ))
            else:
                print(f"[警告] 未找到文本数据")
                
        except Exception as e:
            print(f"[错误] 解析PaddleX结果失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[调试-PaddleX] 最终返回 {len(results)} 个识别结果")
        return results
    
    def _parse_standard_result(self, ocr_result) -> List[OCRResult]:
        """解析标准PaddleOCR结果"""
        results = []
        
        # 处理结果
        print(f"\n[调试-标准] 开始处理OCR结果，共 {len(ocr_result)} 行")
        for line_idx, line in enumerate(ocr_result):
            if line is None:
                print(f"[调试] 第 {line_idx} 行为None，跳过")
                continue
            print(f"[调试] 处理第 {line_idx} 行，包含 {len(line) if line else 0} 个项目")
            for item_idx, item in enumerate(line):
                if item is None or len(item) < 2:
                    print(f"[调试] 第 {line_idx} 行第 {item_idx} 项无效: {item}")
                    continue
                
                try:
                    box = item[0]
                    text_info = item[1]
                    print(f"[调试] 第 {line_idx} 行第 {item_idx} 项: box类型={type(box)}, text_info类型={type(text_info)}")
                    
                    if isinstance(text_info, tuple) and len(text_info) >= 2:
                        text = text_info[0]
                        confidence = float(text_info[1])
                    else:
                        text = str(text_info)
                        confidence = 0.0
                    
                    # 转换box格式 - 添加类型检查和错误处理
                    box_coords = []
                    if isinstance(box, (list, tuple)) and len(box) > 0:
                        for p in box:
                            if isinstance(p, (list, tuple)) and len(p) >= 2:
                                try:
                                    x = int(float(p[0]))
                                    y = int(float(p[1]))
                                    box_coords.append([x, y])
                                except (ValueError, TypeError):
                                    # 如果转换失败，跳过这个点
                                    continue
                    
                    # 只有当成功提取了坐标时才添加结果
                    if box_coords or text:  # 至少要有文本或坐标
                        print(f"[调试] 成功提取: text='{text}', confidence={confidence:.3f}, box点数={len(box_coords)}")
                        results.append(OCRResult(
                            text=text,
                            confidence=confidence,
                            box=box_coords if box_coords else None
                        ))
                    else:
                        print(f"[调试] 跳过空结果: box_coords={len(box_coords)}, text='{text}'")
                        
                except Exception as e:
                    # 如果某个结果处理失败，打印警告但继续处理其他结果
                    print(f"[警告] 处理OCR结果时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        print(f"\n[调试] 最终返回 {len(results)} 个识别结果")
        return results
