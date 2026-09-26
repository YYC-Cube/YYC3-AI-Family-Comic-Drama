# file: schemas.py
# description: API 数据模式定义模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [api],[schema],[validation]

"""
@file: app/api/schemas.py
@description: API 请求和响应的数据模型定义，包含输入验证
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: schemas,python,api,public
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """消息模型"""

    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, max_length=100000, description="消息内容")

    @validator("content")
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("消息内容不能为空")
        return v.strip()


class CompletionRequest(BaseModel):
    """聊天完成请求模型"""

    model: str = Field(..., min_length=1, max_length=100, description="模型标识")
    messages: List[Message] = Field(..., min_items=1, max_items=50, description="消息列表")
    max_tokens: Optional[int] = Field(None, ge=1, le=128000, description="最大生成 Token 数")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p 参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    user_id: Optional[str] = Field(None, max_length=100, description="用户 ID")

    @validator("model")
    def validate_model(cls, v):
        if not v or not v.strip():
            raise ValueError("模型名称不能为空")
        return v.strip()

    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("消息列表不能为空")

        total_length = sum(len(m.content) for m in v)
        if total_length > 1000000:
            raise ValueError("消息总长度超过限制")

        return v

    @validator("user_id")
    def validate_user_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError("用户 ID 不能为空字符串")
        return v.strip() if v else None


class CompletionResponse(BaseModel):
    """聊天完成响应模型"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str
    message: str
    status_code: int
    details: Optional[Dict[str, Any]] = None


class ModelConfig(BaseModel):
    """模型配置模型"""

    id: str
    display_name: str
    backend: str
    enabled: bool
    max_tokens: int
    temperature: float
    top_p: float
    cost_per_1k_tokens: float


class ModelStat(BaseModel):
    """模型统计模型"""

    model_id: str
    usage_count: int
    avg_latency_ms: float
    error_rate: float
    total_tokens: int


class ErrorRecord(BaseModel):
    """错误记录模型"""

    id: str
    timestamp: str
    model: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None


class UsageSummary(BaseModel):
    """使用摘要模型"""

    total_requests: int
    total_tokens: int
    cost_usd: float


class PingResponse(BaseModel):
    """健康检查响应模型"""

    status: str


class MCPToolRequest(BaseModel):
    """MCP 工具请求模型"""

    tool_name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

    @validator("tool_name")
    def validate_tool_name(cls, v):
        if not v or not v.strip():
            raise ValueError("工具名称不能为空")
        return v.strip()


class MCPToolResponse(BaseModel):
    """MCP 工具响应模型"""

    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tool_name: str


class MCPToolsList(BaseModel):
    """MCP 工具列表模型"""

    tools: List[Dict[str, Any]]
