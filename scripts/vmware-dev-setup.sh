#!/bin/bash
# SonjayOS VMware 开发环境自动设置脚本
# 用于在VMware虚拟机中自动设置SonjayOS开发环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[VMWARE-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[VMWARE-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[VMWARE-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[VMWARE-ERROR]${NC} $1"
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        log_warning "推荐使用Ubuntu 24.04 LTS，当前系统: $(lsb_release -d | cut -f2)"
    fi
    
    # 检查内存
    total_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ -n "$total_mem" ] && [ "$total_mem" -lt 8 ]; then
        log_warning "推荐至少8GB内存，当前: ${total_mem}GB"
    fi
    
    # 检查磁盘空间
    available_space=$(df / | awk 'NR==2{print $4}')
    if [ "$available_space" -lt 50000000 ]; then  # 50GB in KB
        log_warning "推荐至少50GB可用磁盘空间"
    fi
    
    log_success "系统要求检查完成"
}

# 更新系统包
update_system() {
    log_info "更新系统包..."
    
    apt update
    apt upgrade -y
    
    # 安装基础依赖
    apt install -y \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        nodejs \
        npm \
        git \
        curl \
        wget \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        vim \
        htop \
        tree \
        net-tools \
        netstat-nat
    
    log_success "系统包更新完成"
}

# 配置网络
configure_network() {
    log_info "配置网络..."
    
    # 检查网络连接
    if ping -c 1 google.com > /dev/null 2>&1; then
        log_success "网络连接正常"
    else
        log_warning "网络连接异常，请检查网络设置"
    fi
    
    # 配置Git
    if [ -z "$(git config --global user.name)" ]; then
        log_info "配置Git用户信息..."
        read -p "请输入Git用户名: " git_name
        read -p "请输入Git邮箱: " git_email
        git config --global user.name "$git_name"
        git config --global user.email "$git_email"
    fi
    
    log_success "网络配置完成"
}

# 安装开发工具
install_dev_tools() {
    log_info "安装开发工具..."
    
    # 安装VS Code
    if ! command -v code &> /dev/null; then
        log_info "安装VS Code..."
        wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
        install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
        sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
        apt update
        apt install code
    fi
    
    # 安装Docker
    if ! command -v docker &> /dev/null; then
        log_info "安装Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        usermod -aG docker $USER
        rm get-docker.sh
    fi
    
    log_success "开发工具安装完成"
}

