"""
图像预处理工具
用于身份证图像的预处理，提高OCR识别效果
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Union
from pathlib import Path


class ImageProcessor:
    """图像预处理器"""
    
    def __init__(self, target_width: int = 1280):
        self.target_width = target_width
    
    @staticmethod
    def is_pdf(file_path: Union[str, Path]) -> bool:
        """检查文件是否为PDF"""
        file_path = Path(file_path)
        return file_path.suffix.lower() == '.pdf'
    
    @staticmethod
    def pdf_to_images(pdf_path: Union[str, Path], 
                      dpi: int = 300,
                      max_pages: Optional[int] = None,
                      verbose: bool = True) -> List[np.ndarray]:
        """
        将PDF转换为图像列表
        
        Args:
            pdf_path: PDF文件路径
            dpi: 图像分辨率，默认300 DPI
            max_pages: 最多转换的页数，None表示全部转换
            verbose: 是否显示进度信息，默认True
            
        Returns:
            图像列表（BGR格式的numpy数组）
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "需要安装PyMuPDF库来处理PDF文件。\n"
                "请运行: pip install PyMuPDF"
            )
        
        pdf_path = str(pdf_path)
        images = []
        
        try:
            # 打开PDF文件
            if verbose:
                print(f"    正在打开PDF文件...")
            
            pdf_document = fitz.open(pdf_path)
            
            if verbose:
                print(f"    PDF文件已打开")
            
            total_pages = len(pdf_document)
            
            if verbose:
                print(f"    检测到{total_pages}页")
            
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            if verbose and total_pages > 1:
                print(f"    PDF共{total_pages}页，开始转换...")
            
            # 计算缩放因子 (dpi / 72，因为PDF默认是72 DPI)
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            
            if verbose:
                print(f"    开始渲染页面 (DPI={dpi})...")
            
            # 转换每一页
            for page_num in range(total_pages):
                if verbose and total_pages > 3 and page_num % 5 == 0:
                    print(f"    转换进度: {page_num + 1}/{total_pages}")
                
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=mat)
                
                # 将pixmap转换为numpy数组
                img_data = np.frombuffer(pix.samples, dtype=np.uint8)
                img_data = img_data.reshape(pix.height, pix.width, pix.n)
                
                # 转换颜色格式
                if pix.n == 4:  # RGBA
                    img = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:  # RGB
                    img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
                else:  # 灰度
                    img = cv2.cvtColor(img_data, cv2.COLOR_GRAY2BGR)
                
                images.append(img)
            
            if verbose:
                if total_pages == 1:
                    print(f"    PDF转换完成 ({images[0].shape[1]}x{images[0].shape[0]})")
                else:
                    print(f"    PDF转换完成: {len(images)}页")
            
            pdf_document.close()
            return images
            
        except Exception as e:
            raise RuntimeError(f"PDF转换失败: {e}")
    
    @staticmethod
    def load_image(file_path: Union[str, Path]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        加载图像或PDF文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            - 如果是图像文件: 返回numpy数组
            - 如果是PDF文件: 返回图像列表
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检查是否为PDF
        if ImageProcessor.is_pdf(file_path):
            return ImageProcessor.pdf_to_images(file_path)
        
        # 加载普通图像
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError(f"无法加载图像: {file_path}")
        
        return img
        
    def preprocess(self, image: np.ndarray, 
                   denoise: bool = True,
                   enhance_contrast: bool = True,
                   deskew: bool = True) -> np.ndarray:
        """
        完整的预处理流程
        
        Args:
            image: 输入图像
            denoise: 是否去噪
            enhance_contrast: 是否增强对比度
            deskew: 是否校正倾斜
            
        Returns:
            预处理后的图像
        """
        result = image.copy()
        
        # 1. 调整大小
        result = self.resize(result)
        
        # 2. 去噪
        if denoise:
            result = self.denoise(result)
            
        # 3. 增强对比度
        if enhance_contrast:
            result = self.enhance_contrast(result)
            
        # 4. 校正倾斜
        if deskew:
            result = self.deskew(result)
            
        return result
    
    def resize(self, image: np.ndarray, 
               target_width: Optional[int] = None) -> np.ndarray:
        """调整图像大小"""
        target_width = target_width or self.target_width
        
        h, w = image.shape[:2]
        if w > target_width:
            ratio = target_width / w
            new_h = int(h * ratio)
            image = cv2.resize(image, (target_width, new_h), 
                              interpolation=cv2.INTER_AREA)
        return image
    
    @staticmethod
    def resize_for_ocr(image: np.ndarray, max_height: int = 1080, max_width: int = 1920) -> Tuple[np.ndarray, bool]:
        """
        为OCR识别调整图片尺寸，避免大尺寸图片导致OCR卡顿
        
        如果图片尺寸超过指定的最大值（默认1080p），将按比例缩小
        
        Args:
            image: 输入图像
            max_height: 最大高度（默认1080）
            max_width: 最大宽度（默认1920）
            
        Returns:
            (调整后的图像, 是否进行了缩放)
        """
        h, w = image.shape[:2]
        
        # 检查是否需要缩放
        if h <= max_height and w <= max_width:
            return image, False
        
        # 计算缩放比例（取最小的比例以确保图片不超过限制）
        scale_h = max_height / h if h > max_height else 1.0
        scale_w = max_width / w if w > max_width else 1.0
        scale = min(scale_h, scale_w)
        
        # 计算新尺寸
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 使用高质量插值方法缩小图片
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return resized, True
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """去噪处理"""
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """增强对比度 (CLAHE)"""
        if len(image.shape) == 3:
            # 转换到LAB颜色空间
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # 对L通道应用CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # 合并通道
            lab = cv2.merge([l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    def deskew(self, image: np.ndarray) -> np.ndarray:
        """校正图像倾斜"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # 霍夫变换检测直线
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
        
        if lines is None:
            return image
            
        # 计算角度
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            if -45 < angle < 45:  # 只考虑小角度倾斜
                angles.append(angle)
                
        if not angles:
            return image
            
        # 计算中位数角度
        median_angle = np.median(angles)
        
        if abs(median_angle) < 0.5:  # 角度太小不需要校正
            return image
            
        # 旋转图像
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def binarize(self, image: np.ndarray, 
                 method: str = "adaptive") -> np.ndarray:
        """
        二值化处理
        
        Args:
            image: 输入图像
            method: 'adaptive' 或 'otsu'
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        if method == "adaptive":
            return cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        else:  # otsu
            _, binary = cv2.threshold(gray, 0, 255, 
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
    
    def detect_id_card_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        检测并裁剪身份证区域
        
        Returns:
            裁剪后的身份证图像，如果未检测到返回None
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 75, 200)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # 按面积排序
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        for contour in contours[:5]:  # 只检查最大的5个轮廓
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # 身份证是矩形，应该有4个角点
            if len(approx) == 4:
                # 检查是否是合理的矩形比例（身份证比例约为 1.58:1）
                x, y, w, h = cv2.boundingRect(approx)
                ratio = w / h if h > 0 else 0
                
                if 1.4 < ratio < 1.8:  # 身份证的宽高比范围
                    # 透视变换
                    return self._four_point_transform(image, approx.reshape(4, 2))
                    
        return None
    
    def _four_point_transform(self, image: np.ndarray, 
                               pts: np.ndarray) -> np.ndarray:
        """四点透视变换"""
        # 排序点：左上，右上，右下，左下
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        
        # 计算新图像的宽度和高度
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # 目标点
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")
        
        # 透视变换
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """将四个点按照 左上、右上、右下、左下 的顺序排列"""
        rect = np.zeros((4, 2), dtype="float32")
        
        # 左上角的点x+y最小，右下角的点x+y最大
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # 右上角x-y最大，左下角x-y最小
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
