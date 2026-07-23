@echo off
chcp 65001 >nul
REM Cipher tool launch script (Windows version)

echo ========================================
echo Cipher Encryption Tool Launch
echo ========================================
echo.

if exist "dist\Cipher.exe" (
    echo Starting Cipher tool...
    echo.
    dist\Cipher.exe
    echo.
    echo Cipher tool has exited
) else (
    echo Error: Executable not found
    echo.
    echo Please build first with:
    echo   python build.py --all
    echo or:
    echo   python build.py --install-deps --build
    exit /b 1
)
