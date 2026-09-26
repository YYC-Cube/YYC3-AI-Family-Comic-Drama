# file: deepseek.py
# description: DeepSeek Provider - 当前协议与 OpenAI 完全一致，显式继承缺省实现
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [providers],[deepseek],[transform]

"""DeepSeek Provider：协议与 OpenAI 兼容（reasoner 的 reasoning_content 由
调用方服务层处理），此处显式继承缺省实现以占位注册表——未来 DeepSeek 协议
变更（如 beta 字段、prefix-cache 参数）只改本文件。"""

from .base import OpenAICompatProvider


class DeepseekProvider(OpenAICompatProvider):
    name = "deepseek"
