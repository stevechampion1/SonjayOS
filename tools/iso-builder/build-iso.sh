#!/bin/bash
# SonjayOS ISO构建脚本
# 用于创建可启动的SonjayOS安装镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
ISO_NAME="SonjayOS-1.0.0"
ISO_VERSION="1.0.0"
ISO_ARCH="amd64"
WORK_DIR="/tmp/sonjayos-iso"
SOURCE_ISO="/tmp/ubuntu-24.04-desktop-amd64.iso"
MOUNT_DIR="/tmp/ubuntu-mount"
EXTRACT_DIR="/tmp/ubuntu-extract"

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

# 检查依赖
check_dependencies() {
    log_info "检查构建依赖..."
    
    # 检查必要的工具
    for tool in wget xorriso isohybrid; do
        if ! command -v $tool &> /dev/null; then
            log_error "缺少必要工具: $tool"
            exit 1
        fi
    done
    
    # 安装缺失的包
    apt update
    apt install -y \
        xorriso \
        isohybrid \
        syslinux-utils \
        squashfs-tools \
        genisoimage \
        wimtools \
        p7zip-full
    
    log_success "依赖检查完成"
}

# 下载Ubuntu ISO
download_ubuntu_iso() {
    log_info "下载Ubuntu 24.04 LTS ISO..."
    
    if [ ! -f "$SOURCE_ISO" ]; then
        wget -O "$SOURCE_ISO" \
            "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso"
    else
        log_info "Ubuntu ISO已存在，跳过下载"
    fi
    
    log_success "Ubuntu ISO下载完成"
}

# 创建构建目录
create_build_directories() {
    log_info "创建构建目录..."
    
    # 清理旧目录
    rm -rf "$WORK_DIR" "$MOUNT_DIR" "$EXTRACT_DIR"
    
    # 创建新目录
    mkdir -p "$WORK_DIR" "$MOUNT_DIR" "$EXTRACT_DIR"
    
    log_success "构建目录创建完成"
}

