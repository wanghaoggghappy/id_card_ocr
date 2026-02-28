@echo off
chcp 65001 > nul
REM 本地打包脚本 - 适用于 Windows

echo ========================================
echo 身份证OCR识别系统 - Windows打包工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)

echo [1/5] 检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 未安装，正在安装...
    pip install pyinstaller
)

echo [2/5] 安装构建依赖...
pip install -r requirements-build.txt

echo [3/5] 开始打包...
python build_exe.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [4/5] 测试可执行文件...
cd dist\id_card_ocr
id_card_ocr.exe --help

echo.
echo [5/5] 完成!
echo.
echo 可执行文件位置: dist\id_card_ocr\
echo.
echo 下一步：
echo   1. 测试: cd dist\id_card_ocr ^&^& id_card_ocr.exe --list-engines
echo   2. 压缩: 将整个 dist\id_card_ocr 目录打包成 zip
echo   3. 分发: 将 zip 文件分享给用户
echo.

pause
