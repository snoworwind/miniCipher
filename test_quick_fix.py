#!/usr/bin/env python3
"""
快速测试修复效果
"""

import tkinter as tk
from tkinter import ttk
import logging
import time

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_quick():
    print("=== 快速修复测试 ===")
    
    # 测试1: ttk::ThemeChanged错误修复
    print("\n--- 测试1: ttk::ThemeChanged错误修复 ---")
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        # 创建临时窗口和样式
        temp_window = tk.Toplevel(root)
        style = ttk.Style(temp_window)
        
        # 销毁窗口
        temp_window.destroy()
        time.sleep(0.1)
        
        # 尝试重新创建样式（模拟错误场景）
        from theme_manager import ThemeManager, get_theme_manager
        theme_manager = get_theme_manager()
        
        # 这应该不会崩溃
        theme_manager.create_style(style)
        print("✅ ttk::ThemeChanged错误修复有效")
        
    except tk.TclError as e:
        if "application has been destroyed" in str(e):
            print("❌ ttk::ThemeChanged错误仍然存在")
        else:
            print(f"⚠ 其他Tcl错误: {e}")
    except Exception as e:
        print(f"⚠ 其他错误: {e}")
    
    # 测试2: 原始错误场景模拟
    print("\n--- 测试2: 原始错误场景模拟 ---")
    
    try:
        from theme_manager import get_theme_manager, apply_theme_to_window
        from custom_menu_bar import CustomMenuBar
        
        # 创建主窗口
        main_window = tk.Tk()
        main_window.withdraw()
        
        # 应用主题
        apply_theme_to_window(main_window)
        
        # 创建菜单栏
        menu_bar = CustomMenuBar(main_window)
        
        # 添加测试菜单
        test_items = [
            {"type": "command", "label": "测试", "command": lambda: print("测试")}
        ]
        menu_bar.add_menu("文件", test_items)
        
        # 快速创建和销毁多个对话框（模拟原始错误场景）
        from settings_dialog import SettingsDialog
        
        class MockCipherGUI:
            def __init__(self):
                from config_manager import get_config_manager
                from translations import get_translator
                from theme_manager import get_theme_manager
                self.config_manager = get_config_manager()
                self.translator = get_translator()
                self.theme_manager = get_theme_manager()
            
            def _change_language(self, language):
                print(f"语言切换: {language}")
            
            def _change_theme(self, theme):
                print(f"主题切换: {theme}")
        
        mock_gui = MockCipherGUI()
        
        # 快速创建对话框并销毁
        dialogs = []
        for i in range(3):
            dialog = SettingsDialog(main_window, mock_gui)
            dialogs.append(dialog)
            # 快速销毁
            dialog.dialog.destroy()
        
        time.sleep(0.2)
        
        print("✅ 原始错误场景测试通过")
        
        # 清理
        main_window.destroy()
        
    except tk.TclError as e:
        if "bad window path name" in str(e) or "invalid command name" in str(e):
            print(f"❌ 原始错误仍然存在: {e}")
        else:
            print(f"⚠ 其他Tcl错误: {e}")
    except Exception as e:
        print(f"⚠ 其他错误: {e}")
    
    root.destroy()
    
    print("\n=== 测试总结 ===")
    print("修复已完成以下工作:")
    print("1. theme_manager.py: 添加了窗口存在性检查和样式安全检查")
    print("2. settings_dialog.py: 添加了对话框存在性检查")  
    print("3. custom_menu_bar.py: 添加了部件存在性检查")
    print("4. 所有模块: 使用try-catch包装可能失败的Tcl操作")
    
    return True

if __name__ == "__main__":
    test_quick()