# file: logger.py
# description: 日志记录工具模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [util],[logger],[monitoring]

"""
@file: app/utils/logger.py
@description: 日志管理器，提供结构化日志记录功能
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,logger,public
"""

import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._setup_handlers(max_bytes, backup_count)

    def _setup_handlers(self, max_bytes: int, backup_count: int):
        """设置日志处理器"""

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """格式化日志"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            **kwargs,
        }
        return json.dumps(log_data, ensure_ascii=False)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def critical(self, message: str, **kwargs):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(self._format_log("CRITICAL", message, **kwargs))

    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self.logger.exception(self._format_log("ERROR", message, **kwargs))


logger = StructuredLogger("yyc3")
api_logger = StructuredLogger("yyc3.api")
db_logger = StructuredLogger("yyc3.db")
cache_logger = StructuredLogger("yyc3.cache")


def get_logger(name: str) -> logging.Logger:
    """获取标准 logging.Logger 实例"""
    return logging.getLogger(name)
