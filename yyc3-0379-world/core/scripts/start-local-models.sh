#!/bin/bash

# YYC³ 本地AI模型快速启动工具
# 快速启动 CogAgent-9B 和 CogVideoX-5B

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 模型路径
COGAGENT_PATH=~/ai_models/Cogagent-9B
COGVIDEOX_PATH=~/ai_models/Cogvideox-5B

echo "========================================"
echo "YYC³ 本地AI模型快速启动工具"
echo "========================================"
echo ""

# 检查模型
check_models() {
    echo -e "${BLUE}[检查模型]${NC}"
    echo ""
    
    # 检查 CogAgent-9B
    if [ -d "$COGAGENT_PATH" ]; then
        SIZE=$(du -sh "$COGAGENT_PATH" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✓ CogAgent-9B${NC} ($SIZE)"
        COGAGENT_OK=true
    else
        echo -e "${RED}✗ CogAgent-9B 未找到${NC}"
        COGAGENT_OK=false
    fi
    
    # 检查 CogVideoX-5B
    if [ -d "$COGVIDEOX_PATH" ]; then
        SIZE=$(du -sh "$COGVIDEOX_PATH" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✓ CogVideoX-5B${NC} ($SIZE)"
        COGVIDEOX_OK=true
    else
        echo -e "${RED}✗ CogVideoX-5B 未找到${NC}"
        COGVIDEOX_OK=false
    fi
    
    echo ""
}

# 检查环境
check_environment() {
    echo -e "${BLUE}[检查环境]${NC}"
    echo ""
    
    # 检查 Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}✗ Python 未安装${NC}"
        exit 1
    fi
    
    # 检查 PyTorch
    if python3 -c "import torch" 2>/dev/null; then
        TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)")
        echo -e "${GREEN}✓ PyTorch $TORCH_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ PyTorch 未安装${NC}"
    fi
    
    # 检查 Transformers
    if python3 -c "import transformers" 2>/dev/null; then
        TF_VERSION=$(python3 -c "import transformers; print(transformers.__version__)")
        echo -e "${GREEN}✓ Transformers $TF_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ Transformers 未安装${NC}"
    fi
    
    # 检查 Diffusers
    if python3 -c "import diffusers" 2>/dev/null; then
        DF_VERSION=$(python3 -c "import diffusers; print(diffusers.__version__)")
        echo -e "${GREEN}✓ Diffusers $DF_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠ Diffusers 未安装${NC}"
    fi
    
    echo ""
}

# 显示菜单
show_menu() {
    echo -e "${CYAN}请选择要使用的模型:${NC}"
    echo ""
    echo "  1) CogAgent-9B  - 多模态对话模型"
    echo "  2) CogVideoX-5B - 视频生成模型"
    echo "  3) 查看模型信息"
    echo "  4) 安装依赖"
    echo "  5) 退出"
    echo ""
}

# 启动 CogAgent-9B
start_cogagent() {
    if [ "$COGAGENT_OK" = false ]; then
        echo -e "${RED}错误: CogAgent-9B 模型未找到${NC}"
        echo "请先下载模型到: $COGAGENT_PATH"
        return
    fi
    
    echo -e "${GREEN}启动 CogAgent-9B...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    python3 cogagent_chat.py
}

# 启动 CogVideoX-5B
start_cogvideox() {
    if [ "$COGVIDEOX_OK" = false ]; then
        echo -e "${RED}错误: CogVideoX-5B 模型未找到${NC}"
        echo "请先下载模型到: $COGVIDEOX_PATH"
        return
    fi
    
    echo -e "${GREEN}启动 CogVideoX-5B...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    python3 cogvideox_generator.py
}

# 显示模型信息
show_info() {
    echo -e "${CYAN}=== 模型信息 ===${NC}"
    echo ""
    
    if [ "$COGAGENT_OK" = true ]; then
        echo -e "${PURPLE}CogAgent-9B${NC}"
        echo "  路径: $COGAGENT_PATH"
        echo "  大小: $(du -sh "$COGAGENT_PATH" 2>/dev/null | cut -f1)"
        echo "  类型: 多模态对话模型"
        echo "  参数: 9B"
        echo ""
    fi
    
    if [ "$COGVIDEOX_OK" = true ]; then
        echo -e "${PURPLE}CogVideoX-5B${NC}"
        echo "  路径: $COGVIDEOX_PATH"
        echo "  大小: $(du -sh "$COGVIDEOX_PATH" 2>/dev/null | cut -f1)"
        echo "  类型: 视频生成模型"
        echo "  参数: 5B"
        echo ""
    fi
}

# 安装依赖
install_dependencies() {
    echo -e "${YELLOW}安装依赖包...${NC}"
    echo ""
    
    # 安装 PyTorch
    echo "安装 PyTorch..."
    pip3 install torch torchvision torchaudio
    
    # 安装 Transformers
    echo "安装 Transformers..."
    pip3 install transformers accelerate sentencepiece
    
    # 安装 Diffusers
    echo "安装 Diffusers..."
    pip3 install diffusers opencv-python pillow imageio imageio-ffmpeg
    
    echo ""
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
}

# 主循环
main() {
    check_models
    check_environment
    
    while true; do
        show_menu
        read -p "请选择 (1-5): " choice
        echo ""
        
        case $choice in
            1)
                start_cogagent
                ;;
            2)
                start_cogvideox
                ;;
            3)
                show_info
                ;;
            4)
                install_dependencies
                ;;
            5)
                echo -e "${GREEN}再见！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择，请重试${NC}"
                echo ""
                ;;
        esac
    done
}

main
