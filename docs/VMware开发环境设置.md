# SonjayOS VMware 开发环境设置指南

## 概述

本指南将帮助您在VMware虚拟机上设置SonjayOS开发环境。VMware提供了更好的性能和更稳定的虚拟化环境，适合开发工作。

## 前置要求

- VMware Workstation Pro 17+ 或 VMware Fusion 13+ (Mac)
- 至少 16GB 主机内存 (推荐 32GB)
- 至少 200GB 可用磁盘空间
- 稳定的网络连接
- Ubuntu 24.04 LTS ISO 文件

## 步骤1：下载必要文件

### 1.1 下载VMware Workstation Pro
- 访问 https://www.vmware.com/products/workstation-pro.html
- 下载VMware Workstation Pro 17+
- 安装并激活VMware

### 1.2 下载Ubuntu 24.04 LTS ISO
- 访问 https://ubuntu.com/download/desktop
- 下载Ubuntu 24.04 LTS Desktop ISO文件
- 文件大小约4.7GB

### 1.3 下载SonjayOS项目
```bash
# 在主机上下载项目
git clone https://github.com/sonjayos/sonjayos.git
```

## 步骤2：创建VMware虚拟机

### 2.1 创建新虚拟机

1. **打开VMware Workstation Pro**
2. **点击"创建新的虚拟机"**
3. **选择"典型(推荐)"配置**
4. **选择"稍后安装操作系统"**
5. **选择"Linux" > "Ubuntu 64位"**

### 2.2 配置虚拟机设置

**虚拟机名称**: `SonjayOS-Dev`
**位置**: 选择有足够空间的磁盘分区

**硬件配置**:
- **内存**: 8GB (推荐16GB)
- **处理器**: 4核心 (推荐8核心)
- **硬盘**: 100GB (推荐200GB)
- **网络**: NAT模式

### 2.3 高级设置

**处理器设置**:
- 启用虚拟化功能
- 启用IOMMU
- 启用硬件虚拟化

**内存设置**:
- 启用内存热插拔
- 启用内存压缩

**显示设置**:
- 启用3D图形加速
- 显存: 128MB

## 步骤3：安装Ubuntu 24.04 LTS

### 3.1 启动虚拟机

1. **选择Ubuntu ISO文件**
2. **启动虚拟机**
3. **选择"Install Ubuntu"**

### 3.2 安装配置

**语言**: 中文(简体) 或 English
**键盘布局**: 根据您的偏好选择
**安装类型**: 正常安装
**磁盘分区**: 使用整个磁盘
**用户设置**:
- 用户名: `sonjayos`
- 密码: 设置强密码
- 计算机名: `sonjayos-dev`

### 3.3 完成安装

1. **等待安装完成**
2. **重启虚拟机**
3. **登录Ubuntu系统**

## 步骤4：配置Ubuntu开发环境

### 4.1 更新系统

```bash
# 更新包列表
sudo apt update && sudo apt upgrade -y

# 安装必要工具
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
    lsb-release \
    vim \
    htop \
    tree
```

### 4.2 配置网络

```bash
# 检查网络连接
ping -c 4 google.com

# 配置Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 4.3 安装开发工具

```bash
# 安装VS Code (可选)
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code

# 安装Docker (可选)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

## 步骤5：设置SonjayOS开发环境

### 5.1 传输项目文件

**方法1: 使用共享文件夹**
1. 在VMware中设置共享文件夹
2. 将SonjayOS项目复制到共享文件夹
3. 在虚拟机中访问共享文件夹

**方法2: 使用Git克隆**
```bash
# 在虚拟机中克隆项目
cd ~
git clone https://github.com/sonjayos/sonjayos.git
cd sonjayos
```

**方法3: 使用SCP传输**
```bash
# 在主机上执行
scp -r sonjayos/ sonjayos@<虚拟机IP>:~/
```

### 5.2 设置项目环境

```bash
# 进入项目目录
cd ~/sonjayos

# 设置权限
chmod +x scripts/*.sh
chmod +x tools/iso-builder/*.sh

# 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
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

### 5.3 配置开发环境

```bash
# 设置环境变量
echo 'export SONJAYOS_DEV_MODE=true' >> ~/.bashrc
echo 'export SONJAYOS_DEBUG_LEVEL=DEBUG' >> ~/.bashrc
echo 'export SONJAYOS_HOT_RELOAD=true' >> ~/.bashrc
echo 'export SONJAYOS_MOCK_AI=true' >> ~/.bashrc
echo 'export SONJAYOS_PROFILING=true' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

## 步骤6：启动开发模式

### 6.1 启动开发服务

```bash
# 进入项目目录
cd ~/sonjayos

# 激活虚拟环境
source venv/bin/activate

# 启动开发模式
./scripts/dev-mode.sh start
```

### 6.2 验证服务状态

```bash
# 查看开发状态
./scripts/dev-mode.sh status

# 查看服务日志
tail -f /tmp/sonjayos-ai-dev.log
tail -f /tmp/sonjayos-ui-dev.log
```

### 6.3 测试功能

```bash
# 测试AI服务
curl http://localhost:8000/api/v1/ai/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好，请介绍一下SonjayOS", "max_tokens": 100}'

# 测试UI服务
curl http://localhost:8001/api/v1/ui/themes

# 测试安全服务
curl http://localhost:8002/api/v1/security/status
```

