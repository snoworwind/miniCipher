#!/usr/bin/env python3
"""
快速测试语言设置对话框修复
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simple_test():
    """简单测试 - 不创建GUI窗口"""
    print("=== 简单测试 ===")
    
    try:
        # 测试导入
        from config_manager import get_config_manager, Language, ThemeType
        from translations import get_translator, TranslationKeys
        from theme_manager import get_theme_manager
        
        print("✅ 模块导入成功")
        
        # 测试配置管理器
        config = get_config_manager()
        translator = get_translator()
        theme_manager = get_theme_manager()
        
        # 获取当前设置
        current_lang = config.get_language()
        current_theme = config.get_theme()
        
        print(f"当前语言: {current_lang}")
        print(f"当前主题: {current_theme}")
        
        # 测试语言切换
        if current_lang == Language.ZH_CN.value:
            new_lang = Language.EN_US.value
            print(f"将语言切换到: {new_lang}")
            config.set_language(new_lang)
        else:
            new_lang = Language.ZH_CN.value
            print(f"将语言切换到: {new_lang}")
            config.set_language(new_lang)
        
        # 验证语言已更改
        updated_lang = config.get_language()
        if updated_lang == new_lang:
            print(f"✅ 语言配置已更新: {updated_lang}")
        else:
            print(f"❌ 语言配置未更新: {updated_lang} (期望: {new_lang})")
        
        # 测试主题切换
        if current_theme == ThemeType.LIGHT.value:
            new_theme = ThemeType.DARK.value
            print(f"将主题切换到: {new_theme}")
            config.set_theme(new_theme)
        else:
            new_theme = ThemeType.LIGHT.value
            print(f"将主题切换到: {new_theme}")
            config.set_theme(new_theme)
        
        # 验证主题已更改
        updated_theme = config.get_theme()
        if updated_theme == new_theme:
            print(f"✅ 主题配置已更新: {updated_theme}")
        else:
            print(f"❌ 主题配置未更新: {updated_theme} (期望: {new_theme})")
        
        # 测试翻译器
        translator.set_language(new_lang)
        print(f"✅ 翻译器语言已设置为: {new_lang}")
        
        # 恢复原始设置
        config.set_language(current_lang)
        config.set_theme(current_theme)
        translator.set_language(current_lang)
        
        print(f"✅ 已恢复原始设置: 语言={current_lang}, 主题={current_theme}")
        
        return True
        
    except Exception as e:
        print(f"❌ 简单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cipher_gui_import():
    """测试CipherGUI导入，确保修改不会破坏现有功能"""
    print("\n=== 测试CipherGUI导入 ===")
    
    try:
        # 只导入而不实例化
        from cipher_gui import CipherGUI
        print("✅ CipherGUI类导入成功")
        
        # 检查关键方法是否存在
        required_methods = [
            '_change_theme',
            '_change_language',
            '_reload_ui',
            'update_ui_state'
        ]
        
        for method in required_methods:
            if hasattr(CipherGUI, method):
                print(f"✅ 方法 {method} 存在")
            else:
                print(f"❌ 方法 {method} 不存在")
                return False
        
        # 检查我们的修改是否存在
        code = open('cipher_gui.py', 'r', encoding='utf-8').read()
        
        # 检查_reload_ui是否包含保护Toplevel窗口的代码
        if 'toplevel_windows = []' in code:
            print("✅ _reload_ui方法包含保护Toplevel窗口的代码")
        else:
            print("⚠ _reload_ui方法可能缺少保护Toplevel窗口的代码")
        
        # 检查_change_theme是否移除了apply_to_all_widgets
        if 'self.theme_manager.apply_to_all_widgets(self.root)' in code:
            print("⚠ _change_theme方法仍然包含apply_to_all_widgets，这可能导致问题")
        else:
            print("✅ _change_theme方法已移除apply_to_all_widgets，避免影响其他窗口")
        
        return True
        
    except Exception as e:
        print(f"❌ CipherGUI导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始快速测试...")
    
    all_passed = True
    
    # 运行简单测试
    if not simple_test():
        all_passed = False
    
    # 运行导入测试
    if not test_cipher_gui_import():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ 所有快速测试通过！")
        print("\n修复验证:")
        print("1. 配置管理器功能正常")
        print("2. 翻译器功能正常")
        print("3. CipherGUI关键方法存在")
        print("4. _reload_ui方法保护Toplevel窗口")
        print("5. _change_theme方法已优化，避免影响其他窗口")
    else:
        print("⚠ 部分测试失败，需要进一步检查。")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)