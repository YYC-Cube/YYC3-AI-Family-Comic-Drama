# ==============================================================
# YYC³ AI FAmily 公共基座 BaseAgent v1.0
# 所有 Agent 的统一基类：统一身份、统一提示词结构、统一LLM调用
# 对齐架构：五标体系-标准化 | 五高-高可用（本地兜底降级）
# 依赖：pip install openai（未配置 LLM_BASE_URL 时自动降级 Mock 模式）
# 部署说明：与其他 Agent 文件置于同一包目录即可直接 import
# ==============================================================
import os


class BaseAgent:
    """AI FAmily Agent 统一基类

    三要素：name（人格化名称）/ role（角色定位）/ system_prompt（系统提示词）
    """

    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self._client = None

    def _get_client(self):
        """懒加载 OpenAI 兼容客户端（对接 NIM 模型服务）"""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                api_key=os.getenv("LLM_API_KEY", "nim-local-dummy"),
                timeout=float(os.getenv("LLM_TIMEOUT", "60")),  # 挂死请求防线（M2 收口实测补充）
            )
            self._max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512"))  # 思考模式长生成防线
        return self._client

    def run(self, prompt: str, context: str = "") -> str:
        """统一LLM调用入口

        :param prompt: 任务提示词
        :param context: RAG知识库注入上下文，格式如 "[来源：xxx] 内容"
        :return: 模型输出文本
        """
        user_content = f"{context}\n\n{prompt}" if context else prompt
        try:
            response = self._get_client().chat.completions.create(
                model=os.getenv("LLM_MODEL", "deepseek-v4-pro"),
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                max_tokens=self._max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            # 高可用降级：LLM服务不可用时切Mock模式，保障调试链路可用
            print(f"[{self.name}] LLM调用失败，降级Mock模式：{e}")
            return self._mock_run(prompt)

    def _mock_run(self, prompt: str) -> str:
        """本地兜底：离线调试用，生产环境由双DGX NIM服务承接"""
        return f"[{self.name}|Mock] 已接收任务：{prompt[:100]}..."

    def heartbeat(self) -> dict:
        """心跳信息（供A2A注册中心使用）"""
        return {"agent_name": self.name, "role": self.role, "status": "online"}
