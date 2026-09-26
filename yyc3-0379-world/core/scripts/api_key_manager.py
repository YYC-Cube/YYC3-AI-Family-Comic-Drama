#!/usr/bin/env python3
"""
@file: api_key_manager.py
@description: API Key 管理工具 - 生成、验证、管理 API Key
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-04-08
@updated: 2026-04-08
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: api,auth,management,python,tools
"""

import argparse
import hashlib
import secrets
import sys
from datetime import datetime
from typing import List, Optional


class APIKeyManager:
    """API Key 管理器"""

    def __init__(self):
        self.prefix = "yyc3_api_key"

    def generate(self, suffix: Optional[str] = None) -> str:
        """
        生成新的 API Key

        Args:
            suffix: 可选的后缀标识（如 dev, prod, test）

        Returns:
            生成的 API Key
        """
        if suffix:
            return f"{self.prefix}_{suffix}_{secrets.token_hex(16)}"
        return f"{self.prefix}_{secrets.token_hex(16)}"

    def hash_key(self, api_key: str) -> str:
        """
        计算 API Key 的哈希值

        Args:
            api_key: API Key

        Returns:
            SHA256 哈希值
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def validate_format(self, api_key: str) -> bool:
        """
        验证 API Key 格式

        Args:
            api_key: API Key

        Returns:
            是否符合格式要求
        """
        return api_key.startswith(self.prefix)

    def generate_batch(self, count: int, suffix: Optional[str] = None) -> List[str]:
        """
        批量生成 API Key

        Args:
            count: 生成数量
            suffix: 可选的后缀标识

        Returns:
            API Key 列表
        """
        return [self.generate(suffix) for _ in range(count)]

    def export_env(self, api_keys: List[str]) -> str:
        """
        导出为 .env 格式

        Args:
            api_keys: API Key 列表

        Returns:
            .env 格式的字符串
        """
        return f"API_KEYS={','.join(api_keys)}"

    def export_json(self, api_keys: List[str]) -> str:
        """
        导出为 JSON 格式

        Args:
            api_keys: API Key 列表

        Returns:
            JSON 格式的字符串
        """
        import json

        return json.dumps(
            {
                "api_keys": api_keys,
                "generated_at": datetime.utcnow().isoformat(),
                "count": len(api_keys),
            },
            indent=2,
        )


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="YYC³ API Key 管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成单个 API Key
  python api_key_manager.py generate

  # 生成带后缀的 API Key
  python api_key_manager.py generate --suffix dev

  # 批量生成 5 个 API Key
  python api_key_manager.py generate --count 5

  # 导出为 .env 格式
  python api_key_manager.py generate --count 3 --format env

  # 导出为 JSON 格式
  python api_key_manager.py generate --count 3 --format json

  # 计算 API Key 哈希值
  python api_key_manager.py hash --key "yyc3_api_key_xxx"

  # 验证 API Key 格式
  python api_key_manager.py validate --key "yyc3_api_key_xxx"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # generate 命令
    gen_parser = subparsers.add_parser("generate", help="生成 API Key")
    gen_parser.add_argument("--suffix", help="API Key 后缀标识（如 dev, prod, test）")
    gen_parser.add_argument("--count", type=int, default=1, help="生成数量（默认：1）")
    gen_parser.add_argument(
        "--format",
        choices=["plain", "env", "json"],
        default="plain",
        help="输出格式（plain/env/json）",
    )

    # hash 命令
    hash_parser = subparsers.add_parser("hash", help="计算 API Key 哈希值")
    hash_parser.add_argument("--key", required=True, help="API Key")

    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证 API Key 格式")
    val_parser.add_argument("--key", required=True, help="API Key")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = APIKeyManager()

    if args.command == "generate":
        keys = manager.generate_batch(args.count, args.suffix)

        if args.format == "plain":
            for key in keys:
                print(key)
        elif args.format == "env":
            print(manager.export_env(keys))
        elif args.format == "json":
            print(manager.export_json(keys))

    elif args.command == "hash":
        hash_value = manager.hash_key(args.key)
        print(f"API Key: {args.key}")
        print(f"SHA256:  {hash_value}")

    elif args.command == "validate":
        is_valid = manager.validate_format(args.key)
        print(f"API Key: {args.key}")
        print(f"Valid:   {'✅ Yes' if is_valid else '❌ No'}")


if __name__ == "__main__":
    main()
