---
file: 06-面板完整HTML代码.md
description: 面板 HTML 蓝图 v1.2（⚠️ 勿直接覆盖 dashboard 现网面板；P1-C2 已对齐真源契约 batchesPayloadSchema）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.2.0
created: 2026-09-25
updated: 2026-09-26
status: active
tags: [dashboard],[html],[echarts],[blueprint]
category: code
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P1-D1 规范化（修复腐蚀 CDN src/补齐 YAML FM） }
  - { version: v1.2.0, date: 2026-09-26, author: 智能应用落地专家, change: P1-C2 契约归一——数据层对齐 batchesPayloadSchema（envelope/0-10 刻度/data/ 路径），quality_level 改面板侧派生 }
---

# 面板完整 HTML 代码

**P1-C2 契约归一版**：数据层对齐仓库真源契约 `batchesPayloadSchema`（`dashboard/data/batches.json`，envelope 结构，0-10 刻度）。本篇为**蓝图**，建议另存部署（如 `dashboard/panel-v2.html`），勿直接覆盖现网 `dashboard/Ref2VA-流水线管理面板.html`（现网面板已契约对齐）。

---

## 优化版可视化面板完整 HTML

### 定位

单文件零依赖部署蓝图（建议命名 `dashboard/panel-v2.html`，与现网面板并存），数据源 `./data/batches.json`（envelope 契约 `batchesPayloadSchema`），须经 http(s) 静态服务访问，包含概览统计、趋势图表、批次列表、详情弹窗全功能。

### 完整代码

