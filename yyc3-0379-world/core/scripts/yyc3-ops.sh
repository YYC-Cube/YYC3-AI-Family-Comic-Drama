#!/bin/bash

# YYC³ 快速运维脚本
# 用于快速执行常见的运维操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 显示帮助信息
show_help() {
    echo "YYC³ 快速运维脚本"
    echo ""
    echo "用法: $0 [命令] [节点] [选项]"
    echo ""
    echo "节点:"
    echo "  yyc3-22    MacBook Pro M4 Max (主开发机)"
    echo "  yyc3-33    阿里云 ECS (生产服务器)"
    echo "  yyc3-45    NAS F4-423 (存储服务)"
    echo "  yyc3-77    iMac M4 (副开发机)"
    echo "  all        所有节点"
    echo ""
    echo "命令:"
    echo "  status     检查节点状态"
    echo "  services   检查服务状态"
    echo "  docker     检查 Docker 容器"
    echo "  logs       查看服务日志"
    echo "  restart    重启服务"
    echo "  update     更新系统"
    echo "  backup     备份数据"
    echo "  shell      SSH 连接到节点"
    echo ""
    echo "示例:"
    echo "  $0 status yyc3-33          # 检查 ECS 状态"
    echo "  $0 docker all              # 检查所有节点的 Docker"
    echo "  $0 logs yyc3-33 nginx      # 查看 ECS 的 nginx 日志"
    echo "  $0 shell yyc3-45           # SSH 连接到 NAS"
    echo ""
}

# 检查节点状态
check_status() {
    local node=$1
    
    echo -e "${BLUE}检查 $node 状态...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        echo "主机名: \$(hostname)"
        echo "系统: \$(uname -s) \$(uname -r)"
        echo "架构: \$(uname -m)"
        echo ""
        
        echo "CPU 信息:"
        if command -v lscpu &> /dev/null; then
            lscpu | grep -E "^Model name|^CPU\(s\)|^Thread|^Core"
        else
            sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "无法获取 CPU 信息"
        fi
        echo ""
        
        echo "内存信息:"
        free -h 2>/dev/null || vm_stat | perl -ne '/page size of (\d+)/ and \$ps=\$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f MB\n", "\$1:", \$2 * \$ps / 1048576);'
        echo ""
        
        echo "磁盘信息:"
        df -h / 2>/dev/null || df -h
        echo ""
        
        echo "系统负载:"
        uptime
        echo ""
        
        echo "网络信息:"
        ip addr show 2>/dev/null | grep -E "inet " | grep -v "127.0.0.1" || ifconfig | grep "inet " | grep -v "127.0.0.1"
EOF
}

# 检查服务状态
check_services() {
    local node=$1
    
    echo -e "${BLUE}检查 $node 服务状态...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        echo "Systemd 服务:"
        systemctl list-units --type=service --state=running --no-pager | grep -E "postgresql|redis|nginx|docker|frp" || echo "  无相关服务"
        echo ""
        
        echo "Docker 容器:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Docker 未运行或未安装"
EOF
}

# 检查 Docker
check_docker() {
    local node=$1
    
    echo -e "${BLUE}检查 $node Docker 状态...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        if ! command -v docker &> /dev/null; then
            echo -e "\${RED}✗ Docker 未安装\${NC}"
            exit 1
        fi
        
        echo "Docker 版本:"
        docker --version
        echo ""
        
        echo "Docker Compose 版本:"
        docker-compose --version 2>/dev/null || docker compose version
        echo ""
        
        echo "运行中的容器:"
        docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "容器资源使用:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
EOF
}

# 查看日志
view_logs() {
    local node=$1
    local service=$2
    
    echo -e "${BLUE}查看 $node 的 $service 日志...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        # 检查是否是 Docker 容器
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            echo "Docker 容器日志:"
            docker logs --tail 100 $service
        elif systemctl is-active --quiet $service 2>/dev/null; then
            echo "Systemd 服务日志:"
            journalctl -u $service -n 100 --no-pager
        else
            echo -e "\${RED}✗ 服务 $service 未找到\${NC}"
        fi
EOF
}

# 重启服务
restart_service() {
    local node=$1
    local service=$2
    
    echo -e "${YELLOW}重启 $node 的 $service...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        # 检查是否是 Docker 容器
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            echo "重启 Docker 容器: $service"
            docker restart $service
            echo -e "\${GREEN}✓ Docker 容器已重启\${NC}"
        elif systemctl is-active --quiet $service 2>/dev/null; then
            echo "重启 Systemd 服务: $service"
            sudo systemctl restart $service
            echo -e "\${GREEN}✓ Systemd 服务已重启\${NC}"
        else
            echo -e "\${RED}✗ 服务 $service 未找到\${NC}"
        fi
EOF
}

