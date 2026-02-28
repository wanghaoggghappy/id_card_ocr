#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车辆档案批处理系统 - 命令行入口
支持批量处理车辆档案压缩包，提取VIN、车主等信息并导出Excel
"""

import argparse
import sys
from pathlib import Path
from process_vehicle_archives import VehicleArchiveProcessor


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='车辆档案批处理系统 - 从压缩包中提取车辆信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  # 处理单个压缩包
  %(prog)s archive.zip
  
  # 处理多个压缩包
  %(prog)s archive1.zip archive2.zip archive3.zip
  
  # 使用通配符批量处理
  %(prog)s *.zip
  
  # 指定输出目录
  %(prog)s archive.zip -o ./results
  
  # 只导出Excel不整理文件
  %(prog)s archive.zip --no-organize
''')
    
    parser.add_argument(
        'archives',
        nargs='+',
        help='车辆档案压缩包路径（支持多个，支持.zip格式）'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./output',
        help='输出目录路径（默认: ./output）'
    )
    
    parser.add_argument(
        '--no-organize',
        action='store_true',
        help='不整理文件到子目录（只提取信息并导出Excel）'
    )
    
    parser.add_argument(
        '--no-excel',
        action='store_true',
        help='不导出Excel文件（只整理文件）'
    )
    
    parser.add_argument(
        '-e', '--engine',
        default='paddleocr',
        choices=['paddleocr', 'rapidocr', 'easyocr', 'tesseract', 'cnocr'],
        help='OCR识别引擎（默认: paddleocr）'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细处理信息'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='车辆档案批处理系统 v1.0.0'
    )
    
    args = parser.parse_args()
    
    # 验证输入文件
    archive_paths = []
    for archive in args.archives:
        path = Path(archive)
        if not path.exists():
            print(f"错误: 文件不存在: {archive}", file=sys.stderr)
            sys.exit(1)
        if not path.suffix.lower() in ['.zip', '.rar', '.7z']:
            print(f"警告: {archive} 不是支持的压缩格式，将尝试处理...", file=sys.stderr)
        archive_paths.append(str(path.absolute()))
    
    # 创建处理器
    try:
        processor = VehicleArchiveProcessor(
            output_dir=args.output,
            ocr_engine=args.engine
        )
    except Exception as e:
        print(f"错误: 初始化处理器失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 执行批处理
    try:
        results = processor.process_multiple_archives(
            archive_paths,
            organize=not args.no_organize,
            export_excel=not args.no_excel
        )
        
        # 输出统计信息
        print("\n" + "=" * 70)
        print("处理完成")
        print("=" * 70)
        
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        
        print(f"总计: {len(results)} 个档案")
        print(f"成功: {success_count} 个")
        if failed_count > 0:
            print(f"失败: {failed_count} 个")
            print("\n失败列表:")
            for result in results:
                if not result['success']:
                    print(f"  - {result['archive_name']}: {result.get('error', '未知错误')}")
        
        print(f"\n输出目录: {Path(args.output).absolute()}")
        
        if success_count > 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n用户中断操作", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: 处理失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
