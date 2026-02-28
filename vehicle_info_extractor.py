"""
车辆文档信息提取器
从OCR识别结果中提取关键信息：车架号、发票金额、车主姓名等
"""

import re
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class VehicleInfo:
    """车辆信息数据类"""
    vin: Optional[str] = None  # 车架号（VIN）
    invoice_amount: Optional[str] = None  # 发票金额
    owner_name: Optional[str] = None  # 车主姓名
    buyer_name: Optional[str] = None  # 买方姓名（发票）
    new_owner_name: Optional[str] = None  # 新车主姓名（登记证转移）
    plate_number: Optional[str] = None  # 车牌号
    vehicle_model: Optional[str] = None  # 车辆型号
    engine_number: Optional[str] = None  # 发动机号
    register_date: Optional[str] = None  # 注册日期


class VehicleInfoExtractor:
    """车辆信息提取器"""
    
    def __init__(self):
        # 车架号正则：17位数字和大写字母（不含I、O、Q，但P是允许的）
        self.vin_pattern = re.compile(r'[A-HJ-NPR-Z0-9]{17}')
        
        # OCR常见错误字符映射（用于VIN码修正）
        # 注意：P是VIN中合法字符，只有I、O、Q不允许
        self.ocr_char_map = {
            'I': '1',  # I不允许出现在VIN中
            'O': '0',  # O不允许出现在VIN中
            'Q': '0',  # Q不允许出现在VIN中
        }
        
        # 金额正则：各种金额格式
        self.amount_patterns = [
            # 发票专用格式：车价合计、价税合计 + 小写
            re.compile(r'[车]价[合]计.*?小写[:：\s]*([0-9,，]+\.?\d*)'),
            re.compile(r'价税合计.*?小写[:：\s]*([0-9,，]+\.?\d*)'),
            re.compile(r'合计金额.*?小写[:：\s]*([0-9,，]+\.?\d*)'),
            # 小写关键词
            re.compile(r'小写[:：\s]*([0-9,，]+\.?\d*)'),
            # 原有格式
            re.compile(r'[金价总]额[:：￥¥]*\s*([0-9,，]+\.?\d*)'),
            re.compile(r'¥\s*([0-9,，]+\.?\d*)'),
            re.compile(r'￥\s*([0-9,，]+\.?\d*)'),
            re.compile(r'([0-9,，]+\.?\d*)\s*元'),
        ]
        
        # 车牌号正则
        self.plate_patterns = [
            re.compile(r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{5}'),
            re.compile(r'号牌号码[:：]\s*([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{5})'),
        ]
        
        # 姓名关键词
        self.owner_keywords = ['所有人', '车主', '姓名', '买方']
        
        # 发动机号正则
        self.engine_pattern = re.compile(r'发动机号码?[:：]\s*([A-Z0-9]{6,})')
        
        # 非姓名词过滤列表
        self.non_name_words = {
            # 地名
            '北京', '上海', '天津', '重庆', '广州', '深圳', '杭州', '南京',
            '成都', '西安', '武汉', '郑州', '长沙', '沈阳', '哈尔滨', '济南',
            '青岛', '大连', '厦门', '福州', '昆明', '兰州', '太原', '石家庄',
            '合肥', '南昌', '贵阳', '海口', '银川', '西宁', '拉萨', '呼和浩特',
            '乌鲁木齐', '朝阳区', '海淀区', '丰台区', '东城区', '西城区',
            # 常见非姓名词
            '单位', '企业', '公司', '集团', '有限', '股份',
            '信息', '摘要', '备注', '说明', '注意', '事项',
            '机动车', '车辆', '登记', '证书', '发票', '行驶',
            '住址', '地址', '联系', '电话',
            # 常见文档词汇
            '转移', '登记证', '行驶证', '所有人', '车主', '姓名',
            '品牌', '型号', '类型', '用途',
            # 行驶证常见技术参数（OCR容易错位）
            '外廓尺寸', '外麻尺寸', '核定载人数', '核定载质量',
            '整备质量', '准牵引总质量', '总质量', '使用性质',
            '车辆类型', '品牌型号', '发动机号码', '注册日期',
            '发证日期', '检验记录', '档案编号'
        }
    
    def extract_from_text(self, text: str, doc_type: str = None) -> VehicleInfo:
        """
        从文本中提取车辆信息
        
        Args:
            text: OCR识别的文本
            doc_type: 文档类型（registration/invoice/license）
            
        Returns:
            VehicleInfo对象
        """
        # 记录输入文本（前500字符）
        logger.info(f"\n{'='*60}")
        logger.info(f"开始提取信息 - 文档类型: {doc_type}")
        logger.info(f"输入文本预览:\n{text[:500]}..." if len(text) > 500 else f"输入文本:\n{text}")
        logger.info(f"{'='*60}")
        
        info = VehicleInfo()
        
        # 提取车架号
        info.vin = self._extract_vin(text)
        logger.info(f"提取车架号: {info.vin}")
        
        # 根据文档类型提取不同信息
        if doc_type == 'invoice' or '发票' in text:
            info.invoice_amount = self._extract_amount(text)
            logger.info(f"提取发票金额: {info.invoice_amount}")
            info.buyer_name = self._extract_buyer_name(text)
            logger.info(f"提取买方: {info.buyer_name}")
        elif doc_type == 'registration_transfer' or '登记栏' in text:
            # 登记证尾页（转移登记）：只提取新车主
            logger.info(f"检测到登记证尾页（登记栏），提取新车主")
            info.new_owner_name = self._extract_new_owner_name(text)
            logger.info(f"提取新车主: {info.new_owner_name}")
        elif doc_type == 'registration' or '注册登记' in text:
            # 登记证（注册登记页）：提取车架号、车主等
            info.owner_name = self._extract_owner_name(text)
            logger.info(f"提取车主: {info.owner_name}")
            info.register_date = self._extract_date(text)
            logger.info(f"提取注册日期: {info.register_date}")
            info.vehicle_model = self._extract_vehicle_model(text)
            logger.info(f"提取车辆型号: {info.vehicle_model}")
        elif doc_type == 'license' or '行驶证' in text:
            info.plate_number = self._extract_plate_number(text)
            logger.info(f"提取车牌号: {info.plate_number}")
            info.owner_name = self._extract_owner_name(text)
            logger.info(f"提取车主: {info.owner_name}")
            info.vehicle_model = self._extract_vehicle_model(text)
            logger.info(f"提取车辆型号: {info.vehicle_model}")
        else:
            # 尝试提取所有信息
            info.invoice_amount = self._extract_amount(text)
            logger.info(f"提取金额: {info.invoice_amount}")
            info.owner_name = self._extract_owner_name(text)
            logger.info(f"提取车主: {info.owner_name}")
            info.buyer_name = self._extract_buyer_name(text)
            logger.info(f"提取买方: {info.buyer_name}")
            info.plate_number = self._extract_plate_number(text)
            logger.info(f"提取车牌号: {info.plate_number}")
            info.vehicle_model = self._extract_vehicle_model(text)
            logger.info(f"提取车辆型号: {info.vehicle_model}")
        
        info.engine_number = self._extract_engine_number(text)
        logger.info(f"提取发动机号: {info.engine_number}")
        logger.info(f"{'='*60}\n")
        
        return info
    
    def _extract_vin(self, text: str) -> Optional[str]:
        """提取车架号（带OCR容错）"""
        # 将换行替换为空格（而不是删除），避免不同行文本粘连误匹配
        # 移除常见标点（OCR可能在末尾加点）
        clean_text = text.replace('\n', ' ').replace('.', '').replace(',', '')
        # 合并多个空格为一个
        clean_text = ' '.join(clean_text.split())
        
        # 调试：打印清理后的文本片段（VIN附近）
        if 'LSV' in clean_text or 'VIN' in clean_text:
            # 查找VIN关键词位置
            for keyword in ['VIN', '车辆识别代号', '车架号']:
                idx = clean_text.find(keyword)
                if idx >= 0:
                    # 打印关键词前后各50个字符
                    start = max(0, idx - 50)
                    end = min(len(clean_text), idx + 70)
                    snippet = clean_text[start:end]
                    logger.debug(f"[VIN调试] 关键词'{keyword}'附近文本: ...{snippet}...")
                    break
        
        # 【优先级1】尝试查找带关键词的VIN（最可靠，因为明确标注了是VIN）
        # 【优先级1】尝试查找带关键词的VIN（最可靠，因为明确标注了是VIN）
        vin_keywords = [
            '9.车辆识别代号/车架号',  # 登记证详细格式
            '车辆识别代号/车架号码',
            '车辆识别代号',
            '车架号码',
            '车架号',
            'VIN',
            '识别代号',
            '识别代码'
        ]
        
        for keyword in vin_keywords:
            # 支持冒号、空格、斜杠等多种分隔符（P是允许的）
            # 同时支持宽松匹配（包含I/O/Q）以便后续纠错
            pattern = re.compile(f'{keyword}[:：\\s/]*([A-Z0-9]{{17}})', re.IGNORECASE)
            match = pattern.search(clean_text)
            if match:
                vin_candidate = match.group(1).upper()
                logger.debug(f"[VIN调试] 关键词'{keyword}'匹配到: {vin_candidate}")
                
                # 检查是否需要OCR纠错
                if any(c in vin_candidate for c in ['I', 'O', 'Q']):
                    corrected = self._correct_vin_ocr_errors(vin_candidate)
                    if corrected and self._is_valid_vin_format(corrected):
                        logger.info(f"✓ 通过关键词'{keyword}'匹配到VIN (OCR修正: {vin_candidate} -> {corrected})")
                        return corrected
                else:
                    # 验证格式
                    if self._is_valid_vin_format(vin_candidate):
                        logger.info(f"✓ 通过关键词'{keyword}'匹配到VIN: {vin_candidate}")
                        return vin_candidate
                    else:
                        logger.debug(f"[VIN调试] 关键词匹配但格式校验失败: {vin_candidate}")
        
        # 【优先级2】全文查找VIN（直接匹配，不含I/O/Q）
        matches = self.vin_pattern.findall(clean_text)
        logger.debug(f"[VIN调试] 全文直接匹配结果: {matches}")
        
        # 验证并选择最合理的VIN（优先选择WMI合理的）
        valid_matches = []
        for match in matches:
            if len(match) == 17 and not any(c in match for c in ['I', 'O', 'Q']):
                if self._is_valid_vin_format(match):
                    valid_matches.append(match)
                    logger.debug(f"[VIN调试] 有效候选: {match} (WMI: {match[:3]})")
                else:
                    logger.debug(f"[VIN调试] 直接匹配但格式校验失败: {match}")
        
        # 如果有多个有效匹配，优先选择WMI更像真实制造商代码的
        if valid_matches:
            # 优先选择以LSV/WVW/LFV等常见制造商代码开头的
            common_wmi_prefixes = ['LSV', 'WVW', 'LFV', 'LDC', 'LHG', 'LVS']
            for match in valid_matches:
                if any(match.startswith(prefix) for prefix in common_wmi_prefixes):
                    logger.info(f"✓ 全文直接匹配到VIN (常见WMI): {match}")
                    return match
            # 否则返回第一个有效匹配
            logger.info(f"✓ 全文直接匹配到VIN: {valid_matches[0]}")
            return valid_matches[0]
        
        # 【优先级3】宽松匹配（包含I/O/Q，用于OCR纠错）
        loose_pattern = re.compile(r'[A-Z0-9]{17}')
        loose_matches = loose_pattern.findall(clean_text)
        logger.debug(f"[VIN调试] 宽松匹配结果 (共{len(loose_matches)}个): {loose_matches[:5]}")
        
        valid_loose_matches = []
        for match in loose_matches:
            if len(match) == 17:
                # 检查是否是有效VIN格式
                if not self._is_valid_vin_format(match):
                    logger.debug(f"[VIN调试] 宽松匹配但格式校验失败: {match}")
                    continue
                
                # 尝试修正常见OCR错误
                corrected = self._correct_vin_ocr_errors(match)
                if corrected and not any(c in corrected for c in ['I', 'O', 'Q']):
                    valid_loose_matches.append((match, corrected))
        
        # 如果有多个有效匹配，优先选择WMI更合理的
        if valid_loose_matches:
            common_wmi_prefixes = ['LSV', 'WVW', 'LFV', 'LDC', 'LHG', 'LVS']
            for original, corrected in valid_loose_matches:
                if any(corrected.startswith(prefix) for prefix in common_wmi_prefixes):
                    logger.info(f"✓ VIN OCR修正 (常见WMI): {original} -> {corrected}")
                    return corrected
            # 否则返回第一个有效匹配
            original, corrected = valid_loose_matches[0]
            logger.info(f"✓ VIN OCR修正: {original} -> {corrected}")
            return corrected
        
        logger.warning("[VIN调试] 所有VIN提取方法均未找到有效结果")
        return None
    
    def _is_valid_vin_format(self, vin: str) -> bool:
        """验证VIN格式特征"""
        if not vin or len(vin) != 17:
            return False
        
        # VIN必须包含字母（排除纯数字的发票号、电话号等）
        if not any(c.isalpha() for c in vin):
            logger.debug(f"VIN格式检查失败: {vin} (纯数字)")
            return False
        
        # VIN必须以字母开头（WMI世界制造商代码第1位是字母或数字，但通常是字母）
        # 排除以数字开头的序列（如社会信用代码：91410100MACFUB487）
        if vin[0].isdigit():
            logger.debug(f"VIN格式检查失败: {vin} (数字开头，可能是社会信用代码)")
            return False
        
        # VIN前3位（WMI）必须包含字母
        wmi = vin[:3]
        if not any(c.isalpha() for c in wmi):
            logger.debug(f"VIN格式检查失败: {vin} (WMI前3位无字母)")
            return False
        
        # VIN中字母和数字应该混合出现（不应该全是字母或几乎全是数字）
        alpha_count = sum(1 for c in vin if c.isalpha())
        digit_count = sum(1 for c in vin if c.isdigit())
        
        if alpha_count < 3:  # 至少3个字母
            logger.debug(f"VIN格式检查失败: {vin} (字母少于3个)")
            return False
        
        if digit_count < 3:  # 至少3个数字
            logger.debug(f"VIN格式检查失败: {vin} (数字少于3个)")
            return False
        
        # 排除社会信用代码特征：91或92开头 + 后面有连续多个数字
        if vin.startswith(('91', '92')) and vin[2:6].isdigit():
            logger.debug(f"VIN格式检查失败: {vin} (疑似社会信用代码)")
            return False
        
        return True
    
    def _correct_vin_ocr_errors(self, vin: str) -> Optional[str]:
        """修正VIN码中的OCR错误"""
        if not vin or len(vin) != 17:
            return None
        
        corrected = list(vin)
        
        # VIN码中不允许出现的字符及其可能的正确字符
        # 注意：P是合法字符，不需要修正
        # I -> 1 (数字1)
        # O -> 0 (数字0)
        # Q -> 0 (数字0)
        for i, char in enumerate(corrected):
            if char == 'I':
                # I不允许，可能是1
                corrected[i] = '1'
                logger.debug(f"VIN修正: 位置{i} I -> 1")
            elif char == 'O':
                # O不允许，可能是0
                corrected[i] = '0'
                logger.debug(f"VIN修正: 位置{i} O -> 0")
            elif char == 'Q':
                # Q不允许，可能是0
                corrected[i] = '0'
                logger.debug(f"VIN修正: 位置{i} Q -> 0")
        
        result = ''.join(corrected)
        
        # 验证修正后的VIN是否合理（P是允许的）
        if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', result):
            return result
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[str]:
        """提取金额"""
        logger.debug("尝试提取金额...")
        
        pattern_names = [
            "车价合计+小写",
            "价税合计+小写",
            "合计金额+小写",
            "小写关键词",
            "金价总额",
            "¥符号",
            "￥符号",
            "数字+元"
        ]
        
        for i, pattern in enumerate(self.amount_patterns):
            pattern_name = pattern_names[i] if i < len(pattern_names) else f"模式{i+1}"
            logger.debug(f"  尝试模式: {pattern_name} - {pattern.pattern}")
            
            match = pattern.search(text)
            if match:
                logger.debug(f"  ✓ 匹配成功! 匹配内容: {match.group(0)}")
                amount = match.group(1).replace(',', '').replace('，', '')
                logger.debug(f"    提取的金额: {amount}")
                try:
                    # 验证是否为有效数字
                    float(amount)
                    logger.info(f"  ✓ 金额验证成功: {amount}")
                    return amount
                except ValueError:
                    logger.debug(f"  ✗ 金额验证失败: {amount} 不是有效数字")
                    continue
            else:
                logger.debug(f"  ✗ 未匹配")
        
        logger.warning("所有金额模式均未匹配成功")
        return None
    
    def _extract_plate_number(self, text: str) -> Optional[str]:
        """提取车牌号"""
        clean_text = text.replace(' ', '').replace('\n', '')
        
        for pattern in self.plate_patterns:
            match = pattern.search(clean_text)
            if match:
                if match.groups():
                    return match.group(1)
                else:
                    return match.group(0)
        
        return None
    
    def _extract_owner_name(self, text: str) -> Optional[str]:
        """提取车主姓名（从登记证或行驶证）"""
        lines = text.split('\n')
        
        # 【方法1】完整关键词匹配
        for keyword in self.owner_keywords:
            for i, line in enumerate(lines):
                if keyword in line:
                    # 查找关键词后的内容（支持长公司名，最多40个字）
                    name_match = re.search(f'{keyword}[:：\\s]*([\\u4e00-\\u9fa5]{{2,40}})', line)
                    if name_match:
                        name = name_match.group(1)
                        # 验证名称
                        if self._is_valid_name_or_company(name):
                            logger.debug(f"[车主提取] 在关键词'{keyword}'同行找到: {name}")
                            return name
                    
                    # 收集候选名称（扩大搜索范围到7行，处理OCR错位）
                    candidates = []
                    for j in range(1, min(8, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        
                        # 跳过空行、纯英文/数字行
                        if not next_line or not re.search(r'[\u4e00-\u9fa5]', next_line):
                            continue
                        
                        # 提取2-40个汉字作为姓名/公司名
                        name_match = re.search(r'([\u4e00-\u9fa5]{2,40})', next_line)
                        if name_match:
                            name = name_match.group(1)
                            # 验证名称
                            if self._is_valid_name_or_company(name):
                                # 优先选择包含"公司"、"企业"等的长名称
                                if any(kw in name for kw in ['公司', '企业', '集团', '中心', '单位']):
                                    logger.debug(f"[车主提取] 在关键词'{keyword}'后{j}行找到公司: {name}")
                                    return name
                                candidates.append(name)
                    
                    # 如果没有明确的公司名，返回第一个候选
                    if candidates:
                        logger.debug(f"[车主提取] 在关键词'{keyword}'后找到候选: {candidates[0]}")
                        return candidates[0]
        
        # 【方法2】检测拆分关键词（OCR将"所有人"拆成"所"+"人"）
        logger.debug("[车主提取] 尝试检测拆分关键词...")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # 检测"所"单独出现
            if line_stripped in ['所', '所有', '所 有'] or (len(line_stripped) <= 3 and '所' in line_stripped):
                # 查看后续1-3行是否有"人"
                for j in range(1, min(4, len(lines) - i)):
                    next_line = lines[i + j].strip()
                    if next_line in ['人', '有人', '所人'] or (len(next_line) <= 3 and '人' in next_line and next_line not in ['人数', '载人']):
                        logger.debug(f"[车主提取] 检测到拆分关键词: 行{i}'{line_stripped}' + 行{i+j}'{next_line}'")
                        # 找到拆分的"所有人"，在后续行查找车主
                        candidates = []
                        for k in range(j+1, min(j+8, len(lines) - i)):
                            candidate_line = lines[i + k].strip()
                            # 跳过空行、纯英文/数字行、单字
                            if not candidate_line or len(candidate_line) < 2 or not re.search(r'[\u4e00-\u9fa5]', candidate_line):
                                continue
                            
                            # 提取2-40个汉字
                            name_match = re.search(r'([\u4e00-\u9fa5]{2,40})', candidate_line)
                            if name_match:
                                name = name_match.group(1)
                                if self._is_valid_name_or_company(name):
                                    # 优先选择公司名
                                    if any(kw in name for kw in ['公司', '企业', '集团', '中心', '单位']):
                                        logger.info(f"[车主提取] ✓ 通过拆分关键词找到公司: {name}")
                                        return name
                                    candidates.append(name)
                        
                        if candidates:
                            logger.info(f"[车主提取] ✓ 通过拆分关键词找到: {candidates[0]}")
                            return candidates[0]
                        break  # 找到拆分模式但无候选，跳出内层循环
        
        logger.warning("[车主提取] 所有方法均未找到有效车主")
        return None
    
    def _extract_buyer_name(self, text: str) -> Optional[str]:
        """提取买方姓名（从发票）"""
        # 发票中的买方信息
        buyer_keywords = ['买方', '购买方', '购方名称', '客户名称']
        
        for keyword in buyer_keywords:
            pattern = re.compile(f'{keyword}[:：\\s]*([\\u4e00-\\u9fa5]{{2,40}})')
            match = pattern.search(text)
            if match:
                name = match.group(1)
                # 验证名称（支持公司名）
                if self._is_valid_name_or_company(name):
                    return name
        
        return None
    
    def _is_valid_name(self, name: str) -> bool:
        """验证是否为有效姓名（严格模式，用于2-4个字的短名称）"""
        if not name or len(name) < 2:
            return False
        
        # 检查是否在非姓名词列表中
        if name in self.non_name_words:
            return False
        
        # 检查是否包含非姓名词的一部分
        for non_name in self.non_name_words:
            if non_name in name or name in non_name:
                return False
        
        # 检查是否全是常见地名后缀
        if name.endswith(('市', '省', '区', '县', '镇', '村', '街', '路', '号')):
            return False
        
        # 检查是否包含明显的非名称特征（数字、单位等）
        if any(keyword in name for keyword in ['kg', 'mm', '人', '质量', '尺寸', '载']):
            return False
        
        return True
    
    def _is_valid_name_or_company(self, name: str) -> bool:
        """验证是否为有效姓名或公司名（宽松模式）"""
        if not name or len(name) < 2:
            return False
        
        # 对于短名称（2-4个字），使用严格检查
        if len(name) <= 4:
            return self._is_valid_name(name)
        
        # 对于长名称（>4个字），宽松检查，允许公司名
        # 只过滤明显的地名和文档词汇
        forbidden_in_long_name = [
            '机动车', '登记证', '行驶证', '发票',
            '车辆类型', '品牌型号', '使用性质',
            '所有人', '车主', '车架号', '发动机号',
            '注册日期', '发证日期', '检验记录',
            '身份证明', '统一社会信用代码'
        ]
        
        for forbidden in forbidden_in_long_name:
            if forbidden in name:
                return False
        
        # 如果包含“公司”、“企业”等，很可能是有效的公司名
        return True
    
    def _extract_new_owner_name(self, text: str) -> Optional[str]:
        """提取新车主姓名（从登记证转移登记）"""
        # 登记证中的转移登记信息
        new_owner_keywords = [
            '转入所有人', '现所有人', '现机动车所有人', 
            '受让方', '姓名/名称', '姓名／名称', '姓名', '名称',
            '过户后车主', '转入车主'
        ]
        
        lines = text.split('\n')
        
        for keyword in new_owner_keywords:
            for i, line in enumerate(lines):
                if keyword in line:
                    # 查找关键词后的内容（支持长公司名，最多40个字）
                    name_match = re.search(f'{keyword}[:：\\s]*([\\u4e00-\\u9fa5]{{2,40}})', line)
                    if name_match:
                        name = name_match.group(1)
                        # 验证名称
                        if self._is_valid_name_or_company(name):
                            return name
                    
                    # 尝试后续行（跳过英文/纯数字行，最多查找3行）
                    for j in range(1, min(4, len(lines) - i)):
                        next_line = lines[i + j].strip()
                        
                        # 跳过空行、纯英文/数字行
                        if not next_line or not re.search(r'[\u4e00-\u9fa5]', next_line):
                            continue
                        
                        # 提取2-40个汉字
                        name_match = re.search(r'([\u4e00-\u9fa5]{2,40})', next_line)
                        if name_match:
                            name = name_match.group(1)
                            # 验证名称，确保不是原车主
                            if self._is_valid_name_or_company(name):
                                original_owner = self._extract_owner_name(text)
                                if name != original_owner:
                                    return name
                            # 找到第一个含中文的行后就停止
                            break
        
        return None
    
    def _extract_vehicle_model(self, text: str) -> Optional[str]:
        """提取车辆型号"""
        keywords = ['品牌型号', '车辆型号', '型号']
        
        for keyword in keywords:
            # 在关键词后查找内容（优先匹配包含中文或长度较长的型号）
            # 匹配到下一个明显的文档关键词或多个换行
            pattern = re.compile(
                f'{keyword}[:：\\s]*(.+?)(?=车辆识别代号|发动机|注册日期|档案编号|\\n{{2,}}|$)', 
                re.DOTALL
            )
            match = pattern.search(text)
            if match:
                content = match.group(1).strip()
                # 按行分割，过滤掉纯英文标签行（如"Use Character", "Model"）
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                # 优先选择包含中文或包含汽车品牌标识的行
                for line in lines:
                    # 跳过常见的英文标签
                    if line in ['Use Character', 'Model', 'VIN', 'Engine No.', 'Owner', 'Address']:
                        continue
                    # 包含中文或数字字母混合（且长度>2）
                    if any('\u4e00' <= c <= '\u9fa5' for c in line) or (len(line) > 3 and any(c.isdigit() for c in line)):
                        return line
                
                # 如果没找到合适的，返回第一个非空行
                if lines:
                    return lines[0]
        
        return None
    
    def _extract_engine_number(self, text: str) -> Optional[str]:
        """提取发动机号"""
        match = self.engine_pattern.search(text.replace(' ', ''))
        if match:
            return match.group(1)
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """提取注册日期"""
        # 日期格式：YYYY年MM月DD日 或 YYYY-MM-DD 或 YYYY/MM/DD
        date_patterns = [
            re.compile(r'注册日期[:：]\s*(\d{4}年\d{1,2}月\d{1,2}日)'),
            re.compile(r'注册日期[:：]\s*(\d{4}-\d{1,2}-\d{1,2})'),
            re.compile(r'注册日期[:：]\s*(\d{4}/\d{1,2}/\d{1,2})'),
            re.compile(r'(\d{4}年\d{1,2}月\d{1,2}日)'),
        ]
        
        for pattern in date_patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        
        return None
    
    def merge_info(self, *infos: VehicleInfo) -> VehicleInfo:
        """
        合并多个VehicleInfo对象，优先选择非空值
        
        Args:
            *infos: 多个VehicleInfo对象
            
        Returns:
            合并后的VehicleInfo
        """
        merged = VehicleInfo()
        
        for info in infos:
            if info.vin and not merged.vin:
                merged.vin = info.vin
            if info.invoice_amount and not merged.invoice_amount:
                merged.invoice_amount = info.invoice_amount
            if info.owner_name and not merged.owner_name:
                merged.owner_name = info.owner_name
            if info.buyer_name and not merged.buyer_name:
                merged.buyer_name = info.buyer_name
            if info.new_owner_name and not merged.new_owner_name:
                merged.new_owner_name = info.new_owner_name
            if info.plate_number and not merged.plate_number:
                merged.plate_number = info.plate_number
            if info.vehicle_model and not merged.vehicle_model:
                merged.vehicle_model = info.vehicle_model
            if info.engine_number and not merged.engine_number:
                merged.engine_number = info.engine_number
            if info.register_date and not merged.register_date:
                merged.register_date = info.register_date
        
        return merged


def extract_vehicle_info(ocr_results: List[Dict], doc_type: str = None) -> VehicleInfo:
    """
    从OCR结果中提取车辆信息（便捷函数）
    
    Args:
        ocr_results: OCR识别结果列表
        doc_type: 文档类型
        
    Returns:
        VehicleInfo对象
    """
    # 合并所有文本
    all_text = '\n'.join([result.get('text', '') for result in ocr_results])
    
    extractor = VehicleInfoExtractor()
    return extractor.extract_from_text(all_text, doc_type)
