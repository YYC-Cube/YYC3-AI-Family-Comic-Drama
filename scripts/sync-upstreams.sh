#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# YYC³ 上游核心代码自动同步脚本
# 用途：从 YYC-Cube 上游仓库拉取核心代码到本地四仓库目录
# 用法：bash scripts/sync-upstreams.sh [ci]
# 清单：scripts/upstreams.tsv（仓库|目标|源路径|目标路径|保护文件|sparse）
# 规则：保护文件（README/.gitignore/.env.example）本地为准不被覆盖
# ══════════════════════════════════════════════════════════════
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$ROOT/.upstream-cache"
CONFIG="$ROOT/scripts/upstreams.tsv"
GH_OWNER="${GH_OWNER:-YYC-Cube}"
# 本地默认 SSH（https 受网络环境阻断）；GitHub Actions 中设 REMOTE_BASE=https://github.com/YYC-Cube
REMOTE_BASE="${REMOTE_BASE:-git@github.com:$GH_OWNER}"
MODE="${1:-manual}"
REPORT="$ROOT/scripts/upstream-sync-report.md"

mkdir -p "$CACHE"

# ── 报告头 ────────────────────────────────────────────────────
{
  echo "# 上游核心代码同步报告"
  echo ""
  echo "| 项目 | 值 |"
  echo "| ---- | ---- |"
  echo "| 执行时间 | $(date '+%Y-%m-%d %H:%M:%S') |"
  echo "| 执行模式 | $MODE |"
  echo "| 上游组织 | $GH_OWNER |"
  echo ""
  echo "| 上游仓库 | 映射 | 上游 SHA | 状态 |"
  echo "| ---- | ---- | ---- | ---- |"
} > "$REPORT"

# ── 单仓库准备（浅克隆 + 可选 sparse checkout）────────────────
ensure_repo() {
  local repo="$1" sparse="$2"
  local dir="$CACHE/$repo"
  if [ -d "$dir/.git" ]; then
    git -C "$dir" fetch --depth 1 origin main >/dev/null 2>&1 \
      || git -C "$dir" fetch --depth 1 origin master >/dev/null 2>&1 || true
    git -C "$dir" reset --hard FETCH_HEAD >/dev/null 2>&1 || true
  else
    if [ -n "$sparse" ]; then
      git clone --depth 1 --filter=blob:none --sparse \
        "$REMOTE_BASE/$repo.git" "$dir" >/dev/null 2>&1
    else
      git clone --depth 1 "$REMOTE_BASE/$repo.git" "$dir" >/dev/null 2>&1
    fi
  fi
  if [ -n "$sparse" ]; then
    git -C "$dir" sparse-checkout set ${sparse//;/ } >/dev/null 2>&1 || true
  fi
  git -C "$dir" rev-parse --short HEAD
}

# ── 单条映射同步 ──────────────────────────────────────────────
sync_mapping() {
  local repo="$1" target="$2" src="$3" dst="$4" protect="$5" sha="$6"
  local srcpath="$CACHE/$repo/$src"
  if [ ! -e "$srcpath" ]; then
    echo "| $repo | \`$src → $dst\` | \`$sha\` | ⚠️ 上游源不存在，跳过 |" >> "$REPORT"
    return
  fi
  local excludes=(--exclude '.git/' --exclude 'node_modules/' --exclude '__pycache__/'
                  --exclude '.next/' --exclude 'dist/' --exclude '*.tsbuildinfo'
                  --exclude 'pnpm-lock.yaml' --exclude 'package-lock.json')
  if [ -n "$protect" ]; then
    local p
    IFS=',' read -ra PROT <<< "$protect"
    for p in "${PROT[@]}"; do excludes+=(--exclude "$p"); done
  fi
  if [ -d "$srcpath" ]; then
    mkdir -p "$ROOT/$target/$dst"
    rsync -a "${excludes[@]}" "$srcpath/" "$ROOT/$target/$dst/"
  else
    mkdir -p "$(dirname "$ROOT/$target/$dst")"
    rsync -a "${excludes[@]}" "$srcpath" "$ROOT/$target/$dst"
  fi
  echo "| $repo | \`$src → $dst\` | \`$sha\` | ✅ |" >> "$REPORT"
}

# ── 主循环（兼容 macOS bash 3.2，不使用关联数组）──────────────
PREPARED=" "
while IFS='|' read -r repo target src dst protect sparse; do
  repo=$(echo "${repo:-}" | xargs); target=$(echo "${target:-}" | xargs)
  src=$(echo "${src:-}" | xargs); dst=$(echo "${dst:-}" | xargs)
  protect=$(echo "${protect:-}" | xargs); sparse=$(echo "${sparse:-}" | xargs)
  [ -z "$repo" ] && continue
  case "$repo" in \#*) continue ;; esac
  case "$PREPARED" in *" $repo "*) ;; *)
    ensure_repo "$repo" "$sparse"
    PREPARED="$PREPARED$repo "
    ;; esac
  sha="$(git -C "$CACHE/$repo" rev-parse --short HEAD)"
  sync_mapping "$repo" "$target" "$src" "$dst" "$protect" "$sha"
done < "$CONFIG"

# ── 报告尾 ────────────────────────────────────────────────────
CHANGED=$(git -C "$ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ' || echo 0)
{
  echo ""
  echo "**本地工作区变更文件数**：$CHANGED"
  echo ""
  echo "> 生成方式：\`bash scripts/sync-upstreams.sh\` · 定时同步见 \`.github/workflows/sync-upstreams.yml\`"
} >> "$REPORT"

echo "✅ 同步完成 → $REPORT"
if [ "$MODE" = "ci" ]; then echo "CI 模式：变更 $CHANGED 个文件"; fi
exit 0
