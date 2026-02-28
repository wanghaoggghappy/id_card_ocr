"""
身份证信息解析器
从OCR结果中提取结构化的身份证信息
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IDCardInfo:
    """身份证信息"""
    # 正面信息
    name: Optional[str] = None           # 姓名
    gender: Optional[str] = None         # 性别
    ethnicity: Optional[str] = None      # 民族
    birth_date: Optional[str] = None     # 出生日期
    address: Optional[str] = None        # 住址
    id_number: Optional[str] = None      # 身份证号码
    
    # 背面信息
    issuing_authority: Optional[str] = None  # 签发机关
    valid_period: Optional[str] = None       # 有效期限
    
    # 元信息
    side: Optional[str] = None           # 正面/背面
    confidence: float = 0.0              # 整体置信度
    raw_text: List[str] = None          # 原始OCR文本
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "姓名": self.name,
            "性别": self.gender,
            "民族": self.ethnicity,
            "出生": self.birth_date,
            "住址": self.address,
            "公民身份号码": self.id_number,
            "签发机关": self.issuing_authority,
            "有效期限": self.valid_period,
            "面": self.side,
            "置信度": round(self.confidence, 3),
        }
    
    def __repr__(self):
        if self.side == "正面":
            return (f"IDCardInfo(姓名={self.name}, 性别={self.gender}, "
                   f"民族={self.ethnicity}, 出生={self.birth_date}, "
                   f"身份证号={self.id_number})")
        else:
            return (f"IDCardInfo(签发机关={self.issuing_authority}, "
                   f"有效期限={self.valid_period})")


class IDCardParser:
    """身份证信息解析器"""
    
    # 身份证号码正则
    ID_PATTERN = re.compile(
        r'[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]'
    )
    
    # 日期模式
    DATE_PATTERN = re.compile(
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
    )
    
    # 有效期模式
    VALID_PERIOD_PATTERN = re.compile(
        r'(\d{4}[.\-年]\d{2}[.\-月]\d{2}日?)\s*[-—至]\s*(\d{4}[.\-年]\d{2}[.\-月]\d{2}日?|长期)'
    )
    
    # 民族列表
    ETHNICITIES = [
        "汉", "蒙古", "回", "藏", "维吾尔", "苗", "彝", "壮", "布依", "朝鲜",
        "满", "侗", "瑶", "白", "土家", "哈尼", "哈萨克", "傣", "黎", "傈僳",
        "佤", "畲", "高山", "拉祜", "水", "东乡", "纳西", "景颇", "柯尔克孜",
        "土", "达斡尔", "仫佬", "羌", "布朗", "撒拉", "毛南", "仡佬", "锡伯",
        "阿昌", "普米", "塔吉克", "怒", "乌孜别克", "俄罗斯", "鄂温克", "德昂",
        "保安", "裕固", "京", "塔塔尔", "独龙", "鄂伦春", "赫哲", "门巴",
        "珞巴", "基诺"
    ]
    
    def __init__(self):
        self.ethnicity_pattern = re.compile(
            f"({'|'.join(self.ETHNICITIES)})族?"
        )
    
    def parse(self, ocr_results: List) -> IDCardInfo:
        """
        解析OCR结果
        
        Args:
            ocr_results: OCR识别结果列表，每项包含text和confidence
            
        Returns:
            解析后的身份证信息
        """
        print(f"\n[调试-解析器] 收到 {len(ocr_results)} 个OCR结果")
        
        # 提取所有文本
        texts = []
        total_confidence = 0.0
        
        for idx, result in enumerate(ocr_results):
            if hasattr(result, 'text'):
                texts.append(result.text)
                total_confidence += result.confidence
                print(f"[调试-解析器] 结果{idx}: '{result.text}' (置信度: {result.confidence:.3f})")
            elif isinstance(result, dict):
                text = result.get('text', '')
                texts.append(text)
                total_confidence += result.get('confidence', 0)
                print(f"[调试-解析器] 结果{idx}: '{text}' (dict格式)")
            else:
                texts.append(str(result))
                print(f"[调试-解析器] 结果{idx}: '{result}' (其他格式)")
                
        avg_confidence = total_confidence / len(ocr_results) if ocr_results else 0
        
        # 合并文本用于某些模式匹配
        full_text = ' '.join(texts)
        print(f"[调试-解析器] 合并文本: {full_text}")
        print(f"[调试-解析器] 平均置信度: {avg_confidence:.3f}")
        
        # 判断是正面还是背面
        side = self._detect_side(texts)
        print(f"[调试-解析器] 判断为: {side}")
        
        # 创建结果对象
        info = IDCardInfo(
            side=side,
            confidence=avg_confidence,
            raw_text=texts
        )
        
        if side == "正面":
            print(f"[调试-解析器] 开始解析正面信息...")
            self._parse_front(texts, full_text, info)
        else:
            print(f"[调试-解析器] 开始解析背面信息...")
            self._parse_back(texts, full_text, info)
        
        print(f"[调试-解析器] 解析完成: {info}")
            
        return info
    
    def _detect_side(self, texts: List[str]) -> str:
        """判断是身份证正面还是背面"""
        full_text = ''.join(texts)
        
        # 背面特征词
        back_keywords = ["签发机关", "有效期", "中华人民共和国", "居民身份证"]
        # 正面特征词
        front_keywords = ["姓名", "性别", "民族", "住址", "公民身份号码"]
        
        back_score = sum(1 for kw in back_keywords if kw in full_text)
        front_score = sum(1 for kw in front_keywords if kw in full_text)
        
        # 如果有身份证号，很可能是正面
        if self.ID_PATTERN.search(full_text):
            front_score += 2
            
        return "正面" if front_score >= back_score else "背面"
    
    def _parse_front(self, texts: List[str], full_text: str, 
                     info: IDCardInfo) -> None:
        """解析正面信息"""
        
        # 1. 提取身份证号码
        id_match = self.ID_PATTERN.search(full_text.replace(' ', ''))
        if id_match:
            info.id_number = id_match.group().upper()
            # 从身份证号提取出生日期
            birth_str = info.id_number[6:14]
            info.birth_date = f"{birth_str[:4]}年{birth_str[4:6]}月{birth_str[6:8]}日"
            # 从身份证号提取性别
            gender_code = int(info.id_number[16])
            info.gender = "男" if gender_code % 2 == 1 else "女"
        
        # 2. 提取姓名（通常在第一行或"姓名"后面）
        info.name = self._extract_name(texts)
        
        # 3. 提取民族
        eth_match = self.ethnicity_pattern.search(full_text)
        if eth_match:
            info.ethnicity = eth_match.group()
            if not info.ethnicity.endswith("族"):
                info.ethnicity += "族"
        
        # 4. 提取住址
        info.address = self._extract_address(texts)
        
        # 5. 如果之前没提取到出生日期，尝试从文本提取
        if not info.birth_date:
            date_match = self.DATE_PATTERN.search(full_text)
            if date_match:
                info.birth_date = f"{date_match.group(1)}年{date_match.group(2)}月{date_match.group(3)}日"
        
        # 6. 如果没从身份证号提取到性别，从文本提取
        if not info.gender:
            if "男" in full_text:
                info.gender = "男"
            elif "女" in full_text:
                info.gender = "女"
    
    def _parse_back(self, texts: List[str], full_text: str, 
                    info: IDCardInfo) -> None:
        """解析背面信息"""
        
        # 1. 提取签发机关
        for i, text in enumerate(texts):
            if "签发机关" in text:
                # 签发机关可能在同一行或下一行
                content = text.replace("签发机关", "").strip()
                if content:
                    info.issuing_authority = content
                elif i + 1 < len(texts):
                    info.issuing_authority = texts[i + 1].strip()
                break
        
        # 如果没找到，尝试找包含"公安局"或"派出所"的文本
        if not info.issuing_authority:
            for text in texts:
                if "公安" in text or "派出所" in text:
                    info.issuing_authority = text.strip()
                    break
        
        # 2. 提取有效期限
        period_match = self.VALID_PERIOD_PATTERN.search(full_text.replace(' ', ''))
        if period_match:
            start_date = period_match.group(1)
            end_date = period_match.group(2)
            info.valid_period = f"{start_date}-{end_date}"
        else:
            # 尝试其他方式提取
            for i, text in enumerate(texts):
                if "有效期" in text:
                    content = text.replace("有效期限", "").replace("有效期", "").strip()
                    if content:
                        info.valid_period = content
                    elif i + 1 < len(texts):
                        info.valid_period = texts[i + 1].strip()
                    break
    
    def _extract_name(self, texts: List[str]) -> Optional[str]:
        """提取姓名"""
        for text in texts:
            if "姓名" in text:
                name = text.replace("姓名", "").strip()
                if name and len(name) <= 10:  # 姓名不会太长
                    return name
        
        # 如果没有"姓名"关键字，尝试找2-4个汉字的文本作为姓名
        for text in texts[:3]:  # 只看前几行
            text = text.strip()
            if 2 <= len(text) <= 4 and all('\u4e00' <= c <= '\u9fff' for c in text):
                # 排除一些常见的非姓名词
                if text not in ["姓名", "性别", "民族", "住址", "出生"]:
                    return text
                    
        return None
    
    def _extract_address(self, texts: List[str]) -> Optional[str]:
        """提取住址"""
        address_parts = []
        in_address = False
        
        for text in texts:
            if "住址" in text:
                in_address = True
                content = text.replace("住址", "").strip()
                if content:
                    address_parts.append(content)
            elif in_address:
                # 检查是否还是地址的一部分
                # 地址通常包含省、市、县、区、镇、村、路、号等
                if any(kw in text for kw in ["省", "市", "县", "区", "镇", "乡", 
                                              "村", "路", "街", "号", "幢", "室"]):
                    address_parts.append(text.strip())
                elif "公民身份" in text or "身份号码" in text:
                    break  # 到身份证号了，地址结束
                    
        if address_parts:
            return ''.join(address_parts)
            
        return None
    
    def validate_id_number(self, id_number: str) -> bool:
        """验证身份证号码是否有效"""
        if not id_number or len(id_number) != 18:
            return False
            
        # 验证格式
        if not self.ID_PATTERN.match(id_number):
            return False
            
        # 验证校验码
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = "10X98765432"
        
        try:
            total = sum(int(id_number[i]) * weights[i] for i in range(17))
            expected_check = check_codes[total % 11]
            return id_number[17].upper() == expected_check
        except (ValueError, IndexError):
            return False
