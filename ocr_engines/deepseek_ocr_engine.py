"""
DeepSeek-OCR-2引擎
DeepSeek AI开源的视觉语言OCR模型
优点：
- 最新的OCR技术，基于视觉-语言模型
- 支持文档理解和Markdown转换
- 支持grounding（定位）功能
- 动态分辨率支持
- 多语言支持
缺点：
- 模型较大（3B参数）
- 需要较好的GPU支持
- 首次加载较慢

要求：
- torch>=2.6.0
- transformers>=4.46.3
- flash-attn==2.7.3（推荐，用于加速）
- CUDA 11.8+（GPU推荐）
"""

import numpy as np
from typing import List, Optional
import cv2
from pathlib import Path
import tempfile
from .base_engine import BaseOCREngine, OCRResult


class DeepSeekOCREngine(BaseOCREngine):
    """DeepSeek-OCR-2引擎"""
    
    def __init__(self, use_gpu: bool = True, 
                 model_name: str = "deepseek-ai/DeepSeek-OCR-2",
                 use_flash_attn: bool = True,
                 base_size: int = 1024,
                 image_size: int = 768,
                 **kwargs):
        """
        初始化DeepSeek-OCR-2引擎
        
        Args:
            use_gpu: 是否使用GPU（强烈推荐）
            model_name: 模型名称或本地路径
            use_flash_attn: 是否使用Flash Attention加速
            base_size: 基础图像大小
            image_size: 裁剪图像大小
        """
        super().__init__(use_gpu, **kwargs)
        self.engine_name = "deepseek-ocr-2"
        self.model_name = model_name
        self.use_flash_attn = use_flash_attn
        self.base_size = base_size
        self.image_size = image_size
        self._tokenizer = None
        self._init_model()
        
    def _init_model(self):
        """初始化DeepSeek-OCR-2模型"""
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            
            print(f"正在加载 DeepSeek-OCR-2 模型（首次加载需要下载，请耐心等待）...")
            
            # 加载tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            
            # 加载模型
            model_kwargs = {
                'trust_remote_code': True,
                'use_safetensors': True,
            }
            
            # 如果使用Flash Attention
            if self.use_flash_attn and self.use_gpu:
                try:
                    model_kwargs['_attn_implementation'] = 'flash_attention_2'
                except Exception as e:
                    print(f"⚠ Flash Attention不可用，将使用标准注意力机制: {e}")
            
            self._model = AutoModel.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # 设置设备和精度
            if self.use_gpu and torch.cuda.is_available():
                self._model = self._model.eval().cuda().to(torch.bfloat16)
                device = "CUDA"
            else:
                self._model = self._model.eval()
                device = "CPU"
                print("⚠ 注意: DeepSeek-OCR-2在CPU上运行会非常慢，强烈建议使用GPU")
            
            print(f"✓ DeepSeek-OCR-2 初始化成功 (设备: {device})")
            
        except ImportError as e:
            raise ImportError(
                f"请安装必要的依赖:\n"
                f"  pip install torch>=2.6.0 transformers>=4.46.3 tokenizers einops addict easydict\n"
                f"  pip install flash-attn==2.7.3 --no-build-isolation  # 可选，用于加速\n"
                f"错误: {e}"
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek-OCR-2初始化失败: {e}")
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """识别图像中的文字"""
        if self._model is None or self._tokenizer is None:
            self._init_model()
        
        results = []
        
        # DeepSeek-OCR-2需要图像文件路径，所以需要临时保存
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, image)
        
        try:
            # 使用Free OCR模式（只提取文本，不做格式化）
            # 对于身份证识别，这个模式更合适
            prompt = "<image>\nFree OCR. "
            
            # 调用模型推理
            res = self._model.infer(
                self._tokenizer,
                prompt=prompt,
                image_file=tmp_path,
                output_path=None,  # 不保存输出
                base_size=self.base_size,
                image_size=self.image_size,
                crop_mode=True,
                save_results=False
            )
            
            print(f"[调试-DeepSeek] 原始结果: {res[:200] if res else 'None'}")
            
            # 解析结果
            if res:
                # DeepSeek-OCR-2返回的是完整文本
                # 我们需要按行分割
                lines = res.strip().split('\n')
                
                for idx, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        print(f"[调试-DeepSeek] 第{idx}行: '{line}'")
                        results.append(OCRResult(
                            text=line,
                            confidence=0.95,  # DeepSeek不提供置信度，使用固定值
                            box=None  # Free OCR模式不返回坐标
                        ))
            
        except Exception as e:
            print(f"[错误] DeepSeek-OCR-2识别失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理临时文件
            try:
                Path(tmp_path).unlink()
            except:
                pass
        
        print(f"[调试-DeepSeek] 最终返回 {len(results)} 个识别结果")
        return results
    
    def recognize_with_grounding(self, image: np.ndarray) -> dict:
        """
        使用grounding模式识别（包含坐标定位）
        返回Markdown格式的文档和坐标信息
        """
        if self._model is None or self._tokenizer is None:
            self._init_model()
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            cv2.imwrite(tmp_path, image)
        
        try:
            # 使用grounding模式
            prompt = "<image>\n<|grounding|>Convert the document to markdown. "
            
            res = self._model.infer(
                self._tokenizer,
                prompt=prompt,
                image_file=tmp_path,
                output_path=None,
                base_size=self.base_size,
                image_size=self.image_size,
                crop_mode=True,
                save_results=False
            )
            
            return {
                'markdown': res,
                'raw_result': res
            }
            
        finally:
            try:
                Path(tmp_path).unlink()
            except:
                pass
    
    def recognize_to_markdown(self, image: np.ndarray) -> str:
        """
        将图像识别为Markdown格式
        特别适合文档OCR
        """
        result = self.recognize_with_grounding(image)
        return result.get('markdown', '')
