"""
DeepSeek-OCR GGUF引擎（通过NexaSDK）
使用GGUF量化模型，适合在Mac和CPU环境运行
优点：
- 可在CPU上高效运行（Mac友好）
- 模型量化，体积小（1.65GB - 5.87GB）
- 不需要GPU
- 通过NexaSDK简单易用
- 支持多种量化级别（4-bit到16-bit）
缺点：
- 需要安装NexaSDK
- 速度比GPU版本慢

推荐量化级别：
- Q4_0: 1.65GB - 最快，略低精度
- Q5_0: 2.02GB - 平衡选择
- Q6_K: 2.61GB - 高精度
- Q8_0: 3.12GB - 接近原始精度

安装：
pip install nexaai
"""

import numpy as np
from typing import List, Optional
import cv2
from pathlib import Path
import tempfile
from .base_engine import BaseOCREngine, OCRResult


class DeepSeekGGUFEngine(BaseOCREngine):
    """DeepSeek-OCR GGUF引擎（NexaSDK）"""
    
    def __init__(self, use_gpu: bool = False,
                 model_path: str = "NexaAI/DeepSeek-OCR-GGUF:Q4_0",
                 **kwargs):
        """
        初始化DeepSeek-OCR GGUF引擎
        
        Args:
            use_gpu: GGUF版本主要为CPU优化，GPU可选
            model_path: 模型路径，格式: "NexaAI/DeepSeek-OCR-GGUF:量化级别"
                       可选量化级别: Q4_0, Q5_0, Q6_K, Q8_0, BF16, F16
        """
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "deepseek-gguf"
        self.model_path = model_path
        self._nexa_model = None
        self._init_model()
        
    def _init_model(self):
        """初始化NexaSDK模型"""
        try:
            # NexaAI SDK 的正确导入方式
            from nexaai import VLM
            import os
            
            # 检查是否为本地路径
            if os.path.exists(self.model_path):
                print(f"正在加载本地 DeepSeek-OCR GGUF 模型: {self.model_path}")
                model_path = self.model_path
            else:
                print(f"正在加载 DeepSeek-OCR GGUF 模型: {self.model_path}")
                print("首次使用会自动下载模型，请稍候...")
                model_path = self.model_path
            
            # 初始化模型
            self._nexa_model = VLM.from_(model=model_path)
            
            print(f"✓ DeepSeek-OCR GGUF 初始化成功")
            print(f"  模型路径: {model_path}")
            print(f"  适合在 Mac/CPU 环境运行")
            
        except ImportError as ie:
            raise ImportError(
                "请安装 NexaSDK:\n"
                "  pip install nexaai\n\n"
                "或访问: https://github.com/NexaAI/nexa-sdk\n\n"
                f"详细错误: {ie}"
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek-OCR GGUF初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._nexa_model is None:
            self._init_model()
        
        results = []
        
        # 保存临时图像文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, image)
        
        try:
            # 使用 Free OCR 模式提取文本
            prompt = "Free OCR."
            
            print(f"[调试-DeepSeek-GGUF] 开始识别，图像: {tmp_path}")
            
            # 使用 NexaAI VLM 的 create 方法进行推理
            # 构建消息格式
            response = self._nexa_model.create(
                messages=[{
                    "role": "user", 
                    "content": [
                        {"type": "image", "image": tmp_path},
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            
            # 解析响应
            if response:
                # 获取生成的文本
                text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                if not text:
                    # 尝试直接获取
                    text = str(response)
                
                print(f"[调试-DeepSeek-GGUF] 原始结果: {text[:200]}")
                
                # 按行分割文本
                lines = text.strip().split('\n')
                for idx, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        print(f"[调试-DeepSeek-GGUF] 第{idx}行: '{line}'")
                        results.append(OCRResult(
                            text=line,
                            confidence=0.95,
                            box=None
                        ))
            
        except Exception as e:
            print(f"[错误] DeepSeek-OCR GGUF识别失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 尝试使用简化的推理方式
            try:
                print("[调试-DeepSeek-GGUF] 尝试使用简化推理...")
                
                # 重新初始化或使用现有实例
                if not hasattr(self._nexa_model, 'model'):
                    self._init_model()
                
                # 构建输入
                image_path = tmp_path
                user_input = f"{image_path} {prompt}"
                
                # 简单的文本生成
                output = self._nexa_model._chat(user_input)
                
                if output:
                    print(f"[调试-DeepSeek-GGUF] 简化推理结果: {output[:200]}")
                    lines = output.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            results.append(OCRResult(
                                text=line,
                                confidence=0.95,
                                box=None
                            ))
                            
            except Exception as e2:
                print(f"[错误] 简化推理也失败: {e2}")
                import traceback
                traceback.print_exc()
        finally:
            # 清理临时文件
            try:
                Path(tmp_path).unlink()
            except:
                pass
        
        print(f"[调试-DeepSeek-GGUF] 最终返回 {len(results)} 个识别结果")
        return results
    
    def recognize_with_grounding(self, image: np.ndarray) -> str:
        """使用grounding模式识别（包含坐标定位）"""
        if self._nexa_model is None:
            self._init_model()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, image)
        
        try:
            prompt = "<|grounding|>Convert the document to markdown."
            
            response = self._nexa_model.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": tmp_path},
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            
            if response:
                text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                if not text:
                    text = str(response)
                return text
            
            return ""
            
        finally:
            try:
                Path(tmp_path).unlink()
            except:
                pass


def get_available_quantizations():
    """获取可用的量化级别"""
    return {
        "Q4_0": {"size": "1.65GB", "desc": "4-bit量化，最快，略低精度"},
        "Q5_0": {"size": "2.02GB", "desc": "5-bit量化，速度和精度平衡"},
        "Q6_K": {"size": "2.61GB", "desc": "6-bit量化，高精度"},
        "Q8_0": {"size": "3.12GB", "desc": "8-bit量化，接近原始精度"},
        "BF16": {"size": "5.87GB", "desc": "BF16精度，最高质量"},
        "F16": {"size": "5.87GB", "desc": "FP16精度，最高质量"},
    }
