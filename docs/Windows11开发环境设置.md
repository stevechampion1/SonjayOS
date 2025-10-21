# SonjayOS Windows 11 开发环境设置指南

## 概述

本指南将帮助您在Windows 11上设置SonjayOS开发环境。由于SonjayOS是基于Ubuntu的Linux系统，我们需要在Windows上创建Linux环境来运行开发模式。

## 前置要求

- Windows 11 (版本 22H2 或更高)
- 至少 16GB RAM (推荐 32GB)
- 至少 100GB 可用磁盘空间
- 管理员权限
- 稳定的网络连接

## 方法一：使用WSL2 (推荐)

### 步骤1：启用WSL2

1. **以管理员身份打开PowerShell**
   ```powershell
   # 启用WSL功能
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   
   # 启用虚拟机平台
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   
   # 重启计算机
   Restart-Computer
   ```

2. **安装WSL2**
   ```powershell
   # 设置WSL2为默认版本
   wsl --set-default-version 2
   
   # 安装Ubuntu 24.04 LTS
   wsl --install -d Ubuntu-24.04
   ```

### 步骤2：配置WSL2

1. **启动Ubuntu**
   ```bash
   wsl
   ```

2. **更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **安装必要工具**
   ```bash
   sudo apt install -y \
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
   ```

### 步骤3：克隆SonjayOS项目

```bash
# 克隆项目
git clone https://github.com/sonjayos/sonjayos.git
cd sonjayos

# 设置权限
chmod +x scripts/*.sh
chmod +x tools/iso-builder/*.sh
```

### 步骤4：设置开发环境

```bash
# 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装Python依赖
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
```

### 步骤5：启动开发模式

```bash
# 启动开发模式
./scripts/dev-mode.sh start

# 查看状态
./scripts/dev-mode.sh status
```

## 方法二：使用Docker Desktop

### 步骤1：安装Docker Desktop

1. **下载Docker Desktop**
   - 访问 https://www.docker.com/products/docker-desktop/
   - 下载Windows版本
   - 安装并启动Docker Desktop

2. **启用WSL2后端**
   - 打开Docker Desktop设置
   - 启用"Use the WSL 2 based engine"

### 步骤2：创建开发容器

1. **创建Dockerfile**
   ```dockerfile
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
   ```

2. **创建docker-compose.yml**
   ```yaml
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
   ```

3. **启动开发容器**
   ```bash
   # 构建并启动容器
   docker-compose up --build
   
   # 进入容器
   docker-compose exec sonjayos-dev bash
   ```

## 方法三：使用VirtualBox虚拟机

### 步骤1：安装VirtualBox

1. **下载VirtualBox**
   - 访问 https://www.virtualbox.org/
   - 下载Windows版本
   - 安装VirtualBox

2. **下载Ubuntu 24.04 LTS ISO**
   - 访问 https://ubuntu.com/download/desktop
   - 下载Ubuntu 24.04 LTS ISO文件

### 步骤2：创建虚拟机

1. **创建新虚拟机**
   - 打开VirtualBox
   - 点击"新建"
   - 名称：SonjayOS-Dev
   - 类型：Linux
   - 版本：Ubuntu (64-bit)

2. **配置虚拟机**
   - 内存：8GB (推荐16GB)
   - 硬盘：100GB (推荐200GB)
   - 启用虚拟化功能
   - 启用3D加速

3. **安装Ubuntu**
   - 启动虚拟机
   - 选择Ubuntu ISO文件
   - 按照安装向导完成安装

### 步骤3：配置开发环境

1. **更新系统**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **安装开发工具**
   ```bash
   sudo apt install -y \
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
   ```

3. **克隆项目**
   ```bash
   git clone https://github.com/sonjayos/sonjayos.git
   cd sonjayos
   ```

4. **设置开发环境**
   ```bash
   # 创建虚拟环境
   python3.11 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 设置权限
   chmod +x scripts/*.sh
   ```

5. **启动开发模式**
   ```bash
   ./scripts/dev-mode.sh start
   ```

