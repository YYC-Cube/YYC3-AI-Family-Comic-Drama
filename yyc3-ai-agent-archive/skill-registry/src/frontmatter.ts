/**
 * @description YAML 子集解析器 — SKILL.md frontmatter
 * @module @yyc3/skill-registry/frontmatter
 *
 * 覆盖仓库内真实 SKILL.md 文件使用的 YAML 语法子集：
 * - 简单键值对（key: value）
 * - 带引号的值（单引号 / 双引号，含转义）
 * - 内联数组（[a, b, c]）
 * - 多行折叠（> 与 >-）与字面量块（| 与 |-）
 * - 空行与 # 注释行
 *
 * 不引入完整 YAML 依赖（js-yaml），保持零额外运行时成本。
 */

export type FrontmatterValue = string | string[];
export type Frontmatter = Record<string, FrontmatterValue>;

/** 块标量修饰符（> | 及其 chomping 变体） */
const BLOCK_SCALAR_RE = /^([>|])([-+]?)$/;

/**
 * 从 Markdown 内容中提取并解析 frontmatter。
 * 无 frontmatter 或格式非法时返回空对象。
 */
export function parseFrontmatter(content: string): Frontmatter {
  const match = content.match(/^---[ \t]*\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  return parseYamlSubset(match[1]);
}

/**
 * 解析 YAML 子集文本为键值映射
 */
export function parseYamlSubset(raw: string): Frontmatter {
  const lines = raw.split(/\r?\n/);
  const result: Frontmatter = {};
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // 跳过空行与注释行
    if (!line.trim() || line.trimStart().startsWith('#')) {
      i++;
      continue;
    }

    const kv = line.match(/^([A-Za-z0-9_.-]+)\s*:\s*(.*)$/);
    if (!kv) {
      i++;
      continue;
    }

    const key = kv[1];
    const rawValue = stripTrailingComment(kv[2]).trim();

    // 多行块标量：description: > 或 description: |-
    const blockMatch = rawValue.match(BLOCK_SCALAR_RE);
    if (blockMatch) {
      const folded = blockMatch[1] === '>';
      const { value, nextIndex } = collectBlockScalar(lines, i + 1);
      result[key] = foldLines(value, folded);
      i = nextIndex;
      continue;
    }

    // 内联数组：tags: [a, b, c]
    if (rawValue.startsWith('[')) {
      const { value, nextIndex } = collectInlineArray(lines, i, rawValue);
      result[key] = parseInlineArray(value);
      i = nextIndex;
      continue;
    }

    result[key] = unquote(rawValue);
    i++;
  }

  return result;
}

/**
 * 收集块标量（> 或 |）的缩进续行
 */
function collectBlockScalar(
  lines: string[],
  start: number
): { value: string[]; nextIndex: number } {
  const collected: string[] = [];
  let i = start;

  while (i < lines.length) {
    const next = lines[i];
    if (next.trim() === '') {
      collected.push('');
      i++;
      continue;
    }
    // 块标量续行必须相对缩进
    if (/^\s+\S/.test(next)) {
      collected.push(next.replace(/^\s+/, ''));
      i++;
      continue;
    }
    break;
  }

  // 去除尾部空行
  while (collected.length > 0 && collected[collected.length - 1] === '') {
    collected.pop();
  }

  return { value: collected, nextIndex: i };
}

/**
 * 折叠多行文本：> 以空格连接，| 保留换行
 */
function foldLines(lines: string[], folded: boolean): string {
  return folded ? lines.join(' ').trim() : lines.join('\n').trim();
}

/**
 * 收集内联数组（支持跨行的 [ ... ] 写法）
 */
function collectInlineArray(
  lines: string[],
  currentIndex: number,
  firstValue: string
): { value: string; nextIndex: number } {
  let value = firstValue;
  let i = currentIndex;

  while (!value.endsWith(']') && i + 1 < lines.length && i - currentIndex < 20) {
    i++;
    value += ' ' + lines[i].trim();
  }

  return { value, nextIndex: i + 1 };
}

/**
 * 解析内联数组字符串 [a, b, "c d"] → string[]
 */
export function parseInlineArray(raw: string): string[] {
  const inner = raw.replace(/^\[/, '').replace(/\]$/, '');
  if (!inner.trim()) return [];

  return splitTopLevel(inner)
    .map(item => unquote(item.trim()))
    .filter(item => item.length > 0);
}

/**
 * 按顶层逗号切分（尊重引号内的逗号）
 */
function splitTopLevel(input: string): string[] {
  const parts: string[] = [];
  let current = '';
  let quote: '"' | "'" | null = null;

  for (const ch of input) {
    if (quote) {
      current += ch;
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      current += ch;
      continue;
    }
    if (ch === ',') {
      parts.push(current);
      current = '';
      continue;
    }
    current += ch;
  }
  parts.push(current);

  return parts;
}

/**
 * 去除值尾部的 " # 注释"（仅当 # 前有空白且不在引号内）
 */
function stripTrailingComment(value: string): string {
  let quote: '"' | "'" | null = null;
  for (let i = 0; i < value.length; i++) {
    const ch = value[i];
    if (quote) {
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      continue;
    }
    if (ch === '#' && i > 0 && /\s/.test(value[i - 1])) {
      return value.slice(0, i);
    }
  }
  return value;
}

/**
 * 去除成对引号并处理双引号转义
 */
function unquote(value: string): string {
  const trimmed = value.trim();
  if (trimmed.length >= 2) {
    if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
      return trimmed.slice(1, -1).replace(/\\"/g, '"').replace(/\\n/g, '\n');
    }
    if (trimmed.startsWith("'") && trimmed.endsWith("'")) {
      return trimmed.slice(1, -1).replace(/''/g, "'");
    }
  }
  return trimmed;
}

/**
 * 将 Frontmatter 值规整为字符串数组（数组直接返回；字符串按逗号切分）
 */
export function toStringArray(value: FrontmatterValue | undefined): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  return value
    .split(',')
    .map(item => unquote(item.trim()))
    .filter(item => item.length > 0);
}

/**
 * 将 Frontmatter 值规整为字符串
 */
export function toString(value: FrontmatterValue | undefined): string {
  if (!value) return '';
  return Array.isArray(value) ? value.join(', ') : value;
}
