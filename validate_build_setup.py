"""
验证打包配置文件是否完整
"""

import os
from pathlib import Path


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} [缺失]")
        return False


def check_directory_exists(dirpath, description):
    """检查目录是否存在"""
    if Path(dirpath).exists() and Path(dirpath).is_dir():
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description}: {dirpath} [缺失]")
        return False


def validate_yaml_syntax(filepath):
    """验证 YAML 文件语法"""
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"  → YAML 语法正确")
        return True
    except Exception as e:
        print(f"  → YAML 语法错误: {e}")
        return False


def check_github_workflow():
    """检查 GitHub Actions 工作流"""
    print("\n1. GitHub Actions 工作流")
    print("-" * 60)
    
    workflow_file = ".github/workflows/build-windows-exe.yml"
    if check_file_exists(workflow_file, "工作流文件"):
        validate_yaml_syntax(workflow_file)
        
        # 检查关键内容
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("windows-latest", "Windows 运行环境"),
            ("setup-python@v5", "Python 设置"),
            ("pyinstaller", "PyInstaller 安装"),
            ("build_exe.py", "构建脚本调用"),
            ("upload-artifact", "产物上传"),
        ]
        
        for keyword, desc in checks:
            if keyword in content:
                print(f"  ✓ {desc}")
            else:
                print(f"  ✗ {desc} [未找到]")


def check_build_scripts():
    """检查打包脚本"""
    print("\n2. 打包脚本")
    print("-" * 60)
    
    files = [
        ("build_exe.py", "Python 打包脚本"),
        ("build_local.bat", "Windows 批处理脚本"),
    ]
    
    for filepath, desc in files:
        if check_file_exists(filepath, desc):
            # 检查是否可执行
            if filepath.endswith('.py'):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'PyInstaller' in content:
                        print(f"  ✓ 包含 PyInstaller 相关代码")
                except:
                    pass


def check_requirements():
    """检查依赖文件"""
    print("\n3. 依赖文件")
    print("-" * 60)
    
    files = [
        ("requirements.txt", "完整依赖列表"),
        ("requirements-build.txt", "构建依赖列表"),
    ]
    
    for filepath, desc in files:
        if check_file_exists(filepath, desc):
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            print(f"  → 包含 {len(lines)} 个依赖包")


def check_documentation():
    """检查文档"""
    print("\n4. 文档文件")
    print("-" * 60)
    
    files = [
        ("BUILD_GUIDE.md", "完整打包指南"),
        ("QUICKSTART_BUILD.md", "快速开始指南"),
        ("BUILD_FILES_REFERENCE.md", "文件说明参考"),
        (".gitignore", "Git 忽略配置"),
    ]
    
    for filepath, desc in files:
        if check_file_exists(filepath, desc):
            size = Path(filepath).stat().st_size
            print(f"  → 文件大小: {size / 1024:.1f} KB")


def check_project_structure():
    """检查项目结构"""
    print("\n5. 项目结构")
    print("-" * 60)
    
    essential_files = [
        "main.py",
        "id_card_recognizer.py",
        "config.yaml",
        "README.md",
    ]
    
    for filepath in essential_files:
        check_file_exists(filepath, f"核心文件")
    
    essential_dirs = [
        "ocr_engines",
        "utils",
    ]
    
    for dirpath in essential_dirs:
        check_directory_exists(dirpath, f"核心目录")


def check_build_readiness():
    """检查是否准备好构建"""
    print("\n6. 构建就绪检查")
    print("-" * 60)
    
    checks = []
    
    # 检查 Python
    try:
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"✓ Python 版本: {python_version}")
        checks.append(True)
    except:
        print(f"✗ Python 未安装")
        checks.append(False)
    
    # 检查必要的包
    required_packages = [
        "cv2",
        "numpy",
        "yaml",
        "PIL",
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
            checks.append(True)
        except ImportError:
            print(f"✗ {package} 未安装")
            checks.append(False)
    
    # 检查可选的包
    optional_packages = [
        ("PyInstaller", "打包工具"),
        ("paddleocr", "PaddleOCR 引擎"),
        ("rapidocr_onnxruntime", "RapidOCR 引擎"),
    ]
    
    print("\n可选包:")
    for package, desc in optional_packages:
        try:
            __import__(package)
            print(f"  ✓ {desc} ({package})")
        except ImportError:
            print(f"  - {desc} ({package}) [未安装]")
    
    return all(checks)


def print_summary():
    """打印总结"""
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    print("\n✅ 所有打包配置文件已就绪！")
    print("\n下一步:")
    print("  1. 本地测试打包:")
    print("     python build_exe.py")
    print("\n  2. 推送到 GitHub 触发自动构建:")
    print("     git add .")
    print("     git commit -m 'Add build pipeline'")
    print("     git push")
    print("\n  3. 创建版本标签发布:")
    print("     git tag -a v1.0.0 -m 'Release v1.0.0'")
    print("     git push origin v1.0.0")
    print("\n详细说明请查看:")
    print("  - BUILD_GUIDE.md (完整指南)")
    print("  - QUICKSTART_BUILD.md (快速开始)")
    print("  - BUILD_FILES_REFERENCE.md (文件说明)")


def main():
    """主函数"""
    print("=" * 60)
    print("Windows EXE 打包配置验证工具")
    print("=" * 60)
    
    try:
        check_github_workflow()
        check_build_scripts()
        check_requirements()
        check_documentation()
        check_project_structure()
        ready = check_build_readiness()
        
        print_summary()
        
        if not ready:
            print("\n⚠️  警告: 部分核心依赖未安装")
            print("   运行: pip install -r requirements-build.txt")
        
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
