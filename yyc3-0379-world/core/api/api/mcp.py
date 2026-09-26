"""
@file: app/api/mcp.py
@description: MCP工具统一路由模块 - 集成智谱AI和本地MCP工具
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-04-08
@updated: 2026-04-08
@status: active
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: api,mcp,routing,python,fastapi
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.middleware import auth_required
from app.services.mcp_client import LocalMCPManager
from app.services.mcp_integration import UnifiedMCPManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp")


class MCPToolRequest(BaseModel):
    """MCP工具请求模型"""

    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class MCPToolResponse(BaseModel):
    """MCP工具响应模型"""

    success: bool = Field(..., description="执行是否成功")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    tool_name: str = Field(..., description="工具名称")


class MCPToolsList(BaseModel):
    """MCP工具列表模型"""

    zhipu_tools: List[Dict[str, Any]] = Field(default_factory=list, description="智谱AI工具")
    local_tools: List[Dict[str, Any]] = Field(default_factory=list, description="本地MCP工具")
    total_count: int = Field(..., description="工具总数")


@router.get("/tools", response_model=MCPToolsList)
async def list_all_mcp_tools(user: dict = Depends(auth_required)):
    """
    获取所有可用的MCP工具

    返回智谱AI和本地MCP工具的完整列表
    """
    try:
        manager = UnifiedMCPManager(settings.zhipu_api_key)
        tools = await manager.list_available_tools()
        return MCPToolsList(**tools)
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=MCPToolResponse)
async def execute_mcp_tool(request: MCPToolRequest, user: dict = Depends(auth_required)):
    """
    执行指定的MCP工具

    支持智谱AI和本地MCP工具的统一执行
    """
    try:
        manager = UnifiedMCPManager(settings.zhipu_api_key)
        result = await manager.execute_tool(request.tool_name, request.parameters)

        success = "error" not in result

        return MCPToolResponse(
            success=success,
            result=result if success else {},
            error=result.get("error") if not success else None,
            tool_name=request.tool_name,
        )
    except Exception as e:
        logger.error(f"Failed to execute MCP tool {request.tool_name}: {e}")
        return MCPToolResponse(success=False, error=str(e), tool_name=request.tool_name)


@router.get("/local/tools")
async def list_local_mcp_tools(user: dict = Depends(auth_required)):
    """列出所有本地MCP工具"""
    try:
        manager = LocalMCPManager()
        tools = await manager.list_tools()
        return tools
    except Exception as e:
        logger.error(f"Failed to list local MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local/status")
async def get_local_mcp_status(user: dict = Depends(auth_required)):
    """获取本地MCP服务器状态"""
    try:
        manager = LocalMCPManager()
        status = await manager.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/local/execute", response_model=MCPToolResponse)
async def execute_local_mcp_tool(request: MCPToolRequest, user: dict = Depends(auth_required)):
    """执行本地MCP工具"""
    try:
        manager = LocalMCPManager()
        result = await manager.execute_tool(request.tool_name, request.parameters)

        success = result.get("success", False)

        return MCPToolResponse(
            success=success,
            result=result.get("result", {}) if success else {},
            error=result.get("error") if not success else None,
            tool_name=request.tool_name,
        )
    except Exception as e:
        logger.error(f"Failed to execute local MCP tool {request.tool_name}: {e}")
        return MCPToolResponse(success=False, error=str(e), tool_name=request.tool_name)


@router.post("/web/read")
async def read_webpage(request: dict = Body(...), user: dict = Depends(auth_required)):
    """读取网页内容"""
    manager = UnifiedMCPManager(settings.zhipu_api_key)
    url = request.get("url", "")
    result = await manager.execute_tool("webReader", {"url": url})
    return result


@router.post("/web/search")
async def search_web(request: dict = Body(...), user: dict = Depends(auth_required)):
    """网络搜索"""
    manager = UnifiedMCPManager(settings.zhipu_api_key)
    query = request.get("query", "")
    num_results = request.get("num_results", 5)
    result = await manager.execute_tool(
        "webSearchPrime", {"query": query, "numResults": num_results}
    )
    return result


@router.post("/github/search")
async def search_github(request: dict = Body(...), user: dict = Depends(auth_required)):
    """搜索GitHub仓库文档"""
    manager = UnifiedMCPManager(settings.zhipu_api_key)
    repo = request.get("repo", "")
    query = request.get("query", "")
    result = await manager.execute_tool("search_doc", {"repo": repo, "query": query})
    return result


@router.post("/github/structure")
async def get_github_structure(request: dict = Body(...), user: dict = Depends(auth_required)):
    """获取GitHub仓库结构"""
    manager = UnifiedMCPManager(settings.zhipu_api_key)
    repo = request.get("repo", "")
    result = await manager.execute_tool("get_repo_structure", {"repo": repo})
    return result


@router.post("/filesystem/read")
async def read_file(request: dict = Body(...), user: dict = Depends(auth_required)):
    """读取文件内容"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("read_file", request)
    return result


@router.post("/filesystem/list")
async def list_directory(request: dict = Body(...), user: dict = Depends(auth_required)):
    """列出目录内容"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("list_directory", request)
    return result


@router.get("/docker/containers")
async def list_docker_containers(user: dict = Depends(auth_required)):
    """列出Docker容器"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("list_containers", {})
    return result


@router.post("/docker/logs")
async def get_container_logs(request: dict = Body(...), user: dict = Depends(auth_required)):
    """获取容器日志"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("get_container_logs", request)
    return result


@router.post("/database/query")
async def query_database(request: dict = Body(...), user: dict = Depends(auth_required)):
    """查询数据库"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("query_database", request)
    return result


@router.get("/database/tables")
async def list_database_tables(user: dict = Depends(auth_required)):
    """列出数据库表"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("list_tables", {})
    return result


@router.post("/search")
async def brave_search(request: dict = Body(...), user: dict = Depends(auth_required)):
    """Brave搜索"""
    manager = LocalMCPManager()
    result = await manager.execute_tool("brave_search", request)
    return result


__all__ = ["router"]