# 更新系统
update_system() {
    local node=$1
    
    echo -e "${YELLOW}更新 $node 系统...${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        if command -v apt-get &> /dev/null; then
            echo "Ubuntu/Debian 系统"
            sudo apt-get update
            sudo apt-get upgrade -y
        elif command -v yum &> /dev/null; then
            echo "CentOS/RHEL 系统"
            sudo yum update -y
        elif command -v brew &> /dev/null; then
            echo "macOS 系统"
            brew update
            brew upgrade
        else
            echo -e "\${RED}✗ 不支持的系统\${NC}"
        fi
EOF
}

# 备份数据
backup_data() {
    local node=$1
    
    echo -e "${YELLOW}备份 $node 数据...${NC}"
    echo "----------------------------------------"
    
    local backup_dir="/tmp/yyc3-backup-$(date +%Y%m%d_%H%M%S)"
    
    ssh $node "bash -s" <<EOF
        mkdir -p $backup_dir
        echo "备份目录: $backup_dir"
        
        # 备份数据库
        if command -v pg_dump &> /dev/null; then
            echo "备份 PostgreSQL 数据库..."
            pg_dump -U postgres yyc3_gpt > $backup_dir/yyc3_gpt.sql 2>/dev/null || echo "  数据库备份失败"
        fi
        
        # 备份 Redis
        if command -v redis-cli &> /dev/null; then
            echo "备份 Redis 数据..."
            redis-cli BGSAVE
            sleep 2
            cp /var/lib/redis/dump.rdb $backup_dir/redis_dump.rdb 2>/dev/null || echo "  Redis 备份失败"
        fi
        
        # 备份配置文件
        echo "备份配置文件..."
        cp -r ~/.env $backup_dir/ 2>/dev/null || true
        cp -r ~/docker-compose.yml $backup_dir/ 2>/dev/null || true
        
        # 打包备份
        tar -czf $backup_dir.tar.gz -C $(dirname $backup_dir) $(basename $backup_dir)
        echo -e "\${GREEN}✓ 备份完成: $backup_dir.tar.gz\${NC}"
EOF
}

# SSH 连接
connect_shell() {
    local node=$1
    
    echo -e "${BLUE}连接到 $node...${NC}"
    echo "----------------------------------------"
    
    ssh $node
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    local command=$1
    local node=$2
    local option=$3
    
    # 验证节点
    if [ "$node" != "all" ] && [ -n "$node" ]; then
        if ! grep -q "Host $node" ~/.ssh/config 2>/dev/null; then
            echo -e "${RED}错误: 节点 $node 未在 SSH 配置中找到${NC}"
            exit 1
        fi
    fi
    
    # 执行命令
    case $command in
        status)
            if [ "$node" = "all" ]; then
                for n in yyc3-22 yyc3-33 yyc3-45 yyc3-77; do
                    check_status $n
                    echo ""
                done
            else
                check_status $node
            fi
            ;;
        services)
            if [ "$node" = "all" ]; then
                for n in yyc3-22 yyc3-33 yyc3-45 yyc3-77; do
                    check_services $n
                    echo ""
                done
            else
                check_services $node
            fi
            ;;
        docker)
            if [ "$node" = "all" ]; then
                for n in yyc3-22 yyc3-33 yyc3-45 yyc3-77; do
                    check_docker $n
                    echo ""
                done
            else
                check_docker $node
            fi
            ;;
        logs)
            if [ -z "$option" ]; then
                echo -e "${RED}错误: 请指定服务名称${NC}"
                echo "用法: $0 logs $node <service>"
                exit 1
            fi
            view_logs $node $option
            ;;
        restart)
            if [ -z "$option" ]; then
                echo -e "${RED}错误: 请指定服务名称${NC}"
                echo "用法: $0 restart $node <service>"
                exit 1
            fi
            restart_service $node $option
            ;;
        update)
            if [ "$node" = "all" ]; then
                for n in yyc3-22 yyc3-33 yyc3-45 yyc3-77; do
                    update_system $n
                    echo ""
                done
            else
                update_system $node
            fi
            ;;
        backup)
            if [ "$node" = "all" ]; then
                for n in yyc3-22 yyc3-33 yyc3-45 yyc3-77; do
                    backup_data $n
                    echo ""
                done
            else
                backup_data $node
            fi
            ;;
        shell)
            connect_shell $node
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令 '$command'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
