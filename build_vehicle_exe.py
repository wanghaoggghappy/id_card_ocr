"""
车辆档案批处理系统 - Windows EXE 打包脚本
使用 PyInstaller 将系统打包为独立的可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 修复Windows控制台UTF-8编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'


def clean_build_dirs():
    """清理旧的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理 spec 文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"删除旧的spec文件: {spec_file}")
        spec_file.unlink()


def get_hidden_imports():
    """获取需要包含的隐藏导入"""
    hidden_imports = [
        # PaddleOCR 相关
        'paddleocr',
        'paddle',
        'paddle.vision',
        'paddle.vision.transforms',
        
        # RapidOCR 相关
        'rapidocr_onnxruntime',
        'onnxruntime',
        
        # OpenCV 相关
        'cv2',
        'numpy',
        
        # PIL/Pillow
        'PIL',
        'PIL.Image',
        
        # PyMuPDF
        'fitz',
        
        # Excel处理
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        
        # 压缩文件处理
        'zipfile',
        're',
        
        # 标准库
        'yaml',
        'dateutil',
        'logging',
        'pathlib',
        'dataclasses',
        
        # 项目模块
        'ocr_engines',
        'ocr_engines.base_engine',
        'ocr_engines.paddleocr_engine',
        'ocr_engines.rapidocr_engine',
        'utils',
        'utils.image_processor',
        'utils.id_card_parser',
        'vehicle_info_extractor',
        'vehicle_document_processor',
        'process_vehicle_archives',
    ]
    return hidden_imports


def get_data_files():
    """获取需要包含的数据文件"""
    datas = []
    
    # 配置文件
    if os.path.exists('config.yaml'):
        datas.append(('config.yaml', '.'))
    
    # models 目录（如果存在）
    if os.path.exists('models') and os.path.isdir('models'):
        datas.append(('models', 'models'))
    
    return datas


def create_spec_file():
    """创建 PyInstaller spec 文件"""
    hidden_imports = get_hidden_imports()
    datas = get_data_files()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['vehicle_cli.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'jupyter', 'notebook', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VehicleArchiveProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VehicleArchiveProcessor',
)
'''
    
    spec_file = 'VehicleArchiveProcessor.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ 已创建 spec 文件: {spec_file}")
    return spec_file


def run_pyinstaller(spec_file):
    """运行 PyInstaller"""
    print("\n开始使用 PyInstaller 打包...")
    print("=" * 70)
    
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--clean',
        '--noconfirm',
        spec_file
    ]
    
    print(f"执行命令: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 70)
        print("✓ 打包成功!")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print(f"✗ 打包失败: {e}")
        return False


def copy_additional_files():
    """复制额外的文件到 dist 目录"""
    dist_dir = Path('dist/VehicleArchiveProcessor')
    
    if not dist_dir.exists():
        print("警告: dist 目录不存在")
        return
    
    # 复制文档
    files_to_copy = [
        'README.md',
        'config.yaml',
    ]
    
    for filename in files_to_copy:
        if os.path.exists(filename):
            shutil.copy2(filename, dist_dir / filename)
            print(f"✓ 已复制: {filename}")
    
    # 创建中文使用说明
    usage_txt = dist_dir / '使用说明.txt'
    with open(usage_txt, 'w', encoding='utf-8') as f:
        f.write('''========================================
车辆档案批处理系统 - Windows版本
========================================

系统功能：
---------
从车辆档案压缩包（ZIP格式）中自动提取：
  ✓ 车架号（VIN）- 支持行驶证、登记证、发票
  ✓ 车主姓名 - 支持行驶证
  ✓ 新车主姓名 - 支持登记证/登记证尾页
  ✓ 交易金额 - 支持发票
  ✓ 自动检测VIN不匹配并标红提示

输出内容：
  ✓ Excel汇总表（一行一个档案）
  ✓ 按车架号整理的文件夹（可选）

使用方法：
---------

