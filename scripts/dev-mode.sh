#!/bin/bash
# SonjayOS 开发模式启动脚本
# 用于开发环境下的系统运行和调试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[DEV-INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[DEV-SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[DEV-WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[DEV-ERROR]${NC} $1"
}

# 开发模式配置
DEV_MODE=true
DEBUG_LEVEL=DEBUG
HOT_RELOAD=true
MOCK_AI_SERVICES=false
ENABLE_PROFILING=true
LOG_TO_CONSOLE=true

# 开发环境变量
export SONJAYOS_DEV_MODE=true
export SONJAYOS_DEBUG_LEVEL=DEBUG
export SONJAYOS_HOT_RELOAD=true
export SONJAYOS_MOCK_AI=false
export SONJAYOS_PROFILING=true

# 检查开发环境
check_dev_environment() {
    log_info "检查开发环境..."
    
    # 检查Python虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3.11 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查依赖
    if [ ! -f "venv/pyvenv.cfg" ]; then
        log_error "虚拟环境创建失败"
        exit 1
    fi
    
    log_success "开发环境检查完成"
}

# 安装开发依赖
install_dev_dependencies() {
    log_info "安装开发依赖..."
    
    # 安装基础依赖
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
        watchdog \
        nodemon \
        concurrently
    
    log_success "开发依赖安装完成"
}

# 配置开发环境
configure_dev_environment() {
    log_info "配置开发环境..."
    
    # 创建开发配置目录
    mkdir -p dev_config/{ai,ui,system,security}
    
    # 开发模式AI配置
    cat > dev_config/ai/llama_config.json << 'EOF'
{
    "models": {
        "llama3.1-8b": {
            "name": "llama3.1:8b",
            "size": "8B",
            "memory_usage": 2000,
            "inference_speed": 100.0,
            "quality_score": 0.85
        }
    },
    "default_model": "llama3.1-8b",
    "ollama_host": "http://localhost:11434",
    "max_memory_usage": 0.3,
    "cache_size": 100,
    "auto_model_switching": false,
    "dev_mode": true,
    "mock_responses": true
}
EOF
    
    # 开发模式UI配置
    cat > dev_config/ui/theme_config.json << 'EOF'
{
    "auto_theme_switching": false,
    "learning_enabled": false,
    "brightness_adaptation": false,
    "time_based_themes": {
        "morning": "light_work",
        "afternoon": "light_work",
        "evening": "dark_work",
        "night": "dark_reading"
    },
    "dev_mode": true,
    "hot_reload": true
}
EOF
    
    # 开发模式安全配置
    cat > dev_config/security/ai_security_config.json << 'EOF'
{
    "monitoring": {
        "enabled": true,
        "check_interval": 10,
        "log_retention_days": 7
    },
    "threat_detection": {
        "cpu_threshold": 90.0,
        "memory_threshold": 95.0,
        "network_threshold": 2000,
        "file_access_threshold": 2000,
        "process_threshold": 500
    },
    "dev_mode": true,
    "mock_threats": true,
    "verbose_logging": true
}
EOF
    
    log_success "开发环境配置完成"
}

