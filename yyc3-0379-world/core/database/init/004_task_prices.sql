-- YYC³ 协同事务任务类型计价表（Phase 5：A2A 成本直报持久化）
-- 作者: YanYuCloudCube Team | 创建: 2026-09-27
-- 语义: 每任务固定 USD 成本（协同事务无 token usage）；管理端点运行时 upsert 落此表，
--       网关/编排器启动加载覆盖内存默认（TASK_TYPE_PRICES 内置表为兜底）。

CREATE TABLE IF NOT EXISTS task_prices (
    task_type VARCHAR(64) PRIMARY KEY,
    price_usd NUMERIC(10,6) DEFAULT 0,             -- USD / 每任务
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