【方法1】图形界面拖放（推荐）
  1. 双击运行 "启动-拖放文件.bat"
  2. 将压缩包文件拖放到窗口
  3. 按回车开始处理
  4. 等待完成，结果保存在 output 文件夹

【方法2】命令行（高级）
  1. 打开命令提示符（cmd）
  2. cd 到程序目录
  3. 运行命令：
     VehicleArchiveProcessor.exe 档案.zip
     VehicleArchiveProcessor.exe *.zip          （批量处理）
     VehicleArchiveProcessor.exe -h             （查看帮助）

【方法3】批处理脚本
  1. 将所有压缩包放在 archives 文件夹
  2. 双击运行 "批量处理.bat"
  3. 结果保存在 output 文件夹

常见问题：
---------
Q: 首次运行很慢？
A: 首次运行会自动下载OCR模型（约100MB），需要联网，请耐心等待。

Q: 如何查看处理结果？
A: 打开 output 文件夹，查看生成的Excel文件。

Q: 车架号显示红色是什么意思？
A: 表示行驶证和登记证的VIN不一致，需要人工核对。

Q: 支持哪些压缩格式？
A: 目前主要支持 .zip 格式。

Q: 可以处理多少个档案？
A: 理论上无限制，实际取决于计算机性能和内存大小。

Q: OCR识别不准确怎么办？
A: 确保文档图像清晰，可以尝试不同的OCR引擎（命令行 -e 参数）。

技术支持：
---------
如遇问题，请保留以下信息：
  - 程序版本
  - 错误提示截图
  - 输入文件示例

更多信息请查看 README.md
''')
    print(f"✓ 已创建使用说明: 使用说明.txt")


def create_launch_scripts():
    """创建启动脚本"""
    dist_dir = Path('dist/VehicleArchiveProcessor')
    
    if not dist_dir.exists():
        return
    
    # 1. 拖放式启动脚本
    drag_drop_bat = dist_dir / '启动-拖放文件.bat'
    with open(drag_drop_bat, 'w', encoding='gbk') as f:
        f.write('''@echo off
chcp 65001 > nul
title 车辆档案批处理系统
color 0A
echo.
echo ========================================
echo     车辆档案批处理系统
echo ========================================
echo.
echo 使用方法：
echo   1. 将压缩包文件拖放到此窗口
echo   2. 按回车键开始处理
echo   3. 等待处理完成
echo.
echo 支持格式：.zip 压缩包
echo 输出目录：output 文件夹
echo.
echo ========================================
echo.

:input
set "files="
set /p files=请拖放文件或输入路径（支持多个文件）: 

if "%files%"=="" (
    echo.
    echo 未输入文件路径，请重新输入
    echo.
    goto input
)

echo.
echo ========================================
echo 开始处理...
echo ========================================
echo.

VehicleArchiveProcessor.exe %files%

echo.
echo ========================================
echo 处理完成！
echo ========================================
echo.
echo 结果保存在 output 文件夹
echo 请查看生成的Excel文件
echo.
pause
''')
    print(f"✓ 已创建启动脚本: 启动-拖放文件.bat")
    
    # 2. 批量处理脚本
    batch_bat = dist_dir / '批量处理.bat'
    with open(batch_bat, 'w', encoding='gbk') as f:
        f.write('''@echo off
chcp 65001 > nul
title 车辆档案批量处理
color 0A
echo.
echo ========================================
echo     车辆档案批量处理
echo ========================================
echo.
echo 本脚本将处理 archives 文件夹中的所有压缩包
echo.
echo 请确认：
echo   1. archives 文件夹中有压缩包文件
echo   2. 文件格式为 .zip
echo.
pause

if not exist "archives" (
    echo.
    echo 错误：archives 文件夹不存在
    echo 正在创建 archives 文件夹...
    mkdir archives
    echo.
    echo 请将压缩包文件放入 archives 文件夹后重新运行
    echo.
    pause
    exit
)

echo.
echo ========================================
echo 开始批量处理...
echo ========================================
echo.

VehicleArchiveProcessor.exe archives\\*.zip

