#!/bin/bash
# SonjayOS VMware 开发模式启动脚本
# 用于在VMware虚拟机中启动SonjayOS开发模式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[VMWARE-DEV-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[VMWARE-DEV-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[VMWARE-DEV-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[VMWARE-DEV-ERROR]${NC} $1"
}

# 检查开发环境
check_dev_environment() {
    log_info "检查开发环境..."
    
    # 检查项目目录
    if [ ! -d "$HOME/sonjayos" ]; then
        log_error "项目目录不存在，请先运行 vmware-dev-setup.sh 设置环境"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$HOME/sonjayos/venv" ]; then
        log_error "虚拟环境不存在，请先运行 vmware-dev-setup.sh 设置环境"
        exit 1
    fi
    
    # 检查脚本权限
    if [ ! -x "$HOME/sonjayos/scripts/dev-mode.sh" ]; then
        log_error "脚本权限不足，请检查权限设置"
        exit 1
    fi
    
    log_success "开发环境检查通过"
}

# 优化虚拟机性能
optimize_vmware_performance() {
    log_info "优化VMware虚拟机性能..."
    
    # 设置CPU调度器
    if [ -w "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" ]; then
        echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true
        log_info "CPU调度器已设置为performance模式"
    fi
    
    # 优化内存管理
    echo 1 > /proc/sys/vm/swappiness
    echo 15 > /proc/sys/vm/dirty_ratio
    echo 5 > /proc/sys/vm/dirty_background_ratio
    log_info "内存管理已优化"
    
    # 优化网络
    if ! grep -q "net.core.rmem_max" /etc/sysctl.conf; then
        echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
        echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf
        echo 'net.ipv4.tcp_rmem = 4096 87380 16777216' >> /etc/sysctl.conf
        echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' >> /etc/sysctl.conf
        sysctl -p
        log_info "网络性能已优化"
    fi
    
    log_success "VMware虚拟机性能优化完成"
}

# 设置开发环境变量
setup_dev_environment() {
    log_info "设置开发环境变量..."
    
    # 设置环境变量
    export SONJAYOS_DEV_MODE=true
    export SONJAYOS_DEBUG_LEVEL=DEBUG
    export SONJAYOS_HOT_RELOAD=true
    export SONJAYOS_MOCK_AI=true
    export SONJAYOS_PROFILING=true
    export SONJAYOS_VMWARE_MODE=true
    
    # 设置项目路径
    export PATH="$HOME/sonjayos/scripts:$PATH"
    export PYTHONPATH="$HOME/sonjayos/src:$PYTHONPATH"
    
    log_success "开发环境变量设置完成"
}

# 启动开发服务
start_dev_services() {
    log_info "启动SonjayOS开发服务..."
    
    cd $HOME/sonjayos
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 启动开发模式
    ./scripts/dev-mode.sh start
    
    if [ $? -eq 0 ]; then
        log_success "开发服务启动成功"
    else
        log_error "开发服务启动失败"
        exit 1
    fi
}

# 显示服务状态
show_service_status() {
    log_info "显示服务状态..."
    
    cd $HOME/sonjayos
    
    # 显示开发状态
    ./scripts/dev-mode.sh status
    
    # 显示系统资源
    echo ""
    echo "系统资源使用情况:"
    echo "- CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "- 内存使用率: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    echo "- 磁盘使用率: $(df -h / | awk 'NR==2{print $5}')"
    
    # 显示网络端口
    echo ""
    echo "网络端口状态:"
    netstat -tlnp | grep -E ":(8000|8001|8002)" | awk '{print "- 端口 " $4 ": " $6}' || echo "- 无相关端口监听"
    
    # 显示进程信息
    echo ""
    echo "相关进程:"
    ps aux | grep -E "(python.*sonjayos|watchdog)" | grep -v grep | awk '{print "- " $2 ": " $11 " " $12 " " $13}' || echo "- 无相关进程"
}

