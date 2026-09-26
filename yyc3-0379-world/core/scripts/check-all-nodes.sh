#!/bin/bash

# YYC³ 多端状态检查脚本
# 用于检查各端的实际运行状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 节点配置（使用简单变量）
NODE_22="yyc3-22"
NODE_33="yyc3-33"
NODE_45="yyc3-45"
NODE_77="yyc3-77"

echo "========================================"
echo "YYC³ 多端状态检查"
echo "========================================"
echo ""

# 检查 SSH 配置
check_ssh_config() {
    echo -e "${BLUE}[1] 检查 SSH 配置${NC}"
    echo "----------------------------------------"
    
    if [ -f ~/.ssh/config ]; then
        echo -e "${GREEN}✓ SSH 配置文件存在${NC}"
        
        for node in "${!NODES[@]}"; do
            if grep -q "Host $node" ~/.ssh/config; then
                echo -e "${GREEN}  ✓ $node 配置存在${NC}"
            else
                echo -e "${YELLOW}  ⚠ $node 配置不存在${NC}"
            fi
        done
    else
        echo -e "${RED}✗ SSH 配置文件不存在${NC}"
        return 1
    fi
    echo ""
}

# 检查节点连通性
check_node_connectivity() {
    echo -e "${BLUE}[2] 检查节点连通性${NC}"
    echo "----------------------------------------"
    
    for node in "${!NODES[@]}"; do
        echo -n "  检查 $node ... "
        
        if ssh -o ConnectTimeout=5 -o BatchMode=yes $node exit 2>/dev/null; then
            echo -e "${GREEN}✓ 连接成功${NC}"
        else
            echo -e "${RED}✗ 连接失败${NC}"
        fi
    done
    echo ""
}

# 检查服务状态
check_services() {
    local node=$1
    local services=$2
    
    echo -e "${BLUE}[$node] 检查服务状态${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        for service in $services; do
            if systemctl is-active --quiet \$service 2>/dev/null; then
                echo -e "  \${GREEN}✓ \$service 运行中\${NC}"
            elif docker ps --format '{{.Names}}' | grep -q \$service 2>/dev/null; then
                echo -e "  \${GREEN}✓ \$service (Docker) 运行中\${NC}"
            else
                echo -e "  \${RED}✗ \$service 未运行\${NC}"
            fi
        done
EOF
    echo ""
}

# 检查数据库状态
check_database() {
    local node=$1
    local db_type=$2
    
    echo -e "${BLUE}[$node] 检查 $db_type 数据库${NC}"
    echo "----------------------------------------"
    
    case $db_type in
        "postgresql")
            ssh $node "bash -s" <<EOF
                if command -v psql &> /dev/null; then
                    version=\$(psql --version | head -n1)
                    echo -e "  \${GREEN}✓ PostgreSQL 已安装: \$version\${NC}"
                    
                    if pg_isready &> /dev/null; then
                        echo -e "  \${GREEN}✓ PostgreSQL 服务运行中\${NC}"
                        
                        # 检查数据库列表
                        databases=\$(psql -U postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false;" 2>/dev/null | xargs)
                        if [ -n "\$databases" ]; then
                            echo -e "  \${GREEN}✓ 数据库: \$databases\${NC}"
                        fi
                    else
                        echo -e "  \${RED}✗ PostgreSQL 服务未运行\${NC}"
                    fi
                else
                    echo -e "  \${RED}✗ PostgreSQL 未安装\${NC}"
                fi
EOF
            ;;
        "redis")
            ssh $node "bash -s" <<EOF
                if command -v redis-cli &> /dev/null; then
                    version=\$(redis-cli --version | head -n1)
                    echo -e "  \${GREEN}✓ Redis 已安装: \$version\${NC}"
                    
                    if redis-cli ping &> /dev/null; then
                        echo -e "  \${GREEN}✓ Redis 服务运行中\${NC}"
                        
                        # 检查 Redis 信息
                        info=\$(redis-cli INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
                        echo -e "  \${GREEN}✓ Redis 版本: \$info\${NC}"
                    else
                        echo -e "  \${RED}✗ Redis 服务未运行\${NC}"
                    fi
                else
                    echo -e "  \${RED}✗ Redis 未安装\${NC}"
                fi
EOF
            ;;
    esac
    echo ""
}

