#!/bin/bash

# YYC³ 模型管理器
# 统一管理本地和NFS共享模型

set -e

# 配置
MODEL_DIR=~/ai_models
NFS_MOUNT=~/nfs_vpn_mount
CACHE_DIR=~/.cache/model_cache
STATUS_FILE="$MODEL_DIR/.model_status.json"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 初始化
init() {
    mkdir -p "$MODEL_DIR"
    mkdir -p "$CACHE_DIR"
    
    if [ ! -f "$STATUS_FILE" ]; then
        echo '{}' > "$STATUS_FILE"
    fi
}

# 获取模型状态
get_status() {
    local model=$1
    python3 -c "import json; data=json.load(open('$STATUS_FILE')); print(data.get('$model', 'closed'))" 2>/dev/null || echo "closed"
}

# 设置模型状态
set_status() {
    local model=$1
    local status=$2
    python3 -c "
import json
try:
    data = json.load(open('$STATUS_FILE'))
except:
    data = {}
data['$model'] = '$status'
json.dump(data, open('$STATUS_FILE', 'w'), indent=2)
" 2>/dev/null
}

# 检查NFS挂载
check_nfs() {
    if mount | grep -q "nfs_vpn_mount"; then
        return 0
    else
        return 1
    fi
}

# 挂载NFS
mount_nfs() {
    echo -e "${YELLOW}挂载NFS共享...${NC}"
    
    if check_nfs; then
        echo -e "${GREEN}✓ NFS已挂载${NC}"
        return 0
    fi
    
    mkdir -p "$NFS_MOUNT"
    
    # 尝试挂载
    if sudo mount -t nfs 192.168.3.45:/Volume2/yyc3-33 "$NFS_MOUNT" 2>/dev/null; then
        echo -e "${GREEN}✓ NFS挂载成功${NC}"
        return 0
    else
        echo -e "${RED}✗ NFS挂载失败${NC}"
        echo "  请检查:"
        echo "  1. NAS服务器是否运行 (ping 192.168.3.45)"
        echo "  2. NFS服务是否启动"
        echo "  3. 网络连接是否正常"
        return 1
    fi
}

# 卸载NFS
unmount_nfs() {
    echo -e "${YELLOW}卸载NFS共享...${NC}"
    
    if ! check_nfs; then
        echo -e "${GREEN}✓ NFS未挂载${NC}"
        return 0
    fi
    
    if sudo umount "$NFS_MOUNT" 2>/dev/null; then
        echo -e "${GREEN}✓ NFS已卸载${NC}"
        return 0
    else
        echo -e "${RED}✗ NFS卸载失败${NC}"
        echo "  可能有进程正在使用NFS"
        return 1
    fi
}

# 列出模型
list_models() {
    echo -e "${GREEN}=== 本地模型 ===${NC}"
    
    local count=0
    for model_path in "$MODEL_DIR"/*/; do
        if [ -d "$model_path" ] && [ ! "$(basename "$model_path")" == "." ]; then
            local name=$(basename "$model_path")
            local status=$(get_status "$name")
            local size=$(du -sh "$model_path" 2>/dev/null | cut -f1)
            
            # 状态图标
            case $status in
                running) icon="🟢" ;;
                ready) icon="🟡" ;;
                paused) icon="⏸️" ;;
                archived) icon="📦" ;;
                *) icon="⚪" ;;
            esac
            
            echo "  $icon $name ($size) - $status"
            ((count++))
        fi
    done
    
    if [ $count -eq 0 ]; then
        echo "  (无本地模型)"
    fi
    
    # NFS模型
    if check_nfs && [ -d "$NFS_MOUNT/models" ]; then
        echo ""
        echo -e "${BLUE}=== NFS共享模型 ===${NC}"
        
        local nfs_count=0
        for model_path in "$NFS_MOUNT/models"/*/; do
            if [ -d "$model_path" ]; then
                local name=$(basename "$model_path")
                local size=$(du -sh "$model_path" 2>/dev/null | cut -f1)
                echo "  📦 $name ($size) - nfs"
                ((nfs_count++))
            fi
        done
        
        if [ $nfs_count -eq 0 ]; then
            echo "  (无NFS模型)"
        fi
    fi
    
    # Ollama模型
    if command -v ollama &> /dev/null; then
        echo ""
        echo -e "${YELLOW}=== Ollama模型 ===${NC}"
        ollama list 2>/dev/null | tail -n +2 | while read line; do
            echo "  🤖 $line"
        done
    fi
}

