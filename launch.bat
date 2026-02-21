@echo off
chcp 65001 >nul
REM Cipher工具启动脚本（Windows版）

echo ========================================
echo Cipher加密工具启动
echo ========================================
echo.

if exist "dist\Cipher.exe" (
    echo 正在启动Cipher工具...
    echo.
    dist\Cipher.exe
    echo.
    echo Cipher工具已退出
) else (
    echo 错误: 未找到可执行文件
    echo.
    echo 请先运行以下命令构建:
    echo   python build.py --all
    echo 或:
    echo   python build.py --install-deps --build
    exit /b 1
)