echo.
echo ========================================
echo 批量处理完成！
echo ========================================
echo.
echo 结果保存在 output 文件夹
echo.
pause
''')
    print(f"✓ 已创建批量处理脚本: 批量处理.bat")
    
    # 3. 创建archives文件夹
    archives_dir = dist_dir / 'archives'
    archives_dir.mkdir(exist_ok=True)
    readme = archives_dir / 'README.txt'
    with open(readme, 'w', encoding='utf-8') as f:
        f.write('请将车辆档案压缩包（.zip格式）放入此文件夹\n')
        f.write('然后运行 "批量处理.bat" 进行批量处理\n')
    print(f"✓ 已创建 archives 文件夹")


def print_build_info():
    """打印构建信息"""
    dist_dir = Path('dist/VehicleArchiveProcessor')
    
    print("\n" + "=" * 70)
    print("✓ 构建完成!")
    print("=" * 70)
    
    if dist_dir.exists():
        print(f"\n可执行文件位置: {dist_dir.absolute()}")
        print(f"\n主要文件:")
        
        important_files = [
            'VehicleArchiveProcessor.exe',
            '启动-拖放文件.bat',
            '批量处理.bat',
            '使用说明.txt',
            'README.md',
        ]
        
        total_size = 0
        for filename in important_files:
            filepath = dist_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"  ✓ {filename:40s} {size_mb:>8.2f} MB")
        
        # 计算总目录大小
        for item in dist_dir.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        
        print(f"\n总大小: {total_size / (1024 * 1024):.2f} MB")
        
        print("\n" + "=" * 70)
        print("使用方法:")
        print("=" * 70)
        print("  1. 双击运行 启动-拖放文件.bat（推荐新手）")
        print("  2. 双击运行 批量处理.bat（批量处理archives文件夹）")
        print("  3. 命令行运行: VehicleArchiveProcessor.exe --help")
        print("\n提示：可以将整个文件夹压缩后分发给用户")
    else:
        print("\n警告: 未找到构建输出目录")


def check_dependencies():
    """检查必要的依赖"""
    print("检查依赖...")
    print("-" * 70)
    
    # 包名 -> (导入名, 显示名称, pip包名)
    required_packages = {
        'PyInstaller': ('PyInstaller', 'PyInstaller', 'pyinstaller'),
        'paddleocr': ('paddleocr', 'PaddleOCR', 'paddleocr'),
        'openpyxl': ('openpyxl', 'Excel处理', 'openpyxl'),
        'cv2': ('cv2', 'OpenCV', 'opencv-python'),
        'fitz': ('fitz', 'PDF处理', 'PyMuPDF'),
    }
    
    missing = []
    for import_name, (module_name, display_name, pip_name) in required_packages.items():
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
        except ImportError:
            print(f"  ✗ {display_name} (未安装)")
            missing.append(pip_name)
    
    if missing:
        print(f"\n错误: 缺少以下依赖包:")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\n请运行: pip install {' '.join(missing)}")
        return False
    
    print("\n✓ 所有依赖已安装")
    return True


def main():
    """主函数"""
    print("=" * 70)
    print("车辆档案批处理系统 - Windows EXE 打包工具")
    print("=" * 70)
    print()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    print()
    
    # 清理旧文件
    print("清理构建目录...")
    print("-" * 70)
    clean_build_dirs()
    print()
    
    # 创建 spec 文件
    print("创建打包配置...")
    print("-" * 70)
    spec_file = create_spec_file()
    print()
    
    # 运行 PyInstaller
    success = run_pyinstaller(spec_file)
    
    if not success:
        print("\n✗ 打包失败，请检查错误信息")
        sys.exit(1)
    
    # 复制额外文件
    print("\n复制额外文件...")
    print("-" * 70)
    copy_additional_files()
    print()
    
    # 创建启动脚本
    print("创建启动脚本...")
    print("-" * 70)
    create_launch_scripts()
    print()
    
    # 打印构建信息
    print_build_info()


if __name__ == '__main__':
    main()
