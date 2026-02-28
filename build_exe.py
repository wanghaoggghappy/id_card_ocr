"""
Windows EXE 打包脚本
使用 PyInstaller 将身份证OCR系统打包为独立的可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


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
        
        # 标准库
        'yaml',
        'dateutil',
        
        # 项目模块
        'ocr_engines',
        'ocr_engines.base_engine',
        'ocr_engines.paddleocr_engine',
        'ocr_engines.rapidocr_engine',
        'utils',
        'utils.image_processor',
        'utils.id_card_parser',
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
    ['main.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'jupyter', 'notebook'],
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
    name='id_card_ocr',
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
    name='id_card_ocr',
)
'''
    
    spec_file = 'id_card_ocr.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"已创建 spec 文件: {spec_file}")
    return spec_file


def run_pyinstaller(spec_file):
    """运行 PyInstaller"""
    print("\n开始使用 PyInstaller 打包...")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--clean',
        '--noconfirm',
        spec_file
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 60)
        print("✓ 打包成功!")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"✗ 打包失败: {e}")
        return False


def copy_additional_files():
    """复制额外的文件到 dist 目录"""
    dist_dir = Path('dist/id_card_ocr')
    
    if not dist_dir.exists():
        print("警告: dist 目录不存在")
        return
    
    # 复制 README
    files_to_copy = [
        'README.md',
        'config.yaml',
        'PDF_SUPPORT_GUIDE.md',
    ]
    
    for filename in files_to_copy:
        if os.path.exists(filename):
            shutil.copy2(filename, dist_dir / filename)
            print(f"已复制: {filename}")
    
    # 创建使用说明
    usage_txt = dist_dir / 'USAGE.txt'
    with open(usage_txt, 'w', encoding='utf-8') as f:
        f.write('''身份证OCR识别系统 - Windows版本
========================================

使用方法：

1. 基本用法（识别图像）：
   id_card_ocr.exe 图像路径.jpg

2. 识别PDF：
   id_card_ocr.exe 文件.pdf
   id_card_ocr.exe 文件.pdf --pdf-page 0

3. 使用不同引擎：
   id_card_ocr.exe 图像.jpg -e rapidocr

4. 查看帮助：
   id_card_ocr.exe --help

5. 列出可用引擎：
   id_card_ocr.exe --list-engines

注意事项：
- 首次运行会下载OCR模型，需要联网
- 建议将图像/PDF文件放在同一目录下
- 支持的图像格式：jpg, png, bmp, tiff
- 支持PDF文件（单页和多页）

更多信息请查看 README.md
''')
    print(f"已创建使用说明: USAGE.txt")


def create_launch_script():
    """创建启动脚本"""
    dist_dir = Path('dist/id_card_ocr')
    
    if not dist_dir.exists():
        return
    
    # Windows批处理文件
    batch_file = dist_dir / 'run_gui.bat'
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write('''@echo off
chcp 65001 > nul
echo 身份证OCR识别系统
echo =========================================
echo.
echo 请将身份证图像文件拖放到此窗口，然后按回车
echo 或输入图像文件路径：
echo.
set /p IMAGE_FILE=
echo.
if "%IMAGE_FILE%"=="" (
    echo 未输入文件路径
    pause
    exit
)
echo 正在识别...
echo.
id_card_ocr.exe %IMAGE_FILE%
echo.
pause
''')
    print(f"已创建启动脚本: run_gui.bat")


def print_build_info():
    """打印构建信息"""
    dist_dir = Path('dist/id_card_ocr')
    
    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)
    
    if dist_dir.exists():
        print(f"\n可执行文件位置: {dist_dir.absolute()}")
        print(f"\n目录内容:")
        
        total_size = 0
        for item in sorted(dist_dir.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"  {item.name:40s} {size_mb:>8.2f} MB")
        
        print(f"\n总大小: {total_size / (1024 * 1024):.2f} MB")
        
        print("\n使用方法:")
        print("  1. 运行 id_card_ocr.exe --help 查看帮助")
        print("  2. 运行 run_gui.bat 启动图形界面")
        print("  3. 直接运行: id_card_ocr.exe 图像.jpg")
    else:
        print("\n警告: 未找到构建输出目录")


def main():
    """主函数"""
    print("身份证OCR系统 - Windows EXE 打包工具")
    print("=" * 60)
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未安装 PyInstaller")
        print("请运行: pip install pyinstaller")
        sys.exit(1)
    
    # 清理旧文件
    clean_build_dirs()
    
    # 创建 spec 文件
    spec_file = create_spec_file()
    
    # 运行 PyInstaller
    success = run_pyinstaller(spec_file)
    
    if not success:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)
    
    # 复制额外文件
    copy_additional_files()
    
    # 创建启动脚本
    create_launch_script()
    
    # 打印构建信息
    print_build_info()
    
    print("\n提示: 可以将整个 dist/id_card_ocr 目录分发给用户")


if __name__ == '__main__':
    main()
