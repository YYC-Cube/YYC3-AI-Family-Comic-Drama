/**
 * AI Family 8 位智能体集成测试
 *
 * 场景：全家族协作完成「代码审查 + 安全审计 + 创意优化」完整流程
 *
 * 流程：
 * 1. 言启·千行 接收用户请求，解析意图
 * 2. 元启·天枢 统筹全局，分解任务
 * 3. 语枢·万物 深度分析代码逻辑
 * 4. 格物·宗师 执行代码审查
 * 5. 智云·守护 执行安全审计
 * 6. 创想·灵韵 提供创意优化建议
 * 7. 预见·先知 预测潜在风险
 * 8. 千里·伯乐 推荐最佳实践/资源
 * 9. 汇总所有结果
 */
import type { Agent, FamilyMessage } from '@yyc3/agent-runtime';
import { AgentRuntime, AI_FAMILY_PROFILES } from '@yyc3/agent-runtime';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Orchestrator } from '../src/orchestrator.js';

describe('AI Family 8 Agent Integration', () => {
  let runtime: AgentRuntime;
  let orchestrator: Orchestrator;
  const agents: Agent[] = [];

  // 创建全部 8 位智能体
  beforeEach(() => {
    agents.length = 0;
    runtime = new AgentRuntime();
    orchestrator = new Orchestrator();

    for (const profile of AI_FAMILY_PROFILES) {
      const agent = runtime.createAgent(profile, profile.nameEN);
      agents.push(agent);
    }
  });

  it('应创建全部 8 位 AI Family 智能体', () => {
    expect(runtime.listAgents()).toHaveLength(8);
    expect(runtime.stats().total).toBe(8);
  });

  it('应包含完整的三层架构: 决策层(1) + 保障层(3) + 执行层(4)', () => {
    const decision = agents.filter(a => a.profile.tier === 'decision');
    const safeguard = agents.filter(a => a.profile.tier === 'safeguard');
    const execution = agents.filter(a => a.profile.tier === 'execution');

    expect(decision).toHaveLength(1);  // 元启·天枢
    expect(safeguard).toHaveLength(3); // 智云·守护, 格物·宗师, 创想·灵韵
    expect(execution).toHaveLength(4); // 言启·千行, 语枢·万物, 预见·先知, 千里·伯乐
  });

  it('代表示例: 言启·千行 接收用户意图, 元启·天枢 统筹调度', () => {
    // 1. 用户发送请求给 言启·千行
    runtime.sendMessage(
      '我需要审查一个用户登录模块的代码安全性，并优化 UI 体验',
      'user',
      'QianHang'
    );

    // 2. 言启·千行 解析意图后回复
    const qianHangReply = runtime.agentReply(
      'QianHang',
      '意图分析：用户需要代码安全审查 + UI 优化。转发给元启·天枢统筹调度。'
    );

    // 3. 言启·千行 向 元启·天枢 发送协作请求
    runtime.familyMessage({
      from: 'QianHang',
      to: 'TianShu',
      type: 'request',
      content: '需要统筹：代码审查 + 安全审计 + UI 优化，请分配任务',
    });

    expect(runtime.getMessages('QianHang')).toHaveLength(2);
    expect(qianHangReply.senderId).toBe('QianHang');
  });

  it('协作场景: 格物·宗师 + 智云·守护 联合审查', () => {
    // 元启·天枢 发送任务给 格物·宗师
    runtime.familyMessage({
      from: 'TianShu',
      to: 'Grandmaster',
      type: 'request',
      content: '请审查登录模块代码质量',
      taskId: 'task-001',
    });

    runtime.agentReply('Grandmaster', '收到，开始审查代码结构和最佳实践...');

    // 元启·天枢 发送任务给 智云·守护
    runtime.familyMessage({
      from: 'TianShu',
      to: 'Guardian',
      type: 'request',
      content: '请审计登录模块安全性',
      taskId: 'task-002',
    });

    runtime.agentReply('Guardian', '收到，开始安全审计：SQL注入、XSS、认证绕过...');

    // 格物·宗师 完成审查后汇报
    runtime.familyMessage({
      from: 'Grandmaster',
      to: 'TianShu',
      type: 'response',
      content: '代码审查完成：发现 2 个编码规范问题，建议优化错误处理',
      taskId: 'task-001',
    });

    // 智云·守护 完成审计后汇报
    runtime.familyMessage({
      from: 'Guardian',
      to: 'TianShu',
      type: 'response',
      content: '安全审计完成：发现 1 个 SQL 注入风险，1 个弱密码策略',
      taskId: 'task-002',
    });

    expect(runtime.getMessages('Grandmaster').length).toBeGreaterThan(0);
    expect(runtime.getMessages('Guardian').length).toBeGreaterThan(0);
  });

  it('协作场景: 创想·灵韵 + 语枢·万物 分析优化', () => {
    // 语枢·万物 分析数据
    runtime.familyMessage({
      from: 'TianShu',
      to: 'Thinker',
      type: 'request',
      content: '请分析用户反馈数据，提炼 UI 优化方向',
    });

    runtime.agentReply(
      'Thinker',
      '分析结果：80% 用户反馈登录表单过于复杂，简化为单字段登录可提升 30% 转化率',
      undefined,
      [{ id: 'tc1', name: 'data_analysis', args: {}, status: 'completed' }]
    );

    // 创想·灵韵 基于分析结果提供创意方案
    runtime.familyMessage({
      from: 'Thinker',
      to: 'Grace',
      type: 'request',
      content: '基于分析结果，请提供 UI 优化方案',
    });

    runtime.agentReply(
      'Grace',
      '创意方案：1) 渐变色登录背景 2) 无密码生物识别登录 3) 微交互动画引导',
      undefined,
      [{ id: 'tc2', name: 'generative_design', args: {}, status: 'completed' }]
    );

    expect(runtime.getMessages('Thinker').length).toBeGreaterThan(0);
    expect(runtime.getMessages('Grace').length).toBeGreaterThan(0);
  });

  it('协作场景: 预见·先知 风险预测 + 千里·伯乐 资源推荐', () => {
    // 预见·先知 预测风险
    runtime.familyMessage({
      from: 'TianShu',
      to: 'Prophet',
      type: 'request',
      content: '请预测新登录方案的潜在风险',
    });

    runtime.agentReply(
      'Prophet',
      '风险预测：生物识别方案在低端设备上失败率约 15%，建议保留密码降级方案。'
    );

    // 千里·伯乐 推荐最佳实践
    runtime.familyMessage({
      from: 'TianShu',
      to: 'BoLe',
      type: 'request',
      content: '请推荐登录模块的最佳实践和安全库',
    });

    runtime.agentReply(
      'BoLe',
      '推荐：1) Passkeys (WebAuthn) 标准 2) argon2 密码哈希 3) rate-limiter-flexible 防暴力破解'
    );

    const prophetMessages = runtime.getMessages('Prophet');
    const boleMessages = runtime.getMessages('BoLe');
    expect(prophetMessages.length).toBeGreaterThan(0);
    expect(boleMessages.length).toBeGreaterThan(0);
  });

  it('全链路协作: 8 位智能体完成完整任务', async () => {
    const familyMessages: FamilyMessage[] = [];
    runtime.on('family:message', (msg) => familyMessages.push(msg));

    // 模拟完整协作流程
    const flow = [
      // 1. 用户 → 言启·千行
      { from: 'user', to: 'QianHang', content: '需要全面审查"用户中心"模块' },
      // 2. 言启·千行 → 元启·天枢
      { from: 'QianHang', to: 'TianShu', content: '意图：代码审查 + 安全审计 + UI优化 + 风险预测' },
      // 3. 元启·天枢 → 各执行层
      { from: 'TianShu', to: 'Grandmaster', content: '任务：代码质量审查' },
      { from: 'TianShu', to: 'Guardian', content: '任务：安全漏洞审计' },
      { from: 'TianShu', to: 'Grace', content: '任务：UI/UX 优化建议' },
      { from: 'TianShu', to: 'Thinker', content: '任务：数据分析与洞察' },
      { from: 'TianShu', to: 'Prophet', content: '任务：风险预测' },
      { from: 'TianShu', to: 'BoLe', content: '任务：资源推荐' },
      // 4. 各执行层回复
      { from: 'Grandmaster', to: 'TianShu', content: '审查完成：3 个改进点' },
      { from: 'Guardian', to: 'TianShu', content: '审计完成：无高危漏洞' },
      { from: 'Grace', to: 'TianShu', content: '设计完成：2 个优化方案' },
      { from: 'Thinker', to: 'TianShu', content: '分析完成：用户行为报告' },
      { from: 'Prophet', to: 'TianShu', content: '预测完成：3 个潜在风险' },
      { from: 'BoLe', to: 'TianShu', content: '推荐完成：5 个最佳实践' },
      // 5. 元启·天枢 汇总 → 言启·千行
      { from: 'TianShu', to: 'QianHang', content: '汇总：全部任务完成，生成综合报告' },
      // 6. 言启·千行 → 用户
      { from: 'QianHang', to: 'user', content: '审查完成！以下是综合报告...' },
    ];

    for (const step of flow) {
      if (step.from === 'user') {
        runtime.sendMessage(step.content, step.from, step.to);
      } else if (step.to === 'user') {
        runtime.agentReply(step.from, step.content, 'user');
      } else {
        runtime.familyMessage({
          from: step.from,
          to: step.to,
          type: 'request',
          content: step.content,
        });
        // 模拟接收方回复（将消息存入 agent 历史）
        runtime.agentReply(step.to, `收到来自 ${step.from} 的任务: ${step.content}`);
      }
    }

    // 验证：所有智能体都有消息记录
    for (const agent of agents) {
      const msgs = runtime.getMessages(agent.id);
      expect(msgs.length).toBeGreaterThan(0);
    }

    // 验证：产生了 14 条家族消息
    expect(familyMessages.length).toBe(14);
  });

  it('Orchestrator 集成: 使用 AI Family 执行工作流', async () => {
    const profiles = AI_FAMILY_PROFILES;

    // 执行代码审查 + 安全审计工作流
    const wf = await orchestrator.execute(
      '全面审查用户登录模块',
      ['代码审查', '安全防护', '创意生成', '深度数据分析'],
      profiles
    );

    expect(wf.tasks.length).toBeGreaterThan(0);
    // 所有任务应被分配
    const assigned = wf.tasks.filter(t => t.assignedAgentId);
    expect(assigned.length).toBe(wf.tasks.length);

    // 验证能力匹配
    const grandmasterTasks = assigned.filter(t => t.assignedAgentId === 'Grandmaster');
    const guardianTasks = assigned.filter(t => t.assignedAgentId === 'Guardian');
    const graceTasks = assigned.filter(t => t.assignedAgentId === 'Grace');
    const thinkerTasks = assigned.filter(t => t.assignedAgentId === 'Thinker');

    expect(grandmasterTasks.length).toBeGreaterThan(0);
    expect(guardianTasks.length).toBeGreaterThan(0);
    expect(graceTasks.length).toBeGreaterThan(0);
    expect(thinkerTasks.length).toBeGreaterThan(0);
  });

  it('应支持广播通信', () => {
    const handler = vi.fn();
    runtime.on('family:message', handler);

    // 元启·天枢 广播家族通知
    runtime.broadcast('全体注意：服务器维护计划于 02:00 开始', 'TianShu');

    // 7 个其他智能体都收到消息
    expect(handler).toHaveBeenCalledTimes(7);
  });

  it('应支持心跳监控', () => {
    vi.useFakeTimers();
    const monitored = new AgentRuntime({ autoHeartbeat: true, heartbeatInterval: 1000 });

    for (const profile of AI_FAMILY_PROFILES) {
      monitored.createAgent(profile, profile.nameEN);
    }

    const before = monitored.listAgents().map(a => a.lastActiveAt);
    vi.advanceTimersByTime(3000);

    const after = monitored.listAgents().map(a => a.lastActiveAt);
    for (let i = 0; i < before.length; i++) {
      expect(new Date(after[i]).getTime()).toBeGreaterThan(new Date(before[i]).getTime());
    }

    monitored.listAgents().forEach(a => monitored.destroyAgent(a.id));
    vi.useRealTimers();
  });
});
