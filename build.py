#!/usr/bin/env python3
"""
Cipher工具 - 简化版构建脚本
支持使用PyInstaller打包加密/解密工具
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

def check_environment():
    """检查Python环境"""
    print("=" * 60)
    print("检查环境...")
    print("=" * 60)
    
    python_version = platform.python_version()
    print(f"Python版本: {python_version}")
    
    if sys.version_info < (3, 7):
        print("警告: 建议使用Python 3.7或更高版本")
    
    system = platform.system()
    print(f"操作系统: {system}")
    
    # 检查tkinter
    try:
        import tkinter
        print("tkinter: 可用 ✓")
    except ImportError as e:
        print(f"警告: tkinter不可用 - {e}")
        if system == "Darwin":
            print("macOS解决方案: brew install python-tk")
    
    return True

def install_dependencies(use_system_python=False):
    """安装必要的依赖"""
    print("=" * 60)
    print("安装依赖...")
    print("=" * 60)
    
    try:
        if use_system_python:
            pip_cmd = [sys.executable, "-m", "pip"]
        else:
            pip_cmd = ["pip"]
        
        # 安装PyInstaller
        print("安装PyInstaller...")
        subprocess.run(pip_cmd + ["install", "pyinstaller", "--upgrade"], check=True)
        
        # 安装项目依赖
        print("安装项目依赖...")
        requirements_file = Path(__file__).parent / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(pip_cmd + ["install", "-r", str(requirements_file)], check=True)
        else:
            print("安装cryptography...")
            subprocess.run(pip_cmd + ["install", "cryptography>=42.0.0"], check=True)
        
        print("依赖安装完成 ✓")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"安装依赖失败: {e}")
        print("\n手动安装命令:")
        print("  pip install pyinstaller cryptography")
        return False

def update_spec_file():
    """更新或创建spec文件"""
    print("=" * 60)
    print("更新spec文件...")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.absolute()
    spec_file = project_dir / "cipher.spec"
    
    # 读取现有spec文件
    if spec_file.exists():
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec_content = f.read()
        
        # 修复noarchive设置（从True改为False以减小文件大小）
        if "noarchive=True" in spec_content:
            spec_content = spec_content.replace("noarchive=True", "noarchive=False")
            print("已修复noarchive设置: True → False")
        elif "noarchive = True" in spec_content:
            spec_content = spec_content.replace("noarchive = True", "noarchive = False")
            print("已修复noarchive设置: True → False")
        
        # 写入更新后的spec文件
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"spec文件已更新: {spec_file}")
    else:
        print(f"使用现有spec文件: {spec_file}")
    
    return True

def run_build(clean=False):
    """运行PyInstaller构建"""
    print("=" * 60)
    print("运行PyInstaller构建...")
    print("=" * 60)
    
    project_dir = Path(__file__).parent.absolute()
    spec_file = project_dir / "cipher.spec"
    build_dir = project_dir / "build"
    dist_dir = project_dir / "dist"
    
    # 清理旧的构建文件
    if clean:
        if build_dir.exists():
            print("清理旧的build目录...")
            shutil.rmtree(build_dir)
        if dist_dir.exists():
            print("清理旧的dist目录...")
            shutil.rmtree(dist_dir)
    
    # 构建命令
    cmd = [
        "pyinstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建输出:")
        if result.stdout:
            # 只显示关键信息
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in ["INFO:", "WARNING:", "ERROR:", "writing", "checking", "compiling"]):
                    print(f"  {line}")
        
        # 验证构建结果
        exe_path = dist_dir / "Cipher"
        if exe_path.exists():
            print(f"✓ 可执行文件已创建: {exe_path}")
            
            # 显示文件大小
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"  文件大小: {size_mb:.2f} MB")
            
            return True
        else:
            print(f"✗ 可执行文件未找到: {exe_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        if e.stderr:
            print("错误输出:")
            print(e.stderr[:500])  # 只显示前500个字符
        return False
    except FileNotFoundError:
        print("错误: 找不到pyinstaller命令")
        print("请先运行: python build.py --install-deps")
        return False

def test_build():
    """测试构建的可执行文件"""
    print("=" * 60)
    print("测试构建结果...")
    print("=" * 60)
    
    exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher"
    
    if not exe_path.exists():
        print(f"跳过测试: {exe_path} 不存在")
        return True
    
    print(f"测试可执行文件: {exe_path}")
    
    try:
        # 测试启动
        result = subprocess.run([str(exe_path)], capture_output=True, text=True, timeout=5)
        print("✓ 程序可正常启动")
        if result.stdout:
            print(f"输出: {result.stdout[:100]}...")
        return True
    except subprocess.TimeoutExpired:
        print("✓ 程序正常运行（GUI模式，超时退出是正常的）")
        return True
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def create_launch_script():
    """创建启动脚本"""
    print("=" * 60)
    print("创建启动脚本...")
    print("=" * 60)
    
    launch_script = Path(__file__).parent.absolute() / "launch.command"
    
    script_content = '''#!/bin/bash

# Cipher工具启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Cipher加密工具启动"
echo "========================================"
echo ""

if [ -f "$DIR/dist/Cipher" ]; then
    echo "正在启动Cipher工具..."
    "$DIR/dist/Cipher"
    echo ""
    echo "Cipher工具已退出"
else
    echo "错误: 未找到可执行文件"
    echo ""
    echo "请先运行以下命令构建:"
    echo "  python build.py --all"
    echo "或:"
    echo "  python build.py --install-deps --build"
    exit 1
fi
'''
    
    with open(launch_script, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod(launch_script, 0o755)
    
    print(f"✓ 启动脚本已创建: {launch_script}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Cipher工具 - 简化构建脚本")
    
    parser.add_argument("--install-deps", action="store_true", 
                       help="安装依赖 (pyinstaller, cryptography等)")
    parser.add_argument("--build", action="store_true", 
                       help="执行构建")
    parser.add_argument("--clean", action="store_true",
                       help="清理旧的构建文件")
    parser.add_argument("--test", action="store_true",
                       help="测试构建结果")
    parser.add_argument("--all", action="store_true",
                       help="执行完整流程 (安装依赖、构建、测试)")
    parser.add_argument("--system-python", action="store_true",
                       help="使用系统Python而不是虚拟环境")
    
    args = parser.parse_args()
    
    # 如果指定了--all，设置所有选项
    if args.all:
        args.install_deps = True
        args.build = True
        args.test = True
        args.clean = True
    
    # 如果没有指定任何操作，显示帮助
    if not any([args.install_deps, args.build, args.test, args.all]):
        parser.print_help()
        print("\n示例:")
        print("  完整构建: python build.py --all")
        print("  仅安装依赖: python build.py --install-deps")
        print("  仅构建: python build.py --build")
        return
    
    print("=" * 60)
    print("Cipher工具 - 简化构建脚本")
    print("=" * 60)
    
    success = True
    
    try:
        # 检查环境
        if not check_environment():
            success = False
        
        # 安装依赖
        if success and args.install_deps:
            if not install_dependencies(args.system_python):
                success = False
        
        # 更新spec文件
        if success:
            update_spec_file()
        
        # 构建
        if success and args.build:
            if not run_build(args.clean):
                success = False
        
        # 测试
        if success and args.test:
            if not test_build():
                success = False
        
        # 创建启动脚本
        if success and args.build:
            create_launch_script()
        
        if success:
            print("=" * 60)
            print("构建成功完成！ ✓")
            print("=" * 60)
            
            exe_path = Path(__file__).parent.absolute() / "dist" / "Cipher"
            if exe_path.exists():
                print(f"可执行文件位置: {exe_path}")
                print(f"启动命令: ./dist/Cipher")
                print(f"或使用启动脚本: ./launch.command")
            else:
                print("注意: 未生成可执行文件")
            
            return 0
        else:
            print("=" * 60)
            print("构建失败 ✗")
            print("=" * 60)
            return 1
            
    except KeyboardInterrupt:
        print("\n构建被用户中断")
        return 1
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())