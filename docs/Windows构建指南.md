# SonjayOS Windows构建指南

## 概述

本指南详细介绍了如何在Windows环境中构建SonjayOS自定义ISO镜像。

## 系统要求

- **操作系统**: Windows 10/11
- **内存**: 至少8GB RAM
- **磁盘空间**: 至少20GB可用空间
- **网络**: 稳定的互联网连接

## 必要工具安装

### 1. 安装7-Zip
1. 访问 [7-Zip官网](https://www.7-zip.org/)
2. 下载并安装7-Zip
3. 确保7-Zip添加到系统PATH环境变量

### 2. 安装xorriso
1. 访问 [xorriso官网](https://www.gnu.org/software/xorriso/)
2. 下载Windows版本的xorriso
3. 解压到任意目录（如 `C:\tools\xorriso\`）
4. 将xorriso目录添加到系统PATH环境变量

### 3. 验证安装
打开PowerShell，运行以下命令验证工具安装：

```powershell
# 检查7-Zip
7z

# 检查xorriso
xorriso -version
```

## 构建方法

### 方法1: 使用PowerShell脚本（推荐）

```powershell
# 进入SonjayOS项目目录
cd "D:\code\SonjayOS"

# 运行PowerShell构建脚本
.\build-iso.ps1

# 查看帮助信息
.\build-iso.ps1 -Help
```

### 方法2: 使用批处理脚本

```cmd
REM 进入SonjayOS项目目录
cd "D:\code\SonjayOS"

REM 运行批处理构建脚本
.\build-iso.bat
```

### 方法3: 手动构建

#### 步骤1: 准备环境
```powershell
# 创建构建目录
mkdir sonjayos-iso-build
cd sonjayos-iso-build

# 下载Ubuntu ISO
Invoke-WebRequest -Uri "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso" -OutFile "ubuntu-24.04-desktop-amd64.iso"
```

#### 步骤2: 提取ISO内容
```powershell
# 提取ISO内容
7z x ubuntu-24.04-desktop-amd64.iso -ocustom-iso
```

#### 步骤3: 添加SonjayOS文件
```powershell
# 创建SonjayOS目录
mkdir custom-iso\opt\sonjayos

# 复制SonjayOS文件
Copy-Item -Recurse -Path "..\*" -Destination "custom-iso\opt\sonjayos\" -Exclude "sonjayos-iso-build", "*.iso"
```

#### 步骤4: 创建自动安装配置
```powershell
# 创建server目录
mkdir custom-iso\server

# 创建user-data文件
$userData = @"
#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: sonjayos
    username: sonjayos
    password: `$6`$rounds=4096`$salt`$hash
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
"@

$userData | Out-File -FilePath "custom-iso\server\user-data" -Encoding UTF8

# 创建meta-data文件
$metaData = @"
instance-id: sonjayos-autoinstall
local-hostname: sonjayos
"@

$metaData | Out-File -FilePath "custom-iso\server\meta-data" -Encoding UTF8
```

#### 步骤5: 重新打包ISO
```powershell
# 进入提取目录
cd custom-iso

# 重新打包ISO
xorriso -as mkisofs -r -V "SonjayOS_Autoinstall" -o "..\sonjayos-1.0-alpha-amd64.iso" --grub2-mbr ../BOOT/1-Boot-NoEmul.img -partition_offset 16 --mbr-force-bootable -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b ../BOOT/2-Boot-NoEmul.img -appended_part_as_gpt -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 -c "/boot.catalog" -b "/boot/grub/i386-pc/eltorito.img" -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info -eltorito-alt-boot -e "--interval:appended_partition_2:::" -no-emul-boot .
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

## 故障排除

### 常见问题

#### 1. PowerShell执行策略问题
```powershell
# 设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或者临时绕过执行策略
PowerShell -ExecutionPolicy Bypass -File .\build-iso.ps1
```

#### 2. 路径包含空格问题
```powershell
# 使用引号括起路径
cd "D:\code\SonjayOS"

# 使用调用运算符
& "D:\code\SonjayOS\build-iso.ps1"
```

#### 3. 编码问题
```powershell
# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

#### 4. 工具未找到
- 确保7-Zip和xorriso已正确安装
- 检查PATH环境变量是否包含工具路径
- 重启PowerShell或命令提示符

#### 5. 网络下载失败
- 检查网络连接
- 使用代理设置（如果需要）
- 手动下载Ubuntu ISO文件

### 调试方法

#### 检查构建环境
```powershell
# 检查当前目录
Get-Location

# 检查必要文件
Test-Path "README.md"

# 检查工具安装
Get-Command 7z
Get-Command xorriso
```

#### 查看详细错误信息
```powershell
# 启用详细输出
$VerbosePreference = "Continue"
.\build-iso.ps1
```

## 性能优化

### 构建优化
- 使用SSD存储构建文件
- 确保有足够的磁盘空间
- 关闭不必要的程序释放内存

### 虚拟机优化
- 分配足够的内存（推荐16GB）
- 使用SSD存储虚拟机文件
- 启用硬件加速（如果支持）

## 总结

通过以上步骤，您可以在Windows环境中成功构建SonjayOS自定义ISO镜像。构建完成后，您将获得一个完整的、可启动的SonjayOS安装镜像，可以在VMware虚拟机中直接安装使用。

如有问题，请参考项目文档或提交Issue。
