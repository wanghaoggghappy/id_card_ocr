# Windows UTF-8 编码修复说明

## 问题描述

在GitHub Actions的Windows环境中运行Python脚本时，遇到UTF-8编码错误：

```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-8: 
character maps to <undefined>
```

**原因**：Windows默认使用cp1252编码，无法正确显示中文字符。

## 解决方案

### 1. Python脚本层面修复

在每个需要输出中文的Python脚本开头添加：

```python
import sys
import os

# 修复Windows控制台UTF-8编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
```

**已修复的文件**：
- ✅ `build_vehicle_exe.py` - 打包脚本
- ✅ `vehicle_cli.py` - 命令行入口

### 2. GitHub Actions层面配置

在workflow文件中添加环境变量：

```yaml
- name: 🔨 Build Windows EXE
  env:
    PYTHONIOENCODING: utf-8  # 设置Python输出编码
  run: |
    chcp 65001  # 设置控制台代码页为UTF-8
    python build_vehicle_exe.py
```

**已修复的步骤**：
- ✅ Build Windows EXE - 构建步骤
- ✅ Test EXE - 测试步骤

### 3. 批处理文件（.bat）

在bat文件开头添加：

```batch
@echo off
chcp 65001 > nul
REM ... 其他命令
```

**已有配置**：
- ✅ `启动-拖放文件.bat`
- ✅ `批量处理.bat`

## 编码处理方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| `io.TextIOWrapper` | 最可靠，不影响其他功能 | 需要修改代码 | ✅ 推荐用于Python脚本 |
| `PYTHONIOENCODING` | 环境变量，不改代码 | 可能被覆盖 | ✅ CI/CD环境 |
| `chcp 65001` | Windows原生支持 | 仅限批处理 | ✅ .bat启动脚本 |
| `sys.stdout.reconfigure()` | Python 3.7+ 原生 | 老版本不支持 | Python 3.7+ |

## 测试验证

### 本地Windows测试

```cmd
# 测试build脚本
python build_vehicle_exe.py

# 测试CLI
python vehicle_cli.py --help

# 测试EXE
dist\VehicleArchiveProcessor\VehicleArchiveProcessor.exe --help
```

### GitHub Actions测试

推送代码触发自动构建：

```bash
git add .
git commit -m "Fix UTF-8 encoding for Windows"
git push origin main
```

查看Actions日志，确认中文正常显示。

## 常见问题

### Q: 为什么只在Windows上出现？

**A**: macOS和Linux默认使用UTF-8编码，Windows默认使用系统区域设置（如中文环境是GBK，英文环境是cp1252）。

### Q: errors='replace' 会丢失数据吗？

**A**: 不会。它只影响控制台输出显示，不影响文件写入。无法显示的字符会被替换为`?`，但不会中断程序。

### Q: 可以用 sys.stdout.reconfigure() 吗？

**A**: 可以，但需要Python 3.7+：

```python
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```

### Q: 为什么不用 print(..., file=sys.stdout.buffer) ？

**A**: 太繁琐，需要手动编码每个字符串。TextIOWrapper方案更优雅。

### Q: 会影响文件输入输出吗？

**A**: 不会。我们只修改了stdout/stderr，文件操作使用独立的编码指定（如`open(file, encoding='utf-8')`）。

## 最佳实践

### 1. 文件顶部声明编码

```python
# -*- coding: utf-8 -*-
```

### 2. 文件操作显式指定编码

```python
# 读取
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 写入
with open('file.txt', 'w', encoding='utf-8') as f:
    f.write(content)
```

### 3. 环境变量配置（可选）

Windows PowerShell：
```powershell
$env:PYTHONIOENCODING='utf-8'
python script.py
```

Linux/macOS：
```bash
export PYTHONIOENCODING=utf-8
python script.py
```

### 4. PyInstaller打包配置

在.spec文件中添加：

```python
import sys
import io

# 在运行时配置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## 相关资源

- [PEP 686 - Make UTF-8 mode default](https://peps.python.org/pep-0686/)
- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
- [Windows Code Pages](https://docs.microsoft.com/en-us/windows/win32/intl/code-pages)
- [GitHub Actions Windows Runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#supported-runners-and-hardware-resources)

## 修复历史

| 日期 | 修复内容 | 文件 |
|------|---------|------|
| 2026-02-28 | 添加UTF-8编码处理 | build_vehicle_exe.py |
| 2026-02-28 | 添加UTF-8编码处理 | vehicle_cli.py |
| 2026-02-28 | 配置PYTHONIOENCODING | build-vehicle-windows.yml |
| 2026-02-28 | 添加chcp 65001 | build-vehicle-windows.yml |

## ✅ 验证清单

- [x] build_vehicle_exe.py 添加编码处理
- [x] vehicle_cli.py 添加编码处理
- [x] GitHub Actions workflow 配置环境变量
- [x] GitHub Actions workflow 添加chcp命令
- [ ] Windows环境本地测试
- [ ] GitHub Actions构建测试
- [ ] 验证中文输出正常

## 注意事项

⚠️ **Python 3.15+**: 将默认启用UTF-8模式（PEP 686），届时可能不再需要这些修复。

✅ **向后兼容**: 当前修复方案兼容Python 3.6+所有版本。

🔒 **安全性**: 使用`errors='replace'`而非`errors='ignore'`，确保错误可见。
