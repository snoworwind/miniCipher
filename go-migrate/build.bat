@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Auto-detect Go installation
call :find-go
if "%GO_BIN%"=="" (
    echo [ERROR] Go not found. Please install Go from https://go.dev/dl/
    echo         or add Go\bin to your system PATH.
    exit /b 1
)
set "PATH=%GO_BIN%;%PATH%"

:: Set Go module proxy (for users in China or behind firewalls)
if "%GOPROXY%"=="" set "GOPROXY=https://goproxy.cn,https://goproxy.io,direct"

:: Enable CGO (required by Fyne GUI for OpenGL bindings)
set "CGO_ENABLED=1"

:: Auto-detect MinGW/GCC (required by Fyne on Windows)
call :find-mingw
if "%MINGW_BIN%"=="" (
    echo [ERROR] MinGW/GCC not found. Fyne GUI build requires a C compiler.
    echo         Install MSYS2 from https://www.msys2.org/ and run:
    echo           pacman -S mingw-w64-ucrt-x86_64-gcc
    echo         Or install MinGW-w64 from https://www.mingw-w64.org/
    echo         If MSYS2 is installed but not found, set MINGW_BIN manually.
) else (
    set "PATH=%MINGW_BIN%;%PATH%"
    echo [INFO] Using MinGW at: %MINGW_BIN%
)

:: Shared ldflags: strip symbols (-s), strip debug info (-w), remove build paths (-trimpath)
set "GO_LDFLAGS=-s -w"
set "GO_TRIM=-trimpath"

:: Build targets for miniCipher (Windows)

if "%~1"==""      goto :build
if "%~1"=="build" goto :build
if "%~1"=="gui"   goto :build-gui
if "%~1"=="all"   goto :build-all
if "%~1"=="test"  goto :test
if "%~1"=="lint"  goto :lint
if "%~1"=="clean" goto :clean
if "%~1"=="help"  goto :help
goto :help

:build
echo [BUILD] Building minicipher (console subsystem^)...
if not exist bin mkdir bin
cd cmd\minicipher
go build %GO_TRIM% -ldflags="%GO_LDFLAGS%" -o ..\..\bin\minicipher.exe .
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Build failed.
    exit /b 1
)
echo [OK] bin\minicipher.exe built.
exit /b 0

:build-gui
echo [BUILD] Building minicipher (GUI subsystem, no console on double-click^)...
if not exist bin mkdir bin
cd cmd\minicipher
go build %GO_TRIM% -ldflags="%GO_LDFLAGS% -H windowsgui" -o ..\..\bin\minicipher.exe .
if %ERRORLEVEL% neq 0 (
    echo [FAIL] GUI build failed.
    exit /b 1
)
echo [OK] bin\minicipher.exe built with -H windowsgui.
echo       Double-click to launch GUI without console. Drag onto cmd to use CLI.
exit /b 0

:build-all
echo [BUILD] Cross-compiling for all platforms...
if not exist bin mkdir bin

echo   Windows amd64...
go env -w GOOS=windows GOARCH=amd64
go build %GO_TRIM% -ldflags="%GO_LDFLAGS% -H windowsgui" -o bin\minicipher-windows-amd64.exe .\cmd\minicipher\
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Windows amd64 build failed.
    exit /b 1
)

echo   Darwin amd64...
go env -w GOOS=darwin GOARCH=amd64
go build %GO_TRIM% -ldflags="%GO_LDFLAGS%" -o bin\minicipher-darwin-amd64 .\cmd\minicipher\

echo   Darwin arm64...
go env -w GOOS=darwin GOARCH=arm64
go build %GO_TRIM% -ldflags="%GO_LDFLAGS%" -o bin\minicipher-darwin-arm64 .\cmd\minicipher\

echo   Linux amd64...
go env -w GOOS=linux GOARCH=amd64
go build %GO_TRIM% -ldflags="%GO_LDFLAGS%" -o bin\minicipher-linux-amd64 .\cmd\minicipher\

go env -u GOOS GOARCH
echo [OK] Cross-compilation complete. Binaries in bin\
exit /b 0

