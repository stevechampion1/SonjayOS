@echo off
REM SonjayOS ISO构建脚本 - Windows版本
REM 用于在Windows环境中构建SonjayOS自定义ISO

echo ==========================================
echo SonjayOS 自定义ISO构建器 - Windows版本
echo ==========================================
echo.

REM 检查必要工具
echo 检查构建依赖...
where 7z >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 7-Zip未安装，请先安装7-Zip
    pause
    exit /b 1
)

where xorriso >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: xorriso未安装，请先安装xorriso
    echo 下载地址: https://www.gnu.org/software/xorriso/
    pause
    exit /b 1
)

echo 依赖检查完成
echo.

REM 设置变量
set UBUNTU_ISO=ubuntu-24.04-desktop-amd64.iso
set SONJAYOS_ISO=sonjayos-1.0-alpha-amd64.iso
set BUILD_DIR=sonjayos-iso-build
set EXTRACT_DIR=custom-iso

REM 创建构建目录
echo 准备构建环境...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
cd "%BUILD_DIR%"

REM 下载Ubuntu ISO（如果不存在）
if not exist "..\%UBUNTU_ISO%" (
    echo 下载Ubuntu 24.04 LTS ISO...
    powershell -Command "Invoke-WebRequest -Uri 'https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso' -OutFile '..\%UBUNTU_ISO%'"
    if %errorlevel% neq 0 (
        echo 错误: Ubuntu ISO下载失败
        pause
        exit /b 1
    )
    echo Ubuntu ISO下载完成
) else (
    echo Ubuntu ISO已存在，跳过下载
)

REM 提取ISO内容
echo 提取Ubuntu ISO内容...
7z x "..\%UBUNTU_ISO%" -o"%EXTRACT_DIR%"
if %errorlevel% neq 0 (
    echo 错误: ISO提取失败
    pause
    exit /b 1
)
echo ISO内容提取完成

REM 添加SonjayOS文件
echo 添加SonjayOS文件...
mkdir "%EXTRACT_DIR%\opt\sonjayos"
xcopy /E /I /Y "..\*" "%EXTRACT_DIR%\opt\sonjayos\"
if %errorlevel% neq 0 (
    echo 错误: SonjayOS文件复制失败
    pause
    exit /b 1
)
echo SonjayOS文件添加完成

REM 创建自动安装配置
echo 创建自动安装配置...
mkdir "%EXTRACT_DIR%\server"

