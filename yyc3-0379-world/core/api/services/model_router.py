# file: model_router.py
# description: 模型路由器 - 智能路由、负载均衡、动态权重反馈循环
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-04-08
# updated: 2026-07-10
# status: active
# tags: [router],[loadbalancer],[high-availability],[dynamic-weight]

"""
@file: app/services/model_router.py
@description: 模型路由器，基于真实负载数据的动态权重反馈循环
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-04-08
@updated: 2026-07-10
@status: stable
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
@tags: router,loadbalancer,high-availability
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class RoutingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_LATENCY = "weighted_latency"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    ADAPTIVE = "adaptive"


@dataclass
class RequestRecord:
    """单次请求记录，用于动态权重计算"""

    timestamp: float
    latency: float
    success: bool
    tokens: int = 0


@dataclass
class NodeInfo:
    node_id: str
    node_type: str
    models: List[str]
    capacity: int
    current_load: int = 0
    latency: float = 0.0
    status: NodeStatus = NodeStatus.HEALTHY
    last_check: datetime = field(default_factory=datetime.now)
    success_rate: float = 1.0
    total_requests: int = 0
    failed_requests: int = 0
    # ── v2.0 动态权重字段 ──
    ewma_latency: float = 0.0  # EWMA平滑延迟（ms）
    ewma_error_rate: float = 0.0  # EWMA平滑错误率
    dynamic_weight: float = 1.0  # 计算得出的动态权重
    recent_records: deque = field(default_factory=lambda: deque(maxlen=200))
    last_weight_update: float = field(default_factory=time.time)


class NoAvailableNodeError(Exception):
    pass


class ModelRouter:
    """
    模型路由器 v2.0

    新增能力：
    - ADAPTIVE 策略：基于EWMA延迟+错误率+负载的动态权重
    - record_result()：请求完成后上报真实数据，形成反馈循环
    - _update_dynamic_weights()：周期性重新计算所有节点权重
    """

    # EWMA平滑因子（越大越敏感，0~1）
    EWMA_ALPHA = 0.3
    # 动态权重更新间隔（秒）
    WEIGHT_UPDATE_INTERVAL = 10.0
    # 健康检查间隔（秒）
    HEALTH_CHECK_INTERVAL = 15.0
    # 降级阈值
    DEGRADED_ERROR_THRESHOLD = 0.15  # 错误率>15% → DEGRADED
    DEGRADED_LATENCY_THRESHOLD = 5000  # 延迟>5s → DEGRADED

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.nodes: Dict[str, NodeInfo] = {}
        self.routing_strategy = RoutingStrategy.ADAPTIVE
        self._round_robin_index = 0
        self._lock = asyncio.Lock()
        self._weight_task: Optional[asyncio.Task] = None

        self._initialize_nodes()

    def _initialize_nodes(self):
        self.nodes = {
            "yyc3-22": NodeInfo(
                node_id="yyc3-22",
                node_type="ollama",
                models=["llama3.2", "qwen2.5", "deepseek-r1", "mistral"],
                capacity=100,
                latency=50.0,
            ),
            "yyc3-33": NodeInfo(
                node_id="yyc3-33",
                node_type="cloud",
                models=["glm-4-flash", "glm-4-plus", "glm-4-long"],
                capacity=200,
                latency=100.0,
            ),
            "yyc3-45": NodeInfo(
                node_id="yyc3-45",
                node_type="hybrid",
                models=["mixtral", "codellama", "starcoder"],
                capacity=150,
                latency=80.0,
            ),
        }
        # 初始化EWMA为静态初始值
        for node in self.nodes.values():
            node.ewma_latency = node.latency

    # ── 路由选择 ──────────────────────────────────────────

    async def route_request(self, model: str, request: dict) -> str:
        async with self._lock:
            candidate_nodes = [
                node_id
                for node_id, node_info in self.nodes.items()
                if model in node_info.models
                and node_info.status in (NodeStatus.HEALTHY, NodeStatus.DEGRADED)
            ]

            if not candidate_nodes:
                raise NoAvailableNodeError(f"No available node for model: {model}")

            # DEGRADED节点降权但不排除
            strategy = self.routing_strategy
            if strategy == RoutingStrategy.ADAPTIVE:
                selected = self._select_adaptive(candidate_nodes)
            elif strategy == RoutingStrategy.WEIGHTED_LATENCY:
                selected = self._select_by_weighted_latency(candidate_nodes)
            elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
                selected = self._select_by_least_connections(candidate_nodes)
            elif strategy == RoutingStrategy.RANDOM:
                selected = self._select_by_random(candidate_nodes)
            else:
                selected = self._select_by_round_robin(candidate_nodes)

            self.nodes[selected].current_load += 1
            self.nodes[selected].total_requests += 1

            logger.info(
                f"Routed model={model} → node={selected} "
                f"(strategy={strategy.value}, weight={self.nodes[selected].dynamic_weight:.3f})"
            )
            return selected

    def _select_adaptive(self, nodes: List[str]) -> str:
        """
        自适应策略：综合动态权重（EWMA延迟 + 错误率 + 实时负载）

        权重 = (capacity_ratio) × (1 - error_rate) / (ewma_latency_norm + 0.1)
        """
        # 确保权重是最新的
        now = time.time()
        for nid in nodes:
            if now - self.nodes[nid].last_weight_update > self.WEIGHT_UPDATE_INTERVAL:
                self._recompute_weight(nid)

        weights = {}
        for nid in nodes:
            node = self.nodes[nid]
            # 负载比（剩余容量占比）
            load_ratio = max(0.01, 1.0 - node.current_load / node.capacity)
            # 状态惩罚：DEGRADED节点权重×0.3
            status_penalty = 0.3 if node.status == NodeStatus.DEGRADED else 1.0
            # 延迟归一化（基准500ms）
            latency_norm = min(node.ewma_latency / 500.0, 5.0)
            # 综合权重
            weight = (
                load_ratio
                * (1.0 - node.ewma_error_rate)
                / (latency_norm + 0.1)
                * node.dynamic_weight
                * status_penalty
            )
            weights[nid] = max(weight, 0.001)  # 最小权重防止除零

        # 加权随机选择（避免单节点过载）
        total = sum(weights.values())
        import random

        r = random.uniform(0, total)
        cumulative = 0.0
        for nid, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return nid
        return nodes[-1]

    def _recompute_weight(self, node_id: str):
        """根据最近请求记录重新计算节点动态权重"""
        node = self.nodes[node_id]
        records = list(node.recent_records)
        if not records:
            return

        now = time.time()
        # 只看最近5分钟的数据
        recent = [r for r in records if now - r.timestamp < 300]
        if not recent:
            return

        # 计算平均延迟和错误率
        avg_lat = sum(r.latency for r in recent) / len(recent)
        errors = sum(1 for r in recent if not r.success)
        error_rate = errors / len(recent)

        # EWMA平滑
        node.ewma_latency = self.EWMA_ALPHA * avg_lat + (1 - self.EWMA_ALPHA) * node.ewma_latency
        node.ewma_error_rate = (
            self.EWMA_ALPHA * error_rate + (1 - self.EWMA_ALPHA) * node.ewma_error_rate
        )

        # 状态升降级
        if node.ewma_error_rate > self.DEGRADED_ERROR_THRESHOLD:
            node.status = NodeStatus.DEGRADED
        elif (
            node.status == NodeStatus.DEGRADED
            and node.ewma_error_rate < self.DEGRADED_ERROR_THRESHOLD / 2
            and node.ewma_latency < self.DEGRADED_LATENCY_THRESHOLD
        ):
            node.status = NodeStatus.HEALTHY

        node.last_weight_update = now
        node.success_rate = 1.0 - node.ewma_error_rate

    # ── 反馈循环：请求完成后上报 ──────────────────────────

    async def record_result(
        self,
        node_id: str,
        model: str,
        latency: float,
        success: bool,
        tokens: int = 0,
    ):
        """
        上报请求执行结果，形成负载数据反馈循环

        Args:
            node_id: 执行节点ID
            model: 模型名
            latency: 实际延迟（ms）
            success: 是否成功
            tokens: 消耗的token数
        """
        node = self.nodes.get(node_id)
        if not node:
            return

        node.current_load = max(0, node.current_load - 1)

        record = RequestRecord(
            timestamp=time.time(),
            latency=latency,
            success=success,
            tokens=tokens,
        )
        node.recent_records.append(record)

        if not success:
            node.failed_requests += 1

        # 懒更新权重（超过间隔才重新计算）
        now = time.time()
        if now - node.last_weight_update > self.WEIGHT_UPDATE_INTERVAL:
            self._recompute_weight(node_id)

    # ── 传统策略保留 ──────────────────────────────────────

    def _select_by_weighted_latency(self, nodes: List[str]) -> str:
        weights = {}
        for node_id in nodes:
            node = self.nodes[node_id]
            weight = (
                (node.capacity / (node.current_load + 1)) / (node.latency + 1) * node.success_rate
            )
            weights[node_id] = weight
        return max(weights.items(), key=lambda x: x[1])[0]

    def _select_by_least_connections(self, nodes: List[str]) -> str:
        return min(nodes, key=lambda x: self.nodes[x].current_load)

    def _select_by_round_robin(self, nodes: List[str]) -> str:
        selected = nodes[self._round_robin_index % len(nodes)]
        self._round_robin_index += 1
        return selected

    def _select_by_random(self, nodes: List[str]) -> str:
        import random

        return random.choice(nodes)

    # ── 健康检查 ──────────────────────────────────────────

    async def health_check(self):
        tasks = [self._check_node_health(node_id) for node_id in self.nodes.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_node_health(self, node_id: str):
        node = self.nodes[node_id]
        try:
            start = time.monotonic()
            if node.node_type == "ollama":
                url = f"http://{node_id}:11434/api/tags"
            else:
                url = f"http://{node_id}:8000/health"

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

            measured = (time.monotonic() - start) * 1000

            if response.status_code == 200:
                node.status = (
                    NodeStatus.HEALTHY
                    if node.status != NodeStatus.DEGRADED
                    else NodeStatus.DEGRADED
                )
                node.latency = measured
                node.last_check = datetime.now()
                logger.debug(f"Node {node_id} healthy, latency: {measured:.0f}ms")
            else:
                node.status = NodeStatus.UNHEALTHY
                logger.warning(f"Node {node_id} returned status {response.status_code}")
        except Exception as e:
            node.status = NodeStatus.UNHEALTHY
            node.failed_requests += 1
            logger.error(f"Health check failed for {node_id}: {e}")

    # ── 释放节点（兼容旧接口） ────────────────────────────

    def release_node(self, node_id: str, success: bool = True):
        """释放节点负载（同步版，兼容旧代码）"""
        if node_id in self.nodes:
            self.nodes[node_id].current_load = max(0, self.nodes[node_id].current_load - 1)
            if not success:
                self.nodes[node_id].failed_requests += 1

    # ── 统计与管理 ────────────────────────────────────────

    def get_node_stats(self) -> Dict:
        stats = {}
        for node_id, node in self.nodes.items():
            recent = list(node.recent_records)
            avg_lat = sum(r.latency for r in recent) / len(recent) if recent else 0
            stats[node_id] = {
                "status": node.status.value,
                "current_load": node.current_load,
                "capacity": node.capacity,
                "static_latency": round(node.latency, 1),
                "ewma_latency": round(node.ewma_latency, 1),
                "ewma_error_rate": round(node.ewma_error_rate, 4),
                "dynamic_weight": round(node.dynamic_weight, 4),
                "success_rate": round(node.success_rate, 4),
                "total_requests": node.total_requests,
                "failed_requests": node.failed_requests,
                "recent_samples": len(recent),
                "recent_avg_latency": round(avg_lat, 1),
            }
        return stats

    def add_node(self, node_info: NodeInfo):
        self.nodes[node_info.node_id] = node_info
        logger.info(f"Added node: {node_info.node_id}")

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info(f"Removed node: {node_id}")


model_router = ModelRouter()