# 启动开发环境
start_dev_environment() {
    log_info "启动SonjayOS VMware开发环境..."
    
    # 检查开发环境
    check_dev_environment
    
    # 优化虚拟机性能
    optimize_vmware_performance
    
    # 设置开发环境变量
    setup_dev_environment
    
    # 启动开发服务
    start_dev_services
    
    # 显示服务状态
    show_service_status
    
    log_success "SonjayOS VMware开发环境启动完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS VMware开发环境"
    echo "=========================================="
    echo ""
    echo "开发模式特性:"
    echo "- 热重载: 代码修改自动重启"
    echo "- 调试模式: 详细日志和错误信息"
    echo "- 模拟服务: AI和安全服务模拟"
    echo "- 性能分析: 实时性能监控"
    echo "- VMware优化: 虚拟机性能优化"
    echo ""
    echo "可用命令:"
    echo "- 查看状态: ./scripts/dev-mode.sh status"
    echo "- 停止服务: ./scripts/dev-mode.sh stop"
    echo "- 重启服务: ./scripts/dev-mode.sh restart"
    echo "- 进入环境: cd ~/sonjayos && source venv/bin/activate"
    echo ""
    echo "开发工具:"
    echo "- 格式化代码: ./dev_tools/format_code.sh"
    echo "- 检查代码: ./dev_tools/lint_code.sh"
    echo "- 运行测试: ./dev_tools/run_tests.sh"
    echo "- 性能分析: ./dev_tools/profile_performance.sh"
    echo ""
    echo "服务地址:"
    echo "- AI服务: http://localhost:8000"
    echo "- UI服务: http://localhost:8001"
    echo "- 安全服务: http://localhost:8002"
    echo ""
    echo "日志文件:"
    echo "- AI日志: /tmp/sonjayos-ai-dev.log"
    echo "- UI日志: /tmp/sonjayos-ui-dev.log"
    echo "- 安全日志: /tmp/sonjayos-security-dev.log"
    echo ""
}

# 停止开发环境
stop_dev_environment() {
    log_info "停止SonjayOS开发环境..."
    
    cd $HOME/sonjayos
    
    # 停止开发模式
    ./scripts/dev-mode.sh stop
    
    log_success "SonjayOS开发环境已停止"
}

# 重启开发环境
restart_dev_environment() {
    log_info "重启SonjayOS开发环境..."
    
    # 停止开发环境
    stop_dev_environment
    
    # 等待2秒
    sleep 2
    
    # 启动开发环境
    start_dev_environment
}

# 进入开发环境
enter_dev_environment() {
    log_info "进入SonjayOS开发环境..."
    
    cd $HOME/sonjayos
    source venv/bin/activate
    
    # 设置环境变量
    export SONJAYOS_DEV_MODE=true
    export SONJAYOS_DEBUG_LEVEL=DEBUG
    export SONJAYOS_HOT_RELOAD=true
    export SONJAYOS_MOCK_AI=true
    export SONJAYOS_PROFILING=true
    export SONJAYOS_VMWARE_MODE=true
    
    echo "已进入SonjayOS开发环境"
    echo "项目目录: $(pwd)"
    echo "虚拟环境: 已激活"
    echo "环境变量: 已设置"
    echo ""
    echo "可用命令:"
    echo "- 启动服务: ./scripts/dev-mode.sh start"
    echo "- 查看状态: ./scripts/dev-mode.sh status"
    echo "- 停止服务: ./scripts/dev-mode.sh stop"
    echo ""
    
    # 启动交互式shell
    bash
}

# 显示帮助信息
show_help() {
    echo "SonjayOS VMware开发模式启动脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动开发环境"
    echo "  stop      停止开发环境"
    echo "  restart   重启开发环境"
    echo "  status    显示服务状态"
    echo "  enter     进入开发环境"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start      # 启动开发环境"
    echo "  $0 status     # 显示服务状态"
    echo "  $0 enter      # 进入开发环境"
    echo ""
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            start_dev_environment
            ;;
        "stop")
            stop_dev_environment
            ;;
        "restart")
            restart_dev_environment
            ;;
        "status")
            show_service_status
            ;;
        "enter")
            enter_dev_environment
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
