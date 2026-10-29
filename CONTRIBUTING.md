# 贡献指南 · CONTRIBUTING

感谢关注 YYC³ 家族项目！贡献前请先阅读 [团队标准规范 SSOT](../../YYC3-团队通用-标准规范/)。

## 🌿 分支规范

| 分支 | 用途 |
|---|---|
| `main` | 稳定线（受保护，PR 进入） |
| `feat/<主题>` | 功能开发 |
| `fix/<主题>` | 缺陷修复 |
| `docs/<主题>` | 文档 |
| `dependabot/*` | 依赖机器人（自动） |

## 📝 提交规范（Conventional Commits）

```
feat: 新功能        fix: 缺陷修复       docs: 文档
style: 格式         refactor: 重构      perf: 性能
test: 测试          build: 构建         chore: 杂务
```

示例：`feat(settings): 统一设置三层收敛 — 网关管理面入设置页`

## 🔄 贡献流程

1. Fork / 建分支
2. 开发 + 自测（`pnpm test`）
3. 提交（遵循上述规范，一次提交一件事）
4. Push 并发起 PR（关联 Issue，说明验证方式）
5. 通过 CI 与维护者审查后合并

## 📄 许可

贡献即同意以 [MIT](LICENSE) 许可授权贡献内容。

---

> ***YanYuCloudCube*** · *言启象限 | 语枢未来*
