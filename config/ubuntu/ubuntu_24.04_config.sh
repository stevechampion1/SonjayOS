#!/bin/bash
# Ubuntu 24.04 LTS 基础系统配置脚本
# 用于配置SonjayOS的基础系统环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[UBUNTU-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[UBUNTU-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[UBUNTU-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[UBUNTU-ERROR]${NC} $1"
}

# 更新系统包
update_system() {
    log_info "更新系统包..."
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
    log_success "系统包更新完成"
}

# 安装基础开发工具
install_dev_tools() {
    log_info "安装基础开发工具..."
    sudo apt install -y \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        vim \
        htop \
        tree \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    log_success "基础开发工具安装完成"
}

# 配置系统优化
optimize_system() {
    log_info "配置系统优化..."
    
    # 优化内存管理
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
    
    # 优化网络
    echo 'net.core.rmem_max=16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.wmem_max=16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_rmem=4096 87380 16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_wmem=4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
    
    # 应用配置
    sudo sysctl -p
    
    log_success "系统优化配置完成"
}

# 配置用户环境
configure_user_environment() {
    log_info "配置用户环境..."
    
    # 创建用户目录
    mkdir -p ~/.local/bin
    mkdir -p ~/.config/sonjayos
    
    # 配置bashrc
    cat >> ~/.bashrc << 'EOF'

# SonjayOS 环境变量
export SONJAYOS_HOME="$HOME/sonjayos"
export PATH="$SONJAYOS_HOME/scripts:$PATH"
export PYTHONPATH="$SONJAYOS_HOME/src:$PYTHONPATH"

# SonjayOS 别名
alias sonjayos='cd $SONJAYOS_HOME'
alias sonjayos-dev='cd $SONJAYOS_HOME && source venv/bin/activate'
alias sonjayos-start='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh start'
alias sonjayos-stop='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh stop'
alias sonjayos-status='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh status'
EOF
    
    log_success "用户环境配置完成"
}

# 配置系统服务
configure_system_services() {
    log_info "配置系统服务..."
    
    # 创建SonjayOS系统用户
    sudo useradd -r -s /bin/false sonjayos || true
    
    # 创建日志目录
    sudo mkdir -p /var/log/sonjayos
    sudo chown sonjayos:sonjayos /var/log/sonjayos
    sudo chmod 755 /var/log/sonjayos
    
    # 创建配置目录
    sudo mkdir -p /etc/sonjayos
    sudo chown sonjayos:sonjayos /etc/sonjayos
    sudo chmod 755 /etc/sonjayos
    
    log_success "系统服务配置完成"
}

# 主函数
main() {
    echo "=========================================="
    echo "Ubuntu 24.04 LTS 基础系统配置"
    echo "=========================================="
    echo ""
    
    update_system
    install_dev_tools
    optimize_system
    configure_user_environment
    configure_system_services
    
    log_success "Ubuntu 24.04 LTS 基础系统配置完成！"
    echo ""
    echo "请重新加载shell配置: source ~/.bashrc"
    echo ""
}

# 运行主函数
main "$@"
