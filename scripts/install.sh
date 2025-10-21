#!/bin/bash
# SonjayOS 安装脚本
# 用于安装和配置SonjayOS AI集成操作系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_system_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        log_error "此脚本仅支持Ubuntu 24.04 LTS"
        exit 1
    fi
    
    # 检查架构
    if [ "$(uname -m)" != "x86_64" ]; then
        log_error "仅支持x86_64架构"
        exit 1
    fi
    
    # 检查内存
    total_mem=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_mem" -lt 16 ]; then
        log_warning "推荐至少16GB内存，当前: ${total_mem}GB"
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
        python3.11 \
        python3.11-pip \
        python3.11-venv \
        python3.11-dev \
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
        lsb-release
    
    log_success "系统包更新完成"
}

# 安装Python依赖
install_python_dependencies() {
    log_info "安装Python依赖..."
    
    # 创建虚拟环境
    python3.11 -m venv /opt/sonjayos/venv
    source /opt/sonjayos/venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装AI相关依赖
    pip install \
        torch \
        torchvision \
        torchaudio \
        transformers \
        sentence-transformers \
        whisper \
        openai-whisper \
        numpy \
        scipy \
        pandas \
        scikit-learn \
        fastapi \
        uvicorn \
        pydantic \
        psutil \
        pyaudio \
        wave \
        requests \
        aiofiles \
        asyncio-mqtt \
        sqlite3 \
        cryptography
    
    log_success "Python依赖安装完成"
}

