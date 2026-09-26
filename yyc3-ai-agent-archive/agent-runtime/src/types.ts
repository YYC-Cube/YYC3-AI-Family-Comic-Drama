/**
 * Agent Runtime — 类型定义
 * @module @yyc3/agent-runtime
 */
import type { Store } from '@yyc3/store';

/** 智能体状态 */
export type AgentStatus = 'idle' | 'thinking' | 'acting' | 'waiting' | 'error' | 'offline';

/** 智能体层级 */
export type AgentTier = 'decision' | 'safeguard' | 'execution';

/** 消息角色 */
export type MessageRole = 'user' | 'agent' | 'system' | 'tool' | 'family';

/** 对话消息 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  /** 发送者 agent ID（多智能体通信时） */
  senderId?: string;
  /** 目标 agent ID */
  targetId?: string;
  /** 时间戳 */
  timestamp: string;
  /** 引用的工具调用 */
  toolCalls?: ToolCall[];
  /** 元数据 */
  meta?: Record<string, unknown>;
}

/** 工具调用 */
export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: unknown;
  error?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

/** 智能体档案 */
export interface AgentProfile {
  /** 家族编号 */
  familyId: string;
  /** 中文名号 */
  nameCN: string;
  /** 英文名号 */
  nameEN: string;
  /** 角色 */
  role: string;
  /** 层级 */
  tier: AgentTier;
  /** 座右铭 */
  motto: string;
  /** 专属电话 */
  phone: string;
  /** 核心能力 */
  capabilities: string[];
  /** 系统提示词 */
  systemPrompt: string;
  /** 协作对象 */
  collaborators: string[];
  /** 图标 emoji */
  emoji: string;
  /** 颜色 */
  color: string;
}

/** 智能体实例 */
export interface Agent {
  /** 实例 ID */
  id: string;
  /** 档案 */
  profile: AgentProfile;
  /** 状态 */
  status: AgentStatus;
  /** 对话历史 */
  messages: Message[];
  /** 内存（键值存储） */
  memory: Map<string, unknown>;
  /** 创建时间 */
  createdAt: string;
  /** 最后活跃时间 */
  lastActiveAt: string;
}

/** 智能体间消息 */
export interface FamilyMessage {
  from: string;
  to: string;
  type: 'request' | 'response' | 'broadcast' | 'heartbeat';
  content: string;
  timestamp: string;
  /** 关联任务 ID */
  taskId?: string;
}

/** 运行时配置 */
export interface AgentRuntimeConfig {
  /** 最大对话历史 */
  maxMessages: number;
  /** 默认超时 */
  defaultTimeout: number;
  /** 是否自动心跳 */
  autoHeartbeat: boolean;
  /** 心跳间隔(毫秒) */
  heartbeatInterval: number;
  /**
   * 可选持久化存储（P2）：提供后智能体/会话写穿落盘，
   * restore() 可在重启后恢复（Agent 内存 Map 以 entries 序列化）。
   */
  store?: Store;
}

/** 运行时事件 */
export interface AgentRuntimeEvents {
  'agent:created': (agent: Agent) => void;
  'agent:destroyed': (agentId: string) => void;
  'agent:status': (agentId: string, from: AgentStatus, to: AgentStatus) => void;
  'message:sent': (message: Message) => void;
  'message:received': (message: Message) => void;
  'family:message': (msg: FamilyMessage) => void;
  'tool:called': (agentId: string, toolCall: ToolCall) => void;
  'error': (agentId: string, error: string) => void;
}
