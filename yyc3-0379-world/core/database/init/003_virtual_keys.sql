-- YYC³ 虚拟密钥与成本计量（P0-1 基础件）
-- 来源: 七项目对标 litellm L1/L2/L3 范式（docs/0379-world-glm5-turbo-20260920/02 文档）
-- 作者: YanYuCloudCube Team
-- 创建: 2026-09-20

-- 虚拟密钥表：PG 自管密钥（成本主权），替代/叠加 env 静态 API_KEYS
CREATE TABLE IF NOT EXISTS virtual_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) NOT NULL UNIQUE,        -- sha256(明文)，明文只在创建响应出现一次
    name VARCHAR(100) NOT NULL,
    owner VARCHAR(100) DEFAULT 'yanyu',
    model_whitelist TEXT[] DEFAULT '{}',          -- 空数组 = 不限模型
    monthly_budget_usd NUMERIC(10,4) DEFAULT 0,   -- 0 = 不限额
    spent_usd NUMERIC(10,4) DEFAULT 0,
    rate_limit_tpm INT DEFAULT 0,                 -- 0 = 不限（tokens per minute）
    status VARCHAR(20) DEFAULT 'active',          -- active / disabled / expired
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_virtual_keys_status ON virtual_keys(status);
CREATE INDEX IF NOT EXISTS idx_virtual_keys_owner ON virtual_keys(owner);

-- 消费流水表：记录 X-YYC3-Upstream 实际服务者（对齐上游透明契约）
CREATE TABLE IF NOT EXISTS spend_logs (
    id BIGSERIAL PRIMARY KEY,
    key_id UUID REFERENCES virtual_keys(id) ON DELETE SET NULL,
    model VARCHAR(100),
    upstream VARCHAR(100),
    capability VARCHAR(20) DEFAULT 'chat',
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    cost_usd NUMERIC(10,6) DEFAULT 0,
    latency_ms INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spend_logs_created_at ON spend_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_spend_logs_key ON spend_logs(key_id, created_at);
CREATE INDEX IF NOT EXISTS idx_spend_logs_model ON spend_logs(model, created_at);

-- 模型计价表：input/output 每 1M token 单价（USD）；本地模型单价 0 仍记 token 保用量可见
CREATE TABLE IF NOT EXISTS model_prices (
    model VARCHAR(100) PRIMARY KEY,
    input_per_m_usd NUMERIC(10,4) DEFAULT 0,
    output_per_m_usd NUMERIC(10,4) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