# 启动开发服务
start_dev_services() {
    log_info "启动开发服务..."
    
    # 创建开发服务启动脚本
    cat > dev_services.sh << 'EOF'
#!/bin/bash
# SonjayOS 开发服务启动脚本

# 激活虚拟环境
source venv/bin/activate

# 设置开发环境变量
export SONJAYOS_DEV_MODE=true
export SONJAYOS_DEBUG_LEVEL=DEBUG
export SONJAYOS_HOT_RELOAD=true
export SONJAYOS_MOCK_AI=true
export SONJAYOS_PROFILING=true

# 启动AI服务（开发模式）
echo "启动AI服务（开发模式）..."
python src/ai/main.py --dev-mode --debug --mock-ai &
AI_PID=$!

# 启动UI服务（开发模式）
echo "启动UI服务（开发模式）..."
python src/ui/main.py --dev-mode --debug --hot-reload &
UI_PID=$!

# 启动安全服务（开发模式）
echo "启动安全服务（开发模式）..."
python src/system/security/main.py --dev-mode --debug --mock-threats &
SECURITY_PID=$!

# 启动开发工具服务
echo "启动开发工具服务..."
python src/dev_tools/main.py --dev-mode --debug &
DEV_TOOLS_PID=$!

# 启动文件监控（热重载）
echo "启动文件监控..."
watchdog --patterns="*.py" --recursive --command="echo '文件变化检测到，重启服务...'" src/ &
WATCHDOG_PID=$!

echo "开发服务已启动"
echo "AI服务PID: $AI_PID"
echo "UI服务PID: $UI_PID"
echo "安全服务PID: $SECURITY_PID"
echo "开发工具PID: $DEV_TOOLS_PID"
echo "文件监控PID: $WATCHDOG_PID"

# 等待用户输入停止
echo "按Ctrl+C停止所有服务"
trap 'kill $AI_PID $UI_PID $SECURITY_PID $DEV_TOOLS_PID $WATCHDOG_PID; exit' INT
wait
EOF
    
    chmod +x dev_services.sh
    
    log_success "开发服务脚本创建完成"
}

