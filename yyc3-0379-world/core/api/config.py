# file: config.py
# description: 应用配置管理模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [config],[settings],[management]

"""
@file: app/config.py
@description: 应用配置模块，提供环境变量和配置管理
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-13
@updated: 2026-03-13
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: config,python,core,public
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_password: str = ""
    replicator_password: str = ""

    ollama_host: str = "host.docker.internal"
    ollama_port: int = 11434
    ollama_backup_host: str = ""  # 第二台 Ollama（如 DGX N1），留空禁用
    ollama_models: str = "/mnt/models"

    openai_api_key: str = ""
    zhipu_api_key: str = ""
    deepseek_api_key: str = ""

    # ── 云适配器基址外部化（默认值=原硬编码，缺 env 行为不变）──
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    openai_base_url: str = "https://api.openai.com/v1"

    # ── 上游池：通用 OpenAI 兼容上游（vLLM/NIM/SGLang/Ollama兼容）──
    # JSON 数组，元素 schema 见 .env.example「上游池」段；为空数组时路由退回旧三段式
    openai_compatible_upstreams: str = "[]"
    # 灰度开关：False 时 chat 路由完全走旧逻辑（云前缀+Ollama 兜底）
    router_enabled: bool = True

    # ── 上游池主动验活（P0-2：学 one-api 渠道自愈）──
    probe_enabled: bool = True
    probe_interval_seconds: int = 60

    prometheus_multiproc_dir: str = "/tmp/prometheus_multiproc"

    # 旧拓扑遗留字段（历史默认 10.200.0.2 已废弃，保留字段兼容 env）
    host_ip: str = ""
    host_ip_suffix: str = "2"

    db_host: str = "postgres"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "yyc3_gpt"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    auth_enabled: bool = True
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    api_keys: str = ""
    admin_api_keys: str = ""  # 管理面密钥（逗号分隔）；空 = 回退 api_keys（兼容单机部署）

    allowed_origins: str = "https://api.0379.world"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.db_password and self.postgres_password:
            self.db_password = self.postgres_password


settings = Settings()
