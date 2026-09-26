/**
 * Skill Gateway — 独立服务入口
 *
 * 用途：容器化部署（Dockerfile stage: skill-gateway）
 * 组装 registry + loader + executor 并启动 HTTP 服务
 */
import { SkillLoader, SkillExecutor, globalSkillRegistry } from '@yyc3/skill-registry';
import { SkillGateway } from './gateway.js';
import { apiKeysFromEnv } from './middleware/auth.js';

const port = Number(process.env.PORT ?? 3030);
const skillsRootDir = process.env.SKILLS_ROOT_DIR ?? './skills';

const loader = new SkillLoader(globalSkillRegistry, {
  rootDir: skillsRootDir,
  maxDepth: 3,
});

const executor = new SkillExecutor(globalSkillRegistry);

const gateway = new SkillGateway(
  { registry: globalSkillRegistry, loader, executor },
  { port }
);

await gateway.start(port);

// 技能卷空载预警（Task I2）：镜像内置快照缺失或卷未挂载时提示
if (globalSkillRegistry.getStats().totalSkills === 0) {
  console.warn(
    `[SkillGateway] ⚠ skills 目录空载（${skillsRootDir}）：total=0。` +
      '请确认已挂载 skills 卷或使用内置技能快照的镜像。'
  );
}

const authMode = apiKeysFromEnv(process.env.YYC3_API_KEYS).length > 0 ? 'key' : 'fail-closed（未配置 YYC3_API_KEYS，写操作拒绝）';
console.warn(`[SkillGateway] 认证模式: ${authMode}`);

// Node 下 serve() 为异步启动，周期性健康检查由容器 HEALTHCHECK 接管
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
