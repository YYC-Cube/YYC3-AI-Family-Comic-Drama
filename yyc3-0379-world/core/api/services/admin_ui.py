# file: admin_ui.py
# description: vk 管理看板 - 零依赖单页（挂 /v1/admin/dashboard，受 Auth 中间件保护）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [dashboard],[virtual-keys],[visualization]
# flake8: noqa: E501（内嵌 HTML/CSS 为 minified 风格单行，折行破坏模板可维护性）

"""虚拟密钥管理看板（五化-可视化）：
零前端工程依赖——FastAPI 直接返回单页 HTML+fetch，调既有 /v1/admin/virtual-keys* API。
功能：密钥列表（用量/预算进度）+ 创建 + 启停 + 编辑（预算/TPM/白名单）+ 搜索 + 分页 + 按模型用量查询。
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>YYC³ 虚拟密钥看板</title>
<style>
  body{font-family:-apple-system,sans-serif;max-width:1080px;margin:2rem auto;padding:0 1rem;background:#0d1117;color:#e6edf3}
  h1{font-size:1.3rem} table{width:100%;border-collapse:collapse;margin:1rem 0}
  th,td{padding:.5rem .6rem;border-bottom:1px solid #21262d;text-align:left;font-size:.86rem}
  th{color:#8b949e;font-weight:600} tr:hover{background:#161b22}
  .tag{padding:.15rem .5rem;border-radius:10px;font-size:.75rem}
  .on{background:#1a4731;color:#4ade80}.off{background:#4a2229;color:#f87171}
  button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:.3rem .7rem;cursor:pointer;margin:0 .15rem}
  button:hover{background:#30363d} input{background:#0d1117;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:.35rem .5rem}
  form{display:flex;gap:.5rem;flex-wrap:wrap;align-items:end;margin:1rem 0}
  label{font-size:.78rem;color:#8b949e;display:block;margin-bottom:.2rem}
  .bar{background:#21262d;border-radius:6px;height:8px;width:110px;display:inline-block;vertical-align:middle}
  .fill{background:#2f81f7;border-radius:6px;height:8px}
  .toolbar{display:flex;gap:.5rem;align-items:center;margin:1rem 0}
  dialog{background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:10px;max-width:560px}
  pre{white-space:pre-wrap;font-size:.78rem}
  .warn{color:#f0883e;font-size:.82rem}
  .muted{color:#8b949e;font-size:.8rem}
</style>
</head>
<body>
<h1>YYC³ 虚拟密钥看板</h1>
<p class="warn">明文 Key 仅创建时显示一次，请立即保存。</p>
<details><summary>➕ 创建虚拟密钥</summary>
<form onsubmit="createVK(event)">
  <div><label>名称*</label><input id="f-name" required></div>
  <div><label>所有者</label><input id="f-owner" value="yanyu"></div>
  <div><label>月预算USD(0=不限)</label><input id="f-budget" type="number" step="0.01" value="0"></div>
  <div><label>TPM(0=不限)</label><input id="f-tpm" type="number" value="0"></div>
  <div><label>模型白名单(逗号分隔,空=不限,支持*通配)</label><input id="f-wl" placeholder="glm-4*,zhipu:*" size="34"></div>
  <button>创建</button>
</form></details>
<div class="toolbar">
  <input id="q" placeholder="🔍 搜索名称/所有者…" oninput="render()">
  <span class="muted" id="cnt"></span>
  <span style="flex:1"></span>
  <button onclick="page(-1)">‹ 上一页</button>
  <span class="muted" id="pg"></span>
  <button onclick="page(1)">下一页 ›</button>
</div>
<table id="tbl"><thead><tr>
<th>名称</th><th>所有者</th><th>Key</th><th>状态</th><th>预算消耗</th><th>TPM上限</th><th>操作</th>
</tr></thead><tbody></tbody></table>
<dialog id="dlg"><h3 id="dlg-t"></h3><pre id="dlg-b"></pre>
<form method="dialog"><button>关闭</button></form></dialog>
<dialog id="edlg"><h3>编辑 — <span id="ed-name"></span></h3>
<form onsubmit="saveEdit(event)">
  <div><label>月预算USD(0=不限)</label><input id="e-budget" type="number" step="0.01"></div>
  <div><label>TPM(0=不限)</label><input id="e-tpm" type="number"></div>
  <div style="flex-basis:100%"><label>模型白名单(逗号分隔,空=不限)</label><input id="e-wl" size="42"></div>
  <button>保存</button>
  <button type="button" onclick="edlg.close()">取消</button>
</form></dialog>
<script>
const esc = s => String(s??'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let ALL=[], PER=10, CUR=1, EDIT_ID='';
let ADMIN_KEY = sessionStorage.getItem('yyc3-admin-key') || '';
async function authFetch(url, opts = {}) {
  // 空 Key 不设头（fetch 空值头在 Chrome 会 TypeError 且吞掉 403 prompt 分支）
  const h = {...(opts.headers || {})};
  if (ADMIN_KEY) h['X-API-Key'] = ADMIN_KEY;
  const r = await fetch(url, {...opts, headers: h}).catch(() => null);
  if (r && r.status === 403) {
    ADMIN_KEY = prompt('管理面需要 ADMIN_API_KEYS 中的密钥：') || '';
    sessionStorage.setItem('yyc3-admin-key', ADMIN_KEY);
    if (ADMIN_KEY) return authFetch(url, opts);
  }
  return r;
}
async function load(){
  const r = await authFetch('/v1/admin/virtual-keys');
  if (!r || !r.ok) return;
  const d = await r.json();
  ALL = d.keys||[]; render();
}
function render(){
  const q = document.getElementById('q').value.trim().toLowerCase();
  const rows = ALL.filter(k => !q || (k.name||'').toLowerCase().includes(q) || (k.owner||'').toLowerCase().includes(q));
  const maxP = Math.max(1, Math.ceil(rows.length/PER));
  if(CUR>maxP) CUR=maxP;
  const pageRows = rows.slice((CUR-1)*PER, CUR*PER);
  document.getElementById('cnt').textContent = `共 ${rows.length} 条`;
  document.getElementById('pg').textContent = `${CUR}/${maxP}`;
  const tb = document.querySelector('#tbl tbody'); tb.innerHTML = '';
  for (const k of pageRows) {
    const budget = +k.monthly_budget_usd||0, spent = +k.spent_usd||0;
    const pct = budget>0 ? Math.min(100, spent/budget*100) : 0;
    const bar = budget>0
      ? `<span class="bar"><span class="fill" style="width:${pct}%"></span></span> ${spent.toFixed(4)}/${budget} (${pct.toFixed(0)}%)`
      : `${spent.toFixed(4)}` + ' / 不限';
    tb.insertAdjacentHTML('beforeend', `<tr>
      <td>${esc(k.name)}</td><td>${esc(k.owner)}</td><td><code>${esc(k.key_hint)}…</code></td>
      <td><span class="tag ${k.status==='active'?'on':'off'}">${k.status}</span></td>
      <td>${bar}</td><td>${+k.rate_limit_tpm||'不限'}</td>
      <td>
        <button onclick="usage('${k.id}','${esc(k.name)}')">用量</button>
        <button onclick="openEdit('${k.id}')">编辑</button>
        <button onclick="toggle('${k.id}','${k.status==='active'?'disabled':'active'}')">${k.status==='active'?'停用':'启用'}</button>
        <button onclick="del('${k.id}','${esc(k.name)}')">删除</button>
      </td></tr>`);
  }
}
function page(d){CUR+=d; if(CUR<1)CUR=1; render();}
async function createVK(e){e.preventDefault();
  const wl=document.getElementById('f-wl').value.split(',').map(s=>s.trim()).filter(Boolean);
  const r=await authFetch('/v1/admin/virtual-keys',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:document.getElementById('f-name').value,owner:document.getElementById('f-owner').value,
      monthly_budget_usd:+document.getElementById('f-budget').value||0,rate_limit_tpm:+document.getElementById('f-tpm').value||0,
      model_whitelist:wl})});
  const d=await r.json();
  if(r.ok){show('创建成功 — 明文Key（仅此一次）', d.key); e.target.reset(); load();}
  else show('创建失败', JSON.stringify(d,null,2));
}
async function toggle(id,s){await patch(id,{status:s});}
function openEdit(id){
  const k = ALL.find(x=>x.id===id); if(!k) return;
  EDIT_ID=id; document.getElementById('ed-name').textContent=k.name;
  document.getElementById('e-budget').value=k.monthly_budget_usd||0;
  document.getElementById('e-tpm').value=k.rate_limit_tpm||0;
  document.getElementById('e-wl').value=(k.model_whitelist||[]).join(',');
  document.getElementById('edlg').showModal();
}
async function saveEdit(e){e.preventDefault();
  await patch(EDIT_ID,{
    monthly_budget_usd:+document.getElementById('e-budget').value||0,
    rate_limit_tpm:+document.getElementById('e-tpm').value||0,
    model_whitelist:document.getElementById('e-wl').value.split(',').map(s=>s.trim()).filter(Boolean),
  });
  document.getElementById('edlg').close();
}
async function patch(id,body){
  const r=await authFetch(`/v1/admin/virtual-keys/${id}`,{method:'PATCH',
    headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){const d=await r.json().catch(()=>({})); show('更新失败', JSON.stringify(d,null,2));}
  load();
}
async function del(id,name){if(!confirm(`确认删除 ${name}？（消费流水保留）`))return;
  await authFetch(`/v1/admin/virtual-keys/${id}`,{method:'DELETE'});load();}
async function usage(id,name){
  const r=await authFetch(`/v1/admin/virtual-keys/${id}/usage?days=30`);const d=await r.json();
  const rows=(d.by_model||[]).map(m=>`<tr><td>${esc(m.model)}</td><td>${m.calls}</td><td>${m.prompt_tokens}</td><td>${m.completion_tokens}</td><td>$${(+m.cost_usd).toFixed(6)}</td></tr>`).join('');
  show(`用量 — ${name}（近${d.days}天，合计 $${d.total_cost_usd.toFixed(6)}）`,
    `<table><tr><th>模型</th><th>调用</th><th>Prompt</th><th>Completion</th><th>成本</th></tr>${rows||'<tr><td colspan=5>暂无记录</td></tr>'}</table>`);
}
function show(t,b){document.getElementById('dlg-t').textContent=t;
  document.getElementById('dlg-b').innerHTML=b;document.getElementById('dlg').showModal();}
load();
</script>
</body></html>"""


@router.get("/v1/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """vk 管理看板单页（受全局 Auth 中间件保护）"""
    return HTMLResponse(content=_PAGE)
