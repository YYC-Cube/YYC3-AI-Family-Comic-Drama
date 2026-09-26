# file: mcp_client.py
# description: MCP 客户端服务模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [service],[mcp],[client]

# @file mcp_client.py
# @description MCP客户端，用于调用本地MCP服务器
# @author YanYuCloudCube Team <admin@0379.email>
# @version v1.0.0
# @created 2026-03-14
# @status dev
# @license MIT
# @copyright Copyright (c) 2026 YanYuCloudCube Team
# @tags mcp,client,python,asyncio

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClient:
    """MCP客户端，用于调用本地MCP服务器"""

    def __init__(self, mcp_config_path: str = None):
        """
        初始化MCP客户端

        Args:
            mcp_config_path: MCP配置文件路径
        """
        self.mcp_config_path = mcp_config_path or self._find_mcp_config()
        self.mcp_config = self._load_mcp_config()
        self.tool_to_server = self._build_tool_mapping()

    def _find_mcp_config(self) -> str:
        """查找MCP配置文件"""
        possible_paths = [
            "/app/config/mcp_config.json",
            os.getenv("MCP_CONFIG_PATH", ""),
            os.path.expanduser("~/.config/claude/mcp_config.json"),
            "./mcp_config.json",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found MCP config at: {path}")
                return path

        logger.warning("No MCP config found, using empty config")
        return "{}"

    def _load_mcp_config(self) -> Dict[str, Any]:
        """加载MCP配置"""
        try:
            with open(self.mcp_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Loaded MCP config with {len(config.get('mcpServers', {}))} servers")
                return config
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            return {"mcpServers": {}}

    def _build_tool_mapping(self) -> Dict[str, str]:
        """构建工具到MCP服务器的映射"""
        return {
            # 文件系统工具
            "read_file": "mcp-filesystem",
            "write_file": "mcp-filesystem",
            "list_directory": "mcp-filesystem",
            "search_files": "mcp-filesystem",
            "get_file_info": "mcp-filesystem",
            # Docker工具
            "list_containers": "mcp-docker",
            "get_container_logs": "mcp-docker",
            "start_container": "mcp-docker",
            "stop_container": "mcp-docker",
            "inspect_container": "mcp-docker",
            # PostgreSQL工具
            "query_database": "mcp-postgres",
            "list_tables": "mcp-postgres",
            "execute_sql": "mcp-postgres",
            "get_table_schema": "mcp-postgres",
            # GitHub工具
            "search_repositories": "mcp-github-yyc3",
            "get_repository": "mcp-github-yyc3",
            "list_issues": "mcp-github-yyc3",
            "get_file_content": "mcp-github-yyc3",
            # 搜索工具
            "brave_search": "mcp-brave-search",
            "web_search": "mcp-brave-search",
            # YYC3中文助手
            "yyc3_cn_translate": "yyc3-cn-assistant",
            "yyc3_cn_analyze": "yyc3-cn-assistant",
            "yyc3_cn_optimize": "yyc3-cn-assistant",
        }

    def find_mcp_server_for_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """根据工具名称查找对应的MCP服务器"""
        server_name = self.tool_to_server.get(tool_name)
        if server_name:
            return self.mcp_config.get("mcpServers", {}).get(server_name, {})
        return None

    def build_mcp_command(self, mcp_server: Dict, tool_name: str, parameters: Dict) -> List[str]:
        """构建MCP调用命令"""
        command = mcp_server.get("command", "")
        args = mcp_server.get("args", [])
        env = mcp_server.get("env", {})

        # 处理环境变量中的占位符
        processed_env = {}
        for key, value in env.items():
            if value.startswith("${") and value.endswith("}"):
                env_var_name = value[2:-1]
                processed_env[key] = os.getenv(env_var_name, "")
            else:
                processed_env[key] = value

        # 构建命令列表
        cmd_parts = [command] + args

        return cmd_parts, processed_env

    async def execute_mcp_command(self, command: List[str], env: Dict[str, str]) -> Dict[str, Any]:
        """执行MCP命令"""
        try:
            # 创建子进程
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **env},
            )

            # 设置超时
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception("MCP command timeout after 30 seconds")

            # 检查返回码
            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(
                    f"MCP command failed with return code {process.returncode}: {error_msg}"
                )
                raise Exception(f"Command failed: {error_msg}")

            # 解析JSON输出
            try:
                output = stdout.decode("utf-8", errors="ignore")
                result = json.loads(output)
                return result
            except json.JSONDecodeError:
                # 如果不是JSON，返回原始输出
                return {"output": stdout.decode("utf-8", errors="ignore")}

        except FileNotFoundError:
            raise Exception(f"Command not found: {command[0]}")
        except Exception as e:
            logger.error(f"Error executing MCP command: {e}")
            raise

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具

        Args:
            tool_name: 工具名称
            parameters: 工具参数

        Returns:
            工具执行结果
        """
        try:
            # 查找对应的MCP服务器配置
            mcp_server = self.find_mcp_server_for_tool(tool_name)
            if not mcp_server:
                return {
                    "success": False,
                    "error": f"MCP server not found for tool: {tool_name}",
                    "tool_name": tool_name,
                }

            # 构建MCP调用命令
            command, env = self.build_mcp_command(mcp_server, tool_name, parameters)

            logger.info(f"Executing MCP tool: {tool_name}")
            logger.debug(f"Command: {' '.join(command)}")

            # 执行命令
            result = await self.execute_mcp_command(command, env)

            return {"success": True, "result": result, "tool_name": tool_name}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"success": False, "error": str(e), "tool_name": tool_name}

    async def list_available_tools(self) -> Dict[str, Any]:
        """列出所有可用的MCP工具"""
        # 为每个工具生成描述
        tool_descriptions = {
            # 文件系统工具
            "read_file": {
                "name": "read_file",
                "description": "读取文件内容",
                "category": "filesystem",
            },
            "write_file": {
                "name": "write_file",
                "description": "写入文件",
                "category": "filesystem",
            },
            "list_directory": {
                "name": "list_directory",
                "description": "列出目录内容",
                "category": "filesystem",
            },
            "search_files": {
                "name": "search_files",
                "description": "搜索文件",
                "category": "filesystem",
            },
            "get_file_info": {
                "name": "get_file_info",
                "description": "获取文件信息",
                "category": "filesystem",
            },
            # Docker工具
            "list_containers": {
                "name": "list_containers",
                "description": "列出Docker容器",
                "category": "docker",
            },
            "get_container_logs": {
                "name": "get_container_logs",
                "description": "获取容器日志",
                "category": "docker",
            },
            "start_container": {
                "name": "start_container",
                "description": "启动容器",
                "category": "docker",
            },
            "stop_container": {
                "name": "stop_container",
                "description": "停止容器",
                "category": "docker",
            },
            "inspect_container": {
                "name": "inspect_container",
                "description": "检查容器详情",
                "category": "docker",
            },
            # PostgreSQL工具
            "query_database": {
                "name": "query_database",
                "description": "查询数据库",
                "category": "database",
            },
            "list_tables": {
                "name": "list_tables",
                "description": "列出数据库表",
                "category": "database",
            },
            "execute_sql": {
                "name": "execute_sql",
                "description": "执行SQL语句",
                "category": "database",
            },
            "get_table_schema": {
                "name": "get_table_schema",
                "description": "获取表结构",
                "category": "database",
            },
            # GitHub工具
            "search_repositories": {
                "name": "search_repositories",
                "description": "搜索GitHub仓库",
                "category": "github",
            },
            "get_repository": {
                "name": "get_repository",
                "description": "获取GitHub仓库信息",
                "category": "github",
            },
            "list_issues": {
                "name": "list_issues",
                "description": "列出GitHub Issues",
                "category": "github",
            },
            "get_file_content": {
                "name": "get_file_content",
                "description": "获取GitHub文件内容",
                "category": "github",
            },
            # 搜索工具
            "brave_search": {
                "name": "brave_search",
                "description": "Brave搜索引擎",
                "category": "search",
            },
            "web_search": {
                "name": "web_search",
                "description": "网络搜索",
                "category": "search",
            },
            # YYC3中文助手
            "yyc3_cn_translate": {
                "name": "yyc3_cn_translate",
                "description": "YYC3中文翻译",
                "category": "yyc3",
            },
            "yyc3_cn_analyze": {
                "name": "yyc3_cn_analyze",
                "description": "YYC3中文分析",
                "category": "yyc3",
            },
            "yyc3_cn_optimize": {
                "name": "yyc3_cn_optimize",
                "description": "YYC3中文优化",
                "category": "yyc3",
            },
        }

        # 按类别组织工具
        categorized_tools = {}
        for tool_name, tool_info in tool_descriptions.items():
            category = tool_info["category"]
            if category not in categorized_tools:
                categorized_tools[category] = []

            # 添加MCP服务器信息
            server_name = self.tool_to_server.get(tool_name, "")
            tool_info["mcp_server"] = server_name
            tool_info["enabled"] = server_name in self.mcp_config.get("mcpServers", {})

            categorized_tools[category].append(tool_info)

        return {
            "categorized_tools": categorized_tools,
            "total_count": len(tool_descriptions),
            "enabled_count": sum(
                len(tools)
                for tools in categorized_tools.values()
                if any(t["enabled"] for t in tools)
            ),
        }

    async def get_mcp_server_status(self) -> Dict[str, Any]:
        """获取MCP服务器状态"""
        servers = self.mcp_config.get("mcpServers", {})
        status = {}

        for server_name, server_config in servers.items():
            try:
                # 尝试获取第一个工具来测试服务器状态
                tool_name = next(
                    (k for k, v in self.tool_to_server.items() if v == server_name),
                    None,
                )
                if tool_name:
                    result = await self.call_tool(tool_name, {"test": True})
                    status[server_name] = {
                        "status": "online" if result.get("success") else "offline",
                        "command": server_config.get("command", ""),
                        "error": (result.get("error") if not result.get("success") else None),
                    }
                else:
                    status[server_name] = {
                        "status": "unknown",
                        "command": server_config.get("command", ""),
                        "error": "No tools found",
                    }
            except Exception as e:
                status[server_name] = {
                    "status": "error",
                    "command": server_config.get("command", ""),
                    "error": str(e),
                }

        return status


class LocalMCPManager:
    """本地MCP工具管理器"""

    def __init__(self, mcp_config_path: str = None):
        """初始化本地MCP管理器"""
        self.client = MCPClient(mcp_config_path)

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行本地MCP工具"""
        return await self.client.call_tool(tool_name, parameters)

    async def list_tools(self) -> Dict[str, Any]:
        """列出所有本地MCP工具"""
        return await self.client.list_available_tools()

    async def get_status(self) -> Dict[str, Any]:
        """获取MCP服务器状态"""
        return await self.client.get_mcp_server_status()
