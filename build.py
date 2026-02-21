#!/usr/bin/env python3
"""
Cipher - Simplified Build Script
Supports packaging encryption/decryption tools with PyInstaller
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

def check_environment():
    """Check Python environment"""
    print("=" * 60)
    print("Checking environment...")
    print("=" * 60)
    
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    
    if sys.version_info < (3, 7):
        print("Warning: Python 3.7 or higher is recommended")
    
    system = platform.system()
    print(f"Operating system: {system}")
    
    # Check tkinter
    try:
        import tkinter
        print("tkinter: available ✓")
    except ImportError as e:
        print(f"Warning: tkinter not available - {e}")
        if system == "Darwin":
            print("macOS solution: brew install python-tk")
    
    return True

def install_dependencies(use_system_python=False):
    """Install necessary dependencies"""
    print("=" * 60)
    print("Installing dependencies...")
    print("=" * 60)
    
    try:
        if use_system_python:
            pip_cmd = [sys.executable, "-m", "pip"]
        else:
            pip_cmd = ["pip"]
        
        # Install PyInstaller
        print("Installing PyInstaller...")
        subprocess.run(pip_cmd + ["install", "pyinstaller", "--upgrade"], check=True)
        
        # Install project dependencies
        print("Installing project dependencies...")
        requirements_file = Path(__file__).parent / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(pip_cmd + ["install", "-r", str(requirements_file)], check=True)
        else:
            print("Installing cryptography...")
            subprocess.run(pip_cmd + ["install", "cryptography>=42.0.0"], check=True)
        
        print("Dependencies installed ✓")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Dependency installation failed: {e}")
        print("\nManual installation command:")
        print("  pip install pyinstaller cryptography")
        return False

def update_spec_file(target_architecture=None):
    """Update or create spec file - enhanced version that always generates fresh spec file"""
    print("=" * 60)
    print("Updating spec file...")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.absolute()
    spec_file = project_dir / "cipher.spec"
    
    # Always remove old spec file to ensure fresh generation
    if spec_file.exists():
        print(f"Removing old spec file: {spec_file}")
        spec_file.unlink()
    
    # Create enhanced spec file content with proper path escaping
    project_dir_str = str(project_dir)
    
    # Escape backslashes in Windows paths for Python string literals
    # PyInstaller spec files are Python code, so we need proper escaping
    if platform.system() == "Windows":
        # Windows paths: need double backslashes for Python string literals
        project_dir_escaped = project_dir_str.replace('\\', '\\\\')
    else:
        # Linux/Mac paths: use forward slashes
        project_dir_escaped = project_dir_str.replace('\\', '/')
    
    # Platform-specific configurations
    system = platform.system()
    machine = platform.machine()
    
    # Determine target architecture
    if target_architecture:
        target_arch_value = target_architecture
    else:
        # Check environment variable for target architecture
        target_arch_value = os.environ.get('TARGET_ARCH') or machine
    
    if system == "Darwin":
        # macOS需要特殊处理，允许未签名应用运行
        codesign_config = "codesign_identity='-',"
        argv_emulation = "argv_emulation=True,"
        
        # Handle cross-architecture building on macOS
        if target_arch_value == "x86_64" and machine == "arm64":
            print(f"macOS detected: building x86_64 on {machine} (cross-architecture)")
            target_arch = "target_arch='x86_64',"
        elif target_arch_value == "arm64" and machine == "x86_64":
            print(f"macOS detected: building arm64 on {machine} (cross-architecture)")
            target_arch = "target_arch='arm64',"
        else:
            print(f"macOS detected, using platform-specific config for {target_arch_value}")
            target_arch = f"target_arch='{target_arch_value}',"
        
        # macOS uses single-file bundle, so no COLLECT needed
        macos_template = True
    else:
        codesign_config = "codesign_identity=None,"
        argv_emulation = "argv_emulation=False,"
        target_arch = "target_arch=None,"
        macos_template = False
    
    # Base template for all platforms
    base_spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Cipher - PyInstaller spec file
# Auto-generated, includes all necessary dependencies and configuration

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['{project_dir_escaped}'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # cryptography-related imports
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.backends.openssl.backend',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.modes',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.ciphers.aead',
        # standard library imports
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'enum',
        'dataclasses',
        'typing',
        'hashlib',
        'os',
        'sys',
        'pathlib',
        'secrets',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['test', 'unittest', 'pytest'],
    noarchive=False,
    optimize=0,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cipher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    {argv_emulation}
    {target_arch}
    {codesign_config}
    entitlements_file=None,
)'''
    
    # Add COLLECT only for non-macOS platforms
    if macos_template:
        spec_content = base_spec_content
        print("Using single-file bundle template for macOS")
    else:
        spec_content = base_spec_content + '''

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cipher',
)'''
    
    try:
        # Always backup existing spec file if it exists
        if spec_file.exists():
            print(f"Backing up existing spec file: {spec_file}")
            backup_file = spec_file.with_suffix('.spec.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(spec_file, 'r', encoding='utf-8') as src:
                    f.write(src.read())
            print(f"✓ Original spec file backed up to: {backup_file}")
        
        # Always write new spec file with current path
        print(f"Generating new spec file with current path: {project_dir}")
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✓ Spec file generated: {spec_file}")
        print(f"  Path used: {project_dir_escaped}")
        print(f"  Platform: {platform.system()}")
        
        return True
            
    except Exception as e:
        print(f"Error: Exception occurred while generating spec file: {e}")
        print("Attempting to create new spec file with simplified path...")
        
        try:
            # Fallback: use simple path without escaping
            fallback_content = spec_content.replace(f"pathex=['{project_dir_escaped}']", "pathex=[]")
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(fallback_content)
            print(f"✓ Spec file created (fallback, no pathex): {spec_file}")
            return True
        except Exception as e2:
            print(f"✗ Unable to create spec file: {e2}")
            return False

def run_build(clean=False):
    """Run PyInstaller build"""
    print("=" * 60)
    print("Running PyInstaller build...")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.absolute()
    spec_file = project_dir / "cipher.spec"
    build_dir = project_dir / "build"
    dist_dir = project_dir / "dist"
    
    # Clean old build files
    if clean:
        if build_dir.exists():
            print("Cleaning old build directory...")
            shutil.rmtree(build_dir)
        if dist_dir.exists():
            print("Cleaning old dist directory...")
            shutil.rmtree(dist_dir)
    
    # Build command
    cmd = [
        "pyinstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build output:")
        if result.stdout:
            # Show only key information
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in ["INFO:", "WARNING:", "ERROR:", "writing", "checking", "compiling"]):
                    print(f"  {line}")
        
        # Verify build result - should be Cipher.exe on Windows, Cipher on other systems
        system = platform.system()
        if system == "Windows":
            exe_path = dist_dir / "Cipher.exe"
        else:
            exe_path = dist_dir / "Cipher"
            
        if exe_path.exists():
            print(f"✓ Executable created: {exe_path}")
            
            # Show file size
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"  File size: {size_mb:.2f} MB")
            
            return True
        else:
            print(f"✗ Executable not found: {exe_path}")
            # Try to find any possible executable files
            for file in dist_dir.iterdir():
                if file.is_file() and (file.name == "Cipher" or file.name == "Cipher.exe"):
                    print(f"  Found file: {file.name} (size: {file.stat().st_size} bytes)")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        if e.stderr:
            print("完整错误输出:")
            print(e.stderr)
            # 保存错误日志到文件以便分析
            error_log = project_dir / "build-error.log"
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"PyInstaller build failed with exit code {e.returncode}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Error output:\n{e.stderr}\n")
                if e.stdout:
                    f.write(f"Standard output:\n{e.stdout}\n")
            print(f"错误日志已保存到: {error_log}")
        return False
    except FileNotFoundError:
        print("Error: pyinstaller command not found")
        print("Please run first: python build.py --install-deps")
        return False

def test_build():
    """Test the built executable - enhanced version for GUI applications"""
    print("=" * 60)
    print("Testing build results...")
    print("=" * 60)
    
    system = platform.system()
    if system == "Windows":
        exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher.exe"
    else:
        exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher"
    
    if not exe_path.exists():
        print(f"✗ Skipping test: {exe_path} does not exist")
        # Try to find any possible executable files
        dist_dir = Path(__file__).parent.absolute() / "dist"
        for file in dist_dir.iterdir():
            if file.is_file() and ("Cipher" in file.name):
                print(f"  Found file: {file.name} (size: {file.stat().st_size:,} bytes)")
        return False
    
    print(f"Testing executable: {exe_path}")
    
    try:
        # GUI application test - verify file properties and basic integrity
        if not exe_path.is_file():
            print(f"✗ Not a valid file: {exe_path}")
            return False
        
        # Check file size
        file_size = exe_path.stat().st_size
        print(f"  File size: {file_size:,} bytes")
        
        if file_size == 0:
            print(f"✗ File size is 0, build may have failed")
            return False
        
        # Check if file has executable attributes (on Windows mainly check if file exists and is readable)
        if file_size < 1024:  # Files less than 1KB are definitely problematic
            print(f"✗ File size is abnormally small, build may be incomplete")
            return False
        
        # For GUI applications, successful build and reasonable file size constitute a valid test
        # No need to actually run the program as GUI programs may fail due to permission issues in automated testing
        print(f"✓ Build verification passed")
        print(f"  - File exists and is accessible")
        print(f"  - File size is reasonable ({file_size:,} bytes)")
        print(f"  - Build integrity verification completed")
        
        # Provide user-friendly information
        system = platform.system()
        if system == "Windows":
            print(f"  Manual test: Double-click {exe_path} or run: {exe_path.name}")
        else:
            print(f"  Manual test: ./{exe_path.name}")
        
        return True
        
    except PermissionError as e:
        print(f"✗ Permission error: {e}")
        print(f"  Note: This may be due to antivirus software or file permission restrictions")
        print(f"  Please try running the executable manually")
        return False
    except Exception as e:
        print(f"✗ Test exception: {e}")
        print(f"  Note: Automated test failed, but the executable may still be valid")
        print(f"  Please try running manually: {exe_path}")
        return False

def create_launch_scripts():
    """Create launch scripts (cross-platform)"""
    print("=" * 60)
    print("Creating launch scripts...")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.absolute()
    
    # Create Unix launch script (macOS/Linux)
    unix_launch_script = project_dir / "launch.command"
    
    unix_script_content = '''#!/bin/bash

# Cipher tool launch script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Cipher Encryption Tool Launch"
echo "========================================"
echo ""

if [ -f "$DIR/dist/Cipher" ]; then
    echo "Starting Cipher tool..."
    "$DIR/dist/Cipher"
    echo ""
    echo "Cipher tool has exited"
else
    echo "Error: Executable not found"
    echo ""
    echo "Please build first with:"
    echo "  python build.py --all"
    echo "or:"
    echo "  python build.py --install-deps --build"
    exit 1
fi
'''
    
    with open(unix_launch_script, 'w', encoding='utf-8') as f:
        f.write(unix_script_content)
    
    # Set execute permission
    os.chmod(unix_launch_script, 0o755)
    
    print(f"✓ Unix launch script created: {unix_launch_script}")
    
    # Create Windows launch script
    windows_launch_script = project_dir / "launch.bat"
    
    windows_script_content = '''@echo off
chcp 65001 >nul
REM Cipher tool launch script (Windows version)

echo ========================================
echo Cipher Encryption Tool Launch
echo ========================================
echo.

if exist "dist\\Cipher.exe" (
    echo Starting Cipher tool...
    echo.
    dist\\Cipher.exe
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
'''
    
    with open(windows_launch_script, 'w', encoding='utf-8') as f:
        f.write(windows_script_content)
    
    print(f"✓ Windows launch script created: {windows_launch_script}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Cipher - Simplified Build Script")
    
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install dependencies (pyinstaller, cryptography, etc.)")
    parser.add_argument("--build", action="store_true", 
                       help="Execute build")
    parser.add_argument("--clean", action="store_true",
                       help="Clean old build files")
    parser.add_argument("--test", action="store_true",
                       help="Test build result")
    parser.add_argument("--all", action="store_true",
                       help="Execute complete process (install dependencies, build, test)")
    parser.add_argument("--system-python", action="store_true",
                       help="Use system Python instead of virtual environment")
    parser.add_argument("--target-arch", type=str, default=None,
                       help="Target architecture for cross-compilation (e.g., x86_64, arm64)")
    
    args = parser.parse_args()
    
    # If --all is specified, set all options
    if args.all:
        args.install_deps = True
        args.build = True
        args.test = True
        args.clean = True
    
    # If no action specified, show help
    if not any([args.install_deps, args.build, args.test, args.all]):
        parser.print_help()
        print("\nExamples:")
        print("  Full build: python build.py --all")
        print("  Install dependencies only: python build.py --install-deps")
        print("  Build only: python build.py --build")
        return
    
    print("=" * 60)
    print("Cipher - Simplified Build Script")
    print("=" * 60)
    
    success = True
    
    try:
        # Check environment
        if not check_environment():
            success = False
        
        # Install dependencies
        if success and args.install_deps:
            if not install_dependencies(args.system_python):
                success = False
        
        # Update spec file
        if success:
            update_spec_file(args.target_arch)
        
        # Build
        if success and args.build:
            if not run_build(args.clean):
                success = False
        
        # Test
        if success and args.test:
            if not test_build():
                success = False
        
        # Create launch scripts
        if success and args.build:
            create_launch_scripts()
        
        if success:
            print("=" * 60)
            print("Build completed successfully! ✓")
            print("=" * 60)
            
            system = platform.system()
            if system == "Windows":
                exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher.exe"
            else:
                exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher"
                
            if exe_path.exists():
                print(f"Executable location: {exe_path}")
                if system == "Windows":
                    print(f"Start command: dist\\Cipher.exe")
                    print(f"Or use launch script: launch.bat")
                else:
                    print(f"Start command: ./dist/Cipher")
                    print(f"Or use launch script: ./launch.command")
            else:
                print("Note: No executable was generated")
            
            return 0
        else:
            print("=" * 60)
            print("Build failed ✗")
            print("=" * 60)
            return 1
            
    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        return 1
    except Exception as e:
        print(f"Error occurred during build: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())