# 创建开发工具
create_dev_tools() {
    log_info "创建开发工具..."
    
    # 代码格式化脚本
    cat > dev_tools/format_code.sh << 'EOF'
#!/bin/bash
# 代码格式化脚本

echo "格式化Python代码..."
black src/ --line-length 88
isort src/ --profile black

echo "格式化JavaScript代码..."
npx prettier --write src/ui/gnome/sonjayos-ai-assistant/extension.js

echo "代码格式化完成"
EOF
    
    # 代码检查脚本
    cat > dev_tools/lint_code.sh << 'EOF'
#!/bin/bash
# 代码检查脚本

echo "检查Python代码..."
flake8 src/ --max-line-length=88 --extend-ignore=E203,W503
mypy src/ --ignore-missing-imports
bandit -r src/ -f json -o bandit-report.json

echo "检查JavaScript代码..."
npx eslint src/ui/gnome/sonjayos-ai-assistant/extension.js

echo "代码检查完成"
EOF
    
    # 测试脚本
    cat > dev_tools/run_tests.sh << 'EOF'
#!/bin/bash
# 运行测试脚本

echo "运行Python测试..."
pytest src/tests/ -v --cov=src --cov-report=html --cov-report=term

echo "运行JavaScript测试..."
cd src/ui/gnome/sonjayos-ai-assistant/
npm test

echo "测试完成"
EOF
    
    # 性能分析脚本
    cat > dev_tools/profile_performance.sh << 'EOF'
#!/bin/bash
# 性能分析脚本

echo "启动性能分析..."
python -m memory_profiler src/ai/llama/llama_integration.py &
python -m line_profiler src/ai/whisper/speech_recognition.py &
py-spy record -o profile.svg -- python src/system/kernel/ai_scheduler.py &

echo "性能分析已启动"
EOF
    
    chmod +x dev_tools/*.sh
    
    log_success "开发工具创建完成"
}

# 创建开发文档
create_dev_documentation() {
    log_info "创建开发文档..."
    
    # 开发指南
    cat > docs/开发指南.md << 'EOF'
# SonjayOS 开发指南

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

## 开发环境设置

1. 运行开发模式启动脚本
2. 配置开发环境变量
3. 安装开发依赖
4. 启动开发服务

## 调试技巧

1. 使用日志级别控制输出
2. 启用性能分析
3. 使用断点调试
4. 监控资源使用

## 测试策略

1. 单元测试
2. 集成测试
3. 性能测试
4. 安全测试
EOF
    
    log_success "开发文档创建完成"
}

# 启动开发模式
start_dev_mode() {
    log_info "启动SonjayOS开发模式..."
    
    # 检查开发环境
    check_dev_environment
    
    # 安装开发依赖
    install_dev_dependencies
    
    # 配置开发环境
    configure_dev_environment
    
    # 创建开发工具
    create_dev_tools
    
    # 创建开发文档
    create_dev_documentation
    
    # 启动开发服务
    start_dev_services
    
    log_success "SonjayOS开发模式启动完成！"
    
    echo ""
    echo "=========================================="
    echo "SonjayOS 开发模式"
    echo "=========================================="
    echo ""
    echo "开发模式特性:"
    echo "- 热重载: 代码修改自动重启"
    echo "- 调试模式: 详细日志和错误信息"
    echo "- 模拟服务: AI和安全服务模拟"
    echo "- 性能分析: 实时性能监控"
    echo ""
    echo "可用命令:"
    echo "- 启动服务: ./dev_services.sh"
    echo "- 格式化代码: ./dev_tools/format_code.sh"
    echo "- 检查代码: ./dev_tools/lint_code.sh"
    echo "- 运行测试: ./dev_tools/run_tests.sh"
    echo "- 性能分析: ./dev_tools/profile_performance.sh"
    echo ""
    echo "开发文档: docs/开发指南.md"
    echo ""
}

# 停止开发模式
stop_dev_mode() {
    log_info "停止SonjayOS开发模式..."
    
    # 停止所有开发服务
    pkill -f "python.*src/ai/main.py"
    pkill -f "python.*src/ui/main.py"
    pkill -f "python.*src/system/security/main.py"
    pkill -f "python.*src/dev_tools/main.py"
    pkill -f "watchdog"
    
    # 清理临时文件
    rm -f dev_services.sh
    rm -rf dev_config/
    
    log_success "SonjayOS开发模式已停止"
}

# 显示开发状态
show_dev_status() {
    log_info "SonjayOS开发模式状态..."
    
    echo ""
    echo "=========================================="
    echo "SonjayOS 开发模式状态"
    echo "=========================================="
    echo ""
    
    # 检查服务状态
    if pgrep -f "python.*src/ai/main.py" > /dev/null; then
        echo "✅ AI服务: 运行中"
    else
        echo "❌ AI服务: 未运行"
    fi
    
    if pgrep -f "python.*src/ui/main.py" > /dev/null; then
        echo "✅ UI服务: 运行中"
    else
        echo "❌ UI服务: 未运行"
    fi
    
    if pgrep -f "python.*src/system/security/main.py" > /dev/null; then
        echo "✅ 安全服务: 运行中"
    else
        echo "❌ 安全服务: 未运行"
    fi
    
    if pgrep -f "watchdog" > /dev/null; then
        echo "✅ 文件监控: 运行中"
    else
        echo "❌ 文件监控: 未运行"
    fi
    
    echo ""
    echo "开发环境变量:"
    echo "- SONJAYOS_DEV_MODE: $SONJAYOS_DEV_MODE"
    echo "- SONJAYOS_DEBUG_LEVEL: $SONJAYOS_DEBUG_LEVEL"
    echo "- SONJAYOS_HOT_RELOAD: $SONJAYOS_HOT_RELOAD"
    echo "- SONJAYOS_MOCK_AI: $SONJAYOS_MOCK_AI"
    echo "- SONJAYOS_PROFILING: $SONJAYOS_PROFILING"
    echo ""
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            start_dev_mode
            ;;
        "stop")
            stop_dev_mode
            ;;
        "status")
            show_dev_status
            ;;
        "restart")
            stop_dev_mode
            sleep 2
            start_dev_mode
            ;;
        *)
            echo "用法: $0 {start|stop|status|restart}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动开发模式"
            echo "  stop    - 停止开发模式"
            echo "  status  - 显示开发状态"
            echo "  restart - 重启开发模式"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
