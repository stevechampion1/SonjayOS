#!/bin/bash
# SonjayOS 自定义ISO构建脚本
# 用于创建包含SonjayOS的Ubuntu 24.04 LTS自定义ISO镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[ISO-BUILD-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[ISO-BUILD-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[ISO-BUILD-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ISO-BUILD-ERROR]${NC} $1"
}

# 配置变量
UBUNTU_ISO="ubuntu-24.04-desktop-amd64.iso"
SONJAYOS_ISO="sonjayos-1.0-alpha-amd64.iso"
BUILD_DIR="sonjayos-iso-build"
EXTRACT_DIR="custom-iso"
PROJECT_ROOT="$(pwd)"

# 检查依赖
check_dependencies() {
    log_info "检查构建依赖..."
    
    # 检查必要工具
    for tool in xorriso vim wget p7zip-full; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool 未安装，正在安装..."
            sudo apt update
            sudo apt install -y $tool
        fi
    done
    
    log_success "依赖检查完成"
}

# 下载Ubuntu ISO
download_ubuntu_iso() {
    log_info "下载Ubuntu 24.04 LTS ISO..."
    
    if [ ! -f "$UBUNTU_ISO" ]; then
        wget -O "$UBUNTU_ISO" "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso"
        log_success "Ubuntu ISO下载完成"
    else
        log_info "Ubuntu ISO已存在，跳过下载"
    fi
}

# 准备构建环境
prepare_build_environment() {
    log_info "准备构建环境..."
    
    # 创建构建目录
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # 清理之前的构建
    rm -rf "$EXTRACT_DIR"
    
    log_success "构建环境准备完成"
}

