/**
 * Agent Runtime 测试套件
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { AgentRuntime } from '../src/runtime.js';
import { AI_FAMILY_PROFILES, getProfileById, getProfileByName, getProfilesByTier } from '../src/family-registry.js';
import type { AgentProfile } from '../src/types.js';

// ============================================================
// Family Registry 测试
// ============================================================
describe('AI Family Registry', () => {
  it('应包含全部 8 位 AI Family 成员', () => {
    expect(AI_FAMILY_PROFILES).toHaveLength(8);
  });

  it('应有 3 个层级: decision(1), safeguard(3), execution(4)', () => {
    const decision = getProfilesByTier('decision');
    const safeguard = getProfilesByTier('safeguard');
    const execution = getProfilesByTier('execution');

    expect(decision).toHaveLength(1);
    expect(safeguard).toHaveLength(3);
    expect(execution).toHaveLength(4);
  });

  it('元启·天枢 应为决策层 (decision)', () => {
    const tianshu = AI_FAMILY_PROFILES.find(p => p.nameCN === '元启·天枢');
    expect(tianshu).toBeDefined();
    expect(tianshu!.tier).toBe('decision');
    expect(tianshu!.familyId).toBe('010301-05');
  });

  it('应通过 familyId 查找', () => {
    const profile = getProfileById('010301-01');
    expect(profile).toBeDefined();
    expect(profile!.nameCN).toBe('言启·千行');
  });

  it('应通过 nameEN 查找', () => {
    const profile = getProfileById('QianHang');
    expect(profile).toBeDefined();
    expect(profile!.nameCN).toBe('言启·千行');
  });

  it('应通过中文名查找', () => {
    const profile = getProfileByName('语枢·万物');
    expect(profile).toBeDefined();
    expect(profile!.nameEN).toBe('Thinker');
  });

  it('应通过英文名查找', () => {
    const profile = getProfileByName('Thinker');
    expect(profile).toBeDefined();
    expect(profile!.nameCN).toBe('语枢·万物');
  });

  it('应通过小写英文名查找', () => {
    const profile = getProfileByName('prophet');
    expect(profile).toBeDefined();
    expect(profile!.nameCN).toBe('预见·先知');
  });

  it('未找到应返回 undefined', () => {
    expect(getProfileById('nonexistent')).toBeUndefined();
    expect(getProfileByName('不存在')).toBeUndefined();
  });

  it('所有成员应有完整的档案字段', () => {
    for (const p of AI_FAMILY_PROFILES) {
      expect(p.familyId).toBeTruthy();
      expect(p.nameCN).toBeTruthy();
      expect(p.nameEN).toBeTruthy();
      expect(p.role).toBeTruthy();
      expect(p.tier).toBeTruthy();
      expect(p.motto).toBeTruthy();
      expect(p.phone).toBeTruthy();
      expect(p.capabilities.length).toBeGreaterThan(0);
      expect(p.systemPrompt).toBeTruthy();
      expect(p.collaborators.length).toBeGreaterThan(0);
      expect(p.emoji).toBeTruthy();
      expect(p.color).toBeTruthy();
    }
  });

  it('每个成员的 phone 应是唯一的', () => {
    const phones = AI_FAMILY_PROFILES.map(p => p.phone);
    expect(new Set(phones).size).toBe(phones.length);
  });
});

// ============================================================
// AgentRuntime 核心测试
// ============================================================
describe('AgentRuntime', () => {
  let runtime: AgentRuntime;
  const qianHangProfile: AgentProfile = AI_FAMILY_PROFILES[0];

  beforeEach(() => {
    runtime = new AgentRuntime();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ---- 创建 / 销毁 ----
  describe('createAgent', () => {
    it('应创建智能体实例', () => {
      const agent = runtime.createAgent(qianHangProfile);
      expect(agent).toBeDefined();
      expect(agent.profile.nameCN).toBe('言启·千行');
      expect(agent.status).toBe('idle');
      expect(agent.messages).toHaveLength(0);
      expect(agent.memory.size).toBe(0);
    });

    it('应支持自定义 ID', () => {
      const agent = runtime.createAgent(qianHangProfile, 'custom-qianhang');
      expect(agent.id).toBe('custom-qianhang');
    });

    it('重复 ID 应抛出错误', () => {
      runtime.createAgent(qianHangProfile, 'dup');
      expect(() => runtime.createAgent(qianHangProfile, 'dup')).toThrow("already exists");
    });

    it('应触发 agent:created 事件', () => {
      const handler = vi.fn();
      runtime.on('agent:created', handler);
      const agent = runtime.createAgent(qianHangProfile);
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(agent);
    });
  });

  describe('destroyAgent', () => {
    it('应销毁智能体', () => {
      const agent = runtime.createAgent(qianHangProfile);
      expect(runtime.destroyAgent(agent.id)).toBe(true);
      expect(runtime.getAgent(agent.id)).toBeUndefined();
    });

    it('销毁不存在智能体应返回 false', () => {
      expect(runtime.destroyAgent('nonexistent')).toBe(false);
    });

    it('应触发 agent:destroyed 事件', () => {
      const handler = vi.fn();
      runtime.on('agent:destroyed', handler);
      const agent = runtime.createAgent(qianHangProfile);
      runtime.destroyAgent(agent.id);
      expect(handler).toHaveBeenCalledWith(agent.id);
    });
  });

  // ---- 状态管理 ----
  describe('setStatus', () => {
    it('应切换状态', () => {
      const agent = runtime.createAgent(qianHangProfile);
      expect(runtime.setStatus(agent.id, 'thinking')).toBe(true);
      expect(runtime.getAgent(agent.id)!.status).toBe('thinking');
    });

    it('应触发 agent:status 事件', () => {
      const handler = vi.fn();
      runtime.on('agent:status', handler);
      const agent = runtime.createAgent(qianHangProfile);
      runtime.setStatus(agent.id, 'acting');
      expect(handler).toHaveBeenCalledWith(agent.id, 'idle', 'acting');
    });

    it('不存在的智能体应返回 false', () => {
      expect(runtime.setStatus('nonexistent', 'thinking')).toBe(false);
    });
  });

  // ---- 消息发送 ----
  describe('sendMessage', () => {
    it('应向智能体发送消息', () => {
      const agent = runtime.createAgent(qianHangProfile);
      const msg = runtime.sendMessage('你好', 'user', agent.id);
      expect(msg.role).toBe('user');
      expect(msg.content).toBe('你好');
      expect(msg.senderId).toBe('user');
      expect(msg.targetId).toBe(agent.id);
    });

    it('应触发 message:sent 和 message:received 事件', () => {
      const sent = vi.fn();
      const received = vi.fn();
      runtime.on('message:sent', sent);
      runtime.on('message:received', received);
      const agent = runtime.createAgent(qianHangProfile);
      runtime.sendMessage('你好', 'user', agent.id);
      expect(sent).toHaveBeenCalledTimes(1);
      expect(received).toHaveBeenCalledTimes(1);
    });

    it('发送给不存在智能体应抛出错误', () => {
      expect(() => runtime.sendMessage('hi', 'user', 'nonexistent')).toThrow('not found');
    });

    it('应更新最后活跃时间', async () => {
      vi.useFakeTimers();
      const rt = new AgentRuntime();
      const agent = rt.createAgent(qianHangProfile);
      const before = agent.lastActiveAt;
      vi.advanceTimersByTime(1000);
      rt.sendMessage('hi', 'user', agent.id);
      const after = rt.getAgent(agent.id)!.lastActiveAt;
      expect(new Date(after).getTime()).toBeGreaterThan(new Date(before).getTime());
      vi.useRealTimers();
    });
  });

  describe('agentReply', () => {
    it('应记录智能体回复', () => {
      const agent = runtime.createAgent(qianHangProfile);
      const reply = runtime.agentReply(agent.id, '收到，正在处理');
      expect(reply.role).toBe('agent');
      expect(reply.content).toBe('收到，正在处理');
      expect(reply.senderId).toBe(agent.id);
    });

    it('应支持 toolCalls', () => {
      const agent = runtime.createAgent(qianHangProfile);
      const reply = runtime.agentReply(agent.id, '结果如下', undefined, [
        { id: 'tc1', name: 'search', args: {}, status: 'completed' },
      ]);
      expect(reply.toolCalls).toHaveLength(1);
      expect(reply.toolCalls![0].name).toBe('search');
    });
  });

  // ---- 对话历史 ----
  describe('getMessages', () => {
    it('应返回完整对话历史', () => {
      const agent = runtime.createAgent(qianHangProfile);
      runtime.sendMessage('msg1', 'user', agent.id);
      runtime.agentReply(agent.id, 'reply1');
      runtime.sendMessage('msg2', 'user', agent.id);
      expect(runtime.getMessages(agent.id)).toHaveLength(3);
    });

    it('应支持 limit 参数', () => {
      const agent = runtime.createAgent(qianHangProfile);
      for (let i = 0; i < 5; i++) {
        runtime.sendMessage(`msg${i}`, 'user', agent.id);
      }
      expect(runtime.getMessages(agent.id, 2)).toHaveLength(2);
    });

    it('不存在的智能体应返回空数组', () => {
      expect(runtime.getMessages('nonexistent')).toEqual([]);
    });
  });

  // ---- 内存管理 ----
  describe('Memory', () => {
    it('应设置和获取内存', () => {
      const agent = runtime.createAgent(qianHangProfile);
      runtime.setMemory(agent.id, 'preferences', { lang: 'zh' });
      expect(runtime.getMemory(agent.id, 'preferences')).toEqual({ lang: 'zh' });
    });

    it('应清除内存', () => {
      const agent = runtime.createAgent(qianHangProfile);
      runtime.setMemory(agent.id, 'key1', 'val1');
      runtime.setMemory(agent.id, 'key2', 'val2');
      runtime.clearMemory(agent.id);
      expect(runtime.getMemory(agent.id, 'key1')).toBeUndefined();
      expect(runtime.getMemory(agent.id, 'key2')).toBeUndefined();
    });

    it('不存在的智能体应返回 false', () => {
      expect(runtime.setMemory('nonexistent', 'k', 'v')).toBe(false);
      expect(runtime.getMemory('nonexistent', 'k')).toBeUndefined();
      expect(runtime.clearMemory('nonexistent')).toBe(false);
    });
  });

  // ---- 智能体间通信 ----
  describe('familyMessage', () => {
    it('应发送智能体间消息', () => {
      const qianHang = runtime.createAgent(qianHangProfile);
      const tianShu = runtime.createAgent(AI_FAMILY_PROFILES[4]);
      const msg = runtime.familyMessage({
        from: qianHang.id,
        to: tianShu.id,
        type: 'request',
        content: '需要决策支持',
      });
      expect(msg.from).toBe(qianHang.id);
      expect(msg.to).toBe(tianShu.id);
      expect(msg.type).toBe('request');
      expect(msg.timestamp).toBeTruthy();
    });

    it('应触发 family:message 事件', () => {
      const handler = vi.fn();
      runtime.on('family:message', handler);
      const a = runtime.createAgent(qianHangProfile);
      const b = runtime.createAgent(AI_FAMILY_PROFILES[4]);
      const msg = runtime.familyMessage({ from: a.id, to: b.id, type: 'request', content: 'test' });
      expect(handler).toHaveBeenCalledWith(msg);
    });
  });

  describe('broadcast', () => {
    it('应向所有其他智能体广播', () => {
      const handler = vi.fn();
      runtime.on('family:message', handler);
      const a = runtime.createAgent(qianHangProfile);
      runtime.createAgent(AI_FAMILY_PROFILES[1]);
      runtime.createAgent(AI_FAMILY_PROFILES[2]);
      runtime.broadcast('全员注意', a.id);
      // 广播发给 b 和 c，不发给 a 自己
      expect(handler).toHaveBeenCalledTimes(2);
    });
  });

  // ---- 工具调用 ----
  describe('recordToolCall', () => {
    it('应记录工具调用', () => {
      const handler = vi.fn();
      runtime.on('tool:called', handler);
      const agent = runtime.createAgent(qianHangProfile);
      runtime.recordToolCall(agent.id, {
        id: 'tc1',
        name: 'mcp:search',
        args: { q: 'test' },
        status: 'running',
      });
      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(agent.id, expect.objectContaining({ name: 'mcp:search' }));
    });
  });

  // ---- 列表与统计 ----
  describe('listAgents / listByStatus / stats', () => {
    it('应列出所有智能体', () => {
      runtime.createAgent(AI_FAMILY_PROFILES[0]);
      runtime.createAgent(AI_FAMILY_PROFILES[1]);
      expect(runtime.listAgents()).toHaveLength(2);
    });

    it('应按状态筛选', () => {
      const a = runtime.createAgent(AI_FAMILY_PROFILES[0]);
      runtime.createAgent(AI_FAMILY_PROFILES[1]);
      runtime.setStatus(a.id, 'thinking');
      expect(runtime.listByStatus('thinking')).toHaveLength(1);
      expect(runtime.listByStatus('idle')).toHaveLength(1);
    });

    it('stats 应返回正确统计', () => {
      const a = runtime.createAgent(AI_FAMILY_PROFILES[0]);
      runtime.createAgent(AI_FAMILY_PROFILES[1]);
      runtime.createAgent(AI_FAMILY_PROFILES[2]);
      runtime.setStatus(a.id, 'error');
      const stats = runtime.stats();
      expect(stats.total).toBe(3);
      expect(stats.perStatus.idle).toBe(2);
      expect(stats.perStatus.error).toBe(1);
    });
  });

  // ---- 消息历史裁剪 ----
  describe('Message trimming', () => {
    it('超出 maxMessages 时应裁剪历史', async () => {
      const rt = new AgentRuntime({ maxMessages: 5 });
      const agent = rt.createAgent(qianHangProfile);
      for (let i = 0; i < 10; i++) {
        rt.sendMessage(`msg${i}`, 'user', agent.id);
      }
      expect(rt.getMessages(agent.id)).toHaveLength(5);
      expect(rt.getMessages(agent.id)[0].content).toBe('msg5');
    });
  });

  // ---- 自动心跳 ----
  it('autoHeartbeat 应定期更新活跃时间', async () => {
    vi.useFakeTimers();
    const rt = new AgentRuntime({ autoHeartbeat: true, heartbeatInterval: 1000 });
    const agent = rt.createAgent(qianHangProfile);
    const before = agent.lastActiveAt;

    vi.advanceTimersByTime(3000);
    const updated = rt.getAgent(agent.id)!;
    expect(updated.lastActiveAt).not.toBe(before);

    rt.destroyAgent(agent.id);
    vi.useRealTimers();
  });
});