"""
车辆文档处理器
处理压缩包中的车辆相关文档：登记证、发票、行驶证
"""

import os
import zipfile
import shutil
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import tempfile

from id_card_recognizer import IDCardRecognizer
from vehicle_info_extractor import VehicleInfoExtractor, VehicleInfo
from utils.image_processor import ImageProcessor


@dataclass
class DocumentFile:
    """文档文件信息"""
    file_path: str
    doc_type: str  # registration/registration_transfer/invoice/license/unknown
    confidence: float
    ocr_text: str = ""
    vehicle_info: Optional[VehicleInfo] = None


class VehicleDocumentClassifier:
    """车辆文档分类器"""
    
    # 文档类型关键词
    KEYWORDS = {
        'registration': ['注册登记', '机动车登记证书'],
        'registration_transfer': ['登记栏', '转移登记'],
        'invoice': ['发票', '机动车销售统一发票', '增值税发票', '购车发票'],
        'license': ['行驶证', '机动车行驶证', '行驶证正页'],
    }
    
    def classify(self, text: str) -> Tuple[str, float]:
        """
        根据OCR文本分类文档类型
        
        Args:
            text: OCR识别的文本
            
        Returns:
            (文档类型, 置信度)
        """
        text_lower = text.lower()
        scores = {}
        
        # 优先检查登记证尾页（登记栏）
        if '登记栏' in text:
            scores['registration_transfer'] = 4  # 高优先级
        elif any(kw in text for kw in ['转移登记', '现机动车所有人']):
            scores['registration_transfer'] = 3
        
        # 检查注册登记页
        if '注册登记' in text:
            scores['registration'] = 4
        elif '机动车登记证书' in text:
            scores['registration'] = 3
        
        # 检查其他类型
        for doc_type, keywords in self.KEYWORDS.items():
            if doc_type in scores:  # 已经评分的跳过
                continue
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 2
                elif any(char in text for char in keyword):
                    score += 0.5
            
            if score > 0:
                scores[doc_type] = score
        
        if not scores or max(scores.values()) == 0:
            return 'unknown', 0.0
        
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type] / 4.0, 1.0)  # 归一化到0-1
        
        return best_type, confidence
    
    def classify_by_filename(self, filename: str) -> Optional[str]:
        """根据文件名猜测类型"""
        filename_lower = filename.lower()
        
        if any(k in filename_lower for k in ['登记栏', '登记尾', 'transfer']):
            return 'registration_transfer'
        elif any(k in filename_lower for k in ['登记', 'registration', 'djz']):
            return 'registration'
        elif any(k in filename_lower for k in ['发票', 'invoice', 'fp']):
            return 'invoice'
        elif any(k in filename_lower for k in ['行驶', 'license', 'xsz']):
            return 'license'
        
        return None


