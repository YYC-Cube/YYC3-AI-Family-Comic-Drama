#!/usr/bin/env python3
"""
YYC³ 模型服务管理器
控制模型的运行、待运行和关闭状态
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import psutil


class ModelServiceManager:
    """模型服务管理器"""

    def __init__(self):
        self.model_dir = Path.home() / "ai_models"
        self.status_file = self.model_dir / ".model_services.json"
        self.pid_file = self.model_dir / ".model_pids.json"
        self.load_status()

    def load_status(self):
        """加载状态文件"""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    self.services = json.load(f)
            except Exception:
                self.services = {}
        else:
            self.services = {}

        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    self.pids = json.load(f)
            except Exception:
                self.pids = {}
        else:
            self.pids = {}

    def save_status(self):
        """保存状态文件"""
        self.model_dir.mkdir(parents=True, exist_ok=True)

        with open(self.status_file, "w") as f:
            json.dump(self.services, f, indent=2, ensure_ascii=False)

        with open(self.pid_file, "w") as f:
            json.dump(self.pids, f, indent=2, ensure_ascii=False)

    def check_process(self, pid: int) -> bool:
        """检查进程是否存在"""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False

    def start_model(self, model_name: str, port: Optional[int] = None):
        """
        启动模型服务

        Args:
            model_name: 模型名称
            port: 服务端口
        """
        model_path = self.model_dir / model_name

        if not model_path.exists():
            print(f"❌ 模型不存在: {model_name}")
            print(f"   路径: {model_path}")
            return False

        if model_name in self.services and self.services[model_name] == "running":
            pid = self.pids.get(model_name)
            if pid and self.check_process(pid):
                print(f"⚠️  模型已在运行: {model_name} (PID: {pid})")
                return True
            else:
                # 清理无效状态
                self.services[model_name] = "stopped"
                if model_name in self.pids:
                    del self.pids[model_name]

        print(f"🚀 启动模型服务: {model_name}")
        print(f"   路径: {model_path}")

        # 检测模型类型
        model_type = self.detect_model_type(model_path)
        print(f"   类型: {model_type}")

        # 根据模型类型启动服务
        if model_type == "chat":
            success = self.start_chat_model(model_name, model_path, port)
        elif model_type == "video":
            success = self.start_video_model(model_name, model_path, port)
        elif model_type == "ollama":
            success = self.start_ollama_model(model_name)
        else:
            print(f"❌ 不支持的模型类型: {model_type}")
            return False

        if success:
            print("✅ 模型服务已启动")
        return success

    def detect_model_type(self, model_path: Path) -> str:
        """检测模型类型"""
        # 检查是否是 Ollama 模型
        if model_path.suffix == ".gguf":
            return "ollama"

        # 检查配置文件
        config_file = model_path / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                # 检查架构
                architectures = config.get("architectures", [])
                model_type = config.get("model_type", "")

                # 视频模型
                if "CogVideoX" in str(architectures) or "video" in model_type.lower():
                    return "video"

                # 对话模型
                if "ChatGLM" in str(architectures) or "chat" in model_type.lower():
                    return "chat"

                # 默认为对话模型
                return "chat"
            except Exception:
                pass

        # 检查是否有 diffusers 配置
        if (model_path / "model_index.json").exists():
            return "video"

        return "chat"

    def start_chat_model(self, model_name: str, model_path: Path, port: Optional[int]) -> bool:
        """启动对话模型服务"""
        if port is None:
            port = 8000

        # 创建启动脚本
        script = f"""#!/usr/bin/env python3