# 加载模型
load_model() {
    local model=$1
    
    if [ -z "$model" ]; then
        echo -e "${RED}错误: 请指定模型名称${NC}"
        return 1
    fi
    
    local model_path="$MODEL_DIR/$model"
    
    # 检查本地模型
    if [ ! -d "$model_path" ]; then
        # 检查NFS模型
        if check_nfs && [ -d "$NFS_MOUNT/models/$model" ]; then
            model_path="$NFS_MOUNT/models/$model"
            echo -e "${YELLOW}从NFS加载模型: $model${NC}"
        else
            echo -e "${RED}错误: 模型不存在: $model${NC}"
            return 1
        fi
    fi
    
    echo -e "${YELLOW}加载模型: $model${NC}"
    echo "  路径: $model_path"
    
    # 创建缓存
    mkdir -p "$CACHE_DIR"
    ln -sf "$model_path" "$CACHE_DIR/$model" 2>/dev/null || true
    
    # 更新状态
    set_status "$model" "ready"
    
    local size=$(du -sh "$model_path" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✓ 模型已就绪: $model ($size)${NC}"
}

# 卸载模型
unload_model() {
    local model=$1
    
    if [ -z "$model" ]; then
        echo -e "${RED}错误: 请指定模型名称${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}卸载模型: $model${NC}"
    
    # 删除缓存
    rm -rf "$CACHE_DIR/$model" 2>/dev/null || true
    
    # 更新状态
    set_status "$model" "closed"
    
    # 清理内存
    python3 -c "import gc; gc.collect()" 2>/dev/null || true
    
    echo -e "${GREEN}✓ 模型已卸载: $model${NC}"
}

# 归档模型到NFS
archive_model() {
    local model=$1
    
    if [ -z "$model" ]; then
        echo -e "${RED}错误: 请指定模型名称${NC}"
        return 1
    fi
    
    local model_path="$MODEL_DIR/$model"
    
    if [ ! -d "$model_path" ]; then
        echo -e "${RED}错误: 模型不存在: $model${NC}"
        return 1
    fi
    
    # 挂载NFS
    if ! check_nfs; then
        if ! mount_nfs; then
            return 1
        fi
    fi
    
    local archive_path="$NFS_MOUNT/models/archive/$model"
    
    echo -e "${YELLOW}归档模型到NFS: $model${NC}"
    
    # 创建归档目录
    mkdir -p "$NFS_MOUNT/models/archive"
    
    # 移动模型
    mv "$model_path" "$archive_path"
    
    # 创建符号链接
    ln -sf "$archive_path" "$model_path"
    
    # 更新状态
    set_status "$model" "archived"
    
    echo -e "${GREEN}✓ 模型已归档: $model${NC}"
    echo "  归档位置: $archive_path"
    echo "  本地链接: $model_path -> $archive_path"
}

# 从NFS恢复模型
restore_model() {
    local model=$1
    
    if [ -z "$model" ]; then
        echo -e "${RED}错误: 请指定模型名称${NC}"
        return 1
    fi
    
    # 挂载NFS
    if ! check_nfs; then
        if ! mount_nfs; then
            return 1
        fi
    fi
    
    local archive_path="$NFS_MOUNT/models/archive/$model"
    local model_path="$MODEL_DIR/$model"
    
    if [ ! -d "$archive_path" ]; then
        echo -e "${RED}错误: 归档模型不存在: $model${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}从NFS恢复模型: $model${NC}"
    
    # 删除符号链接
    rm -f "$model_path"
    
    # 移动模型
    mv "$archive_path" "$model_path"
    
    # 更新状态
    set_status "$model" "closed"
    
    echo -e "${GREEN}✓ 模型已恢复: $model${NC}"
}

# 查看模型详情
show_info() {
    local model=$1
    
    if [ -z "$model" ]; then
        echo -e "${RED}错误: 请指定模型名称${NC}"
        return 1
    fi
    
    local model_path="$MODEL_DIR/$model"
    local is_nfs=false
    
    if [ ! -d "$model_path" ]; then
        if check_nfs && [ -d "$NFS_MOUNT/models/$model" ]; then
            model_path="$NFS_MOUNT/models/$model"
            is_nfs=true
        else
            echo -e "${RED}错误: 模型不存在: $model${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}=== 模型信息: $model ===${NC}"
    echo ""
    
    local status=$(get_status "$model")
    local size=$(du -sh "$model_path" 2>/dev/null | cut -f1)
    local files=$(find "$model_path" -type f | wc -l)
    
    echo "  名称: $model"
    echo "  状态: $status"
    echo "  大小: $size"
    echo "  文件数: $files"
    echo "  路径: $model_path"
    echo "  存储: $([ "$is_nfs" = true ] && echo "NFS" || echo "本地")"
    
    # 检查配置文件
    if [ -f "$model_path/config.json" ]; then
        echo ""
        echo "  配置信息:"
        python3 -c "
import json
try:
    config = json.load(open('$model_path/config.json'))
    for key in ['model_type', 'architectures', 'hidden_size', 'num_layers']:
        if key in config:
            print(f'    {key}: {config[key]}')
except:
    pass
" 2>/dev/null
    fi
}

# 显示帮助
show_help() {
    echo "YYC³ 模型管理器"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  list                    列出所有模型"
    echo "  load <model>            加载模型到缓存"
    echo "  unload <model>          卸载模型"
    echo "  archive <model>         归档模型到NFS"
    echo "  restore <model>         从NFS恢复模型"
    echo "  info <model>            查看模型详情"
    echo "  mount-nfs               挂载NFS共享"
    echo "  unmount-nfs             卸载NFS共享"
    echo "  status [model]          查看模型状态"
    echo "  help                    显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 list"
    echo "  $0 load CogAgent-9B"
    echo "  $0 archive CogVideoX-5B"
    echo "  $0 restore CogVideoX-5B"
}

# 主函数
main() {
    init
    
    case "${1:-}" in
        list)
            list_models
            ;;
        load)
            load_model "$2"
            ;;
        unload)
            unload_model "$2"
            ;;
        archive)
            archive_model "$2"
            ;;
        restore)
            restore_model "$2"
            ;;
        info)
            show_info "$2"
            ;;
        mount-nfs)
            mount_nfs
            ;;
        unmount-nfs)
            unmount_nfs
            ;;
        status)
            if [ -n "$2" ]; then
                echo "$2: $(get_status "$2")"
            else
                echo "=== 模型状态 ==="
                for model_path in "$MODEL_DIR"/*/; do
                    if [ -d "$model_path" ]; then
                        name=$(basename "$model_path")
                        status=$(get_status "$name")
                        echo "  $name: $status"
                    fi
                done
            fi
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

main "$@"