# 挂载和提取ISO
extract_iso() {
    log_info "提取Ubuntu ISO..."
    
    # 挂载ISO
    mount -o loop "$SOURCE_ISO" "$MOUNT_DIR"
    
    # 复制所有文件
    cp -r "$MOUNT_DIR"/* "$EXTRACT_DIR/"
    
    # 复制隐藏文件
    cp -r "$MOUNT_DIR"/.disk "$EXTRACT_DIR/"
    
    # 卸载ISO
    umount "$MOUNT_DIR"
    
    log_success "ISO提取完成"
}

# 安装SonjayOS组件
install_sonjayos_components() {
    log_info "安装SonjayOS组件..."
    
    # 创建chroot环境
    mount --bind /proc "$EXTRACT_DIR/proc"
    mount --bind /sys "$EXTRACT_DIR/sys"
    mount --bind /dev "$EXTRACT_DIR/dev"
    
    # 复制SonjayOS文件
    cp -r ../.. "$EXTRACT_DIR/opt/sonjayos"
    
    # 创建安装脚本
    cat > "$EXTRACT_DIR/opt/sonjayos/install.sh" << 'EOF'
#!/bin/bash
# SonjayOS自动安装脚本

set -e

echo "开始安装SonjayOS..."

# 检查系统
if [ ! -f /etc/os-release ]; then
    echo "错误: 无法检测操作系统"
    exit 1
fi

# 安装依赖
apt update
apt install -y python3 python3-pip python3-venv nodejs npm git curl wget

# 创建用户
useradd -m -s /bin/bash sonjayos

# 复制文件
cp -r /opt/sonjayos /home/sonjayos/
chown -R sonjayos:sonjayos /home/sonjayos/sonjayos

# 安装Python依赖
cd /home/sonjayos/sonjayos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置服务
cp scripts/install.sh /tmp/sonjayos-install.sh
chmod +x /tmp/sonjayos-install.sh

echo "SonjayOS安装完成"
EOF
    
    chmod +x "$EXTRACT_DIR/opt/sonjayos/install.sh"
    
    # 修改启动脚本
    cat > "$EXTRACT_DIR/usr/share/gnome-session/sessions/sonjayos.session" << 'EOF'
[GNOME Session]
Name=SonjayOS
RequiredComponents=gnome-shell;gnome-settings-daemon;
RequiredProviders=windowmanager;notifications;
DefaultProvider-windowmanager=gnome-shell
DefaultProvider-notifications=gnome-shell
EOF
    
    # 创建自定义启动器
    cat > "$EXTRACT_DIR/usr/share/applications/sonjayos-install.desktop" << 'EOF'
[Desktop Entry]
Name=安装SonjayOS
Comment=安装SonjayOS AI集成操作系统
Exec=/opt/sonjayos/install.sh
Icon=sonjayos
Terminal=true
Type=Application
Categories=System;
EOF
    
    # 复制图标
    cp src/ui/icons/sonjayos.png "$EXTRACT_DIR/usr/share/pixmaps/"
    
    log_success "SonjayOS组件安装完成"
}

# 配置启动选项
configure_boot_options() {
    log_info "配置启动选项..."
    
    # 修改GRUB配置
    cat > "$EXTRACT_DIR/boot/grub/grub.cfg" << 'EOF'
set timeout=10
set default=0

menuentry "SonjayOS Live" {
    set gfxpayload=keep
    linux   /casper/vmlinuz quiet splash ---
    initrd  /casper/initrd
}

menuentry "SonjayOS Install" {
    set gfxpayload=keep
    linux   /casper/vmlinuz quiet splash autoinstall ds=nocloud-net;s=http://_gateway:3003/ ---
    initrd  /casper/initrd
}

menuentry "SonjayOS Safe Mode" {
    set gfxpayload=keep
    linux   /casper/vmlinuz quiet splash nomodeset ---
    initrd  /casper/initrd
}
EOF
    
    # 修改isolinux配置
    cat > "$EXTRACT_DIR/isolinux/txt.cfg" << 'EOF'
default live
label live
  menu label ^SonjayOS Live
  kernel /casper/vmlinuz
  append  file=/cdrom/preseed/ubuntu.seed boot=casper initrd=/casper/initrd quiet splash ---
label install
  menu label ^Install SonjayOS
  kernel /casper/vmlinuz
  append  file=/cdrom/preseed/ubuntu.seed boot=casper only-ubiquity initrd=/casper/initrd quiet splash ---
label check
  menu label ^Check CD for defects
  kernel /casper/vmlinuz
  append  boot=casper integrity-check initrd=/casper/initrd quiet splash ---
label memtest
  menu label ^Memory test
  kernel /install/mt86plus
  append -
label hd
  menu label ^Boot from first hard disk
  localboot 0x80
EOF
    
    log_success "启动选项配置完成"
}

# 创建预配置
create_preseed_config() {
    log_info "创建预配置..."
    
    mkdir -p "$EXTRACT_DIR/preseed"
    
    cat > "$EXTRACT_DIR/preseed/ubuntu.seed" << 'EOF'
# SonjayOS预配置
d-i debian-installer/language string zh_CN
d-i debian-installer/country string CN
d-i debian-installer/locale string zh_CN.UTF-8
d-i keyboard-configuration/layoutcode string us
d-i keyboard-configuration/variantcode string

# 网络配置
d-i netcfg/choose_interface select auto
d-i netcfg/get_hostname string sonjayos
d-i netcfg/get_domain string local

# 用户配置
d-i passwd/user-fullname string SonjayOS User
d-i passwd/username string sonjayos
d-i passwd/user-password-crypted password $6$rounds=4096$salt$hash
d-i passwd/user-password-again string sonjayos
d-i user-setup/allow-password-weak boolean true
d-i user-setup/encrypt-home boolean false

# 分区配置
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true

# 软件包选择
tasksel tasksel/first multiselect standard
d-i pkgsel/include string sonjayos-core
d-i pkgsel/upgrade select none
d-i pkgsel/update-policy select none

# 引导加载程序
d-i grub-installer/only_debian boolean true
d-i grub-installer/with_other_os boolean true
d-i finish-install/reboot_in_progress note
EOF
    
    log_success "预配置创建完成"
}

# 创建自定义软件包
create_custom_packages() {
    log_info "创建自定义软件包..."
    
    # 创建SonjayOS核心包
    mkdir -p "$EXTRACT_DIR/pool/main/s/sonjayos"
    
    # 创建控制文件
    cat > "$EXTRACT_DIR/pool/main/s/sonjayos/control" << 'EOF'
Package: sonjayos-core
Version: 1.0.0
Section: metapackages
Priority: optional
Architecture: all
Depends: python3, python3-pip, nodejs, npm, git, curl, wget
Maintainer: SonjayOS Team <team@sonjayos.com>
Description: SonjayOS AI集成操作系统核心组件
 SonjayOS是一个基于Ubuntu的AI集成操作系统，
 提供智能助手、语音识别、语义搜索等功能。
EOF
    
    # 创建软件包描述
    cat > "$EXTRACT_DIR/pool/main/s/sonjayos/description" << 'EOF'
SonjayOS AI集成操作系统
=======================

SonjayOS是一个革命性的AI集成操作系统，基于Ubuntu 24.04 LTS构建。

主要功能：
- AI驱动的智能助手
- 自然语言语音交互
- 语义文件搜索
- 自适应用户界面
- AI安全威胁检测
- 智能系统优化

系统要求：
- AMD Ryzen 7 8845H或更高
- 32GB RAM（推荐）
- 500GB存储空间
- Radeon 780M或更高显卡

安装后请运行 /opt/sonjayos/install.sh 完成配置。
EOF
    
    log_success "自定义软件包创建完成"
}

# 重新生成文件列表
regenerate_file_lists() {
    log_info "重新生成文件列表..."
    
    # 重新生成md5sum
    cd "$EXTRACT_DIR"
    find . -type f -print0 | xargs -0 md5sum > md5sum.txt
    
    # 重新生成文件大小
    find . -type f -exec wc -c {} + | tail -1 | awk '{print $1}' > filesystem.size
    
    log_success "文件列表重新生成完成"
}

# 构建ISO
build_iso() {
    log_info "构建SonjayOS ISO..."
    
    # 创建ISO
    xorriso -as mkisofs \
        -iso-level 3 \
        -full-iso9660-filenames \
        -volid "SonjayOS $ISO_VERSION" \
        -appid "SonjayOS $ISO_VERSION" \
        -publisher "SonjayOS Team" \
        -preparer "SonjayOS ISO Builder" \
        -eltorito-boot isolinux/isolinux.bin \
        -eltorito-catalog isolinux/boot.cat \
        -no-emul-boot \
        -boot-load-size 4 \
        -boot-info-table \
        -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
        -output "$ISO_NAME.iso" \
        "$EXTRACT_DIR"
    
    # 使ISO可启动
    isohybrid "$ISO_NAME.iso"
    
    log_success "SonjayOS ISO构建完成: $ISO_NAME.iso"
}

# 验证ISO
verify_iso() {
    log_info "验证ISO文件..."
    
    if [ -f "$ISO_NAME.iso" ]; then
        # 检查文件大小
        size=$(du -h "$ISO_NAME.iso" | cut -f1)
        log_info "ISO文件大小: $size"
        
        # 检查ISO结构
        if file "$ISO_NAME.iso" | grep -q "ISO 9660"; then
            log_success "ISO文件验证通过"
        else
            log_error "ISO文件验证失败"
            exit 1
        fi
    else
        log_error "ISO文件不存在"
        exit 1
    fi
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    
    # 卸载绑定挂载
    umount "$EXTRACT_DIR/proc" 2>/dev/null || true
    umount "$EXTRACT_DIR/sys" 2>/dev/null || true
    umount "$EXTRACT_DIR/dev" 2>/dev/null || true
    
    # 删除临时目录
    rm -rf "$WORK_DIR" "$MOUNT_DIR" "$EXTRACT_DIR"
    
    log_success "清理完成"
}

# 显示构建信息
show_build_info() {
    log_success "SonjayOS ISO构建完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS ISO构建信息"
    echo "=========================================="
    echo ""
    echo "ISO文件: $ISO_NAME.iso"
    echo "版本: $ISO_VERSION"
    echo "架构: $ISO_ARCH"
    echo "大小: $(du -h "$ISO_NAME.iso" | cut -f1)"
    echo ""
    echo "使用方法:"
    echo "1. 将ISO文件写入USB驱动器"
    echo "2. 从USB启动计算机"
    echo "3. 选择'Install SonjayOS'进行安装"
    echo "4. 按照安装向导完成配置"
    echo ""
    echo "系统要求:"
    echo "- AMD Ryzen 7 8845H或更高"
    echo "- 32GB RAM（推荐）"
    echo "- 500GB存储空间"
    echo "- Radeon 780M或更高显卡"
    echo ""
}

# 主构建流程
main() {
    echo "=========================================="
    echo "SonjayOS ISO构建程序"
    echo "=========================================="
    echo ""
    
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root权限运行此脚本"
        exit 1
    fi
    
    # 执行构建步骤
    check_dependencies
    download_ubuntu_iso
    create_build_directories
    extract_iso
    install_sonjayos_components
    configure_boot_options
    create_preseed_config
    create_custom_packages
    regenerate_file_lists
    build_iso
    verify_iso
    cleanup
    show_build_info
    
    log_success "构建完成！"
}

# 运行主函数
main "$@"