```
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H3 数字人生产流水线 · 管理面板 | YanYuCloudCube</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#C8A968',
                        secondary: '#3B82F6',
                        dark: {
                            100: '#1E293B',
                            200: '#0F172A',
                            300: '#020617'
                        }
                    },
                    fontFamily: {
                        sans: ['PingFang SC', 'Microsoft YaHei', 'sans-serif']
                    }
                }
            }
        }
    </script>
    <style type="text/tailwindcss">
        @layer utilities {
            .text-shadow-glow {
                text-shadow: 0 0 20px rgba(200, 169, 104, 0.3);
            }
            .card-border {
                border: 1px solid rgba(200, 169, 104, 0.15);
            }
        }
    </style>
</head>
<body class="bg-dark-300 text-gray-100 min-h-screen">
    <!-- 顶部导航 -->
    <header class="bg-dark-200 border-b border-primary/20 px-6 py-4">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <span class="text-primary font-bold text-lg">言</span>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-primary text-shadow-glow">H3 数字人生产流水线</h1>
                    <p class="text-xs text-gray-400">YanYuCloudCube · 言启象限 语枢未来</p>
                </div>
            </div>
            <div class="flex items-center gap-6">
                <div class="text-right">
                    <div class="text-xs text-gray-400">最后更新</div>
                    <div id="lastUpdate" class="text-sm font-medium">加载中...</div>
                </div>
                <div class="flex items-center gap-2">
                    <label class="text-xs text-gray-400">自动刷新</label>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" id="autoRefresh" class="sr-only peer" checked>
                        <div class="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                </div>
                <button id="refreshBtn" class="px-4 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-sm transition-colors border border-primary/20">
                    手动刷新
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-6">
        <!-- 数据概览卡片 -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">总批次</div>
                <div id="statTotal" class="text-2xl font-bold text-white">--</div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">成功率</div>
                <div id="statSuccess" class="text-2xl font-bold text-green-400">--</div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">平均耗时</div>
                <div id="statTime" class="text-2xl font-bold text-secondary">--</div>
                <div class="text-xs text-gray-500">min/批次</div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">平均质量分</div>
                <div id="statScore" class="text-2xl font-bold text-primary">--</div>
                <div class="text-xs text-gray-500">0-10 刻度</div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">峰值内存</div>
                <div id="statMemory" class="text-2xl font-bold text-orange-400">--</div>
                <div class="text-xs text-gray-500">GB</div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <div class="text-gray-400 text-xs mb-1">运行中</div>
                <div id="statRunning" class="text-2xl font-bold text-yellow-400">--</div>
            </div>
        </div>

        <!-- 图表区 -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
            <div class="lg:col-span-2 bg-dark-200 rounded-xl p-4 card-border">
                <h3 class="text-sm font-medium mb-3 text-gray-300">近 10 批耗时与质量分趋势</h3>
                <div id="trendChart" class="h-64"></div>
            </div>
            <div class="bg-dark-200 rounded-xl p-4 card-border">
                <h3 class="text-sm font-medium mb-3 text-gray-300">质量等级分布</h3>
                <div id="qualityChart" class="h-64"></div>
            </div>
        </div>

        <!-- 筛选栏 -->
        <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
                <span class="text-sm text-gray-400">状态筛选：</span>
                <select id="filterStatus" class="bg-dark-100 border border-gray-700 rounded-lg px-3 py-1.5 text-sm">
                    <option value="all">全部</option>
                    <option value="completed">已完成</option>
                    <option value="failed">失败</option>
                    <option value="running">运行中</option>
                </select>
                <select id="filterMode" class="bg-dark-100 border border-gray-700 rounded-lg px-3 py-1.5 text-sm">
                    <option value="all">全部模式</option>
                    <option value="ref2va">Ref2VA</option>
                    <option value="fl2va">FL2VA</option>
                </select>
            </div>
            <div class="text-xs text-gray-500">数据来源：NAS RAID1 高可用区 · 每 5 分钟自动同步</div>
        </div>

        <!-- 批次列表 -->
        <div class="bg-dark-200 rounded-xl card-border overflow-hidden">
            <table class="w-full text-sm">
                <thead class="bg-dark-100 text-gray-400 text-xs">
                    <tr>
                        <th class="text-left px-4 py-3 font-medium">批次ID</th>
                        <th class="text-left px-4 py-3 font-medium">时间</th>
                        <th class="text-left px-4 py-3 font-medium">模型</th>
                        <th class="text-left px-4 py-3 font-medium">状态</th>
                        <th class="text-right px-4 py-3 font-medium">成功视频</th>
                        <th class="text-right px-4 py-3 font-medium">耗时(min)</th>
                        <th class="text-right px-4 py-3 font-medium">平均分</th>
                        <th class="text-left px-4 py-3 font-medium">质量等级</th>
                        <th class="text-center px-4 py-3 font-medium">操作</th>
                    </tr>
                </thead>
                <tbody id="batchList" class="divide-y divide-gray-800">
                    <tr><td colspan="9" class="text-center py-12 text-gray-500">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    </main>

    <!-- 详情弹窗 -->
    <div id="detailModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 hidden items-center justify-center p-4">
        <div class="bg-dark-200 rounded-2xl card-border max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div class="p-6 border-b border-gray-800 flex items-center justify-between">
                <h3 class="text-lg font-bold text-primary">批次详情</h3>
                <button id="closeModal" class="text-gray-400 hover:text-white text-xl">×</button>
            </div>
            <div id="detailContent" class="p-6 text-sm space-y-4">
            </div>
        </div>
    </div>

    <footer class="text-center py-6 text-xs text-gray-600">
        <p>© 2026 YanYuCloudCube · All things converge in cloud pivot; Deep stacks ignite a new era of intelligence</p>
        <p class="mt-1">v2.1.0 · 对齐 A2A 生产节点 · NAS 双分区高可用</p>
    </footer>

    <script>
        // ==================== 配置 ====================
        const CONFIG = {
            // 数据源：dashboard/data/batches.json（真源契约 batchesPayloadSchema，须 http(s) 访问）
            dataSource: "data/batches.json",
            // 自动刷新间隔（毫秒），与 NAS 同步对齐
            refreshInterval: 300000,
            // 质量等级颜色映射（展示层派生，非契约字段，阈值见 qualityOf()）
            qualityColor: {
                "优秀": "text-green-400",
                "良好": "text-blue-400",
                "合格": "text-yellow-400",
                "待优化": "text-red-400"
            },
            statusColor: {
                "completed": "bg-green-500/10 text-green-400 border-green-500/20",
                "failed": "bg-red-500/10 text-red-400 border-red-500/20",
                "running": "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
            }
        };

        let batchesData = [];
        let trendChart = null;
        let qualityChart = null;
        let autoRefreshTimer = null;

        // 质量等级派生（展示层专用；契约不含 quality_level；avgScore 为 0-10 刻度）
        function qualityOf(avgScore) {
            if (avgScore >= 9) return "优秀";
            if (avgScore >= 8) return "良好";
            if (avgScore >= 6) return "合格";
            return "待优化";
        }

        // ==================== 数据加载 ====================
        async function loadData() {
            try {
                const res = await fetch(CONFIG.dataSource + "?t=" + Date.now(), { cache: "no-store" });
                const payload = await res.json();
                // envelope 契约：{ schema_version, generated_at, score_scale, batches[], top10[] }
                if (!Array.isArray(payload.batches)) throw new Error("契约不符：缺少 batches[]");
                batchesData = payload.batches;
                renderAll();
                document.getElementById("lastUpdate").textContent = new Date().toLocaleString("zh-CN");
            } catch (e) {
                console.warn("[panel] batches.json 加载失败：", e.message);
                document.getElementById("batchList").innerHTML =
                    '<tr><td colspan="9" class="text-center py-12 text-red-400">数据加载失败，请检查 data/batches.json（契约：batchesPayloadSchema）</td></tr>';
            }
        }

        // ==================== 渲染 ====================
        function renderAll() {
            renderStats();
            renderCharts();
            renderTable();
        }

        function renderStats() {
            const completed = batchesData.filter(b => b.status === "completed");
            const successRate = batchesData.length
                ? ((completed.length / batchesData.length) * 100).toFixed(1) + "%"
                : "--";

            // durationMin：批次耗时（分钟，契约字段）
            const avgTime = completed.length
                ? (completed.reduce((s, b) => s + (b.durationMin || 0), 0) / completed.length).toFixed(1)
                : "--";

            // avgScore：0-10 刻度（人工分或口型分×10，契约字段）
            const avgScore = completed.length
                ? (completed.reduce((s, b) => s + (b.avgScore || 0), 0) / completed.length).toFixed(2)
                : "--";

            // 批次峰值内存：videos[].peak_rss_gb 取 max（展示层派生）
            const peakMem = Math.max(...batchesData.flatMap(b => (b.videos || []).map(v => v.peak_rss_gb || 0)), 0).toFixed(1);
            const running = batchesData.filter(b => b.status === "running").length;

            document.getElementById("statTotal").textContent = batchesData.length;
            document.getElementById("statSuccess").textContent = successRate;
            document.getElementById("statTime").textContent = avgTime;
            document.getElementById("statScore").textContent = avgScore;
            document.getElementById("statMemory").textContent = peakMem;
            document.getElementById("statRunning").textContent = running;
        }

        function renderCharts() {
            const recent = batchesData.slice(0, 10).reverse();

            // 趋势图
            if (!trendChart) {
                trendChart = echarts.init(document.getElementById("trendChart"));
                window.addEventListener("resize", () => trendChart.resize());
            }
            trendChart.setOption({
                tooltip: { trigger: "axis" },
                legend: { data: ["耗时(min)", "质量分"], textStyle: { color: "#94a3b8", fontSize: 11 } },
                grid: { left: 40, right: 40, top: 30, bottom: 30 },
                xAxis: {
                    type: "category",
                    data: recent.map(b => b.id),
                    axisLabel: { color: "#64748b", fontSize: 10 }
                },
                yAxis: [
                    { type: "value", name: "耗时(min)", axisLabel: { color: "#64748b" } },
                    { type: "value", name: "质量分", min: 0, max: 10, axisLabel: { color: "#64748b" } }
                ],
                series: [
                    {
                        name: "耗时(min)",
                        type: "bar",
                        data: recent.map(b => b.durationMin || 0),
                        itemStyle: { color: "#3B82F6", borderRadius: [4,4,0,0] }
                    },
                    {
                        name: "质量分",
                        type: "line",
                        yAxisIndex: 1,
                        data: recent.map(b => b.avgScore || 0),
                        itemStyle: { color: "#C8A968" },
                        lineStyle: { width: 2 },
                        symbol: "circle",
                        symbolSize: 6
                    }
                ]
            });

            // 质量分布图
            if (!qualityChart) {
                qualityChart = echarts.init(document.getElementById("qualityChart"));
                window.addEventListener("resize", () => qualityChart.resize());
            }
            const qualityCount = {};
            batchesData.forEach(b => {
                const lv = qualityOf(b.avgScore || 0);
                qualityCount[lv] = (qualityCount[lv] || 0) + 1;
            });
            qualityChart.setOption({
                tooltip: { trigger: "item" },
                series: [{
                    type: "pie",
                    radius: ["50%", "75%"],
                    center: ["50%", "55%"],
                    data: [
                        { value: qualityCount["优秀"] || 0, name: "优秀", itemStyle: { color: "#4ade80" } },
                        { value: qualityCount["良好"] || 0, name: "良好", itemStyle: { color: "#60a5fa" } },
                        { value: qualityCount["合格"] || 0, name: "合格", itemStyle: { color: "#facc15" } },
                        { value: qualityCount["待优化"] || 0, name: "待优化", itemStyle: { color: "#f87171" } }
                    ],
                    label: { color: "#94a3b8", fontSize: 11 }
                }]
            });
        }

        function renderTable() {
            const statusFilter = document.getElementById("filterStatus").value;
            const modeFilter = document.getElementById("filterMode").value;

            const filtered = batchesData.filter(b => {
                if (statusFilter !== "all" && b.status !== statusFilter) return false;
                if (modeFilter !== "all" && b.pipeline !== modeFilter) return false;
                return true;
            });

            if (!filtered.length) {
                document.getElementById("batchList").innerHTML =
                    '<tr><td colspan="9" class="text-center py-12 text-gray-500">暂无匹配数据</td></tr>';
                return;
            }

            document.getElementById("batchList").innerHTML = filtered.map(b => `
                <tr class="hover:bg-dark-100/50 transition-colors">
                    <td class="px-4 py-3 font-mono text-xs">${b.id}</td>
                    <td class="px-4 py-3 text-gray-400 text-xs">${b.time}</td>
                    <td class="px-4 py-3 text-xs uppercase">${(b.model || "").toUpperCase()}·${b.pipeline || "-"}</td>
                    <td class="px-4 py-3">
                        <span class="px-2 py-0.5 rounded text-xs border ${CONFIG.statusColor[b.status]}">${b.status}</span>
                    </td>
                    <td class="px-4 py-3 text-right">${b.success}/${(b.videos || []).length}</td>
                    <td class="px-4 py-3 text-right">${b.durationMin ?? "-"}min</td>
                    <td class="px-4 py-3 text-right font-mono">${b.avgScore ?? "-"}</td>
                    <td class="px-4 py-3 ${CONFIG.qualityColor[qualityOf(b.avgScore || 0)]}">${qualityOf(b.avgScore || 0)}</td>
                    <td class="px-4 py-3 text-center">
                        <button onclick="showDetail('${b.id}')" class="text-primary hover:text-primary/80 text-xs">详情</button>
                    </td>
                </tr>
            `).join("");
        }

        // ==================== 详情弹窗 ====================
        function showDetail(batchId) {
            const batch = batchesData.find(b => b.id === batchId);
            if (!batch) return;

            const peakMem = Math.max(...(batch.videos || []).map(v => v.peak_rss_gb || 0), 0);
            const defects = Object.entries(batch.defects || {}).slice(0, 3)
                .map(([k, n]) => `${k}×${n}`).join("、") || "无标注";
            const p = batch.params || {};

            document.getElementById("detailContent").innerHTML = `
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <div class="text-gray-400 text-xs mb-1">批次ID</div>
                        <div class="font-mono">${batch.id}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">启动时间</div>
                        <div>${batch.time || "-"}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">结束时间</div>
                        <div>${batch.ended || "进行中"}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">状态</div>
                        <span class="px-2 py-0.5 rounded text-xs border ${CONFIG.statusColor[batch.status]}">${batch.status}</span>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">模型 · 流水线</div>
                        <div class="uppercase">${(batch.model || "").toUpperCase()}·${batch.pipeline || "-"}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">参考图 / 种子数</div>
                        <div>${batch.refImages} / ${batch.seeds}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">成功 / 失败 / 跳过</div>
                        <div>${batch.success} / ${batch.failed} / ${batch.skipped}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">批次耗时</div>
                        <div>${batch.durationMin ?? "-"} 分钟</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">平均分（0-10）</div>
                        <div class="${CONFIG.qualityColor[qualityOf(batch.avgScore || 0)]} font-medium">${batch.avgScore ?? "-"} · ${qualityOf(batch.avgScore || 0)}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">最高分（0-10）</div>
                        <div>${batch.maxScore ?? "-"}</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">峰值内存（派生）</div>
                        <div>${peakMem} GB</div>
                    </div>
                    <div>
                        <div class="text-gray-400 text-xs mb-1">生成参数</div>
                        <div class="text-xs">${p.height || "?"}×${p.width || "?"} · ${p.num_frames || "?"}帧 · ${p.num_inference_steps || "?"}步 · ${p.fps || "?"}fps</div>
                    </div>
                </div>
                <div class="pt-4 border-t border-gray-800">
                    <div class="text-gray-400 text-xs mb-1">缺陷分布（Top3）</div>
                    <div class="text-gray-200">${defects}</div>
                </div>
                <div class="pt-4 border-t border-gray-800">
                    <div class="text-gray-400 text-xs mb-1">视频明细（前 5 条）</div>
                    <div class="text-gray-200 text-xs font-mono leading-relaxed">
                        ${(batch.videos || []).slice(0, 5).map(v => `${v.name} · ${v.score}分(${v.source})`).join("<br>") || "-"}
                    </div>
                </div>
            `;
            document.getElementById("detailModal").classList.remove("hidden");
            document.getElementById("detailModal").classList.add("flex");
        }

        // ==================== 事件 ====================
        document.getElementById("refreshBtn").addEventListener("click", loadData);
        document.getElementById("filterStatus").addEventListener("change", renderTable);
        document.getElementById("filterMode").addEventListener("change", renderTable);
        document.getElementById("closeModal").addEventListener("click", () => {
            document.getElementById("detailModal").classList.add("hidden");
            document.getElementById("detailModal").classList.remove("flex");
        });
        document.getElementById("detailModal").addEventListener("click", e => {
            if (e.target.id === "detailModal") {
                document.getElementById("detailModal").classList.add("hidden");
                document.getElementById("detailModal").classList.remove("flex");
            }
        });

        document.getElementById("autoRefresh").addEventListener("change", e => {
            if (e.target.checked) {
                startAutoRefresh();
            } else {
                clearInterval(autoRefreshTimer);
            }
        });

        function startAutoRefresh() {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = setInterval(loadData, CONFIG.refreshInterval);
        }

        // 初始化
        loadData();
        startAutoRefresh();
    </script>
</body>
</html>
```

