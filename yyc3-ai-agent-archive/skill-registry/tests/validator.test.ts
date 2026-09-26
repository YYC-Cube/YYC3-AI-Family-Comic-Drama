/**
 * 校验器测试 — validateFrontmatter / validateUnifiedSkill
 */
import { describe, it, expect } from 'vitest';
import {
  validateFrontmatter,
  validateUnifiedSkill,
  validateAllSkills,
} from '../src/validator.js';
import { parseFrontmatter } from '../src/frontmatter.js';
import type { UnifiedSkill } from '../src/types.js';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'V-001',
    name: '校验技能',
    description: '用于校验测试',
    domain: 'marketplace',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

describe('validateFrontmatter', () => {
  it('完整清单通过校验', () => {
    const fm = parseFrontmatter(
      '---\nname: good-skill\ndescription: 一个完整的技能描述文本\ncategory: development-code\nversion: 1.2.3\n---\n'
    );
    const result = validateFrontmatter(fm);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
    expect(result.warnings).toHaveLength(0);
  });

  it('缺失 name 报 error', () => {
    const fm = parseFrontmatter('---\ndescription: 缺少名称的技能\n---\n');
    const result = validateFrontmatter(fm);
    expect(result.valid).toBe(false);
    expect(result.errors[0].path).toBe('name');
  });

  it('非法 version 报 error', () => {
    const fm = parseFrontmatter(
      '---\nname: bad-version\nversion: "1.0"\ndescription: 合法长度描述文本\n---\n'
    );
    const result = validateFrontmatter(fm);
    expect(result.valid).toBe(false);
    expect(result.errors.some(e => e.path === 'version')).toBe(true);
  });

  it('v 前缀 SemVer 通过', () => {
    const fm = parseFrontmatter(
      '---\nname: v-prefix\nversion: v2.0.1\ndescription: 合法长度描述文本\n---\n'
    );
    expect(validateFrontmatter(fm).valid).toBe(true);
  });

  it('description 缺失/过短报 warning', () => {
    const short = validateFrontmatter(parseFrontmatter('---\nname: short-desc\ndescription: 太短\n---\n'));
    expect(short.valid).toBe(true);
    expect(short.warnings.some(w => w.path === 'description')).toBe(true);

    const missing = validateFrontmatter(parseFrontmatter('---\nname: no-desc\n---\n'));
    expect(missing.warnings.some(w => w.path === 'description')).toBe(true);
  });

  it('allowed-tools 空数组报 error', () => {
    const fm = parseFrontmatter('---\nname: empty-tools\nallowed-tools: []\n---\n');
    const result = validateFrontmatter(fm);
    expect(result.errors.some(e => e.path === 'allowed-tools')).toBe(true);
  });

  it('多行 description 正确参与校验', () => {
    const fm = parseFrontmatter(
      '---\nname: multi\nversion: 1.0.0\ncategory: ai-ml\ndescription: >\n  这是一段足够长的多行描述文本，\n  用于验证折叠语法解析后的校验。\n---\n'
    );
    const result = validateFrontmatter(fm);
    expect(result.valid).toBe(true);
    expect(result.warnings).toHaveLength(0);
  });
});

describe('validateUnifiedSkill', () => {
  it('合法 Skill 通过', () => {
    const result = validateUnifiedSkill(makeSkill({ securityAudited: true }));
    expect(result.valid).toBe(true);
    expect(result.warnings).toHaveLength(0);
  });

  it('非法 domain 枚举报 error', () => {
    const result = validateUnifiedSkill(makeSkill({ domain: 'not-a-domain' as UnifiedSkill['domain'] }));
    expect(result.valid).toBe(false);
    expect(result.errors.some(e => e.path === 'domain')).toBe(true);
  });

  it('fallback 自引用报 error', () => {
    const result = validateUnifiedSkill(makeSkill({ fallback: 'V-001' }));
    expect(result.errors.some(e => e.path === 'fallback')).toBe(true);
  });

  it('非 native 运行时缺 entry 报 warning', () => {
    const result = validateUnifiedSkill(makeSkill({ runtime: 'python', entry: '' }));
    expect(result.warnings.some(w => w.path === 'entry')).toBe(true);
  });

  it('未安全审计报 warning', () => {
    const result = validateUnifiedSkill(makeSkill());
    expect(result.warnings.some(w => w.path === 'securityAudited')).toBe(true);
  });
});

describe('validateAllSkills', () => {
  it('批量报告统计正确', () => {
    const good = makeSkill({ id: 'OK-001', securityAudited: true });
    const bad = makeSkill({ id: 'BAD-001', domain: 'xxx' as UnifiedSkill['domain'] });
    const warned = makeSkill({ id: 'WARN-001' });

    const report = validateAllSkills([good, bad, warned]);
    expect(report.total).toBe(3);
    expect(report.passed).toBe(2);
    expect(report.failed).toBe(1);
    expect(report.warningCount).toBeGreaterThan(0);
    expect(report.issues.map(i => i.id)).toContain('BAD-001');
  });
});
