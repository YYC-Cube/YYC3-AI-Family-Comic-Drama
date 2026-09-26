# 贡献指南（Contributing）

> 感谢你对 MiniMax-H3 本地生产线的关注。本指南面向外部贡献者；团队内部协作用户规则见仓库根 `README.md` 与 `docs/YYC3-团队通用-标规文档/`。

## 一、开始之前

1. 先读 [docs/08-开发者文档.md](docs/08-开发者文档.md)——架构、API、manifest 契约、故障排除全在其中
2. 概念词典：[docs/05-全局释义与指导文档.md](docs/05-全局释义与指导文档.md)
3. 环境部署：[docs/01-环境部署指南.md](docs/01-环境部署指南.md)

## 二、开发流程

```bash
# 1. Fork 后克隆
git clone git@github.com:YOUR_FORK/YYC3-MiniMax-H3.git
cd YYC3-MiniMax-H3

# 2. 建分支（命名：feat|fix|docs|chore/<主题>）
git checkout -b feat/my-topic

# 3. 安装（Python ≥3.10，GPU 节点参考部署指南）
pip install -r requirements.txt
```

## 三、提交前必须通过的门禁

| 门禁 | 命令 | 标准 |
| ---- | ---- | ---- |
| 语法编译 | `python3 -m py_compile <改动文件>` | 0 错误 |
| 核心回归 | `python3 -m unittest discover scripts/pipeline-tools -v` | 全绿 |
| 冒烟（涉及流水线） | `bash scripts/pipeline-tools/pipeline_smoke_mac.sh` | 4 步 PASS |
| 安全红线 | 改动中无 `shell=True` 拼接用户输入、无明文密钥 | 零容忍 |
| 秘密检查 | 提交不含 `.env`/`.secrets/`/密钥（git diff 自查） | 零容忍 |

## 四、提交规范

- 提交信息格式：`<type>(<scope>): <一句话概述>`（type ∈ feat/fix/docs/chore/refactor/test）
- 中文概述、正文说明「为什么」；敏感值一律用 `${ENV_VAR}` 占位
- 一个 PR 只做一件事；附带验证证据（命令输出摘要或截图）

## 五、Pull Request 检查单

- [ ] 门禁全过（附输出）
- [ ] 文档同步更新（改了行为就必须改对应 docs/）
- [ ] 无硬编码密钥 / 无个人路径（如 `/Users/yanyu/...`）
- [ ] 变更历史已说明影响面

## 六、行为准则

互相尊重、对事不对人；安全相关问题请走私下渠道（admin@0379.email）而非公开 issue。

> 「言启千行代码，语枢万物智能」——欢迎你的 PR。
