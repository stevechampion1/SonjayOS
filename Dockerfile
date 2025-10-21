# SonjayOS Dockerfile
# 用于构建SonjayOS Docker镜像

FROM ubuntu:24.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV SONJAYOS_DOCKER_MODE=true
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
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
    tree \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 设置权限
RUN chmod +x scripts/*.sh
RUN chmod +x tools/iso-builder/*.sh

# 创建Python虚拟环境
RUN python3.11 -m venv venv

# 激活虚拟环境并安装Python依赖
RUN . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# 安装Node.js依赖
RUN npm install

# 创建必要的目录
RUN mkdir -p /var/lib/sonjayos
RUN mkdir -p /var/log/sonjayos
RUN mkdir -p /etc/sonjayos

# 创建用户
RUN useradd -r -s /bin/false sonjayos
RUN chown -R sonjayos:sonjayos /app
RUN chown -R sonjayos:sonjayos /var/lib/sonjayos
RUN chown -R sonjayos:sonjayos /var/log/sonjayos

# 暴露端口
EXPOSE 8000 8001 8002

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置启动命令
CMD ["./scripts/dev-mode.sh", "start"]
