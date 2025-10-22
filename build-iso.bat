@echo off
REM SonjayOS ISO快速构建脚本
REM 一键构建SonjayOS自定义ISO镜像

echo ==========================================
echo SonjayOS ISO快速构建器
echo ==========================================
echo.

REM 检查当前目录
if not exist "README.md" (
    echo 错误: 请在SonjayOS项目根目录中运行此脚本
    pause
    exit /b 1
)

echo 开始构建SonjayOS ISO...
echo.

REM 运行构建脚本
call tools\iso-builder\build-iso-windows.bat

echo.
echo 构建完成！
pause