import sys
sys.path.insert(0, "{model_path}")
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("加载模型: {model_name}")
tokenizer = AutoTokenizer.from_pretrained("{model_path}", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    "{model_path}",
    trust_remote_code=True,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

if torch.cuda.is_available():
    model = model.to("cuda")
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    model = model.to("mps")

print("模型加载完成，开始服务...")
print("服务端口: {port}")

# 简单的交互式服务
while True:
    try:
        query = input("\\n用户: ")
        if query.lower() in ['exit', 'quit']:
            break

        response, history = model.chat(tokenizer, query, history=[])
        print(f"AI: {{response}}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"错误: {{e}}")
"""

        # 保存脚本
        script_file = self.model_dir / f".start_{model_name}.py"
        with open(script_file, "w") as f:
            f.write(script)

        # 启动进程
        try:
            process = subprocess.Popen(
                [sys.executable, str(script_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            # 等待一下确认启动
            time.sleep(2)

            if self.check_process(process.pid):
                self.pids[model_name] = process.pid
                self.services[model_name] = "running"
                self.save_status()
                return True
            else:
                print("❌ 模型启动失败")
                return False

        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def start_video_model(self, model_name: str, model_path: Path, port: Optional[int]) -> bool:
        """启动视频模型服务"""
        print("⚠️  视频模型服务暂不支持后台运行")
        print("   请使用脚本直接运行:")
        print("   python3 cogvideox_generator.py")
        return False

    def start_ollama_model(self, model_name: str) -> bool:
        """启动 Ollama 模型"""
        try:
            # 检查 ollama 是否运行
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)

            if result.returncode != 0:
                print("❌ Ollama 未运行，请先启动 Ollama")
                return False

            # 运行模型
            process = subprocess.Popen(
                ["ollama", "run", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )

            time.sleep(2)

            if self.check_process(process.pid):
                self.pids[model_name] = process.pid
                self.services[model_name] = "running"
                self.save_status()
                return True
            else:
                print("❌ Ollama 模型启动失败")
                return False

        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def stop_model(self, model_name: str):
        """停止模型服务"""
        if model_name not in self.services:
            print(f"❌ 模型服务不存在: {model_name}")
            return False

        if model_name not in self.pids:
            print(f"⚠️  模型PID不存在: {model_name}")
            self.services[model_name] = "stopped"
            self.save_status()
            return True

        pid = self.pids[model_name]

        try:
            if self.check_process(pid):
                process = psutil.Process(pid)
                print(f"🛑 停止模型服务: {model_name} (PID: {pid})")

                # 发送SIGTERM信号
                process.terminate()

                # 等待进程结束
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # 强制结束
                    print("   强制结束进程...")
                    process.kill()
                    process.wait()

                print("✅ 模型服务已停止")
            else:
                print(f"⚠️  进程不存在 (PID: {pid})")

            # 更新状态
            self.services[model_name] = "stopped"
            del self.pids[model_name]
            self.save_status()

            return True

        except Exception as e:
            print(f"❌ 停止失败: {e}")
            return False

    def pause_model(self, model_name: str):
        """暂停模型服务（待运行状态）"""
        if model_name not in self.services:
            print(f"❌ 模型服务不存在: {model_name}")
            return False

        if model_name not in self.pids:
            print(f"⚠️  模型PID不存在: {model_name}")
            return False

        pid = self.pids[model_name]

        try:
            if self.check_process(pid):
                process = psutil.Process(pid)
                print(f"⏸️  暂停模型服务: {model_name}")

                # 发送SIGSTOP信号
                process.suspend()

                # 更新状态
                self.services[model_name] = "paused"
                self.save_status()

                print("✅ 模型服务已暂停")
                return True
            else:
                print("⚠️  进程不存在")
                return False

        except Exception as e:
            print(f"❌ 暂停失败: {e}")
            return False

    def resume_model(self, model_name: str):
        """恢复模型服务"""
        if model_name not in self.services:
            print(f"❌ 模型服务不存在: {model_name}")
            return False

        if self.services[model_name] != "paused":
            print(f"⚠️  模型未暂停: {model_name}")
            return False

        if model_name not in self.pids:
            print(f"⚠️  模型PID不存在: {model_name}")
            return False

        pid = self.pids[model_name]

        try:
            if self.check_process(pid):
                process = psutil.Process(pid)
                print(f"▶️  恢复模型服务: {model_name}")

                # 发送SIGCONT信号
                process.resume()

                # 更新状态
                self.services[model_name] = "running"
                self.save_status()

                print("✅ 模型服务已恢复")
                return True
            else:
                print("⚠️  进程不存在")
                return False

        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False

    def get_status(self, model_name: Optional[str] = None):
        """获取模型状态"""
        if model_name:
            if model_name in self.services:
                status = self.services[model_name]
                pid = self.pids.get(model_name, "N/A")

                # 检查进程是否真实存在
                if pid != "N/A" and not self.check_process(pid):
                    status = "stopped (进程已退出)"

                print(f"{model_name}: {status} (PID: {pid})")
            else:
                print(f"{model_name}: 未配置")
        else:
            print("=== 模型服务状态 ===")
            if not self.services:
                print("  (无运行中的服务)")
            else:
                for name, status in self.services.items():
                    pid = self.pids.get(name, "N/A")

                    # 检查进程是否真实存在
                    if pid != "N/A" and not self.check_process(pid):
                        status = "stopped (进程已退出)"

                    # 状态图标
                    icon = {"running": "🟢", "paused": "⏸️", "stopped": "🔴"}.get(status, "⚪")

                    print(f"  {icon} {name}: {status} (PID: {pid})")

    def list_models(self):
        """列出所有模型"""
        print("=== 本地模型 ===")

        if not self.model_dir.exists():
            print("  (模型目录不存在)")
            return

        for model_path in self.model_dir.iterdir():
            if model_path.is_dir() and not model_path.name.startswith("."):
                name = model_path.name
                status = self.services.get(name, "stopped")
                _ = self.pids.get(name, "N/A")

                # 计算大小
                try:
                    size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
                    size_gb = size / (1024**3)
                    size_str = f"{size_gb:.2f} GB"
                except Exception:
                    size_str = "未知"

                # 状态图标
                icon = {"running": "🟢", "paused": "⏸️", "stopped": "⚪"}.get(status, "⚪")

                print(f"  {icon} {name}: {status} ({size_str})")


def main():
    """主函数"""
    manager = ModelServiceManager()

    if len(sys.argv) < 2:
        print("YYC³ 模型服务管理器")
        print("")
        print("用法: python model_service_manager.py <命令> [模型名称]")
        print("")
        print("命令:")
        print("  list              列出所有模型")
        print("  start <model>     启动模型服务")
        print("  stop <model>      停止模型服务")
        print("  pause <model>     暂停模型服务")
        print("  resume <model>    恢复模型服务")
        print("  status [model]    查看模型状态")
        print("")
        print("示例:")
        print("  python model_service_manager.py list")
        print("  python model_service_manager.py start CogAgent-9B")
        print("  python model_service_manager.py stop CogAgent-9B")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        manager.list_models()
    elif command == "start":
        if len(sys.argv) < 3:
            print("❌ 请指定模型名称")
            sys.exit(1)
        manager.start_model(sys.argv[2])
    elif command == "stop":
        if len(sys.argv) < 3:
            print("❌ 请指定模型名称")
            sys.exit(1)
        manager.stop_model(sys.argv[2])
    elif command == "pause":
        if len(sys.argv) < 3:
            print("❌ 请指定模型名称")
            sys.exit(1)
        manager.pause_model(sys.argv[2])
    elif command == "resume":
        if len(sys.argv) < 3:
            print("❌ 请指定模型名称")
            sys.exit(1)
        manager.resume_model(sys.argv[2])
    elif command == "status":
        model = sys.argv[2] if len(sys.argv) > 2 else None
        manager.get_status(model)
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
