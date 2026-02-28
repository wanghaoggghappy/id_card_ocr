"""
身份证OCR识别系统 - 主程序
支持多种OCR引擎的比较和使用
支持图像和PDF文件输入
"""

import argparse
import cv2
from pathlib import Path
import sys

from id_card_recognizer import IDCardRecognizer, MultiEngineComparator
from utils.image_processor import ImageProcessor


def single_engine_demo(image_path: str, engine: str = "paddleocr", pdf_page: int = 0):
    """单引擎演示"""
    file_path = Path(image_path)
    
    # 检查是否是PDF文件
    if ImageProcessor.is_pdf(file_path):
        print(f"\n检测到PDF文件，使用 {engine} 引擎识别...")
        if pdf_page == -1:
            print("识别模式: 自动选择最佳结果（所有页面）")
        else:
            print(f"识别模式: 第 {pdf_page + 1} 页")
    else:
        print(f"\n使用 {engine} 引擎识别身份证...")
    
    print("-" * 50)
    
    recognizer = IDCardRecognizer(engine=engine)
    
    try:
        result, elapsed = recognizer.recognize_with_timing(image_path, pdf_page=pdf_page)
        
        print(f"识别耗时: {elapsed:.2f}ms")
        print(f"检测到: {result.side}")
        print(f"置信度: {result.confidence:.3f}")
        print("\n识别结果:")
        
        for key, value in result.to_dict().items():
            if value and key not in ["面", "置信度"]:
                print(f"  {key}: {value}")
                
        # 验证身份证号
        if result.id_number:
            from utils.id_card_parser import IDCardParser
            parser = IDCardParser()
            try:
                is_valid = parser.validate_id_number(result.id_number)
                print(f"\n身份证号校验: {'✓ 有效' if is_valid else '✗ 无效'}")
            except Exception as e:
                print(f"\n身份证号校验: ✗ 无法验证 ({e})")
            
    except Exception as e:
        import traceback
        print(f"识别失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()


def multi_engine_demo(image_path: str, engines: list = None):
    """多引擎比较演示"""
    print("\n多引擎比较模式")
    print("=" * 50)
    
    # 默认比较这些引擎
    if engines is None:
        engines = ["paddleocr", "rapidocr", "easyocr"]
    
    comparator = MultiEngineComparator(engines=engines)
    results = comparator.compare(image_path)
    comparator.print_comparison(results)
    
    # 找出最佳结果
    best_engine = None
    best_confidence = 0
    
    for engine, result in results.items():
        if result["success"] and result["info"].confidence > best_confidence:
            best_confidence = result["info"].confidence
            best_engine = engine
            
    if best_engine:
        print(f"\n推荐引擎: {best_engine} (置信度: {best_confidence:.3f})")


def visualize_result(image_path: str, engine: str = "paddleocr"):
    """可视化识别结果"""
    recognizer = IDCardRecognizer(engine=engine)
    
    # 加载图像
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法加载图像: {image_path}")
        return
        
    # 获取OCR结果
    ocr_results = recognizer.ocr_engine.recognize(image)
    
    # 绘制检测框
    for result in ocr_results:
        if result.box:
            pts = result.box
            for i in range(4):
                cv2.line(image, 
                        tuple(pts[i]), 
                        tuple(pts[(i + 1) % 4]),
                        (0, 255, 0), 2)
            # 在框上方显示文字
            cv2.putText(image, 
                       f"{result.text[:10]}...", 
                       (pts[0][0], pts[0][1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 0, 255), 1)
    
    # 保存结果
    output_path = Path(image_path).stem + "_result.jpg"
    cv2.imwrite(output_path, image)
    print(f"可视化结果已保存到: {output_path}")
    
    # 显示图像
    cv2.imshow("OCR Result", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="身份证OCR识别系统 - 支持图像和PDF文件输入"
    )
    parser.add_argument("image", nargs="?", help="身份证图像或PDF文件路径")
    parser.add_argument("-e", "--engine", default="paddleocr",
                       choices=["paddleocr", "easyocr", "tesseract", "rapidocr", "cnocr", "deepseek", "deepseek-gguf"],
                       help="OCR引擎 (默认: paddleocr)")
    parser.add_argument("-c", "--compare", action="store_true",
                       help="多引擎比较模式")
    parser.add_argument("-v", "--visualize", action="store_true",
                       help="可视化识别结果")
    parser.add_argument("--list-engines", action="store_true",
                       help="列出所有可用引擎")
    parser.add_argument("--gpu", action="store_true",
                       help="使用GPU加速")
    parser.add_argument("--pdf-page", type=int, default=0,
                       help="PDF页码(从0开始)，-1表示识别所有页并返回最佳结果 (默认: 0)")
    
    args = parser.parse_args()
    
    # 列出引擎
    if args.list_engines:
        print("可用的OCR引擎:")
        for engine in IDCardRecognizer.available_engines():
            print(f"  - {engine}")
        return
    
    # 检查图像参数
    if not args.image:
        print("请提供身份证图像或PDF文件路径")
        print("使用 --help 查看帮助")
        
        # 提示演示
        print("\n示例用法:")
        print("  python main.py id_card.jpg                      # 使用默认引擎识别图像")
        print("  python main.py id_card.pdf                      # 识别PDF文件的第一页")
        print("  python main.py id_card.pdf --pdf-page -1        # 识别PDF所有页，返回最佳结果")
        print("  python main.py id_card.jpg -e easyocr           # 使用EasyOCR引擎")
        print("  python main.py id_card.jpg -c                   # 多引擎比较")
        print("  python main.py id_card.jpg -v                   # 可视化结果")
        return
    
    # 检查文件是否存在
    if not Path(args.image).exists():
        print(f"文件不存在: {args.image}")
        return
    
    # 执行相应操作
    if args.compare:
        multi_engine_demo(args.image)
    elif args.visualize:
        visualize_result(args.image, args.engine)
    else:
        single_engine_demo(args.image, args.engine, args.pdf_page)


if __name__ == "__main__":
    main()