# 检查 Docker 容器
check_docker() {
    local node=$1
    
    echo -e "${BLUE}[$node] 检查 Docker 容器${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        if command -v docker &> /dev/null; then
            echo -e "  \${GREEN}✓ Docker 已安装\${NC}"
            
            containers=\$(docker ps --format '{{.Names}} ({{.Status}})' 2>/dev/null)
            if [ -n "\$containers" ]; then
                echo -e "  \${GREEN}✓ 运行中的容器:\${NC}"
                echo "\$containers" | while read container; do
                    echo -e "    - \$container"
                done
            else
                echo -e "  \${YELLOW}⚠ 没有运行中的容器\${NC}"
            fi
        else
            echo -e "  \${RED}✗ Docker 未安装\${NC}"
        fi
EOF
    echo ""
}

# 检查系统资源
check_system_resources() {
    local node=$1
    
    echo -e "${BLUE}[$node] 检查系统资源${NC}"
    echo "----------------------------------------"
    
    ssh $node "bash -s" <<EOF
        # CPU 使用率
        cpu_usage=\$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - \$1}')
        echo -e "  CPU 使用率: \${cpu_usage}%"
        
        # 内存使用
        mem_info=\$(free -m | awk 'NR==2{printf "%.2f%% (%.2fGB/%.2fGB)", \$3*100/\$2, \$3/1024, \$2/1024}')
        echo -e "  内存使用: \${mem_info}"
        
        # 磁盘使用
        disk_info=\$(df -h / | awk 'NR==2{printf "%s (%s/%s)", \$5, \$3, \$2}')
        echo -e "  磁盘使用: \${disk_info}"
        
        # 系统负载
        load_avg=\$(uptime | awk -F'load average:' '{print \$2}')
        echo -e "  系统负载: \${load_avg}"
EOF
    echo ""
}

# 主检查流程
main() {
    echo -e "${GREEN}开始检查各端状态...${NC}"
    echo ""
    
    # 1. 检查 SSH 配置
    check_ssh_config
    
    # 2. 检查节点连通性
    check_node_connectivity
    
    # 3. 检查各端服务
    echo -e "${BLUE}[3] 检查各端服务${NC}"
    echo "========================================"
    echo ""
    
    # yyc3-22 (MacBook)
    echo -e "${YELLOW}>>> yyc3-22 (MacBook Pro M4 Max)${NC}"
    check_database yyc3-22 postgresql
    check_database yyc3-22 redis
    check_docker yyc3-22
    check_system_resources yyc3-22
    
    # yyc3-33 (ECS)
    echo -e "${YELLOW}>>> yyc3-33 (阿里云 ECS)${NC}"
    check_services yyc3-33 "nginx docker frps"
    check_docker yyc3-33
    check_system_resources yyc3-33
    
    # yyc3-45 (NAS)
    echo -e "${YELLOW}>>> yyc3-45 (NAS F4-423)${NC}"
    check_database yyc3-45 postgresql
    check_services yyc3-45 "docker frpc nfs-server"
    check_docker yyc3-45
    check_system_resources yyc3-45
    
    # yyc3-77 (iMac)
    echo -e "${YELLOW}>>> yyc3-77 (iMac M4)${NC}"
    check_database yyc3-77 postgresql
    check_docker yyc3-77
    check_system_resources yyc3-77
    
    echo "========================================"
    echo -e "${GREEN}✅ 检查完成${NC}"
    echo "========================================"
}

# 执行主函数
main
