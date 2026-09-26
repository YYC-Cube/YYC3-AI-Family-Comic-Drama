/**
 * SkillLoader 文件系统加载器测试 — 使用临时目录构建真实 SKILL.md 结构
 */
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { SkillLoader } from '../src/loader.js';
import { SkillRegistry } from '../src/registry.js';

let root: string;

beforeAll(() => {
  root = mkdtempSync(join(tmpdir(), 'yyc3-skills-'));
});

afterAll(() => {
  rmSync(root, { recursive: true, force: true });
});

function writeSkill(dir: string, frontmatter: string): void {
  mkdirSync(join(root, dir), { recursive: true });
  writeFileSync(join(root, dir, 'SKILL.md'), `---\n${frontmatter}\n---\n\n# Skill\n`);
}

describe('SkillLoader', () => {
  it('加载简单 SKILL.md', () => {
    writeSkill('simple-skill', 'name: simple-skill\ndescription: 简单技能\nversion: 1.0.0');
    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    const skill = registry.get('simple-skill');
    expect(skill).toBeDefined();
    expect(skill!.name).toBe('simple-skill');
    expect(skill!.description).toBe('简单技能');
    expect(skill!.version).toBe('1.0.0');
    expect(skill!.status).toBe('active');
  });

  it('正确解析多行 description（真实仓库格式）', () => {
    writeSkill(
      'multiline-skill',
      'name: multiline-skill\nversion: 2.1.0\ndescription: >\n  AI 论文速读工具，\n  支持三档深度模式。\nallowed-tools: [read_file, execute_command]'
    );

    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    const skill = registry.get('multiline-skill');
    expect(skill).toBeDefined();
    expect(skill!.description).toBe('AI 论文速读工具， 支持三档深度模式。');
  });

  it('通过 category 映射领域', () => {
    writeSkill('cat-skill', 'name: cat-skill\ncategory: business-productivity');
    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    const skill = registry.get('cat-skill');
    expect(skill!.domain).toBe('marketplace');
  });

  it('通过 domainMap 路径映射领域', () => {
    mkdirSync(join(root, 'glm-skills/glm-ocr-demo'), { recursive: true });
    writeFileSync(join(root, 'glm-skills/glm-ocr-demo/SKILL.md'), '---\nname: glm-ocr-demo\n---\n');

    const registry = new SkillRegistry();
    new SkillLoader(registry, {
      rootDir: root,
      recursive: true,
      maxDepth: 3,
      domainMap: { 'glm-skills': 'glm-ocr' },
    }).load();

    expect(registry.get('glm-ocr-demo')!.domain).toBe('glm-ocr');
  });

  it('目录名推断 GLM 领域', () => {
    writeSkill('glm-stock-analysis', 'name: glm-stock-analysis');
    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    expect(registry.get('glm-stock-analysis')!.domain).toBe('glm-finance');
  });

  it('跳过隐藏目录与 node_modules', () => {
    writeSkill('.hidden-skill', 'name: hidden-skill');
    writeSkill('node_modules/pkg-skill', 'name: pkg-skill');
    mkdirSync(join(root, 'visible'), { recursive: true });

    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    expect(registry.has('hidden-skill')).toBe(false);
    expect(registry.has('pkg-skill')).toBe(false);
  });

  it('rootDir 不存在时返回空数组且不抛错', () => {
    const registry = new SkillRegistry();
    const loaded = new SkillLoader(registry, {
      rootDir: join(root, 'not-exist'),
      recursive: true,
    }).load();
    expect(loaded).toEqual([]);
  });

  it('含 SKILL.md 的目录不再递归子目录', () => {
    writeSkill('parent-skill', 'name: parent-skill');
    writeSkill('parent-skill/nested-skill', 'name: nested-skill');

    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 5 }).load();

    expect(registry.has('parent-skill')).toBe(true);
    expect(registry.has('nested-skill')).toBe(false);
  });

  it('source 记录相对路径', () => {
    writeSkill('src-skill', 'name: src-skill');
    const registry = new SkillRegistry();
    new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

    expect(registry.get('src-skill')!.source).toBe('src-skill');
  });

  // P1-3：loader 注册前接 validateUnifiedSkill，非法资产进隔离区
  describe('validate 接线（P1-3）', () => {
    it('默认拒绝非法 domain 并记入 quarantine', () => {
      writeSkill('bad-domain-skill', 'name: bad-domain-skill\ndomain: not-a-real-domain');
      const registry = new SkillRegistry();
      const loader = new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 });

      loader.load();

      expect(registry.has('bad-domain-skill')).toBe(false);
      const q = loader.quarantine.filter(e => e.id === 'bad-domain-skill');
      expect(q).toHaveLength(1);
      expect(q[0].source).toBe('bad-domain-skill');
      expect(q[0].issues.some(i => i.path === 'domain')).toBe(true);
    });

    it('默认拒绝非法 version（非 SemVer）', () => {
      writeSkill('bad-version-skill', 'name: bad-version-skill\nversion: latest');
      const registry = new SkillRegistry();
      const loader = new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 });

      loader.load();

      expect(registry.has('bad-version-skill')).toBe(false);
      expect(loader.quarantine.some(e => e.id === 'bad-version-skill' &&
        e.issues.some(i => i.path === 'version'))).toBe(true);
    });

    it('fallback 自引用被拦截', () => {
      writeSkill('self-fallback', 'name: self-fallback\nfallback: self-fallback');
      const registry = new SkillRegistry();
      const loader = new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 });

      loader.load();

      expect(registry.has('self-fallback')).toBe(false);
      expect(loader.quarantine.some(e => e.id === 'self-fallback' &&
        e.issues.some(i => i.path === 'fallback'))).toBe(true);
    });

    it('validate:false 宽容模式仅记录不阻止注册', () => {
      writeSkill('lenient-skill', 'name: lenient-skill\ndomain: bogus-domain');
      const registry = new SkillRegistry();
      const loader = new SkillLoader(registry, {
        rootDir: root,
        recursive: true,
        maxDepth: 3,
        validate: false,
      });

      loader.load();

      expect(registry.has('lenient-skill')).toBe(true);
      expect(loader.quarantine).toHaveLength(0);
    });

    it('合法资产正常注册且 quarantine 为空', () => {
      // 独立临时目录，避免共享 root 中其他用例写入的坏资产污染隔离计数
      const dir = mkdtempSync(join(tmpdir(), 'yyc3-loader-clean-'));
      try {
        mkdirSync(join(dir, 'valid-skill'), { recursive: true });
        writeFileSync(
          join(dir, 'valid-skill', 'SKILL.md'),
          '---\nname: valid-skill\ndescription: 合法技能\ncategory: development-code\nversion: 1.2.3\n---\n'
        );
        const registry = new SkillRegistry();
        const loader = new SkillLoader(registry, { rootDir: dir, recursive: true, maxDepth: 3 });

        loader.load();

        expect(registry.has('valid-skill')).toBe(true);
        expect(loader.quarantine).toHaveLength(0);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    });

    it('发出 skill:quarantined 事件，含错误明细', () => {
      writeSkill('quarantine-event', 'name: quarantine-event\ndomain: nope');
      const registry = new SkillRegistry();
      const events: Array<{ id: string; source: string; issues: Array<{ path: string }> }> = [];
      registry.on('skill:quarantined', (e) => events.push(e));

      new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();

      expect(events.some(e => e.id === 'quarantine-event' && e.source === 'quarantine-event')).toBe(true);
    });
  });

  // P2：reload sync 语义 — 磁盘为唯一事实源，已删除技能从注册表清除
  describe('reload（sync 语义）', () => {
    it('reload 清除磁盘上已删除的技能', () => {
      writeSkill('reload-keep', 'name: reload-keep\nversion: 1.0.0');
      writeSkill('reload-drop', 'name: reload-drop\nversion: 1.0.0');
      const registry = new SkillRegistry();
      const loader = new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 });
      loader.load();
      expect(registry.get('reload-keep')).toBeDefined();
      expect(registry.get('reload-drop')).toBeDefined();

      // 磁盘删除 + 手工注册幽灵技能（双重漂移场景）
      rmSync(join(root, 'reload-drop'), { recursive: true, force: true });
      registry.register({
        id: 'ghost-skill',
        name: 'ghost-skill',
        description: 'x',
        domain: 'marketplace',
        type: 'hybrid',
        runtime: 'native',
        entry: '',
        inputs: [],
        outputs: [{ type: 'markdown' }],
      });

      loader.reload();

      expect(registry.get('reload-drop')).toBeUndefined(); // 磁盘已删 → 清除
      expect(registry.get('ghost-skill')).toBeUndefined(); // 非磁盘来源 → 清除
      expect(registry.get('reload-keep')).toBeDefined(); // 磁盘仍在 → 保留
    });

    it('默认 load 保持追加语义（不破坏既有行为）', () => {
      writeSkill('append-skill', 'name: append-skill\nversion: 1.0.0');
      const registry = new SkillRegistry();
      registry.register({
        id: 'manual-skill',
        name: 'manual-skill',
        description: 'x',
        domain: 'marketplace',
        type: 'hybrid',
        runtime: 'native',
        entry: '',
        inputs: [],
        outputs: [{ type: 'markdown' }],
      });
      new SkillLoader(registry, { rootDir: root, recursive: true, maxDepth: 3 }).load();
      expect(registry.get('manual-skill')).toBeDefined(); // load 不清除手工注册
      expect(registry.get('append-skill')).toBeDefined();
    });
  });
});
