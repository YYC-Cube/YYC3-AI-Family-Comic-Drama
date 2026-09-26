/**
 * @description YYC³ CowAgent 工具 MCP 适配器
 * @module @yyc3/mcp-runtime/cowagent-bridge
 *
 * 将 CowAgent 的 15+ Python 工具暴露为 MCP Tool。
 * 通过 subprocess 调用 Python 工具，实现跨语言桥接。
 *
 * CowAgent 工具清单：
 *   bash, browser, edit, env_config, ls, memory_get, memory_search,
 *   read, scheduler, send, vision, web_fetch, web_search, write
 */

import { spawn } from 'child_process';
import type { MCPTool, MCPToolCall, MCPToolResult, SourcedTool } from './types.js';

// ==================== CowAgent 工具清单 ====================

export const COWAGENT_TOOLS: MCPTool[] = [
  {
    name: 'cowagent_bash',
    description: '执行 Bash 命令（来自 CowAgent）',
    inputSchema: {
      type: 'object',
      properties: {
        command: { type: 'string', description: '要执行的命令' },
        cwd: { type: 'string', description: '工作目录' },
        timeout: { type: 'number', description: '超时时间（毫秒）', default: 30000 },
      },
      required: ['command'],
    },
  },
  {
    name: 'cowagent_browser',
    description: '浏览器自动化（导航/点击/输入/截图）',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          description: '操作类型',
          enum: ['navigate', 'click', 'input', 'screenshot', 'evaluate', 'close'],
        },
        url: { type: 'string', description: '目标 URL（navigate 时使用）' },
        selector: { type: 'string', description: 'CSS 选择器（click/input 时使用）' },
        text: { type: 'string', description: '输入文本（input 时使用）' },
        script: { type: 'string', description: 'JS 脚本（evaluate 时使用）' },
      },
      required: ['action'],
    },
  },
  {
    name: 'cowagent_edit',
    description: '编辑文件（基于搜索替换）',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: '文件路径' },
        old_text: { type: 'string', description: '要搜索的文本' },
        new_text: { type: 'string', description: '替换为的文本' },
      },
      required: ['path', 'old_text', 'new_text'],
    },
  },
  {
    name: 'cowagent_read',
    description: '读取文件内容',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: '文件路径' },
        offset: { type: 'number', description: '起始行' },
        limit: { type: 'number', description: '读取行数' },
      },
      required: ['path'],
    },
  },
  {
    name: 'cowagent_write',
    description: '写入文件',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: '文件路径' },
        content: { type: 'string', description: '文件内容' },
      },
      required: ['path', 'content'],
    },
  },
  {
    name: 'cowagent_ls',
    description: '列出目录内容',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: '目录路径' },
      },
      required: ['path'],
    },
  },
  {
    name: 'cowagent_web_search',
    description: '网络搜索',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '搜索查询' },
        num_results: { type: 'number', description: '结果数量', default: 10 },
      },
      required: ['query'],
    },
  },
  {
    name: 'cowagent_web_fetch',
    description: '获取网页内容',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: '目标 URL' },
        format: { type: 'string', description: '输出格式', enum: ['text', 'markdown', 'html'], default: 'markdown' },
      },
      required: ['url'],
    },
  },
  {
    name: 'cowagent_vision',
    description: '图像分析（OCR/物体识别/场景描述）',
    inputSchema: {
      type: 'object',
      properties: {
        image_path: { type: 'string', description: '图像路径' },
        task: {
          type: 'string',
          description: '分析任务',
          enum: ['ocr', 'describe', 'objects', 'classify'],
        },
        prompt: { type: 'string', description: '自定义分析提示词' },
      },
      required: ['image_path', 'task'],
    },
  },
  {
    name: 'cowagent_scheduler',
    description: '任务调度（定时/延迟执行）',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          description: '操作类型',
          enum: ['create', 'list', 'cancel', 'execute'],
        },
        task_name: { type: 'string', description: '任务名称' },
        schedule: { type: 'string', description: '调度表达式（cron）或延迟时间' },
        command: { type: 'string', description: '要执行的命令' },
        task_id: { type: 'string', description: '任务 ID（cancel/execute 时使用）' },
      },
      required: ['action'],
    },
  },
  {
    name: 'cowagent_memory_search',
    description: '搜索记忆库（语义检索）',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '搜索查询' },
        limit: { type: 'number', description: '结果数量', default: 5 },
      },
      required: ['query'],
    },
  },
  {
    name: 'cowagent_memory_get',
    description: '获取指定记忆',
    inputSchema: {
      type: 'object',
      properties: {
        memory_id: { type: 'string', description: '记忆 ID' },
      },
      required: ['memory_id'],
    },
  },
  {
    name: 'cowagent_send',
    description: '发送消息到渠道（微信/钉钉/飞书/QQ/Web）',
    inputSchema: {
      type: 'object',
      properties: {
        channel: { type: 'string', description: '目标渠道', enum: ['wechat', 'dingtalk', 'feishu', 'qq', 'web', 'terminal'] },
        message: { type: 'string', description: '消息内容' },
        recipient: { type: 'string', description: '接收者（可选）' },
      },
      required: ['channel', 'message'],
    },
  },
];