REM 创建user-data文件
echo #cloud-config > "%EXTRACT_DIR%\server\user-data"
echo autoinstall: >> "%EXTRACT_DIR%\server\user-data"
echo   version: 1 >> "%EXTRACT_DIR%\server\user-data"
echo   identity: >> "%EXTRACT_DIR%\server\user-data"
echo     hostname: sonjayos >> "%EXTRACT_DIR%\server\user-data"
echo     username: sonjayos >> "%EXTRACT_DIR%\server\user-data"
echo     password: $6$rounds=4096$salt$hash >> "%EXTRACT_DIR%\server\user-data"
echo     realname: SonjayOS User >> "%EXTRACT_DIR%\server\user-data"
echo   locale: zh_CN.UTF-8 >> "%EXTRACT_DIR%\server\user-data"
echo   keyboard: >> "%EXTRACT_DIR%\server\user-data"
echo     layout: cn >> "%EXTRACT_DIR%\server\user-data"
echo   network: >> "%EXTRACT_DIR%\server\user-data"
echo     network: >> "%EXTRACT_DIR%\server\user-data"
echo       version: 2 >> "%EXTRACT_DIR%\server\user-data"
echo       ethernets: >> "%EXTRACT_DIR%\server\user-data"
echo         eth0: >> "%EXTRACT_DIR%\server\user-data"
echo           dhcp4: true >> "%EXTRACT_DIR%\server\user-data"
echo   packages: >> "%EXTRACT_DIR%\server\user-data"
echo     - build-essential >> "%EXTRACT_DIR%\server\user-data"
echo     - python3 >> "%EXTRACT_DIR%\server\user-data"
echo     - python3-pip >> "%EXTRACT_DIR%\server\user-data"
echo     - python3-venv >> "%EXTRACT_DIR%\server\user-data"
echo     - python3-dev >> "%EXTRACT_DIR%\server\user-data"
echo     - git >> "%EXTRACT_DIR%\server\user-data"
echo     - curl >> "%EXTRACT_DIR%\server\user-data"
echo     - wget >> "%EXTRACT_DIR%\server\user-data"
echo     - vim >> "%EXTRACT_DIR%\server\user-data"
echo     - htop >> "%EXTRACT_DIR%\server\user-data"
echo     - tree >> "%EXTRACT_DIR%\server\user-data"
echo     - software-properties-common >> "%EXTRACT_DIR%\server\user-data"
echo     - apt-transport-https >> "%EXTRACT_DIR%\server\user-data"
echo     - ca-certificates >> "%EXTRACT_DIR%\server\user-data"
echo     - gnupg >> "%EXTRACT_DIR%\server\user-data"
echo     - lsb-release >> "%EXTRACT_DIR%\server\user-data"
echo   late-commands: >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- cp -r /cdrom/opt/sonjayos /opt/ >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- chown -R sonjayos:sonjayos /opt/sonjayos >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- chmod +x /opt/sonjayos/scripts/*.sh >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- chmod +x /opt/sonjayos/tools/iso-builder/*.sh >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- /opt/sonjayos/scripts/install.sh >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- systemctl enable sonjayos-ai-scheduler.service >> "%EXTRACT_DIR%\server\user-data"
echo     - curtin in-target -- systemctl enable sonjayos-ai-security.service >> "%EXTRACT_DIR%\server\user-data"

REM 创建meta-data文件
echo instance-id: sonjayos-autoinstall > "%EXTRACT_DIR%\server\meta-data"
echo local-hostname: sonjayos >> "%EXTRACT_DIR%\server\meta-data"

echo 自动安装配置创建完成

REM 重新打包ISO
echo 重新打包ISO镜像...
cd "%EXTRACT_DIR%"
xorriso -as mkisofs -r -V "SonjayOS_Autoinstall" -o "..\%SONJAYOS_ISO%" --grub2-mbr ../BOOT/1-Boot-NoEmul.img -partition_offset 16 --mbr-force-bootable -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b ../BOOT/2-Boot-NoEmul.img -appended_part_as_gpt -iso_mbr_part_type a2a0d0ebe5b9334487c068b6b72699c7 -c "/boot.catalog" -b "/boot/grub/i386-pc/eltorito.img" -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info -eltorito-alt-boot -e "--interval:appended_partition_2:::" -no-emul-boot .
if %errorlevel% neq 0 (
    echo 错误: ISO重新打包失败
    pause
    exit /b 1
)

cd ..
echo ISO镜像重新打包完成

REM 验证ISO
if exist "%SONJAYOS_ISO%" (
    echo.
    echo ==========================================
    echo SonjayOS ISO构建成功！
    echo ==========================================
    echo.
    echo 生成的ISO文件: %SONJAYOS_ISO%
    echo ISO大小: 
    dir "%SONJAYOS_ISO%" | findstr "%SONJAYOS_ISO%"
    echo.
    echo 使用方法：
    echo 1. 在VMware中创建新虚拟机
    echo 2. 选择 '%SONJAYOS_ISO%' 作为安装介质
    echo 3. 启动虚拟机后选择 'Autoinstall SonjayOS'
    echo 4. 系统将自动安装并配置SonjayOS
    echo.
    echo 默认用户信息：
    echo   用户名: sonjayos
    echo   密码: sonjayos
    echo   主机名: sonjayos
    echo.
    echo 安装完成后，SonjayOS将自动启动。
) else (
    echo 错误: ISO创建失败
    pause
    exit /b 1
)

REM 清理构建环境
echo 清理构建环境...
rmdir /s /q "%EXTRACT_DIR%"
echo 构建环境清理完成

echo.
echo SonjayOS ISO构建完成！
pause
