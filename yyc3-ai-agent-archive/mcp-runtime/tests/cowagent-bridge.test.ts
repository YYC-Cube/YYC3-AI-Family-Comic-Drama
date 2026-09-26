/**
 * CowAgentMCPBridge 安全防护测试
 * 重点：工具名注入防护（白名单校验 + stdin 传参，不向 Python 源码内插参数）
 */
import { describe, it, expect } from 'vitest';
import { CowAgentMCPBridge } from '../src/cowagent-bridge.js';

describe('CowAgentMCPBridge 注入防护', () => {
  const bridge = new CowAgentMCPBridge({
    cowagentRoot: '/nonexistent-cowagent',
    pythonPath: 'python3',
  });

  it('工具清单可导出且命名带前缀', () => {
    const tools = bridge.toMCPTools();
    expect(tools.length).toBeGreaterThan(0);
    for (const t of tools) {
      expect(t.tool.name.startsWith('cowagent_')).toBe(true);
    }
  });

  it('含特殊字符的工具名被拒绝（不进入子进程）', async () => {
    const maliciousNames = [
      'cowagent_os; import os; os.system("id")',
      'cowagent_bash;print("pwned")',
      'cowagent_x\nimport os',
      'cowagent_${inject}',
      'cowagent_-bad-start',
      'cowagent_BadUpper',
      'cowagent_9numeric',
    ];
    for (const name of maliciousNames) {
      const result = await bridge.handleToolCall({
        id: 'call-inj',
        name,
        arguments: {},
      });
      expect(result.isError, `应拒绝: ${name}`).toBe(true);
      expect(result.content[0].text).toContain('Invalid tool name');
    }
  });

  it('合法工具名通过校验（子进程失败不影响校验逻辑）', async () => {
    // python3 在不存在的 cwd 下 spawn 会失败，但校验已通过：
    // 返回的是进程错误而非 "Invalid tool name"
    const result = await bridge.handleToolCall({
      id: 'call-ok',
      name: 'cowagent_bash',
      arguments: { command: 'echo hi' },
    });
    expect(result.content[0].text).not.toContain('Invalid tool name');
  });
});
