#!/usr/bin/env python3
"""调试VIN提取"""

import re

text = """LSVNP60CIPN048194."""

# 测试1: 原始文本
print(f"原始文本: '{text}'")
print(f"长度: {len(text)}")

# 测试2: 清理后
clean = text.replace(' ', '').replace('\n', '').replace('.', '').replace(',', '')
print(f"\n清理后: '{clean}'")
print(f"长度: {len(clean)}")

# 测试3: 标准VIN模式
pattern1 = re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b')
matches1 = pattern1.findall(clean)
print(f"\n标准模式匹配 [A-HJ-NPR-Z0-9]{{17}}: {matches1}")

# 测试4: 宽松VIN模式（允许所有字母）
pattern2 = re.compile(r'\b[A-Z0-9]{17}\b')
matches2 = pattern2.findall(clean)
print(f"宽松模式匹配 [A-Z0-9]{{17}}: {matches2}")

# 测试5: 不带单词边界
pattern3 = re.compile(r'[A-Z0-9]{17}')
matches3 = pattern3.findall(clean)
print(f"无边界模式匹配 [A-Z0-9]{{17}}: {matches3}")

# 测试6: 检查字符
print(f"\n字符检查:")
for i, char in enumerate(clean):
    print(f"  [{i}] {char} - ASCII:{ord(char)} - 数字:{char.isdigit()} 字母:{char.isalpha()}")