# 设置SonjayOS项目
setup_sonjayos_project() {
    log_info "设置SonjayOS项目..."
    
    # 检查项目目录
    if [ ! -d "$HOME/sonjayos" ]; then
        log_info "克隆SonjayOS项目..."
        cd $HOME
        git clone https://github.com/sonjayos/sonjayos.git
    else
        log_info "更新SonjayOS项目..."
        cd $HOME/sonjayos
        git pull origin main
    fi
    
    cd $HOME/sonjayos
    
    # 设置权限
    chmod +x scripts/*.sh
    chmod +x tools/iso-builder/*.sh
    
    # 创建Python虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 安装开发工具
    pip install \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        flake8 \
        mypy \
        pre-commit \
        isort \
        bandit \
        safety \
        memory-profiler \
        line-profiler \
        py-spy \
        watchdog
    
    log_success "SonjayOS项目设置完成"
}

# 配置开发环境
configure_dev_environment() {
    log_info "配置开发环境..."
    
    # 设置环境变量
    cat >> ~/.bashrc << 'EOF'

# SonjayOS 开发环境变量
export SONJAYOS_DEV_MODE=true
export SONJAYOS_DEBUG_LEVEL=DEBUG
export SONJAYOS_HOT_RELOAD=true
export SONJAYOS_MOCK_AI=true
export SONJAYOS_PROFILING=true
export SONJAYOS_VMWARE_MODE=true

# 添加项目路径
export PATH="$HOME/sonjayos/scripts:$PATH"
export PYTHONPATH="$HOME/sonjayos/src:$PYTHONPATH"
EOF
    
    # 创建开发配置文件
    mkdir -p $HOME/sonjayos/dev_config/{ai,ui,system,security}
    
    # AI开发配置
    cat > $HOME/sonjayos/dev_config/ai/llama_config.json << 'EOF'
{
    "models": {
        "llama3.1-8b": {
            "name": "llama3.1:8b",
            "size": "8B",
            "memory_usage": 2000,
            "inference_speed": 100.0,
            "quality_score": 0.85
        }
    },
    "default_model": "llama3.1-8b",
    "ollama_host": "http://localhost:11434",
    "max_memory_usage": 0.3,
    "cache_size": 100,
    "auto_model_switching": false,
    "dev_mode": true,
    "mock_responses": true,
    "vmware_mode": true
}
EOF
    
    # UI开发配置
    cat > $HOME/sonjayos/dev_config/ui/theme_config.json << 'EOF'
{
    "auto_theme_switching": false,
    "learning_enabled": false,
    "brightness_adaptation": false,
    "time_based_themes": {
        "morning": "light_work",
        "afternoon": "light_work",
        "evening": "dark_work",
        "night": "dark_reading"
    },
    "dev_mode": true,
    "hot_reload": true,
    "vmware_mode": true
}
EOF
    
    # 安全开发配置
    cat > $HOME/sonjayos/dev_config/security/ai_security_config.json << 'EOF'
{
    "monitoring": {
        "enabled": true,
        "check_interval": 10,
        "log_retention_days": 7
    },
    "threat_detection": {
        "cpu_threshold": 90.0,
        "memory_threshold": 95.0,
        "network_threshold": 2000,
        "file_access_threshold": 2000,
        "process_threshold": 500
    },
    "dev_mode": true,
    "mock_threats": true,
    "verbose_logging": true,
    "vmware_mode": true
}
EOF
    
    log_success "开发环境配置完成"
}

# 创建开发工具
create_dev_tools() {
    log_info "创建开发工具..."
    
    # 创建开发服务启动脚本
    cat > $HOME/sonjayos/vmware-dev-services.sh << 'EOF'
#!/bin/bash
# SonjayOS VMware 开发服务启动脚本

echo "启动SonjayOS VMware开发环境..."

# 激活虚拟环境
source ~/sonjayos/venv/bin/activate

# 设置环境变量
export SONJAYOS_DEV_MODE=true
export SONJAYOS_DEBUG_LEVEL=DEBUG
export SONJAYOS_HOT_RELOAD=true
export SONJAYOS_MOCK_AI=true
export SONJAYOS_PROFILING=true
export SONJAYOS_VMWARE_MODE=true

# 启动AI服务（开发模式）
echo "启动AI服务（开发模式）..."
cd ~/sonjayos
python src/ai/main.py --dev-mode --debug --mock-ai &
AI_PID=$!

# 启动UI服务（开发模式）
echo "启动UI服务（开发模式）..."
python src/ui/main.py --dev-mode --debug --hot-reload &
UI_PID=$!

# 启动安全服务（开发模式）
echo "启动安全服务（开发模式）..."
python src/system/security/main.py --dev-mode --debug --mock-threats &
SECURITY_PID=$!

# 启动开发工具服务
echo "启动开发工具服务..."
python src/dev_tools/main.py --dev-mode --debug &
DEV_TOOLS_PID=$!

# 启动文件监控（热重载）
echo "启动文件监控..."
watchdog --patterns="*.py" --recursive --command="echo '文件变化检测到，重启服务...'" src/ &
WATCHDOG_PID=$!

echo "VMware开发服务已启动"
echo "AI服务PID: $AI_PID"
echo "UI服务PID: $UI_PID"
echo "安全服务PID: $SECURITY_PID"
echo "开发工具PID: $DEV_TOOLS_PID"
echo "文件监控PID: $WATCHDOG_PID"

# 等待用户输入停止
echo "按Ctrl+C停止所有服务"
trap 'kill $AI_PID $UI_PID $SECURITY_PID $DEV_TOOLS_PID $WATCHDOG_PID; exit' INT
wait
EOF
    
    chmod +x $HOME/sonjayos/vmware-dev-services.sh
    
    # 创建VMware优化脚本
    cat > $HOME/sonjayos/vmware-optimize.sh << 'EOF'
#!/bin/bash
# VMware 虚拟机优化脚本

echo "优化VMware虚拟机性能..."

# 设置CPU调度器
echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true

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

echo "VMware虚拟机优化完成"
EOF
    
    chmod +x $HOME/sonjayos/vmware-optimize.sh
    
    log_success "开发工具创建完成"
}

# 测试开发环境
test_dev_environment() {
    log_info "测试开发环境..."
    
    cd $HOME/sonjayos
    
    # 测试Python环境
    source venv/bin/activate
    python -c "import sys; print(f'Python版本: {sys.version}')"
    
    # 测试项目结构
    if [ -f "scripts/dev-mode.sh" ]; then
        log_success "项目结构检查通过"
    else
        log_error "项目结构检查失败"
        return 1
    fi
    
    # 测试权限
    if [ -x "scripts/dev-mode.sh" ]; then
        log_success "脚本权限检查通过"
    else
        log_error "脚本权限检查失败"
        return 1
    fi
    
    log_success "开发环境测试完成"
}

# 显示完成信息
show_completion_info() {
    log_success "SonjayOS VMware开发环境设置完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS VMware开发环境"
    echo "=========================================="
    echo ""
    echo "环境信息:"
    echo "- 操作系统: $(lsb_release -d | cut -f2)"
    echo "- 内存: $(free -h | awk '/^Mem:/{print $2}')"
    echo "- 磁盘: $(df -h / | awk 'NR==2{print $4}') 可用"
    echo "- 网络: $(ping -c 1 google.com > /dev/null 2>&1 && echo '正常' || echo '异常')"
    echo ""
    echo "项目位置: $HOME/sonjayos"
    echo "虚拟环境: $HOME/sonjayos/venv"
    echo ""
    echo "使用方法:"
    echo "- 启动开发环境: cd ~/sonjayos && ./vmware-dev-services.sh"
    echo "- 优化虚拟机: ./vmware-optimize.sh"
    echo "- 启动开发模式: ./scripts/dev-mode.sh start"
    echo "- 查看状态: ./scripts/dev-mode.sh status"
    echo ""
    echo "开发工具:"
    echo "- 代码格式化: ./dev_tools/format_code.sh"
    echo "- 代码检查: ./dev_tools/lint_code.sh"
    echo "- 运行测试: ./dev_tools/run_tests.sh"
    echo "- 性能分析: ./dev_tools/profile_performance.sh"
    echo ""
    echo "配置文件:"
    echo "- AI配置: dev_config/ai/"
    echo "- UI配置: dev_config/ui/"
    echo "- 安全配置: dev_config/security/"
    echo ""
    echo "请重新加载shell配置: source ~/.bashrc"
    echo ""
}

# 主函数
main() {
    echo "=========================================="
    echo "SonjayOS VMware开发环境自动设置"
    echo "=========================================="
    echo ""
    
    # 检查是否为root用户
    if [ "$EUID" -eq 0 ]; then
        log_warning "建议不要使用root用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 执行设置步骤
    check_system_requirements
    update_system
    configure_network
    install_dev_tools
    setup_sonjayos_project
    configure_dev_environment
    create_dev_tools
    test_dev_environment
    show_completion_info
    
    log_success "设置完成！"
}

# 运行主函数
main "$@"
