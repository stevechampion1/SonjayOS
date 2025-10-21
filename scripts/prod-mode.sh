#!/bin/bash
# SonjayOS 生产模式启动脚本
# 用于生产环境下的系统运行

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[PROD-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PROD-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[PROD-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[PROD-ERROR]${NC} $1"
}

# 生产模式配置
PROD_MODE=true
DEBUG_LEVEL=INFO
HOT_RELOAD=false
MOCK_AI_SERVICES=false
ENABLE_PROFILING=false
LOG_TO_FILE=true

# 生产环境变量
export SONJAYOS_PROD_MODE=true
export SONJAYOS_DEBUG_LEVEL=INFO
export SONJAYOS_HOT_RELOAD=false
export SONJAYOS_MOCK_AI=false
export SONJAYOS_PROFILING=false

# 检查生产环境
check_prod_environment() {
    log_info "检查生产环境..."
    
    # 检查系统服务
    if ! systemctl is-active --quiet sonjayos-ai; then
        log_warning "AI服务未运行，尝试启动..."
        systemctl start sonjayos-ai
    fi
    
    if ! systemctl is-active --quiet sonjayos-ui; then
        log_warning "UI服务未运行，尝试启动..."
        systemctl start sonjayos-ui
    fi
    
    if ! systemctl is-active --quiet sonjayos-security; then
        log_warning "安全服务未运行，尝试启动..."
        systemctl start sonjayos-security
    fi
    
    # 检查Ollama服务
    if ! systemctl is-active --quiet ollama; then
        log_warning "Ollama服务未运行，尝试启动..."
        systemctl start ollama
    fi
    
    log_success "生产环境检查完成"
}

# 优化系统性能
optimize_system_performance() {
    log_info "优化系统性能..."
    
    # 设置CPU调度器
    echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    
    # 优化内存管理
    echo 1 > /proc/sys/vm/swappiness
    echo 15 > /proc/sys/vm/dirty_ratio
    echo 5 > /proc/sys/vm/dirty_background_ratio
    
    # 优化网络
    echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
    echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf
    echo 'net.ipv4.tcp_rmem = 4096 87380 16777216' >> /etc/sysctl.conf
    echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' >> /etc/sysctl.conf
    
    # 应用配置
    sysctl -p
    
    log_success "系统性能优化完成"
}

# 配置生产服务
configure_prod_services() {
    log_info "配置生产服务..."
    
    # 创建生产配置目录
    mkdir -p /etc/sonjayos/{ai,ui,system,security}
    
    # 生产模式AI配置
    cat > /etc/sonjayos/ai/llama_config.json << 'EOF'
{
    "models": {
        "llama3.1-8b": {
            "name": "llama3.1:8b",
            "size": "8B",
            "memory_usage": 8000,
            "inference_speed": 50.0,
            "quality_score": 0.85
        },
        "llama3.1-70b": {
            "name": "llama3.1:70b",
            "size": "70B",
            "memory_usage": 40000,
            "inference_speed": 15.0,
            "quality_score": 0.95
        }
    },
    "default_model": "llama3.1-8b",
    "ollama_host": "http://localhost:11434",
    "max_memory_usage": 0.8,
    "cache_size": 10000,
    "auto_model_switching": true,
    "prod_mode": true,
    "mock_responses": false
}
EOF
    
    # 生产模式UI配置
    cat > /etc/sonjayos/ui/theme_config.json << 'EOF'
{
    "auto_theme_switching": true,
    "learning_enabled": true,
    "brightness_adaptation": true,
    "time_based_themes": {
        "morning": "light_work",
        "afternoon": "light_work",
        "evening": "dark_work",
        "night": "dark_reading"
    },
    "prod_mode": true,
    "hot_reload": false
}
EOF
    
    # 生产模式安全配置
    cat > /etc/sonjayos/security/ai_security_config.json << 'EOF'
{
    "monitoring": {
        "enabled": true,
        "check_interval": 30,
        "log_retention_days": 30
    },
    "threat_detection": {
        "cpu_threshold": 80.0,
        "memory_threshold": 85.0,
        "network_threshold": 1000,
        "file_access_threshold": 1000,
        "process_threshold": 200
    },
    "prod_mode": true,
    "mock_threats": false,
    "verbose_logging": false
}
EOF
    
    log_success "生产服务配置完成"
}

# 启动生产服务
start_prod_services() {
    log_info "启动生产服务..."
    
    # 启动AI服务
    systemctl start sonjayos-ai
    systemctl enable sonjayos-ai
    
    # 启动UI服务
    systemctl start sonjayos-ui
    systemctl enable sonjayos-ui
    
    # 启动安全服务
    systemctl start sonjayos-security
    systemctl enable sonjayos-security
    
    # 启动Ollama服务
    systemctl start ollama
    systemctl enable ollama
    
    # 启动GNOME扩展
    gsettings set org.gnome.shell enabled-extensions "['sonjayos-ai-assistant@sonjayos.com']"
    
    log_success "生产服务启动完成"
}

# 监控服务状态
monitor_services() {
    log_info "监控服务状态..."
    
    # 检查服务状态
    services=("sonjayos-ai" "sonjayos-ui" "sonjayos-security" "ollama")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service: 运行中"
        else
            log_error "$service: 未运行"
        fi
    done
    
    # 检查端口
    ports=(8000 8001 8002 11434)
    
    for port in "${ports[@]}"; do
        if netstat -tlnp | grep -q ":$port "; then
            log_success "端口 $port: 监听中"
        else
            log_warning "端口 $port: 未监听"
        fi
    done
}

# 创建生产监控脚本
create_prod_monitoring() {
    log_info "创建生产监控脚本..."
    
    cat > /opt/sonjayos/bin/sonjayos-monitor << 'EOF'
#!/bin/bash
# SonjayOS 生产监控脚本

echo "SonjayOS 生产环境监控"
echo "======================"
echo ""

# 系统状态
echo "系统状态:"
echo "- CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "- 内存使用率: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "- 磁盘使用率: $(df -h / | awk 'NR==2{print $5}')"
echo ""

# 服务状态
echo "服务状态:"
systemctl is-active --quiet sonjayos-ai && echo "- AI服务: 运行中" || echo "- AI服务: 未运行"
systemctl is-active --quiet sonjayos-ui && echo "- UI服务: 运行中" || echo "- UI服务: 未运行"
systemctl is-active --quiet sonjayos-security && echo "- 安全服务: 运行中" || echo "- 安全服务: 未运行"
systemctl is-active --quiet ollama && echo "- Ollama: 运行中" || echo "- Ollama: 未运行"
echo ""

# 网络状态
echo "网络状态:"
netstat -tlnp | grep -E ":(8000|8001|8002|11434)" | awk '{print "- 端口 " $4 ": " $6}'
echo ""

# 日志状态
echo "日志状态:"
echo "- AI日志: $(tail -1 /var/log/sonjayos/ai.log 2>/dev/null | cut -c1-50)..."
echo "- UI日志: $(tail -1 /var/log/sonjayos/ui.log 2>/dev/null | cut -c1-50)..."
echo "- 安全日志: $(tail -1 /var/log/sonjayos/security.log 2>/dev/null | cut -c1-50)..."
EOF
    
    chmod +x /opt/sonjayos/bin/sonjayos-monitor
    
    log_success "生产监控脚本创建完成"
}

# 创建生产日志轮转
create_log_rotation() {
    log_info "创建日志轮转配置..."
    
    cat > /etc/logrotate.d/sonjayos << 'EOF'
/var/log/sonjayos/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 sonjayos sonjayos
    postrotate
        systemctl reload sonjayos-ai
        systemctl reload sonjayos-ui
        systemctl reload sonjayos-security
    endscript
}
EOF
    
    log_success "日志轮转配置创建完成"
}