# 安装Node.js依赖
install_nodejs_dependencies() {
    log_info "安装Node.js依赖..."
    
    cd /opt/sonjayos
    
    # 创建package.json
    cat > package.json << EOF
{
  "name": "sonjayos",
  "version": "1.0.0",
  "description": "SonjayOS AI集成操作系统",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "socket.io": "^4.7.2",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "compression": "^1.7.4",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
EOF
    
    npm install
    
    log_success "Node.js依赖安装完成"
}

# 安装Ollama
install_ollama() {
    log_info "安装Ollama..."
    
    # 下载并安装Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # 启动Ollama服务
    systemctl enable ollama
    systemctl start ollama
    
    # 等待服务启动
    sleep 10
    
    # 拉取Llama 3.1模型
    log_info "下载Llama 3.1模型..."
    ollama pull llama3.1:8b
    
    log_success "Ollama安装完成"
}

# 安装ROCm (AMD GPU支持)
install_rocm() {
    log_info "安装ROCm..."
    
    # 添加ROCm仓库
    wget https://repo.radeon.com/amdgpu-install/5.7/ubuntu/jammy/amdgpu-install_5.7.50700-1_all.deb
    dpkg -i amdgpu-install_5.7.50700-1_all.deb
    
    # 安装ROCm
    amdgpu-install --usecase=rocm
    
    # 配置环境变量
    echo 'export ROCM_PATH=/opt/rocm' >> /etc/environment
    echo 'export PATH=$PATH:/opt/rocm/bin' >> /etc/environment
    echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib' >> /etc/environment
    
    log_success "ROCm安装完成"
}

# 配置系统服务
configure_system_services() {
    log_info "配置系统服务..."
    
    # 创建SonjayOS服务目录
    mkdir -p /etc/sonjayos/{ai,ui,system,security}
    mkdir -p /var/lib/sonjayos
    mkdir -p /var/log/sonjayos
    mkdir -p /opt/sonjayos/{bin,lib,config}
    
    # 复制配置文件
    cp -r src/config/* /etc/sonjayos/
    
    # 创建AI服务
    cat > /etc/systemd/system/sonjayos-ai.service << EOF
[Unit]
Description=SonjayOS AI Service
After=network.target ollama.service

[Service]
Type=simple
User=sonjayos
Group=sonjayos
WorkingDirectory=/opt/sonjayos
ExecStart=/opt/sonjayos/venv/bin/python /opt/sonjayos/src/ai/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建UI服务
    cat > /etc/systemd/system/sonjayos-ui.service << EOF
[Unit]
Description=SonjayOS UI Service
After=network.target sonjayos-ai.service

[Service]
Type=simple
User=sonjayos
Group=sonjayos
WorkingDirectory=/opt/sonjayos
ExecStart=/opt/sonjayos/venv/bin/python /opt/sonjayos/src/ui/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建安全服务
    cat > /etc/systemd/system/sonjayos-security.service << EOF
[Unit]
Description=SonjayOS Security Service
After=network.target

[Service]
Type=simple
User=sonjayos
Group=sonjayos
WorkingDirectory=/opt/sonjayos
ExecStart=/opt/sonjayos/venv/bin/python /opt/sonjayos/src/system/security/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建用户
    useradd -r -s /bin/false sonjayos
    
    # 设置权限
    chown -R sonjayos:sonjayos /opt/sonjayos
    chown -R sonjayos:sonjayos /var/lib/sonjayos
    chown -R sonjayos:sonjayos /var/log/sonjayos
    
    # 启用服务
    systemctl daemon-reload
    systemctl enable sonjayos-ai
    systemctl enable sonjayos-ui
    systemctl enable sonjayos-security
    
    log_success "系统服务配置完成"
}

# 安装GNOME扩展
install_gnome_extensions() {
    log_info "安装GNOME扩展..."
    
    # 安装GNOME扩展工具
    apt install -y gnome-shell-extensions gnome-tweaks
    
    # 复制扩展文件
    cp -r src/ui/gnome/sonjayos-ai-assistant /usr/share/gnome-shell/extensions/
    
    # 设置扩展权限
    chmod +x /usr/share/gnome-shell/extensions/sonjayos-ai-assistant/extension.js
    
    # 启用扩展
    gsettings set org.gnome.shell enabled-extensions "['sonjayos-ai-assistant@sonjayos.com']"
    
    log_success "GNOME扩展安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 安装UFW
    apt install -y ufw
    
    # 配置防火墙规则
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 22
    ufw allow 80
    ufw allow 443
    ufw allow 11434  # Ollama端口
    
    # 启用防火墙
    ufw --force enable
    
    log_success "防火墙配置完成"
}

# 优化系统性能
optimize_system() {
    log_info "优化系统性能..."
    
    # 配置内核参数
    cat >> /etc/sysctl.conf << EOF

# SonjayOS性能优化
vm.swappiness=10
vm.dirty_ratio=15
vm.dirty_background_ratio=5
kernel.sched_rt_runtime_us=-1
kernel.sched_rt_period_us=1000000
EOF
    
    # 配置CPU调度器
    echo 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash intel_pstate=enable"' >> /etc/default/grub
    update-grub
    
    # 配置内存管理
    echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf
    
    # 配置文件系统
    echo 'vm.dirty_writeback_centisecs=1500' >> /etc/sysctl.conf
    
    log_success "系统性能优化完成"
}

# 创建启动脚本
create_startup_scripts() {
    log_info "创建启动脚本..."
    
    # 创建启动脚本
    cat > /opt/sonjayos/bin/sonjayos-start << 'EOF'
#!/bin/bash
# SonjayOS启动脚本

echo "启动SonjayOS AI集成操作系统..."

# 启动AI服务
systemctl start sonjayos-ai
systemctl start sonjayos-ui
systemctl start sonjayos-security

# 启动Ollama
systemctl start ollama

# 启动GNOME扩展
gsettings set org.gnome.shell enabled-extensions "['sonjayos-ai-assistant@sonjayos.com']"

echo "SonjayOS启动完成"
EOF
    
    chmod +x /opt/sonjayos/bin/sonjayos-start
    
    # 创建停止脚本
    cat > /opt/sonjayos/bin/sonjayos-stop << 'EOF'
#!/bin/bash
# SonjayOS停止脚本

echo "停止SonjayOS服务..."

systemctl stop sonjayos-ai
systemctl stop sonjayos-ui
systemctl stop sonjayos-security
systemctl stop ollama

echo "SonjayOS已停止"
EOF
    
    chmod +x /opt/sonjayos/bin/sonjayos-stop
    
    log_success "启动脚本创建完成"
}

# 运行安装后配置
post_install_config() {
    log_info "运行安装后配置..."
    
    # 启动服务
    systemctl start sonjayos-ai
    systemctl start sonjayos-ui
    systemctl start sonjayos-security
    
    # 等待服务启动
    sleep 30
    
    # 检查服务状态
    if systemctl is-active --quiet sonjayos-ai; then
        log_success "AI服务运行正常"
    else
        log_warning "AI服务启动失败"
    fi
    
    if systemctl is-active --quiet sonjayos-ui; then
        log_success "UI服务运行正常"
    else
        log_warning "UI服务启动失败"
    fi
    
    if systemctl is-active --quiet sonjayos-security; then
        log_success "安全服务运行正常"
    else
        log_warning "安全服务启动失败"
    fi
    
    log_success "安装后配置完成"
}

# 显示安装完成信息
show_completion_info() {
    log_success "SonjayOS安装完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS AI集成操作系统安装完成"
    echo "=========================================="
    echo ""
    echo "系统信息:"
    echo "- 操作系统: Ubuntu 24.04 LTS"
    echo "- AI模型: Llama 3.1 8B"
    echo "- 语音识别: Whisper"
    echo "- 语义搜索: Sentence Transformers"
    echo ""
    echo "服务状态:"
    echo "- AI服务: $(systemctl is-active sonjayos-ai)"
    echo "- UI服务: $(systemctl is-active sonjayos-ui)"
    echo "- 安全服务: $(systemctl is-active sonjayos-security)"
    echo ""
    echo "使用方法:"
    echo "- 启动系统: /opt/sonjayos/bin/sonjayos-start"
    echo "- 停止系统: /opt/sonjayos/bin/sonjayos-stop"
    echo "- 查看日志: journalctl -u sonjayos-ai"
    echo ""
    echo "配置文件位置:"
    echo "- AI配置: /etc/sonjayos/ai/"
    echo "- UI配置: /etc/sonjayos/ui/"
    echo "- 安全配置: /etc/sonjayos/security/"
    echo ""
    echo "请重启系统以完成安装。"
    echo ""
}

# 主安装流程
main() {
    echo "=========================================="
    echo "SonjayOS AI集成操作系统安装程序"
    echo "=========================================="
    echo ""
    
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
    
    # 执行安装步骤
    check_system_requirements
    update_system
    install_python_dependencies
    install_nodejs_dependencies
    install_ollama
    install_rocm
    configure_system_services
    install_gnome_extensions
    configure_firewall
    optimize_system
    create_startup_scripts
    post_install_config
    show_completion_info
    
    log_success "安装完成！"
}

# 运行主函数
main "$@"
