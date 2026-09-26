/**
 * Frontmatter 解析器测试 — 覆盖仓库真实 SKILL.md 使用的 YAML 子集
 */
import { describe, it, expect } from 'vitest';
import {
  parseFrontmatter,
  parseYamlSubset,
  parseInlineArray,
  toString,
  toStringArray,
} from '../src/frontmatter.js';

describe('parseFrontmatter', () => {
  it('解析简单键值对', () => {
    const content = `---
name: my-skill
version: 1.0.0
description: 一个简单技能
---

# 正文内容
`;
    const fm = parseFrontmatter(content);
    expect(fm['name']).toBe('my-skill');
    expect(fm['version']).toBe('1.0.0');
    expect(fm['description']).toBe('一个简单技能');
  });

  it('无 frontmatter 时返回空对象', () => {
    expect(parseFrontmatter('# 只有正文')).toEqual({});
    expect(parseFrontmatter('')).toEqual({});
  });

  it('解析折叠多行文本（> 语法）', () => {
    const content = `---
name: paper-quick-reader
description: >
  AI 论文速读 Skill，
  支持三档深度模式，
  含溯源体系。
---
`;
    const fm = parseFrontmatter(content);
    expect(fm['description']).toBe(
      'AI 论文速读 Skill， 支持三档深度模式， 含溯源体系。'
    );
  });

  it('解析字面量多行文本（| 语法）保留换行', () => {
    const content = `---
prompt: |
  第一行
  第二行
---
`;
    const fm = parseFrontmatter(content);
    expect(fm['prompt']).toBe('第一行\n第二行');
  });

  it('解析 >- 去尾换行的折叠语法', () => {
    const content = `---
description: >-
  折叠文本
  续行
---
`;
    const fm = parseFrontmatter(content);
    expect(fm['description']).toBe('折叠文本 续行');
  });

  it('解析内联数组', () => {
    const content = `---
allowed-tools: [read_file, execute_command, write_to_file]
tags: [data, glm]
---
`;
    const fm = parseFrontmatter(content);
    expect(fm['allowed-tools']).toEqual([
      'read_file',
      'execute_command',
      'write_to_file',
    ]);
    expect(fm['tags']).toEqual(['data', 'glm']);
  });

  it('解析带引号的值（含逗号与转义）', () => {
    const content = `---
title: "包含, 逗号的标题"
quote: '单引号值'
escaped: "带\\"转义\\""
---
`;
    const fm = parseFrontmatter(content);
    expect(fm['title']).toBe('包含, 逗号的标题');
    expect(fm['quote']).toBe('单引号值');
    expect(fm['escaped']).toBe('带"转义"');
  });

  it('跳过注释行与空行', () => {
    const raw = `# 顶部注释
name: demo

# 中间注释
version: 2.0.0
`;
    const fm = parseYamlSubset(raw);
    expect(fm['name']).toBe('demo');
    expect(fm['version']).toBe('2.0.0');
    expect(Object.keys(fm)).toHaveLength(2);
  });

  it('处理值内 # 不误判为注释', () => {
    const raw = 'color: #ff0000';
    const fm = parseYamlSubset(raw);
    expect(fm['color']).toBe('#ff0000');
  });

  it('处理空值字段', () => {
    const raw = 'description:\nname: demo';
    const fm = parseYamlSubset(raw);
    expect(fm['description']).toBe('');
    expect(fm['name']).toBe('demo');
  });

  it('兼容 CRLF 换行', () => {
    const content = '---\r\nname: crlf-skill\r\nversion: 1.0.0\r\n---\r\n';
    const fm = parseFrontmatter(content);
    expect(fm['name']).toBe('crlf-skill');
  });
});

describe('parseInlineArray', () => {
  it('空数组', () => {
    expect(parseInlineArray('[]')).toEqual([]);
  });

  it('引号内逗号不切分', () => {
    expect(parseInlineArray('["a, b", c]')).toEqual(['a, b', 'c']);
  });
});

describe('toString / toStringArray', () => {
  it('字符串按逗号切分', () => {
    expect(toStringArray('a, b ,c')).toEqual(['a', 'b', 'c']);
  });

  it('数组直接返回', () => {
    expect(toStringArray(['x', 'y'])).toEqual(['x', 'y']);
  });

  it('undefined 返回空', () => {
    expect(toStringArray(undefined)).toEqual([]);
    expect(toString(undefined)).toBe('');
  });

  it('数组转字符串以逗号连接', () => {
    expect(toString(['a', 'b'])).toBe('a, b');
  });
});