class VehicleDocumentProcessor:
    """车辆文档处理器"""
    
    def __init__(self, ocr_engine: str = "paddleocr"):
        """
        初始化处理器
        
        Args:
            ocr_engine: OCR引擎名称
        """
        self.ocr_recognizer = IDCardRecognizer(engine=ocr_engine)
        self.classifier = VehicleDocumentClassifier()
        self.info_extractor = VehicleInfoExtractor()
        self.image_processor = ImageProcessor()
    
    def extract_archive(self, archive_path: str, extract_to: Optional[str] = None) -> str:
        """
        解压压缩文件
        
        Args:
            archive_path: 压缩文件路径
            extract_to: 解压目标目录，None则使用临时目录
            
        Returns:
            解压后的目录路径
        """
        archive_path = Path(archive_path)
        
        if extract_to is None:
            extract_to = tempfile.mkdtemp(prefix='vehicle_docs_')
        else:
            extract_to = str(extract_to)
            os.makedirs(extract_to, exist_ok=True)
        
        print(f"解压文件: {archive_path.name}")
        print(f"目标目录: {extract_to}")
        
        try:
            if archive_path.suffix.lower() in ['.zip']:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_path.suffix.lower() in ['.rar']:
                # 需要安装 rarfile 和 unrar
                try:
                    import rarfile
                    with rarfile.RarFile(archive_path, 'r') as rar_ref:
                        rar_ref.extractall(extract_to)
                except ImportError:
                    raise ImportError(
                        "处理RAR文件需要安装 rarfile 和 unrar\n"
                        "pip install rarfile\n"
                        "并安装 unrar: https://www.rarlab.com/rar_add.htm"
                    )
            else:
                raise ValueError(f"不支持的压缩格式: {archive_path.suffix}")
            
            print(f"✓ 解压完成")
            return extract_to
            
        except Exception as e:
            raise RuntimeError(f"解压失败: {e}")
    
    def find_image_files(self, directory: str) -> List[str]:
        """
        查找目录中的所有图像和PDF文件
        
        Args:
            directory: 目录路径
            
        Returns:
            图像文件路径列表
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'}
        image_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in image_extensions:
                    image_files.append(str(file_path))
        
        print(f"找到 {len(image_files)} 个图像/PDF文件")
        return image_files
    
    def process_document(self, file_path: str) -> DocumentFile:
        """
        处理单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            DocumentFile对象
        """
        print(f"\n处理文件: {Path(file_path).name}")
        
        # 先根据文件名猜测类型
        filename_type = self.classifier.classify_by_filename(Path(file_path).name)
        if filename_type:
            print(f"  根据文件名推测: {filename_type}")
        
        try:
            # 读取并预处理图片
            if not ImageProcessor.is_pdf(file_path):
                img = cv2.imread(file_path)
                if img is not None:
                    # 检查图片尺寸，如果过大则缩小
                    h, w = img.shape[:2]
                    img_resized, was_resized = ImageProcessor.resize_for_ocr(img)
                    
                    if was_resized:
                        print(f"  图片尺寸: {w}x{h} → {img_resized.shape[1]}x{img_resized.shape[0]} (自动缩放以优化OCR)")
                    
                    # OCR识别
                    print(f"  OCR识别中...")
                    ocr_results = self.ocr_recognizer.ocr_engine.recognize(img_resized)
                    ocr_text = '\n'.join([r.text for r in ocr_results])
                else:
                    print(f"  OCR识别中...")
                    # 使用OCR引擎直接识别获取原始文本
                    ocr_results = self.ocr_recognizer.ocr_engine.recognize(file_path)
                    ocr_text = '\n'.join([r.text for r in ocr_results])
            else:
                # PDF情况
                print(f"  识别PDF...")
                try:
                    # 检查文件是否存在和可读
                    if not Path(file_path).exists():
                        raise FileNotFoundError(f"PDF文件不存在: {file_path}")
                    
                    file_size = Path(file_path).stat().st_size
                    print(f"    文件大小: {file_size / 1024:.1f} KB")
                    
                    # 转换PDF为图像（只处理第一页，使用较低DPI以提高性能）
                    pdf_images = ImageProcessor.pdf_to_images(file_path, dpi=150, max_pages=1, verbose=True)
                    
                    if pdf_images:
                        img = pdf_images[0]  # 使用第一页
                        
                        # 调整图像尺寸以避免OCR卡顿
                        img, was_resized = ImageProcessor.resize_for_ocr(img, max_height=1080, max_width=1920)
                        if was_resized:
                            print(f"    图像已缩放至: {img.shape[1]}x{img.shape[0]}")
                        else:
                            print(f"    图像尺寸: {img.shape[1]}x{img.shape[0]}")
                        
                        # 使用OCR引擎直接识别获取原始文本
                        ocr_results = self.ocr_recognizer.ocr_engine.recognize(img)
                        ocr_text = '\n'.join([r.text for r in ocr_results])
                    else:
                        print(f"    警告: PDF转换失败，未获取到图像")
                        ocr_results = []
                        ocr_text = ""
                    img = None
                    
                except Exception as pdf_error:
                    print(f"    PDF处理失败: {pdf_error}")
                    ocr_results = []
                    ocr_text = ""
                    img = None
            
            print(f"  OCR文本长度: {len(ocr_text)} 字符")
            
            # 分类文档类型
            doc_type, confidence = self.classifier.classify(ocr_text)
            
            # 优先使用OCR分类，如果不确定则使用文件名
            if confidence < 0.3 and filename_type:
                doc_type = filename_type
                confidence = 0.5
            
            print(f"  文档类型: {doc_type} (置信度: {confidence:.2f})")
            
            # 提取车辆信息
            if 'ocr_results' in locals():
                ocr_results_list = [{'text': r.text} for r in ocr_results]
            else:
                ocr_results_list = [{'text': ocr_text}]
            
            from vehicle_info_extractor import extract_vehicle_info
            vehicle_info = extract_vehicle_info(ocr_results_list, doc_type)
            
            if vehicle_info.vin:
                print(f"  → 车架号: {vehicle_info.vin}")
            if vehicle_info.owner_name:
                print(f"  → 车主: {vehicle_info.owner_name}")
            if vehicle_info.invoice_amount:
                print(f"  → 金额: {vehicle_info.invoice_amount}")
            
            return DocumentFile(
                file_path=file_path,
                doc_type=doc_type,
                confidence=confidence,
                ocr_text=ocr_text,
                vehicle_info=vehicle_info
            )
            
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            return DocumentFile(
                file_path=file_path,
                doc_type='unknown',
                confidence=0.0,
                vehicle_info=VehicleInfo()
            )
    
    def process_folder(self, folder_path: str) -> List[DocumentFile]:
        """
        处理单个文件夹中的文档
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            DocumentFile列表（合并后的，去除重复页）
        """
        # 查找图像文件（仅当前文件夹，不递归）
        image_files = []
        folder = Path(folder_path)
        
        for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']:
            image_files.extend(folder.glob(f'*{ext}'))
            image_files.extend(folder.glob(f'*{ext.upper()}'))
        
        # 按文件名排序，确保同类型文件相邻
        image_files = sorted([str(f) for f in image_files])
        
        if not image_files:
            return []
        
        # 处理每个文件
        documents = []
        for i, file_path in enumerate(image_files, 1):
            print(f"\n  [{i}/{len(image_files)}] ", end='')
            doc = self.process_document(file_path)
            documents.append(doc)
        
        # 去重：合并同一类型的连续文档（通常是多页扫描）
        merged_documents = self._merge_duplicate_documents(documents)
        
        return merged_documents
    
    def _merge_duplicate_documents(self, documents: List[DocumentFile]) -> List[DocumentFile]:
        """
        合并重复文档（登记证和登记证尾页不合并，分别处理）
        
        Args:
            documents: 原始文档列表
            
        Returns:
            去重后的文档列表
        """
        if not documents:
            return []
        
        merged = []
        current_type = None
        current_vin = None
        
        for doc in documents:
            # 如果是未知类型或置信度很低，直接添加
            if doc.doc_type == 'unknown' or doc.confidence < 0.3:
                merged.append(doc)
                current_type = None
                current_vin = None
                continue
            
            # 获取当前文档的类型和车架号
            doc_type = doc.doc_type
            doc_vin = doc.vehicle_info.vin if doc.vehicle_info else None
            
            # 判断是否与上一个文档重复
            is_duplicate = False
            
            if current_type == doc_type:
                # 同类型文档
                if doc_type in ['registration', 'license']:
                    # 登记证和行驶证：如果车架号相同或都为空，认为是重复页
                    if doc_vin and current_vin:
                        # 两者都有车架号，比较相似度（允许1-2个字符差异，可能是OCR错误）
                        if self._are_vins_similar(doc_vin, current_vin):
                            is_duplicate = True
                            print(f"    [检测到重复页，跳过: {Path(doc.file_path).name}]")
                    elif not doc_vin and not current_vin:
                        # 两者都没有车架号，可能是封面页，认为是重复
                        is_duplicate = True
                        print(f"    [检测到重复页（无车架号），跳过: {Path(doc.file_path).name}]")
                elif doc_type == 'registration_transfer':
                    # 登记证尾页：如果连续出现，认为是重复
                    is_duplicate = True
                    print(f"    [检测到重复登记证尾页，跳过: {Path(doc.file_path).name}]")
            
            if not is_duplicate:
                merged.append(doc)
                current_type = doc_type
                current_vin = doc_vin
        
        if len(merged) < len(documents):
            print(f"\n  ℹ 合并重复文档: {len(documents)} → {len(merged)}")
        
        return merged
    
    def _are_vins_similar(self, vin1: str, vin2: str, max_diff: int = 2) -> bool:
        """
        判断两个车架号是否相似（允许少量OCR错误）
        
        Args:
            vin1: 车架号1
            vin2: 车架号2
            max_diff: 允许的最大差异字符数
            
        Returns:
            是否相似
        """
        if not vin1 or not vin2:
            return False
        
        if len(vin1) != len(vin2):
            return False
        
        # 计算不同字符的数量
        diff_count = sum(c1 != c2 for c1, c2 in zip(vin1, vin2))
        
        return diff_count <= max_diff
    
    def process_archive(self, archive_path: str) -> List[DocumentFile]:
        """
        处理压缩包（简单模式，所有文件在一起）
        
        Args:
            archive_path: 压缩包路径
            
        Returns:
            DocumentFile列表
        """
        print("=" * 60)
        print(f"开始处理压缩包: {Path(archive_path).name}")
        print("=" * 60)
        
        # 解压
        extract_dir = self.extract_archive(archive_path)
        
        try:
            # 查找图像文件
            image_files = self.find_image_files(extract_dir)
            
            if not image_files:
                print("警告: 未找到图像文件")
                return []
            
            # 处理每个文件
            documents = []
            for i, file_path in enumerate(image_files, 1):
                print(f"\n[{i}/{len(image_files)}] ", end='')
                doc = self.process_document(file_path)
                documents.append(doc)
            
            print("\n" + "=" * 60)
            print(f"处理完成，共 {len(documents)} 个文档")
            print("=" * 60)
            
            return documents
            
        finally:
            # 清理临时目录
            if extract_dir.startswith(tempfile.gettempdir()):
                shutil.rmtree(extract_dir, ignore_errors=True)
    
    def get_type_name_cn(self, doc_type: str) -> str:
        """获取文档类型的中文名称"""
        type_names = {
            'registration': '登记证',
            'invoice': '发票',
            'license': '行驶证',
            'unknown': '未知'
        }
        return type_names.get(doc_type, '未知')