## 开发模式配置

### 环境变量设置

```bash
# 设置开发环境变量
export SONJAYOS_DEV_MODE=true
export SONJAYOS_DEBUG_LEVEL=DEBUG
export SONJAYOS_HOT_RELOAD=true
export SONJAYOS_MOCK_AI=true
export SONJAYOS_PROFILING=true
```

### 开发配置文件

```json
{
    "dev_mode": true,
    "debug_level": "DEBUG",
    "hot_reload": true,
    "mock_ai": true,
    "profiling": true,
    "log_to_console": true,
    "services": {
        "ai_service": {
            "enabled": true,
            "port": 8000,
            "workers": 1,
            "dev_mode": true,
            "mock_ai": true
        },
        "ui_service": {
            "enabled": true,
            "port": 8001,
            "workers": 1,
            "hot_reload": true
        },
        "security_service": {
            "enabled": true,
            "port": 8002,
            "workers": 1,
            "mock_threats": true
        }
    }
}
```

## 开发工具使用

### 代码格式化

```bash
# 格式化Python代码
./dev_tools/format_code.sh

# 格式化JavaScript代码
npx prettier --write src/ui/gnome/sonjayos-ai-assistant/extension.js
```

### 代码检查

```bash
# 检查Python代码
./dev_tools/lint_code.sh

# 检查JavaScript代码
npx eslint src/ui/gnome/sonjayos-ai-assistant/extension.js
```

### 运行测试

```bash
# 运行Python测试
./dev_tools/run_tests.sh

# 运行JavaScript测试
cd src/ui/gnome/sonjayos-ai-assistant/
npm test
```

### 性能分析

```bash
# 启动性能分析
./dev_tools/profile_performance.sh

# 查看内存使用
python -m memory_profiler src/ai/llama/llama_integration.py

# 查看CPU使用
python -m line_profiler src/ai/whisper/speech_recognition.py
```

## 常见问题解决

### 1. WSL2问题

**问题**: WSL2启动失败
**解决方案**:
```powershell
# 重启WSL
wsl --shutdown
wsl --start

# 检查WSL版本
wsl --list --verbose
```

### 2. 权限问题

**问题**: 脚本执行权限不足
**解决方案**:
```bash
# 设置执行权限
chmod +x scripts/*.sh
chmod +x tools/iso-builder/*.sh

# 检查权限
ls -la scripts/
```

### 3. 依赖安装失败

**问题**: Python包安装失败
**解决方案**:
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 清理缓存
pip cache purge
```

### 4. 端口占用

**问题**: 端口8000/8001/8002被占用
**解决方案**:
```bash
# 检查端口占用
netstat -tlnp | grep -E ":(8000|8001|8002)"

# 杀死占用进程
sudo kill -9 <PID>

# 或修改配置文件中的端口
```

### 5. 内存不足

**问题**: 内存使用过高
**解决方案**:
```bash
# 检查内存使用
free -h
top

# 减少服务数量
# 修改配置文件中的workers数量
```

## 开发模式特性

### 1. 热重载

- 代码修改后自动重启服务
- 配置文件变更自动应用
- 实时错误检测和修复

### 2. 调试功能

- 详细日志输出
- 性能分析工具
- 内存使用监控
- 错误堆栈跟踪

### 3. 模拟服务

- AI模型模拟响应
- 安全威胁模拟
- 硬件资源模拟
- 网络请求模拟

### 4. 开发工具

- 代码格式化
- 静态代码检查
- 单元测试
- 性能分析

## 下一步

1. **熟悉开发环境**
   - 阅读开发文档
   - 了解项目结构
   - 学习API接口

2. **开始开发**
   - 修改代码
   - 测试功能
   - 调试问题

3. **贡献代码**
   - 提交代码
   - 编写测试
   - 更新文档

## 支持

如有问题，请参考：
- 项目文档：`docs/`
- 开发指南：`docs/开发指南.md`
- 问题反馈：GitHub Issues
- 社区讨论：GitHub Discussions

---

**祝您开发愉快！** 🚀
