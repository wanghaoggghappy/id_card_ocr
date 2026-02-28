"""
PDF身份证识别示例
演示如何使用系统识别PDF格式的身份证文件
"""

from id_card_recognizer import IDCardRecognizer
from pathlib import Path


def example_single_page():
    """示例1: 识别PDF的单页"""
    print("\n" + "="*60)
    print("示例1: 识别PDF的单页")
    print("="*60)
    
    recognizer = IDCardRecognizer(engine="paddleocr")
    
    # 假设PDF文件路径
    pdf_path = "id_card.pdf"
    
    if Path(pdf_path).exists():
        # 识别第一页 (页码从0开始)
        result = recognizer.recognize(pdf_path, pdf_page=0)
        
        print(f"检测到: {result.side}")
        print(f"置信度: {result.confidence:.3f}")
        print("\n识别结果:")
        for key, value in result.to_dict().items():
            if value and key not in ["面", "置信度"]:
                print(f"  {key}: {value}")
    else:
        print(f"文件不存在: {pdf_path}")


def example_best_page():
    """示例2: 自动选择最佳结果（识别所有页面）"""
    print("\n" + "="*60)
    print("示例2: 自动选择最佳结果")
    print("="*60)
    
    recognizer = IDCardRecognizer(engine="paddleocr")
    
    pdf_path = "id_card_multi_page.pdf"
    
    if Path(pdf_path).exists():
        # 识别所有页面，自动返回置信度最高的结果
        result = recognizer.recognize(pdf_path, pdf_page=-1)
        
        print(f"检测到: {result.side}")
        print(f"置信度: {result.confidence:.3f}")
        print("\n识别结果:")
        for key, value in result.to_dict().items():
            if value and key not in ["面", "置信度"]:
                print(f"  {key}: {value}")
    else:
        print(f"文件不存在: {pdf_path}")


def example_all_pages():
    """示例3: 获取所有页面的识别结果"""
    print("\n" + "="*60)
    print("示例3: 获取所有页面的识别结果")
    print("="*60)
    
    recognizer = IDCardRecognizer(engine="paddleocr")
    
    pdf_path = "id_card_multi_page.pdf"
    
    if Path(pdf_path).exists():
        # 识别所有页面，返回每一页的结果
        results = recognizer.recognize_pdf_all_pages(pdf_path)
        
        for result in results:
            print(f"\n第 {result['page']} 页:")
            if result['success']:
                info = result['info']
                print(f"  置信度: {info.confidence:.3f}")
                print(f"  姓名: {info.name or 'N/A'}")
                print(f"  身份证号: {info.id_number or 'N/A'}")
            else:
                print(f"  识别失败: {result['error']}")
    else:
        print(f"文件不存在: {pdf_path}")


def example_with_timing():
    """示例4: 带计时的PDF识别"""
    print("\n" + "="*60)
    print("示例4: 带计时的PDF识别")
    print("="*60)
    
    recognizer = IDCardRecognizer(engine="paddleocr")
    
    pdf_path = "id_card.pdf"
    
    if Path(pdf_path).exists():
        result, elapsed = recognizer.recognize_with_timing(pdf_path, pdf_page=0)
        
        print(f"识别耗时: {elapsed:.2f}ms")
        print(f"检测到: {result.side}")
        print(f"置信度: {result.confidence:.3f}")
    else:
        print(f"文件不存在: {pdf_path}")


if __name__ == "__main__":
    print("PDF身份证识别示例")
    print("注意: 请确保已安装PyMuPDF: pip install PyMuPDF")
    
    # 运行示例
    # example_single_page()
    # example_best_page()
    # example_all_pages()
    # example_with_timing()
    
    print("\n提示: 取消注释上面的函数调用来运行相应示例")
    print("\n命令行使用:")
    print("  python main.py id_card.pdf                    # 识别PDF第一页")
    print("  python main.py id_card.pdf --pdf-page 2       # 识别PDF第三页")
    print("  python main.py id_card.pdf --pdf-page -1      # 识别所有页，返回最佳结果")
