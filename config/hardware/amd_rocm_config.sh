#!/bin/bash
# AMD Ryzen 和 Radeon 优化配置脚本
# 用于配置ROCm和AMD GPU加速

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[AMD-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[AMD-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[AMD-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[AMD-ERROR]${NC} $1"
}

# 检测AMD硬件
detect_amd_hardware() {
    log_info "检测AMD硬件..."
    
    # 检测CPU
    if lscpu | grep -i "amd" > /dev/null; then
        CPU_INFO=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
        log_success "检测到AMD CPU: $CPU_INFO"
    else
        log_warning "未检测到AMD CPU"
    fi
    
    # 检测GPU
    if lspci | grep -i "radeon\|amd/ati" > /dev/null; then
        GPU_INFO=$(lspci | grep -i "radeon\|amd/ati" | head -1)
        log_success "检测到AMD GPU: $GPU_INFO"
    else
        log_warning "未检测到AMD GPU"
    fi
}

# 安装ROCm
install_rocm() {
    log_info "安装ROCm..."
    
    # 添加ROCm仓库
    wget https://repo.radeon.com/amdgpu-install/5.7/ubuntu/jammy/amdgpu-install_5.7.50700-1_all.deb
    sudo apt install ./amdgpu-install_5.7.50700-1_all.deb
    
    # 安装ROCm
    sudo amdgpu-install --usecase=rocm
    
    # 添加用户到render和video组
    sudo usermod -a -G render $USER
    sudo usermod -a -G video $USER
    
    log_success "ROCm安装完成"
}

# 配置ROCm环境
configure_rocm() {
    log_info "配置ROCm环境..."
    
    # 设置环境变量
    cat >> ~/.bashrc << 'EOF'

# ROCm 环境变量
export PATH=$PATH:/opt/rocm/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rocm/lib
export HIP_PLATFORM=amd
export HSA_OVERRIDE_GFX_VERSION=10.3.0
EOF
    
    # 创建ROCm配置文件
    sudo tee /etc/rocm.conf << 'EOF'
# ROCm 配置文件
rocm_version=5.7
rocm_path=/opt/rocm
EOF
    
    log_success "ROCm环境配置完成"
}

# 安装PyTorch with ROCm
install_pytorch_rocm() {
    log_info "安装PyTorch with ROCm支持..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装PyTorch with ROCm
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
    
    # 验证ROCm支持
    python3 -c "
import torch
print(f'PyTorch版本: {torch.__version__}')
print(f'ROCm可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU数量: {torch.cuda.device_count()}')
    print(f'GPU名称: {torch.cuda.get_device_name(0)}')
"
    
    log_success "PyTorch with ROCm安装完成"
}

# 优化AMD GPU性能
optimize_amd_gpu() {
    log_info "优化AMD GPU性能..."
    
    # 设置GPU性能模式
    echo 'performance' | sudo tee /sys/class/drm/card*/device/power_dpm_force_performance_level
    
    # 配置GPU内存
    echo 'gpu_mem=128' | sudo tee -a /boot/firmware/config.txt
    
    # 优化GPU调度
    echo 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amdgpu.dc=1 amdgpu.dpm=1"' | sudo tee -a /etc/default/grub
    sudo update-grub
    
    log_success "AMD GPU性能优化完成"
}

# 配置AI模型优化
configure_ai_optimization() {
    log_info "配置AI模型优化..."
    
    # 创建AI优化配置
    cat > config/ai/amd_optimization.json << 'EOF'
{
    "hardware": {
        "cpu": "AMD Ryzen 7 8845H",
        "gpu": "Radeon 780M",
        "rocm_version": "5.7"
    },
    "optimization": {
        "use_rocm": true,
        "gpu_memory_fraction": 0.8,
        "mixed_precision": true,
        "batch_size_optimization": true
    },
    "models": {
        "llama": {
            "use_gpu": true,
            "rocm_optimization": true,
            "memory_efficient": true
        },
        "whisper": {
            "use_gpu": true,
            "rocm_optimization": true
        },
        "embeddings": {
            "use_gpu": true,
            "rocm_optimization": true
        }
    }
}
EOF
    
    log_success "AI模型优化配置完成"
}

# 测试ROCm功能
test_rocm() {
    log_info "测试ROCm功能..."
    
    # 测试ROCm安装
    /opt/rocm/bin/rocminfo
    
    # 测试PyTorch ROCm支持
    python3 -c "
import torch
print('测试ROCm功能...')
if torch.cuda.is_available():
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    z = torch.mm(x, y)
    print('ROCm功能测试成功！')
else:
    print('ROCm功能测试失败！')
"
    
    log_success "ROCm功能测试完成"
}

# 主函数
main() {
    echo "=========================================="
    echo "AMD Ryzen 和 Radeon 优化配置"
    echo "=========================================="
    echo ""
    
    detect_amd_hardware
    install_rocm
    configure_rocm
    install_pytorch_rocm
    optimize_amd_gpu
    configure_ai_optimization
    test_rocm
    
    log_success "AMD硬件优化配置完成！"
    echo ""
    echo "请重新启动系统以确保所有配置生效。"
    echo "重启后，运行 'rocminfo' 验证ROCm安装。"
    echo ""
}

# 运行主函数
main "$@"