# 启动生产模式
start_prod_mode() {
    log_info "启动SonjayOS生产模式..."
    
    # 检查生产环境
    check_prod_environment
    
    # 优化系统性能
    optimize_system_performance
    
    # 配置生产服务
    configure_prod_services
    
    # 启动生产服务
    start_prod_services
    
    # 创建生产监控
    create_prod_monitoring
    
    # 创建日志轮转
    create_log_rotation
    
    # 监控服务状态
    monitor_services
    
    log_success "SonjayOS生产模式启动完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS 生产模式"
    echo "=========================================="
    echo ""
    echo "生产模式特性:"
    echo "- 高性能优化: 系统资源优化配置"
    echo "- 稳定运行: 生产级服务配置"
    echo "- 安全监控: 实时威胁检测"
    echo "- 日志管理: 自动日志轮转"
    echo ""
    echo "可用命令:"
    echo "- 监控状态: sonjayos-monitor"
    echo "- 查看日志: journalctl -u sonjayos-ai"
    echo "- 重启服务: systemctl restart sonjayos-ai"
    echo "- 停止服务: systemctl stop sonjayos-ai"
    echo ""
    echo "配置文件:"
    echo "- AI配置: /etc/sonjayos/ai/"
    echo "- UI配置: /etc/sonjayos/ui/"
    echo "- 安全配置: /etc/sonjayos/security/"
    echo ""
}

