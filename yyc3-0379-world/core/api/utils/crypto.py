# file: crypto.py
# description: 加密工具函数模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [util],[crypto],[security]

"""
@file: app/utils/crypto.py
@description: 加密工具，提供 API Key 加密解密功能
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,crypto,public
"""

import logging
import os
from typing import Optional

from cryptography.fernet import Fernet


class CryptoManager:
    """加密管理器"""

    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = os.environ.get("ENCRYPTION_KEY")

            if not self.key:
                self.key = Fernet.generate_key()
                logging.warning(
                    "No ENCRYPTION_KEY found, generated a new one. "
                    "Please set ENCRYPTION_KEY environment variable for persistence."
                )
            else:
                self.key = self.key.encode()

        self.fernet = Fernet(self.key)
        self.logger = logging.getLogger(__name__)

    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise

    def encrypt_dict(self, data: dict, keys: list) -> dict:
        """加密字典中的指定字段"""
        encrypted_data = data.copy()
        for key in keys:
            if key in encrypted_data and encrypted_data[key]:
                encrypted_data[key] = self.encrypt(str(encrypted_data[key]))
        return encrypted_data

    def decrypt_dict(self, data: dict, keys: list) -> dict:
        """解密字典中的指定字段"""
        decrypted_data = data.copy()
        for key in keys:
            if key in decrypted_data and decrypted_data[key]:
                try:
                    decrypted_data[key] = self.decrypt(str(decrypted_data[key]))
                except Exception as e:
                    self.logger.warning(f"Failed to decrypt {key}: {e}")
        return decrypted_data


crypto_manager = CryptoManager()