## 步骤7：开发工具使用

### 7.1 代码格式化

```bash
# 格式化Python代码
./dev_tools/format_code.sh

# 格式化JavaScript代码
npx prettier --write src/ui/gnome/sonjayos-ai-assistant/extension.js
```

### 7.2 代码检查

```bash
# 检查Python代码
./dev_tools/lint_code.sh

# 检查JavaScript代码
npx eslint src/ui/gnome/sonjayos-ai-assistant/extension.js
```

### 7.3 运行测试

```bash
# 运行Python测试
./dev_tools/run_tests.sh

# 运行JavaScript测试
cd src/ui/gnome/sonjayos-ai-assistant/
npm test
```

### 7.4 性能分析

```bash
# 启动性能分析
./dev_tools/profile_performance.sh

# 查看内存使用
python -m memory_profiler src/ai/llama/llama_integration.py

# 查看CPU使用
python -m line_profiler src/ai/whisper/speech_recognition.py
```

## 步骤8：VMware优化设置

### 8.1 虚拟机设置优化

**内存设置**:
- 启用内存热插拔
- 启用内存压缩
- 设置内存预留

**处理器设置**:
- 启用虚拟化功能
- 启用IOMMU
- 设置CPU亲和性

**存储设置**:
- 启用磁盘压缩
- 启用磁盘去重
- 设置磁盘缓存

### 8.2 网络设置

**网络适配器**:
- 类型: NAT或桥接
- 启用网络适配器
- 设置MAC地址

**端口转发**:
- 8000 -> 8000 (AI服务)
- 8001 -> 8001 (UI服务)
- 8002 -> 8002 (安全服务)

### 8.3 显示设置

**显示适配器**:
- 启用3D图形加速
- 显存: 128MB
- 启用硬件加速

## 步骤9：常见问题解决

### 9.1 性能问题

**问题**: 虚拟机运行缓慢
**解决方案**:
1. 增加虚拟机内存
2. 启用硬件虚拟化
3. 优化VMware设置
4. 关闭不必要的服务

### 9.2 网络问题

**问题**: 无法访问外部网络
**解决方案**:
1. 检查网络适配器设置
2. 配置端口转发
3. 检查防火墙设置
4. 重启网络服务

### 9.3 文件传输问题

**问题**: 无法传输文件
**解决方案**:
1. 启用共享文件夹
2. 使用SCP传输
3. 使用Git同步
4. 检查权限设置

### 9.4 开发服务问题

**问题**: 服务启动失败
**解决方案**:
1. 检查依赖安装
2. 查看错误日志
3. 重启服务
4. 检查端口占用

## 步骤10：开发工作流

### 10.1 日常开发流程

```bash
# 1. 启动开发环境
cd ~/sonjayos
source venv/bin/activate
./scripts/dev-mode.sh start

# 2. 修改代码
vim src/ai/llama/llama_integration.py

# 3. 格式化代码
./dev_tools/format_code.sh

# 4. 检查代码
./dev_tools/lint_code.sh

# 5. 运行测试
./dev_tools/run_tests.sh

# 6. 提交代码
git add .
git commit -m "feat: 添加新功能"
git push
```

### 10.2 调试流程

```bash
# 1. 查看服务状态
./scripts/dev-mode.sh status

# 2. 查看日志
tail -f /tmp/sonjayos-ai-dev.log

# 3. 性能分析
./dev_tools/profile_performance.sh

# 4. 重启服务
./scripts/dev-mode.sh restart
```

### 10.3 部署流程

```bash
# 1. 停止开发模式
./scripts/dev-mode.sh stop

# 2. 构建生产版本
./scripts/prod-mode.sh start

# 3. 测试生产环境
curl http://localhost:8000/api/v1/system/status

# 4. 部署到生产环境
./tools/iso-builder/build-iso.sh
```

## 步骤11：备份和恢复

### 11.1 虚拟机备份

```bash
# 在主机上执行
# 关闭虚拟机
# 复制虚拟机文件夹
cp -r "SonjayOS-Dev" "SonjayOS-Dev-Backup"

# 或使用VMware快照功能
```

### 11.2 项目备份

```bash
# 在虚拟机中执行
cd ~/sonjayos
git add .
git commit -m "backup: 开发环境备份"
git push

# 或创建项目压缩包
tar -czf sonjayos-backup.tar.gz ~/sonjayos
```

### 11.3 环境恢复

```bash
# 恢复虚拟机
# 1. 从备份恢复虚拟机文件夹
# 2. 启动虚拟机
# 3. 恢复项目文件

# 恢复项目
cd ~
git clone https://github.com/sonjayos/sonjayos.git
cd sonjayos
chmod +x scripts/*.sh
source venv/bin/activate
./scripts/dev-mode.sh start
```

## 总结

通过以上步骤，您已经成功在VMware虚拟机上设置了SonjayOS开发环境。这个环境提供了：

1. **完整的Linux开发环境**
2. **SonjayOS项目代码**
3. **开发工具和调试功能**
4. **热重载和模拟服务**
5. **性能分析和监控**

现在您可以开始SonjayOS的开发工作了！记住定期备份您的工作，并保持开发环境的更新。

---

**祝您开发愉快！** 🚀