# 停止生产模式
stop_prod_mode() {
    log_info "停止SonjayOS生产模式..."
    
    # 停止所有服务
    systemctl stop sonjayos-ai
    systemctl stop sonjayos-ui
    systemctl stop sonjayos-security
    systemctl stop ollama
    
    # 禁用服务
    systemctl disable sonjayos-ai
    systemctl disable sonjayos-ui
    systemctl disable sonjayos-security
    systemctl disable ollama
    
    log_success "SonjayOS生产模式已停止"
}

# 显示生产状态
show_prod_status() {
    log_info "SonjayOS生产模式状态..."
    
    echo ""
    echo "=========================================="
    echo "SonjayOS 生产模式状态"
    echo "=========================================="
    echo ""
    
    # 检查服务状态
    if systemctl is-active --quiet sonjayos-ai; then
        echo "✅ AI服务: 运行中"
    else
        echo "❌ AI服务: 未运行"
    fi
    
    if systemctl is-active --quiet sonjayos-ui; then
        echo "✅ UI服务: 运行中"
    else
        echo "❌ UI服务: 未运行"
    fi
    
    if systemctl is-active --quiet sonjayos-security; then
        echo "✅ 安全服务: 运行中"
    else
        echo "❌ 安全服务: 未运行"
    fi
    
    if systemctl is-active --quiet ollama; then
        echo "✅ Ollama: 运行中"
    else
        echo "❌ Ollama: 未运行"
    fi
    
    echo ""
    echo "生产环境变量:"
    echo "- SONJAYOS_PROD_MODE: $SONJAYOS_PROD_MODE"
    echo "- SONJAYOS_DEBUG_LEVEL: $SONJAYOS_DEBUG_LEVEL"
    echo "- SONJAYOS_HOT_RELOAD: $SONJAYOS_HOT_RELOAD"
    echo "- SONJAYOS_MOCK_AI: $SONJAYOS_MOCK_AI"
    echo "- SONJAYOS_PROFILING: $SONJAYOS_PROFILING"
    echo ""
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            start_prod_mode
            ;;
        "stop")
            stop_prod_mode
            ;;
        "status")
            show_prod_status
            ;;
        "restart")
            stop_prod_mode
            sleep 2
            start_prod_mode
            ;;
        *)
            echo "用法: $0 {start|stop|status|restart}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动生产模式"
            echo "  stop    - 停止生产模式"
            echo "  status  - 显示生产状态"
            echo "  restart - 重启生产模式"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
