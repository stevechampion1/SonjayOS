# SonjayOS ISO构建脚本 - PowerShell版本
# 用于在Windows PowerShell中构建SonjayOS自定义ISO

param(
    [switch]$Help
)

if ($Help) {
    Write-Host "SonjayOS ISO构建脚本" -ForegroundColor Green
    Write-Host "用法: .\build-iso.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "此脚本将构建包含SonjayOS的Ubuntu 24.04 LTS自定义ISO镜像"
    Write-Host "构建完成后，可在VMware中直接安装SonjayOS"
    exit 0
}

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SonjayOS ISO Builder - PowerShell Version" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查当前目录
if (-not (Test-Path "README.md")) {
    Write-Host "错误: 请在SonjayOS项目根目录中运行此脚本" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查必要工具
Write-Host "检查构建依赖..." -ForegroundColor Yellow

$tools = @("7z", "xorriso")
$missingTools = @()

foreach ($tool in $tools) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        $missingTools += $tool
    }
}

if ($missingTools.Count -gt 0) {
    Write-Host "错误: 以下工具未安装:" -ForegroundColor Red
    foreach ($tool in $missingTools) {
        Write-Host "  - $tool" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "请安装以下工具:" -ForegroundColor Yellow
    Write-Host "  - 7-Zip: https://www.7-zip.org/" -ForegroundColor Yellow
    Write-Host "  - xorriso: https://www.gnu.org/software/xorriso/" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "依赖检查完成" -ForegroundColor Green
Write-Host ""

# 设置变量
$UBUNTU_ISO = "ubuntu-24.04-desktop-amd64.iso"
$SONJAYOS_ISO = "sonjayos-1.0-alpha-amd64.iso"
$BUILD_DIR = "sonjayos-iso-build"
$EXTRACT_DIR = "custom-iso"

# 创建构建目录
Write-Host "准备构建环境..." -ForegroundColor Yellow
if (Test-Path $BUILD_DIR) {
    Remove-Item -Recurse -Force $BUILD_DIR
}
New-Item -ItemType Directory -Path $BUILD_DIR | Out-Null
Set-Location $BUILD_DIR

# 下载Ubuntu ISO（如果不存在）
if (-not (Test-Path "..\$UBUNTU_ISO")) {
    Write-Host "下载Ubuntu 24.04 LTS ISO..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso" -OutFile "..\$UBUNTU_ISO"
        Write-Host "Ubuntu ISO下载完成" -ForegroundColor Green
    }
    catch {
        Write-Host "错误: Ubuntu ISO下载失败" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
} else {
    Write-Host "Ubuntu ISO已存在，跳过下载" -ForegroundColor Green
}

# 提取ISO内容
Write-Host "提取Ubuntu ISO内容..." -ForegroundColor Yellow
try {
    & 7z x "..\$UBUNTU_ISO" -o"$EXTRACT_DIR" | Out-Null
    Write-Host "ISO内容提取完成" -ForegroundColor Green
}
catch {
    Write-Host "错误: ISO提取失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 添加SonjayOS文件
Write-Host "添加SonjayOS文件..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$EXTRACT_DIR\opt\sonjayos" -Force | Out-Null
Copy-Item -Recurse -Path "..\*" -Destination "$EXTRACT_DIR\opt\sonjayos\" -Exclude "sonjayos-iso-build", "*.iso"
Write-Host "SonjayOS文件添加完成" -ForegroundColor Green

# 创建自动安装配置
Write-Host "创建自动安装配置..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$EXTRACT_DIR\server" -Force | Out-Null

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

$userData | Out-File -FilePath "$EXTRACT_DIR\server\user-data" -Encoding UTF8

# 创建meta-data文件
$metaData = @"
instance-id: sonjayos-autoinstall
local-hostname: sonjayos
"@

$metaData | Out-File -FilePath "$EXTRACT_DIR\server\meta-data" -Encoding UTF8

Write-Host "自动安装配置创建完成" -ForegroundColor Green

# 重新打包ISO
Write-Host "重新打包ISO镜像..." -ForegroundColor Yellow
Set-Location $EXTRACT_DIR

try {
    & xorriso -as mkisofs -r -V "SonjayOS_Autoinstall" -o "..\$SONJAYOS_ISO" --grub2-mbr ../BOOT/1-Boot-NoEmul.img -partition_offset 16 --mbr-force-bootable -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b ../BOOT/2-Boot-NoEmul.img -appended_part_as_gpt -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 -c "/boot.catalog" -b "/boot/grub/i386-pc/eltorito.img" -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info -eltorito-alt-boot -e "--interval:appended_partition_2:::" -no-emul-boot .
    Write-Host "ISO镜像重新打包完成" -ForegroundColor Green
}
catch {
    Write-Host "错误: ISO重新打包失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Set-Location ..

# 验证ISO
if (Test-Path $SONJAYOS_ISO) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "SonjayOS ISO构建成功！" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "生成的ISO文件: $SONJAYOS_ISO" -ForegroundColor Yellow
    $isoSize = (Get-Item $SONJAYOS_ISO).Length / 1GB
    Write-Host "ISO大小: $([math]::Round($isoSize, 2)) GB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "使用方法：" -ForegroundColor Cyan
    Write-Host "1. 在VMware中创建新虚拟机" -ForegroundColor White
    Write-Host "2. 选择 '$SONJAYOS_ISO' 作为安装介质" -ForegroundColor White
    Write-Host "3. 启动虚拟机后选择 'Autoinstall SonjayOS'" -ForegroundColor White
    Write-Host "4. 系统将自动安装并配置SonjayOS" -ForegroundColor White
    Write-Host ""
    Write-Host "默认用户信息：" -ForegroundColor Cyan
    Write-Host "  用户名: sonjayos" -ForegroundColor White
    Write-Host "  密码: sonjayos" -ForegroundColor White
    Write-Host "  主机名: sonjayos" -ForegroundColor White
    Write-Host ""
    Write-Host "安装完成后，SonjayOS将自动启动。" -ForegroundColor Green
} else {
    Write-Host "错误: ISO创建失败" -ForegroundColor Red
}

# 清理构建环境
Write-Host ""
Write-Host "清理构建环境..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $EXTRACT_DIR
Write-Host "构建环境清理完成" -ForegroundColor Green

Write-Host ""
Write-Host "SonjayOS ISO构建完成！" -ForegroundColor Green
Read-Host "按回车键退出"