:test
echo [TEST] Running unit tests...
go test .\internal\... -v -count=1
exit /b %ERRORLEVEL%

:lint
echo [LINT] Running go vet...
go vet .\...
echo [LINT] Running go fmt...
go fmt .\...
exit /b 0

:clean
echo [CLEAN] Removing bin\...
if exist bin rd /s /q bin
echo [CLEAN] Cleaning Go cache...
go clean -cache -testcache
exit /b 0

:help
echo Usage: build.bat [target]
echo.
echo Targets:
echo   (none^)   Default: build with console (for CLI usage in terminal^)
echo   gui       Build with -H windowsgui (double-click = GUI only, no console^)
echo   all       Cross-compile for Windows/macOS/Linux
echo   test      Run unit tests
echo   lint      Run go vet and go fmt
echo   clean     Remove bin\ and Go cache
echo   help      Show this help message
exit /b 0

:: ========== Helper: auto-detect Go installation ==========
:find-go
set "GO_BIN="

:: 1. Check if "go" is already in PATH
where go >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where go') do set "GO_BIN=%%~dpi"
    set "GO_BIN=!GO_BIN:~0,-1!"
    echo [INFO] Using Go at: !GO_BIN!
    exit /b 0
)

:: 2. Search common install locations
set "SEARCH_PATHS=C:\Go\bin;C:\Program Files\Go\bin;D:\Go\bin;%USERPROFILE%\go\bin;%LOCALAPPDATA%\go\bin"
for %%p in (%SEARCH_PATHS%) do (
    if exist "%%~p\go.exe" (
        set "GO_BIN=%%~p"
        echo [INFO] Found Go at: !GO_BIN!
        exit /b 0
    )
)

:: 3. Search SDK paths (e.g. %USERPROFILE%\sdk\go1.21\bin)
for /d %%d in ("%USERPROFILE%\sdk\*") do (
    if exist "%%~d\bin\go.exe" (
        set "GO_BIN=%%~d\bin"
        echo [INFO] Found Go at: !GO_BIN!
        exit /b 0
    )
)

:: Not found
exit /b 0

:: ========== Helper: auto-detect MinGW/GCC installation ==========
:find-mingw
set "MINGW_BIN="

:: 1. Check if gcc is already in PATH
where gcc >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where gcc') do set "MINGW_BIN=%%~dpi"
    set "MINGW_BIN=!MINGW_BIN:~0,-1!"
    exit /b 0
)

:: 2. Search known MSYS2 install paths (quoted to handle spaces in paths)
::    Cover ucrt64, mingw64, clang64 environments
for %%m in (
    "C:\msys64"
    "C:\msys2"
    "D:\msys64"
    "D:\msys2"
    "D:\D Program Files\msys2"
    "C:\Program Files\msys64"
    "C:\Program Files\msys2"
) do (
    for %%e in (ucrt64 mingw64 clang64) do (
        if exist "%%~m\%%e\bin\gcc.exe" (
            set "MINGW_BIN=%%~m\%%e\bin"
            exit /b 0
        )
    )
)
:: Also try wildcard: any top-level dir containing "msys" on any drive
for %%d in (C D E F G) do (
    if exist "%%d:\" (
        for /d %%w in ("%%d:\*msys*") do (
            for %%e in (ucrt64 mingw64 clang64) do (
                if exist "%%~w\%%e\bin\gcc.exe" (
                    set "MINGW_BIN=%%~w\%%e\bin"
                    exit /b 0
                )
            )
        )
    )
)

:: 3. Search standalone MinGW-w64
set "MINGW_PATHS=C:\mingw64\bin;D:\mingw64\bin;C:\mingw-w64\bin;D:\mingw-w64\bin"
for %%p in (%MINGW_PATHS%) do (
    if exist "%%~p\gcc.exe" (
        set "MINGW_BIN=%%~p"
        exit /b 0
    )
)

:: 4. Search PATH for common GCC names
where x86_64-w64-mingw32-gcc >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where x86_64-w64-mingw32-gcc') do set "MINGW_BIN=%%~dpi"
    set "MINGW_BIN=!MINGW_BIN:~0,-1!"
    exit /b 0
)

exit /b 0
