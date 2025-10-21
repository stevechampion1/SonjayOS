# SonjayOS Makefile
# 用于构建、安装和开发SonjayOS

.PHONY: help install dev test clean build iso docker

# 默认目标
help:
	@echo "SonjayOS 构建系统"
	@echo "=================="
	@echo ""
	@echo "可用命令:"
	@echo "  make install    - 安装SonjayOS"
	@echo "  make dev        - 启动开发模式"
	@echo "  make test       - 运行测试"
	@echo "  make clean      - 清理构建文件"
	@echo "  make build      - 构建项目"
	@echo "  make iso        - 构建ISO镜像"
	@echo "  make docker     - 构建Docker镜像"
	@echo "  make help       - 显示帮助信息"

# 安装SonjayOS
install:
	@echo "安装SonjayOS..."
	chmod +x scripts/install.sh
	./scripts/install.sh

# 开发模式
dev:
	@echo "启动开发模式..."
	chmod +x scripts/dev-mode.sh
	./scripts/dev-mode.sh start

# 生产模式
prod:
	@echo "启动生产模式..."
	chmod +x scripts/prod-mode.sh
	./scripts/prod-mode.sh start

# 运行测试
test:
	@echo "运行测试..."
	python -m pytest tests/ -v
	npm test

# 代码格式化
format:
	@echo "格式化代码..."
	black src/ --line-length 88
	isort src/ --profile black
	npx prettier --write src/ui/gnome/sonjayos-ai-assistant/extension.js

# 代码检查
lint:
	@echo "检查代码..."
	flake8 src/ --max-line-length=88 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports
	bandit -r src/ -f json -o bandit-report.json
	npx eslint src/ui/gnome/sonjayos-ai-assistant/extension.js

# 清理构建文件
clean:
	@echo "清理构建文件..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf node_modules/
	rm -rf .venv/
	rm -rf venv/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.log" -delete

# 构建项目
build: clean
	@echo "构建项目..."
	python -m build
	npm run build

# 构建ISO镜像
iso:
	@echo "构建ISO镜像..."
	chmod +x tools/iso-builder/build-iso.sh
	./tools/iso-builder/build-iso.sh

# Docker相关
docker:
	@echo "构建Docker镜像..."
	docker build -t sonjayos:latest .

docker-run:
	@echo "运行Docker容器..."
	docker run -d --name sonjayos --privileged sonjayos:latest

docker-stop:
	@echo "停止Docker容器..."
	docker stop sonjayos
	docker rm sonjayos

# 开发环境设置
dev-setup:
	@echo "设置开发环境..."
	python -m venv venv
	source venv/bin/activate && pip install -r requirements.txt
	npm install
	chmod +x scripts/*.sh
	chmod +x tools/iso-builder/*.sh

# 安装依赖
deps:
	@echo "安装依赖..."
	pip install -r requirements.txt
	npm install

# 更新依赖
update-deps:
	@echo "更新依赖..."
	pip install --upgrade -r requirements.txt
	npm update

# 安全检查
security:
	@echo "安全检查..."
	safety check
	bandit -r src/
	npm audit

# 性能测试
perf:
	@echo "性能测试..."
	python -m memory_profiler src/ai/llama/llama_integration.py
	python -m line_profiler src/ai/whisper/speech_recognition.py

# 文档生成
docs:
	@echo "生成文档..."
	sphinx-build -b html docs/ docs/_build/html

# 发布
release:
	@echo "发布版本..."
	python -m build
	twine upload dist/*

# 完整构建流程
all: clean deps test build

# 开发环境完整设置
dev-all: dev-setup test format lint

# 生产环境完整设置
prod-all: clean deps test build iso