# 提取ISO内容
extract_iso() {
    log_info "提取Ubuntu ISO内容..."
    
    # 使用7zip提取ISO
    p7zip -d "$UBUNTU_ISO"
    
    # 挂载ISO并复制内容
    sudo mkdir -p /mnt/iso
    sudo mount -o loop "$UBUNTU_ISO" /mnt/iso
    cp -r /mnt/iso/* "$EXTRACT_DIR/"
    sudo umount /mnt/iso
    
    log_success "ISO内容提取完成"
}

# 添加SonjayOS文件
add_sonjayos_files() {
    log_info "添加SonjayOS文件..."
    
    # 创建SonjayOS目录
    sudo mkdir -p "$EXTRACT_DIR/opt/sonjayos"
    
    # 复制SonjayOS项目文件
    sudo cp -r "$PROJECT_ROOT"/* "$EXTRACT_DIR/opt/sonjayos/"
    
    # 设置权限
    sudo chown -R root:root "$EXTRACT_DIR/opt/sonjayos"
    sudo chmod -R 755 "$EXTRACT_DIR/opt/sonjayos"
    
    # 设置脚本执行权限
    sudo chmod +x "$EXTRACT_DIR/opt/sonjayos/scripts"/*.sh
    sudo chmod +x "$EXTRACT_DIR/opt/sonjayos/tools/iso-builder"/*.sh
    
    log_success "SonjayOS文件添加完成"
}

# 创建自动安装配置
create_autoinstall_config() {
    log_info "创建自动安装配置..."
    
    # 创建server目录
    mkdir -p "$EXTRACT_DIR/server"
    
    # 创建user-data文件
    cat > "$EXTRACT_DIR/server/user-data" << 'EOF'
#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: sonjayos
    username: sonjayos
    password: $6$rounds=4096$salt$hash
    realname: SonjayOS User
  locale: zh_CN.UTF-8
  keyboard:
    layout: cn
  network:
    network:
      version: 2
      ethernets:
        eth0:
          dhcp4: true
  packages:
    - build-essential
    - python3
    - python3-pip
    - python3-venv
    - python3-dev
    - git
    - curl
    - wget
    - vim
    - htop
    - tree
    - software-properties-common
    - apt-transport-https
    - ca-certificates
    - gnupg
    - lsb-release
  late-commands:
    - curtin in-target -- cp -r /cdrom/opt/sonjayos /opt/
    - curtin in-target -- chown -R sonjayos:sonjayos /opt/sonjayos
    - curtin in-target -- chmod +x /opt/sonjayos/scripts/*.sh
    - curtin in-target -- chmod +x /opt/sonjayos/tools/iso-builder/*.sh
    - curtin in-target -- /opt/sonjayos/scripts/install.sh
    - curtin in-target -- systemctl enable sonjayos-ai-scheduler.service
    - curtin in-target -- systemctl enable sonjayos-ai-security.service
EOF

    # 创建meta-data文件
    cat > "$EXTRACT_DIR/server/meta-data" << 'EOF'
instance-id: sonjayos-autoinstall
local-hostname: sonjayos
EOF

    log_success "自动安装配置创建完成"
}

# 修改GRUB配置
modify_grub_config() {
    log_info "修改GRUB配置..."
    
    # 备份原始配置
    cp "$EXTRACT_DIR/boot/grub/grub.cfg" "$EXTRACT_DIR/boot/grub/grub.cfg.backup"
    
    # 添加SonjayOS自动安装菜单项
    cat > /tmp/grub_entry.txt << 'EOF'
menuentry "Autoinstall SonjayOS" {
    set gfxpayload=keep
    linux   /casper/vmlinuz quiet autoinstall ds=nocloud-net\;s=/cdrom/server/ ---
    initrd  /casper/initrd
}
EOF

    # 在现有菜单项前插入新菜单项
    sed -i '/menuentry "Try or Install Ubuntu"/i\
menuentry "Autoinstall SonjayOS" {\
    set gfxpayload=keep\
    linux   /casper/vmlinuz quiet autoinstall ds=nocloud-net\\;s=/cdrom/server/ ---\
    initrd  /casper/initrd\
}' "$EXTRACT_DIR/boot/grub/grub.cfg"

    log_success "GRUB配置修改完成"
}

# 创建安装后脚本
create_post_install_script() {
    log_info "创建安装后脚本..."
    
    cat > "$EXTRACT_DIR/opt/sonjayos/scripts/post-install.sh" << 'EOF'
#!/bin/bash
# SonjayOS 安装后配置脚本

set -e

echo "配置SonjayOS安装后设置..."

# 设置环境变量
cat >> /home/sonjayos/.bashrc << 'BASHRC_EOF'

# SonjayOS 环境变量
export SONJAYOS_HOME="/opt/sonjayos"
export PATH="$SONJAYOS_HOME/scripts:$PATH"
export PYTHONPATH="$SONJAYOS_HOME/src:$PYTHONPATH"

# SonjayOS 别名
alias sonjayos='cd $SONJAYOS_HOME'
alias sonjayos-dev='cd $SONJAYOS_HOME && source venv/bin/activate'
alias sonjayos-start='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh start'
alias sonjayos-stop='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh stop'
alias sonjayos-status='cd $SONJAYOS_HOME && ./scripts/dev-mode.sh status'
BASHRC_EOF

# 创建桌面快捷方式
cat > /home/sonjayos/Desktop/SonjayOS.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Name=SonjayOS
Comment=AI Integrated Operating System
Exec=gnome-terminal -- bash -c "cd /opt/sonjayos && python3 sonjayos_terminal.py; exec bash"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;Utility;
DESKTOP_EOF

chmod +x /home/sonjayos/Desktop/SonjayOS.desktop

# 设置自动启动
mkdir -p /home/sonjayos/.config/autostart
cat > /home/sonjayos/.config/autostart/sonjayos.desktop << 'AUTOSTART_EOF'
[Desktop Entry]
Type=Application
Name=SonjayOS
Exec=/opt/sonjayos/scripts/dev-mode.sh start
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
AUTOSTART_EOF

echo "SonjayOS安装后配置完成！"
echo "请重新启动系统以完成安装。"
EOF

    chmod +x "$EXTRACT_DIR/opt/sonjayos/scripts/post-install.sh"
    
    log_success "安装后脚本创建完成"
}

# 重新打包ISO
repack_iso() {
    log_info "重新打包ISO镜像..."
    
    cd "$EXTRACT_DIR"
    
    # 使用xorriso重新创建ISO
    xorriso -as mkisofs -r \
        -V 'SonjayOS_Autoinstall' \
        -o "../$SONJAYOS_ISO" \
        --grub2-mbr ../BOOT/1-Boot-NoEmul.img \
        -partition_offset 16 \
        --mbr-force-bootable \
        -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b ../BOOT/2-Boot-NoEmul.img \
        -appended_part_as_gpt \
        -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 \
        -c '/boot.catalog' \
        -b '/boot/grub/i386-pc/eltorito.img' \
        -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
        -eltorito-alt-boot \
        -e '--interval:appended_partition_2:::' \
        -no-emul-boot \
        .
    
    cd ..
    
    log_success "ISO镜像重新打包完成"
}

# 验证ISO
verify_iso() {
    log_info "验证生成的ISO..."
    
    if [ -f "$SONJAYOS_ISO" ]; then
        log_success "SonjayOS ISO创建成功: $SONJAYOS_ISO"
        log_info "ISO大小: $(du -h "$SONJAYOS_ISO" | cut -f1)"
        log_info "ISO MD5: $(md5sum "$SONJAYOS_ISO" | cut -d' ' -f1)"
    else
        log_error "ISO创建失败"
        exit 1
    fi
}

# 清理构建环境
cleanup() {
    log_info "清理构建环境..."
    
    # 清理临时文件
    rm -rf "$EXTRACT_DIR"
    
    log_success "构建环境清理完成"
}

# 显示使用说明
show_usage() {
    echo "SonjayOS ISO构建完成！"
    echo ""
    echo "使用方法："
    echo "1. 在VMware中创建新虚拟机"
    echo "2. 选择 '$SONJAYOS_ISO' 作为安装介质"
    echo "3. 启动虚拟机后选择 'Autoinstall SonjayOS'"
    echo "4. 系统将自动安装并配置SonjayOS"
    echo ""
    echo "默认用户信息："
    echo "  用户名: sonjayos"
    echo "  密码: sonjayos"
    echo "  主机名: sonjayos"
    echo ""
    echo "安装完成后，SonjayOS将自动启动。"
}

# 主函数
main() {
    echo "=========================================="
    echo "SonjayOS 自定义ISO构建器"
    echo "=========================================="
    echo ""
    
    check_dependencies
    download_ubuntu_iso
    prepare_build_environment
    extract_iso
    add_sonjayos_files
    create_autoinstall_config
    modify_grub_config
    create_post_install_script
    repack_iso
    verify_iso
    cleanup
    show_usage
    
    log_success "SonjayOS ISO构建完成！"
}

# 运行主函数
main "$@"
