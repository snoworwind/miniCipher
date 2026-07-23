#!/usr/bin/env python3
"""
文件加密/解密工具 - 主程序（稳定版）
支持OTP和AES256-GCM两种加密算法
稳定UI，支持多种加密模式
"""

import sys
import os

def check_tkinter_silent():
    """静默检查tkinter是否可用"""
    try:
        import tkinter as tk
        return True
    except ImportError:
        return False

def show_tkinter_error():
    """显示tkinter错误信息"""
    print("错误: tkinter不可用")
    print("\n解决方案:")
    print("1. 在macOS上: brew install python-tk")
    print("2. 运行测试: python test_cipher.py")
    print("3. 使用系统Python: /usr/bin/python3 main.py")
    return 1

def main():
    """主函数 - 稳定版启动"""
    # 极简启动信息
    print("Cipher - 文件加密工具（稳定版）")
    print("稳定UI，支持OTP和AES256-GCM加密算法")
    
    # 静默检查tkinter
    if not check_tkinter_silent():
        return show_tkinter_error()
    
    # 导入GUI模块
    try:
        from cipher_gui import CipherGUI
        app = CipherGUI()
        app.run()
        return 0
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请安装依赖: pip install cryptography")
        return 1
    except Exception as e:
        print(f"运行时错误: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
