# file: pricing.py
# description: 成本计价器 - 模型单价加载 + completion_cost 纯函数（学 litellm L2 范式）
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-09-20
# status: active
# tags: [pricing],[cost],[billing]

"""
@file: app/services/pricing.py
@description: 成本计价器。单价来源优先级：DB model_prices 表 → 环境变量 JSON
             （MODEL_PRICES_JSON）→ 内置默认（全 0）。单价缺失时警告并按 0 计，
             绝不因计价失败阻塞推理主链路。
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelPrice:
    """单模型单价（USD / 1M tokens）"""

    input_per_m: float = 0.0
    output_per_m: float = 0.0


# 内置兜底单价（仅列已开通云模型；本地/DGX 模型单价 0 但仍记 token 保用量可见）
_DEFAULT_PRICES: Dict[str, ModelPrice] = {
    "glm-4-flash": ModelPrice(0.0, 0.0),  # 免费档
    "glm-4-plus": ModelPrice(6.86, 6.86),  # ¥50/1M ≈ $6.86
    "glm-4": ModelPrice(13.7, 13.7),
    "deepseek-chat": ModelPrice(0.27, 1.10),
    "deepseek-coder": ModelPrice(0.27, 1.10),
    "gpt-4o": ModelPrice(2.50, 10.0),
    "gpt-4": ModelPrice(30.0, 60.0),
    "gpt-3.5-turbo": ModelPrice(0.50, 1.50),
}


class PricingCalculator:
    """计价器：completion_cost(tokens × price) 纯函数 + 单价解析"""

    def __init__(self):
        self._prices: Dict[str, ModelPrice] = dict(_DEFAULT_PRICES)
        self._load_env_overrides()

    def _load_env_overrides(self) -> None:
        """MODEL_PRICES_JSON: {"model": {"input": x, "output": y}}（USD/1M tokens）"""
        raw = os.getenv("MODEL_PRICES_JSON", "").strip()
        if not raw:
            return
        try:
            data = json.loads(raw)
            for model, p in data.items():
                self._prices[model] = ModelPrice(
                    input_per_m=float(p.get("input", 0)),
                    output_per_m=float(p.get("output", 0)),
                )
            logger.info(f"MODEL_PRICES_JSON 覆盖 {len(data)} 个模型单价")
        except Exception as e:
            logger.warning(f"MODEL_PRICES_JSON 解析失败（用内置单价）: {e}")

    def get_price(self, model: str) -> Optional[ModelPrice]:
        """查询单价；未登记返回 None（调用方决定是否告警/按 0 计）"""
        price = self._prices.get(model)
        if price is None:
            logger.info(f"模型 {model} 无登记单价（按 0 计，用量仍会记录）")
        return price

    def completion_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """核心纯函数：tokens × price → USD。任何异常按 0 计，绝不抛出。"""
        try:
            price = self._prices.get(model)
            if price is None:
                return 0.0
            cost = (
                prompt_tokens * price.input_per_m / 1_000_000
                + completion_tokens * price.output_per_m / 1_000_000
            )
            return round(cost, 6)
        except Exception as e:
            logger.warning(f"计价异常（按 0 计）: {e}")
            return 0.0

    def upsert_price(self, model: str, input_per_m: float, output_per_m: float) -> None:
        """运行时登记/更新单价（未来管理端点用）"""
        self._prices[model] = ModelPrice(input_per_m, output_per_m)


# ── 协同事务按任务类型固定定价（A2A 成本直报：端点回填 X-A2A-Cost 供中间件记账）──
# 定价语义：每任务 USD 固定成本（无 token usage 可估）；未知类型 0.0 → 中间件兜底常量接管
TASK_TYPE_PRICES = {
    "data_analysis": 0.002,
    "trend_forecast": 0.003,
    "qualitative_analysis": 0.002,
    "report_polish": 0.001,
    "creative_brainstorm": 0.001,
    "content_validation": 0.001,
    "code_review": 0.002,
    "content_formatting": 0.0005,
}


def task_cost(task_type: str) -> float:
    """协同事务固定成本（USD/任务）；未知/空类型 0.0（调用方走兜底常量）。"""
    try:
        return float(TASK_TYPE_PRICES.get((task_type or "").strip(), 0.0))
    except Exception:
        return 0.0


def upsert_task_price(task_type: str, price_usd: float) -> None:
    """运行时登记/更新任务类型单价（内存态；/v1/admin/pricing/task-types 端点用）。

    注意：本表为进程内存态（对齐 MODEL_PRICES_JSON 一次性加载语义）；
    多网关实例部署时各进程需分别设置，或经 TASK_PRICES_JSON 启动统一注入。
    """
    key = (task_type or "").strip()
    if not key:
        raise ValueError("task_type 不能为空")
    if price_usd < 0:
        raise ValueError("price_usd 不能为负")
    TASK_TYPE_PRICES[key] = float(price_usd)


async def load_task_prices_from_db() -> int:
    """启动加载：PG task_prices 表覆盖内存默认（best-effort，DB 不可达用内置表）。

    返回加载数（0 = 无表/无行/DB 不可达，均不阻断启动）。
    """
    try:
        from sqlalchemy import text

        from app.db import engine

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT task_type, price_usd FROM task_prices"))
            rows = result.fetchall()
        for task_type, price_usd in rows:
            TASK_TYPE_PRICES[task_type] = float(price_usd)
        if rows:
            logger.info(f"task_prices 表加载 {len(rows)} 条任务单价（覆盖内存默认）")
        return len(rows)
    except Exception as e:
        logger.warning(f"task_prices 表加载失败（用内存默认表）: {e}")
        return 0


async def upsert_task_price_persisted(task_type: str, price_usd: float) -> bool:
    """管理端点写路径：内存 + PG 双写（ON CONFLICT upsert）。

    返回 PG 落库是否成功；表未迁移/DB 不可达时仅内存生效（不阻断端点，
    响应带 persisted=false 提示运维补迁移）。
    """
    upsert_task_price(task_type, price_usd)  # 校验 + 内存即时生效
    try:
        from sqlalchemy import text

        from app.db import engine

        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO task_prices (task_type, price_usd) VALUES (:t, :p) "
                    "ON CONFLICT (task_type) DO UPDATE SET "
                    "price_usd = EXCLUDED.price_usd, updated_at = CURRENT_TIMESTAMP"
                ),
                {"t": (task_type or "").strip(), "p": float(price_usd)},
            )
        return True
    except Exception as e:
        logger.warning(f"task_prices PG 落库失败（仅内存生效，请执行 004 迁移）: {e}")
        return False


pricing = PricingCalculator()
