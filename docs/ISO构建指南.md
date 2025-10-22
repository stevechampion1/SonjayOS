# SonjayOS ISO构建指南

## 概述

本指南详细介绍了如何构建包含SonjayOS的自定义Ubuntu 24.04 LTS ISO镜像，以便在VMware虚拟机中直接安装。

## 准备工作

### 系统要求
- **操作系统**: Ubuntu 20.04+ 或 Windows 10/11
- **内存**: 至少8GB RAM
- **磁盘空间**: 至少20GB可用空间
- **网络**: 稳定的互联网连接

### 必要工具

#### Ubuntu/Linux环境
```bash
sudo apt update
sudo apt install -y xorriso vim wget p7zip-full
```

#### Windows环境
- **7-Zip**: 下载并安装 [7-Zip](https://www.7-zip.org/)
- **xorriso**: 下载并安装 [xorriso](https://www.gnu.org/software/xorriso/)

## 构建方法

### 方法1: 使用Linux脚本（推荐）

```bash
# 进入项目目录
cd /path/to/SonjayOS

# 运行构建脚本
./tools/iso-builder/build-sonjayos-iso.sh
```

### 方法2: 使用Windows脚本

```cmd
REM 进入项目目录
cd D:\code\SonjayOS

REM 运行构建脚本
tools\iso-builder\build-iso-windows.bat
```

### 方法3: 手动构建

#### 步骤1: 下载Ubuntu ISO
```bash
wget https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso
```

#### 步骤2: 提取ISO内容
```bash
mkdir custom-iso
7z x ubuntu-24.04-desktop-amd64.iso -ocustom-iso
```

#### 步骤3: 添加SonjayOS文件
```bash
sudo mkdir -p custom-iso/opt/sonjayos
sudo cp -r /path/to/SonjayOS/* custom-iso/opt/sonjayos/
sudo chown -R root:root custom-iso/opt/sonjayos
sudo chmod -R 755 custom-iso/opt/sonjayos
```

#### 步骤4: 创建自动安装配置
```bash
mkdir custom-iso/server

# 创建user-data文件
cat > custom-iso/server/user-data << 'EOF'
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
cat > custom-iso/server/meta-data << 'EOF'
instance-id: sonjayos-autoinstall
local-hostname: sonjayos
EOF
```

#### 步骤5: 修改GRUB配置
```bash
# 备份原始配置
cp custom-iso/boot/grub/grub.cfg custom-iso/boot/grub/grub.cfg.backup

# 添加SonjayOS自动安装菜单项
sed -i '/menuentry "Try or Install Ubuntu"/i\
menuentry "Autoinstall SonjayOS" {\
    set gfxpayload=keep\
    linux   /casper/vmlinuz quiet autoinstall ds=nocloud-net\\;s=/cdrom/server/ ---\
    initrd  /casper/initrd\
}' custom-iso/boot/grub/grub.cfg
```

#### 步骤6: 重新打包ISO
```bash
cd custom-iso
xorriso -as mkisofs -r \
    -V 'SonjayOS_Autoinstall' \
    -o ../sonjayos-1.0-alpha-amd64.iso \
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
```

## 在VMware中安装

### 创建虚拟机
1. 打开VMware Workstation/Player
2. 创建新虚拟机
3. 选择"自定义(高级)"
4. 选择"稍后安装操作系统"
5. 选择"Linux" -> "Ubuntu 64位"
6. 设置虚拟机名称: "SonjayOS"
7. 设置内存: 至少8GB（推荐16GB）
8. 设置磁盘: 至少50GB
9. 完成虚拟机创建

### 配置虚拟机
1. 编辑虚拟机设置
2. 选择"CD/DVD"设备
3. 选择"使用ISO镜像文件"
4. 浏览并选择生成的`sonjayos-1.0-alpha-amd64.iso`
5. 确保"启动时连接"已勾选

### 安装SonjayOS
1. 启动虚拟机
2. 在GRUB菜单中选择"Autoinstall SonjayOS"
3. 系统将自动安装并配置SonjayOS
4. 安装完成后，系统将自动重启
5. 使用默认凭据登录:
   - 用户名: `sonjayos`
   - 密码: `sonjayos`

## 安装后配置

### 首次启动
安装完成后，SonjayOS将自动启动以下服务:
- AI调度器服务
- AI安全系统
- 自适应主题系统
- 性能监控系统

### 验证安装
```bash
# 检查服务状态
systemctl status sonjayos-ai-scheduler
systemctl status sonjayos-ai-security

# 检查SonjayOS项目
ls -la /opt/sonjayos

# 启动SonjayOS界面
cd /opt/sonjayos
python3 sonjayos_terminal.py
```

### 自定义配置
```bash
# 编辑配置文件
sudo nano /opt/sonjayos/config/ubuntu/sonjayos_config.json

# 重启服务
sudo systemctl restart sonjayos-ai-scheduler
sudo systemctl restart sonjayos-ai-security
```

## 故障排除

### 常见问题

#### 1. ISO构建失败
- 检查磁盘空间是否足够
- 确保所有依赖工具已安装
- 检查网络连接

#### 2. 自动安装失败
- 检查user-data文件格式
- 确保所有路径正确
- 查看安装日志

#### 3. 服务启动失败
- 检查Python环境
- 查看服务日志
- 手动启动服务进行调试

### 调试方法
```bash
# 查看系统日志
journalctl -u sonjayos-ai-scheduler
journalctl -u sonjayos-ai-security

# 手动启动服务
cd /opt/sonjayos
./scripts/dev-mode.sh start

# 检查配置文件
python3 -c "import json; print(json.load(open('config/ubuntu/sonjayos_config.json')))"
```

## 性能优化

### 虚拟机设置
- **内存**: 推荐16GB或更多
- **CPU**: 推荐8核心或更多
- **磁盘**: 使用SSD，至少50GB
- **网络**: 使用NAT或桥接模式

### 系统优化
```bash
# 启用硬件加速
sudo apt install mesa-vulkan-drivers

# 优化内存使用
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 总结

通过以上步骤，您可以成功构建包含SonjayOS的自定义ISO镜像，并在VMware虚拟机中直接安装。安装完成后，您将拥有一个完整的AI集成操作系统，具备所有SonjayOS的功能和特性。

如有问题，请参考项目文档或提交Issue。
