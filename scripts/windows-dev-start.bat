@echo off
REM SonjayOS Windows 11 开发模式启动脚本
REM 用于在Windows 11上启动SonjayOS开发模式

setlocal enabledelayedexpansion

REM 颜色定义
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "WHITE=[97m"
set "RESET=[0m"

REM 日志函数
:log_info
echo %BLUE%[INFO]%RESET% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%RESET% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%RESET% %~1
goto :eof

:log_error
echo %RED%[ERROR]%RESET% %~1
goto :eof

REM 检查WSL2是否可用
:check_wsl2
call :log_info "检查WSL2环境..."
wsl --list --verbose >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "WSL2不可用，请先运行 windows-dev-setup.ps1 设置环境"
    exit /b 1
)
call :log_success "WSL2环境检查通过"
goto :eof

REM 检查项目目录
:check_project
call :log_info "检查项目目录..."
wsl -d Ubuntu-24.04 -e test -d ~/sonjayos
if %errorlevel% neq 0 (
    call :log_error "项目目录不存在，请先运行 windows-dev-setup.ps1 设置环境"
    exit /b 1
)
call :log_success "项目目录检查通过"
goto :eof

REM 启动开发模式
:start_dev_mode
call :log_info "启动SonjayOS开发模式..."
wsl -d Ubuntu-24.04 -e bash -c "cd ~/sonjayos && ./scripts/dev-mode.sh start"
if %errorlevel% neq 0 (
    call :log_error "开发模式启动失败"
    exit /b 1
)
call :log_success "开发模式启动成功"
goto :eof

REM 显示状态
:show_status
call :log_info "显示开发状态..."
wsl -d Ubuntu-24.04 -e bash -c "cd ~/sonjayos && ./scripts/dev-mode.sh status"
goto :eof

REM 停止开发模式
:stop_dev_mode
call :log_info "停止SonjayOS开发模式..."
wsl -d Ubuntu-24.04 -e bash -c "cd ~/sonjayos && ./scripts/dev-mode.sh stop"
if %errorlevel% neq 0 (
    call :log_error "开发模式停止失败"
    exit /b 1
)
call :log_success "开发模式停止成功"
goto :eof

REM 进入开发环境
:enter_dev_env
call :log_info "进入SonjayOS开发环境..."
wsl -d Ubuntu-24.04 -e bash -c "cd ~/sonjayos && bash"
goto :eof

REM 显示帮助
:show_help
echo %GREEN%SonjayOS Windows 11 开发模式启动脚本%RESET%
echo.
echo 用法: windows-dev-start.bat [命令]
echo.
echo 命令:
echo   start    启动开发模式
echo   stop     停止开发模式
echo   status   显示开发状态
echo   enter    进入开发环境
echo   help     显示帮助信息
echo.
echo 示例:
echo   windows-dev-start.bat start
echo   windows-dev-start.bat status
echo   windows-dev-start.bat enter
goto :eof

REM 主函数
:main
if "%1"=="" (
    call :show_help
    exit /b 0
)

if "%1"=="help" (
    call :show_help
    exit /b 0
)

if "%1"=="start" (
    call :check_wsl2
    if %errorlevel% neq 0 exit /b 1
    call :check_project
    if %errorlevel% neq 0 exit /b 1
    call :start_dev_mode
    exit /b 0
)

if "%1"=="stop" (
    call :stop_dev_mode
    exit /b 0
)

if "%1"=="status" (
    call :show_status
    exit /b 0
)

if "%1"=="enter" (
    call :enter_dev_env
    exit /b 0
)

call :log_error "未知命令: %1"
call :show_help
exit /b 1

REM 运行主函数
call :main %*
