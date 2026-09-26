# ==============================================================
# run_gateway_local.py — 0379-World 网关本地启动器（G1 E2E 用）
# 背景：core/api 以 `app.*` 绝对导入风格编写（上游部署形态），本地以
#       importlib 别名方式将 core/api 装载为 `app` 包，免改上游代码。
# 运行：cd <repo-root> && yyc3-0379-world/.venv/bin/python scripts/run_gateway_local.py
# 端口：GATEWAY_PORT（默认 25080，对齐 25xxx 后端红线与 G1 验收记录）
# ==============================================================
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORLD = REPO / "yyc3-0379-world"
CORE_API = WORLD / "core" / "api"

# .env 相对 cwd 解析（pydantic-settings env_file=".env"），必须先切到网关仓根
os.chdir(WORLD)
sys.path.insert(0, str(WORLD))

spec = importlib.util.spec_from_file_location(
    "app", CORE_API / "__init__.py", submodule_search_locations=[str(CORE_API)]
)
app_pkg = importlib.util.module_from_spec(spec)
sys.modules["app"] = app_pkg
spec.loader.exec_module(app_pkg)

from app.main import app as fastapi_app  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("GATEWAY_PORT", "25080"))
    print(f"[launcher] 0379-World 网关本地启动：http://127.0.0.1:{port}（G1 E2E）")
    uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_level="info")
