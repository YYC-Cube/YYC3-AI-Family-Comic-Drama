# file: models.py
# description: 数据模型定义模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [models],[schema],[data]

# @file models.py
# @description FastAPI 数据模型定义
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-03-14
# @updated 2026-03-14
# @status stable
# @license MIT
# @copyright Copyright (c) 2026 YanYuCloudCube Team
# @tags python,fastapi,models

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    id: str = Field(..., description="模型唯一标识")
    display_name: str = Field(..., description="前端友好名称")
    backend: Literal["local", "openai", "zhipu", "deepseek", "ollama", "upstream"] = Field(
        ..., description="后端类型"
    )
    version: Optional[str] = None
    enabled: bool = True
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="最大 Token 数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[float] = None
    cost_per_1k_tokens: float = Field(default=0.0, ge=0.0, description="每 1k Token 成本（USD）")


class ModelStat(BaseModel):
    model_id: str = Field(..., description="模型 ID")
    usage_count: int = Field(0, ge=0, description="本月请求次数")
    avg_latency_ms: float = Field(0.0, ge=0.0, description="平均延迟（毫秒）")
    error_rate: float = Field(0.0, ge=0.0, le=1.0, description="错误率（0-1）")
    total_tokens: int = Field(0, ge=0, description="总 Token 数")


class ErrorRecord(BaseModel):
    id: str = Field(..., description="错误 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    model_id: str = Field(..., description="模型 ID")
    error_type: Literal["timeout", "validation", "quota", "internal"] = Field(
        ..., description="错误类型"
    )
    message: str = Field(..., description="错误消息")
    stack: Optional[str] = Field(None, description="错误堆栈")


class UsageSummary(BaseModel):
    total_requests: int = Field(0, ge=0, description="总请求数")
    total_tokens: int = Field(0, ge=0, description="总 Token 数")
    cost_usd: float = Field(0.0, ge=0.0, description="总成本（USD）")


class MCPToolRequest(BaseModel):
    tool_name: str = Field(..., description="工具名称")
    parameters: dict = Field(default={}, description="工具参数")


class MCPToolResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    result: dict = Field(default={}, description="工具执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    tool_name: str = Field(..., description="工具名称")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间")


class MCPToolInfo(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: str = Field(..., description="工具分类")
    parameters: dict = Field(default={}, description="参数定义")


class MCPToolsList(BaseModel):
    zhipu_tools: list[MCPToolInfo] = Field(default=[], description="智谱AI工具")
    local_tools: list[dict] = Field(default=[], description="本地MCP工具")
    total_count: int = Field(..., description="总工具数量")


class PingResponse(BaseModel):
    status: str = Field("ok", description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
