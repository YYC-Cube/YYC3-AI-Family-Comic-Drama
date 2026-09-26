# file: filter.py
# description: 数据过滤工具模块 - 增强版 v2.0（中英文敏感词 + 正则模式）
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-03-21
# updated: 2026-07-24
# status: active
# tags: [util],[filter],[validation],[security]

"""
@file: app/utils/filter.py
@description: 内容过滤器 v2.0，提供中英文敏感词过滤、正则模式检测、内容审核
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-03-19
@updated: 2026-07-24
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,filter,public
"""

import logging
import re
from typing import List, Tuple


class ContentFilter:
    """内容过滤器 v2.0

    能力：
    - 中英文敏感词检测与脱敏
    - 正则模式匹配（手机号、身份证、银行卡等）
    - BASE64/SHA 等编码密钥检测
    - Token / API Key 格式识别
    """

    def __init__(self):
        self.sensitive_words = self._load_sensitive_words()
        self.regex_patterns = self._load_regex_patterns()
        self.logger = logging.getLogger(__name__)

        self.filter_stats = {
            "filtered": 0,
            "blocked": 0,
            "passed": 0,
        }

    def _load_sensitive_words(self) -> List[str]:
        """加载中英文敏感词列表"""
        # ── 英文敏感词 ──
        en_words = [
            "password",
            "pwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "private_key",
            "privatekey",
            "credit_card",
            "creditcard",
            "ssn",
            "social_security",
            "bank_account",
            "bankaccount",
            "routing_number",
            "cvv",
            "pin_code",
            "auth_code",
            "access_key",
            "secret_key",
            "master_key",
            "ssh_key",
            "ssh-privatekey",
            "jwt_secret",
            "session_id",
            "sessionid",
            "csrf_token",
            "csrf-token",
            "bearer",
            "authorization",
        ]
        # ── 中文敏感词 ──
        cn_words = [
            "密码",
            "登录密码",
            "支付密码",
            "交易密码",
            "身份证",
            "身份证号",
            "身份证号码",
            "手机号",
            "手机号码",
            "联系电话",
            "银行卡",
            "银行卡号",
            "信用卡",
            "信用卡号",
            "验证码",
            "短信验证码",
            "登录凭证",
            "授权码",
            "私钥",
            "密钥",
            "API密钥",
            "API秘钥",
            "访问密钥",
            "秘密密钥",
            "令牌",
            "会话ID",
            "会话标识",
        ]
        return en_words + cn_words

    def _load_regex_patterns(self) -> List[Tuple[str, str, str]]:
        """加载正则检测模式

        Returns:
            [(pattern_name, regex, replacement_template), ...]
        """
        return [
            # ── 中国大陆身份证（18位） ──
            (
                "身份证号",
                r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
                "身份证号[已脱敏]",
            ),
            # ── 中国大陆手机号 ──
            (
                "手机号",
                r"\b1[3-9]\d{9}\b",
                "手机号[已脱敏]",
            ),
            # ── 固定电话 ──
            (
                "固定电话",
                r"\b0\d{2,3}[-\s]?\d{7,8}\b",
                "固定电话[已脱敏]",
            ),
            # ── 银行卡号（16-19位数字） ──
            (
                "银行卡号",
                r"\b(?:62|60|58|56|55|54|53|52|51|50|49|48|47|46|45|44|43|42|41|40)\d{14,17}\b",
                "银行卡号[已脱敏]",
            ),
            # ── JWT Token ──
            (
                "JWT",
                r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b",
                "JWT[已脱敏]",
            ),
            # ── API Key 格式（sk- / pk- 开头） ──
            (
                "API Key",
                r"\b(?:sk|pk|sk-ant|sk-live|sk-test|pk-live|pk-test)[-_][a-zA-Z0-9]{20,}\b",
                "API Key[已脱敏]",
            ),
            # ── SHA / MD5 哈希（40位或64位十六进制） ──
            (
                "哈希密钥",
                r"\b[a-fA-F0-9]{32,64}\b",
                None,  # 不自动屏蔽，仅标记
            ),
            # ── BASE64 编码密钥（长度 > 40） ──
            (
                "BASE64密钥",
                r"\b[A-Za-z0-9+/]{40,}={0,2}\b",
                None,
            ),
            # ── 邮箱地址 ──
            (
                "邮箱",
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "邮箱[已脱敏]",
            ),
            # ── IP 地址（内网） ──
            (
                "内网IP",
                r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
                r"|192\.168\.\d{1,3}\.\d{1,3})\b",
                "内网IP[已脱敏]",
            ),
        ]

    def filter_content(self, content: str, mask_char: str = "*") -> Tuple[str, bool]:
        """过滤敏感内容

        Args:
            content: 输入文本
            mask_char: 脱敏字符

        Returns:
            (过滤后内容, 是否被拦截)
        """
        if not content:
            return content, False

        filtered_content = content
        is_blocked = False

        # 1. 敏感词检测
        for word in self.sensitive_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            matches = pattern.findall(filtered_content)

            if matches:
                filtered_content = pattern.sub(
                    mask_char * 4,  # 统一替换为 ****
                    filtered_content,
                )
                self.filter_stats["filtered"] += len(matches)

                if len(matches) > 3:
                    is_blocked = True
                    self.filter_stats["blocked"] += 1

        # 2. 正则模式检测
        for name, regex, replacement in self.regex_patterns:
            if replacement is None:
                # 仅计数，不替换
                matches = re.findall(regex, filtered_content)
                if matches:
                    self.filter_stats["filtered"] += len(matches)
                continue

            pattern = re.compile(regex)
            matches = pattern.findall(filtered_content)
            if matches:
                filtered_content = pattern.sub(replacement, filtered_content)
                self.filter_stats["filtered"] += len(matches)
                if len(matches) > 2:
                    is_blocked = True
                    self.filter_stats["blocked"] += 1

        if not is_blocked:
            self.filter_stats["passed"] += 1

        return filtered_content, is_blocked

    def filter_response(self, response: dict, mask_char: str = "*") -> Tuple[dict, bool]:
        """过滤响应内容"""
        if not response or "choices" not in response:
            return response, False

        is_blocked = False

        for choice in response["choices"]:
            if "message" in choice and "content" in choice["message"]:
                filtered_content, blocked = self.filter_content(
                    choice["message"]["content"], mask_char
                )

                choice["message"]["content"] = filtered_content

                if blocked:
                    is_blocked = True

        return response, is_blocked

    def get_stats(self) -> dict:
        """获取过滤统计"""
        return self.filter_stats.copy()

    def reset_stats(self):
        """重置过滤统计"""
        self.filter_stats = {
            "filtered": 0,
            "blocked": 0,
            "passed": 0,
        }
        self.logger.info("Content filter stats reset")


content_filter = ContentFilter()
