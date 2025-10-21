# SonjayOS Windows 11 开发环境自动设置脚本
# PowerShell脚本，用于在Windows 11上自动设置SonjayOS开发环境

param(
    [string]$Method = "WSL2",
    [switch]$Force = $false,
    [switch]$Help = $false
)

# 颜色定义
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$White = "White"

# 日志函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# 显示帮助信息
function Show-Help {
    Write-Host "SonjayOS Windows 11 开发环境设置脚本" -ForegroundColor $Green
    Write-Host ""
    Write-Host "用法: .\windows-dev-setup.ps1 [-Method <WSL2|Docker|VirtualBox>] [-Force] [-Help]"
    Write-Host ""
    Write-Host "参数:"
    Write-Host "  -Method    设置方法 (WSL2|Docker|VirtualBox) 默认: WSL2"
    Write-Host "  -Force     强制重新安装"
    Write-Host "  -Help      显示帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\windows-dev-setup.ps1                    # 使用WSL2方法"
    Write-Host "  .\windows-dev-setup.ps1 -Method Docker     # 使用Docker方法"
    Write-Host "  .\windows-dev-setup.ps1 -Force             # 强制重新安装"
}

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 检查系统要求
function Test-SystemRequirements {
    Write-Info "检查系统要求..."
    
    # 检查Windows版本
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -lt 10 -or ($osVersion.Major -eq 10 -and $osVersion.Build -lt 22000)) {
        Write-Error "需要Windows 11 (版本 22H2 或更高)"
        return $false
    }
    
    # 检查内存
    $memory = Get-WmiObject -Class Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
    $memoryGB = [math]::Round($memory / 1GB, 2)
    if ($memoryGB -lt 16) {
        Write-Warning "推荐至少16GB内存，当前: ${memoryGB}GB"
    }
    
    # 检查磁盘空间
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    if ($freeSpaceGB -lt 100) {
        Write-Warning "推荐至少100GB可用磁盘空间，当前: ${freeSpaceGB}GB"
    }
    
    Write-Success "系统要求检查完成"
    return $true
}