### 部署与验证

#### 1. 本地部署验证

1. 将上述 HTML 保存为 `dashboard/panel-v2.html`（蓝图与现网面板并存，勿覆盖现网文件）
2. 执行 `python3 scripts/pipeline-tools/export_dashboard_data.py`，确认 `dashboard/data/batches.json` 已生成
3. `cd dashboard && python3 -m http.server 8080`，浏览器打开 `http://localhost:8080/panel-v2.html`，查看数据加载与图表渲染（评分应为 0-10 刻度）

#### 2. NAS 多终端访问

1. 确认前文 NAS 同步脚本已包含 `dashboard/` 目录（含 `data/batches.json`）
2. 内网访问：NAS 静态站点 `dashboard-h3.0379.world`（数据于 `/data/batches.json`）
3. 公网访问：复用 `api.0379.world` 网关代理 `/h3-dashboard/` 路径（数据于 `/h3-dashboard/data/batches.json`）

### 核心优化点

- **视觉对齐**：暗金主题配色，对齐 YYC³ 品牌视觉体系与古文化风格质感
- **契约对齐（P1-C2）**：数据层严格消费 `batchesPayloadSchema` envelope（`payload.batches`），0-10 评分刻度，与唯一写端 `export_dashboard_data.py` 输出逐字段一致
- **派生与契约分离**：质量等级（qualityOf）、批次峰值内存等展示层指标均为前端派生，不污染契约字段
- **全功能覆盖**：概览统计、双图表趋势分析、多维度筛选、详情弹窗（含缺陷分布与视频明细）、自动刷新
- **零依赖部署**：单文件 HTML，仅通过 CDN 引入 ECharts 与 Tailwind，无需构建
- **响应式适配**：适配桌面、平板多尺寸屏幕