// ==================== 适配器 ====================

export interface CowAgentBridgeConfig {
  /** CowAgent 项目根目录 */
  cowagentRoot: string;
  /** Python 解释器路径 */
  pythonPath?: string;
  /** 执行超时（毫秒） */
  timeout?: number;
}

export class CowAgentMCPBridge {
  private config: CowAgentBridgeConfig;

  constructor(config: CowAgentBridgeConfig) {
    this.config = {
      pythonPath: 'python3',
      timeout: 30_000,
      ...config,
    };
  }

  /**
   * 获取所有 CowAgent 工具作为 MCP Tool
   */
  toMCPTools(): SourcedTool[] {
    return COWAGENT_TOOLS.map(tool => ({
      tool,
      source: 'cowagent' as const,
      sourceId: tool.name,
    }));
  }

  /**
   * 处理 MCP Tool 调用
   */
  async handleToolCall(call: MCPToolCall): Promise<MCPToolResult> {
    const toolName = call.name.replace('cowagent_', '');

    // 工具名白名单校验：防止构造工具名向 Python 源码注入代码
    if (!/^[a-z][a-z0-9_]*$/.test(toolName)) {
      return {
        id: call.id,
        content: [{ type: 'text', text: `Invalid tool name: ${toolName}` }],
        isError: true,
      };
    }

    const pythonScript = this.buildPythonWrapper(toolName);

    return new Promise(resolve => {
      const proc = spawn(
        this.config.pythonPath!,
        ['-c', pythonScript],
        {
          cwd: this.config.cowagentRoot,
          timeout: this.config.timeout,
          env: { ...process.env },
        }
      );

      // 输出上限：单流最多累积 1MB，防内存 DoS（P2，与 skill-registry executor 同口径）
      const MAX_OUTPUT_BYTES = 1024 * 1024;
      let stdout = '';
      let stderr = '';
      let truncated = false;

      const append = (current: string, chunk: Buffer): string => {
        if (current.length >= MAX_OUTPUT_BYTES) {
          truncated = true;
          return current;
        }
        const next = current + chunk.toString();
        if (next.length > MAX_OUTPUT_BYTES) {
          truncated = true;
          return next.slice(0, MAX_OUTPUT_BYTES);
        }
        return next;
      };

      // 参数经 stdin 传递并以 json.loads 解析，杜绝源码级注入；
      // EPIPE：子进程先退出（如 python 未安装/语法错）时写入 stdin 触发 EPIPE，
      // 必须监听否则作为进程级异常抛出导致 Node 崩溃（P2）
      proc.stdin.on('error', () => {
        // 由 'close' 事件统一收敛结果；此处仅吞掉 EPIPE
      });
      proc.stdin.write(JSON.stringify(call.arguments ?? {}));
      proc.stdin.end();

      proc.stdout.on('data', (data: Buffer) => {
        stdout = append(stdout, data);
      });
      proc.stderr.on('data', (data: Buffer) => {
        stderr = append(stderr, data);
      });

      proc.on('error', err => {
        resolve({
          id: call.id,
          content: [{ type: 'text', text: `Error: ${err.message}` }],
          isError: true,
        });
      });

      proc.on('close', code => {
        const tail = truncated ? '\n[output truncated at 1MB]' : '';
        if (code === 0) {
          resolve({
            id: call.id,
            content: [{ type: 'text', text: stdout.trim() + tail }],
          });
        } else {
          resolve({
            id: call.id,
            content: [{ type: 'text', text: (stderr.trim() || `Process exited with code ${code}`) + tail }],
            isError: true,
          });
        }
      });
    });
  }

  /**
   * 构建 Python 包装脚本
   */
  private buildPythonWrapper(toolName: string): string {
    // 工具名已经白名单校验（^[a-z][a-z0-9_]*$），参数经 stdin 传递
    return `
import sys, json
sys.path.insert(0, '.')
args = json.loads(sys.stdin.read() or '{}')
try:
    from agent.tools.${toolName} import *
    # Tool execution will be handled by the specific tool module
    print(json.dumps({"status": "ok", "tool": "${toolName}", "args": args}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
    sys.exit(1)
`;
  }
}