# 设置WSL2方法
function Setup-WSL2 {
    Write-Info "设置WSL2开发环境..."
    
    # 启用WSL功能
    Write-Info "启用WSL功能..."
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    
    # 下载并安装WSL2内核更新
    Write-Info "下载WSL2内核更新..."
    $wslUpdateUrl = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    $wslUpdatePath = "$env:TEMP\wsl_update_x64.msi"
    Invoke-WebRequest -Uri $wslUpdateUrl -OutFile $wslUpdatePath
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $wslUpdatePath /quiet" -Wait
    
    # 设置WSL2为默认版本
    Write-Info "设置WSL2为默认版本..."
    wsl --set-default-version 2
    
    # 安装Ubuntu 24.04 LTS
    Write-Info "安装Ubuntu 24.04 LTS..."
    wsl --install -d Ubuntu-24.04
    
    # 等待用户完成Ubuntu初始设置
    Write-Warning "请完成Ubuntu初始设置，然后按任意键继续..."
    Read-Host
    
    # 配置Ubuntu环境
    Write-Info "配置Ubuntu环境..."
    wsl -d Ubuntu-24.04 -e bash -c "
        sudo apt update && sudo apt upgrade -y
        sudo apt install -y build-essential python3.11 python3.11-pip python3.11-venv python3.11-dev nodejs npm git curl wget unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
    "
    
    # 克隆项目
    Write-Info "克隆SonjayOS项目..."
    wsl -d Ubuntu-24.04 -e bash -c "
        cd ~
        git clone https://github.com/sonjayos/sonjayos.git
        cd sonjayos
        chmod +x scripts/*.sh
        chmod +x tools/iso-builder/*.sh
    "
    
    # 设置Python环境
    Write-Info "设置Python环境..."
    wsl -d Ubuntu-24.04 -e bash -c "
        cd ~/sonjayos
        python3.11 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit isort bandit safety memory-profiler line-profiler py-spy watchdog
    "
    
    Write-Success "WSL2开发环境设置完成！"
    Write-Info "使用方法:"
    Write-Host "  wsl -d Ubuntu-24.04" -ForegroundColor $Yellow
    Write-Host "  cd ~/sonjayos" -ForegroundColor $Yellow
    Write-Host "  ./scripts/dev-mode.sh start" -ForegroundColor $Yellow
}

# 设置Docker方法
function Setup-Docker {
    Write-Info "设置Docker开发环境..."
    
    # 检查Docker Desktop是否已安装
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Info "下载Docker Desktop..."
        $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $dockerPath = "$env:TEMP\DockerDesktopInstaller.exe"
        Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerPath
        
        Write-Info "安装Docker Desktop..."
        Start-Process -FilePath $dockerPath -ArgumentList "install" -Wait
        
        Write-Warning "请启动Docker Desktop并完成初始设置，然后按任意键继续..."
        Read-Host
    }
    
    # 创建Dockerfile
    Write-Info "创建Dockerfile..."
    $dockerfile = @"
FROM ubuntu:24.04

# 安装基础依赖
RUN apt update && apt install -y \
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

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install -r requirements.txt

# 设置权限
RUN chmod +x scripts/*.sh

# 暴露端口
EXPOSE 8000 8001 8002

# 启动命令
CMD ["./scripts/dev-mode.sh", "start"]
"@
    
    $dockerfile | Out-File -FilePath "Dockerfile" -Encoding UTF8
    
    # 创建docker-compose.yml
    Write-Info "创建docker-compose.yml..."
    $dockerCompose = @"
version: '3.8'

services:
  sonjayos-dev:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
      - "8002:8002"
    volumes:
      - .:/app
      - /app/venv
    environment:
      - SONJAYOS_DEV_MODE=true
      - SONJAYOS_DEBUG_LEVEL=DEBUG
      - SONJAYOS_HOT_RELOAD=true
      - SONJAYOS_MOCK_AI=true
    stdin_open: true
    tty: true
"@
    
    $dockerCompose | Out-File -FilePath "docker-compose.yml" -Encoding UTF8
    
    # 构建并启动容器
    Write-Info "构建并启动Docker容器..."
    docker-compose up --build -d
    
    Write-Success "Docker开发环境设置完成！"
    Write-Info "使用方法:"
    Write-Host "  docker-compose exec sonjayos-dev bash" -ForegroundColor $Yellow
    Write-Host "  ./scripts/dev-mode.sh start" -ForegroundColor $Yellow
}

# 设置VirtualBox方法
function Setup-VirtualBox {
    Write-Info "设置VirtualBox开发环境..."
    
    # 检查VirtualBox是否已安装
    if (-not (Get-Command VBoxManage -ErrorAction SilentlyContinue)) {
        Write-Info "下载VirtualBox..."
        $vboxUrl = "https://download.virtualbox.org/virtualbox/7.0.12/VirtualBox-7.0.12-159484-Win.exe"
        $vboxPath = "$env:TEMP\VirtualBox-7.0.12-159484-Win.exe"
        Invoke-WebRequest -Uri $vboxUrl -OutFile $vboxPath
        
        Write-Info "安装VirtualBox..."
        Start-Process -FilePath $vboxPath -ArgumentList "--silent" -Wait
        
        Write-Warning "请重启计算机以完成VirtualBox安装，然后重新运行此脚本..."
        return
    }
    
    # 下载Ubuntu 24.04 LTS ISO
    Write-Info "下载Ubuntu 24.04 LTS ISO..."
    $ubuntuUrl = "https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso"
    $ubuntuPath = "$env:USERPROFILE\Downloads\ubuntu-24.04-desktop-amd64.iso"
    
    if (-not (Test-Path $ubuntuPath)) {
        Write-Info "正在下载Ubuntu ISO文件，这可能需要一些时间..."
        Invoke-WebRequest -Uri $ubuntuUrl -OutFile $ubuntuPath
    }
    
    # 创建虚拟机
    Write-Info "创建VirtualBox虚拟机..."
    VBoxManage createvm --name "SonjayOS-Dev" --ostype "Ubuntu_64" --register
    VBoxManage modifyvm "SonjayOS-Dev" --memory 8192 --cpus 4 --vram 128
    VBoxManage createhd --filename "$env:USERPROFILE\VirtualBox VMs\SonjayOS-Dev\SonjayOS-Dev.vdi" --size 100000
    VBoxManage storagectl "SonjayOS-Dev" --name "SATA Controller" --add sata --controller IntelAHCI
    VBoxManage storageattach "SonjayOS-Dev" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "$env:USERPROFILE\VirtualBox VMs\SonjayOS-Dev\SonjayOS-Dev.vdi"
    VBoxManage storageattach "SonjayOS-Dev" --storagectl "SATA Controller" --port 1 --device 0 --type dvddrive --medium $ubuntuPath
    
    Write-Success "VirtualBox虚拟机创建完成！"
    Write-Info "请启动虚拟机并安装Ubuntu，然后手动设置开发环境"
    Write-Info "虚拟机名称: SonjayOS-Dev"
    Write-Info "ISO文件: $ubuntuPath"
}

# 主函数
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Host "SonjayOS Windows 11 开发环境设置脚本" -ForegroundColor $Green
    Write-Host "==========================================" -ForegroundColor $Green
    Write-Host ""
    
    # 检查管理员权限
    if (-not (Test-Administrator)) {
        Write-Error "需要管理员权限运行此脚本"
        Write-Info "请以管理员身份运行PowerShell"
        return
    }
    
    # 检查系统要求
    if (-not (Test-SystemRequirements)) {
        Write-Error "系统要求检查失败"
        return
    }
    
    # 根据选择的方法设置环境
    switch ($Method.ToLower()) {
        "wsl2" {
            Setup-WSL2
        }
        "docker" {
            Setup-Docker
        }
        "virtualbox" {
            Setup-VirtualBox
        }
        default {
            Write-Error "不支持的方法: $Method"
            Write-Info "支持的方法: WSL2, Docker, VirtualBox"
            return
        }
    }
    
    Write-Success "SonjayOS开发环境设置完成！"
    Write-Info "详细使用说明请参考: docs/Windows11开发环境设置.md"
}

# 运行主函数
Main
