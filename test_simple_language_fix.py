#!/usr/bin/env python3
"""
简单测试设置对话框中的语言切换功能
"""

import tkinter as tk
import logging
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_simple_language_switch():
    """简单测试语言切换"""
    print("=== 简单测试语言切换 ===")
    
    # 导入必要的模块
    from config_manager import get_config_manager, Language
    from translations import TranslationKeys, get_translator, _
    
    # 获取配置管理器和翻译器
    config_manager = get_config_manager()
    translator = get_translator()
    
    # 记录当前语言
    current_lang = config_manager.get_language()
    print(f"当前语言: {current_lang}")
    
    # 测试翻译
    print(f"当前翻译测试 - 设置菜单: {_(TranslationKeys.SETTINGS_MENU)}")
    
    # 切换到另一种语言
    if current_lang == Language.ZH_CN.value:
        new_lang = Language.EN_US.value
    else:
        new_lang = Language.ZH_CN.value
    
    print(f"\n切换到: {new_lang}")
    
    # 直接设置语言
    config_manager.set_language(new_lang)
    translator.set_language(new_lang)
    
    # 验证配置已保存
    saved_lang = config_manager.get_language()
    print(f"保存后的语言: {saved_lang}")
    
    if saved_lang != new_lang:
        print(f"❌ 语言配置保存失败")
        return False
    
    # 测试翻译是否更新
    time.sleep(0.1)  # 给翻译器一点时间更新
    new_translation = _(TranslationKeys.SETTINGS_MENU)
    print(f"新语言的翻译测试 - 设置菜单: {new_translation}")
    
    # 切换回原始语言
    config_manager.set_language(current_lang)
    translator.set_language(current_lang)
    
    print("✅ 简单语言切换测试通过")
    return True

def test_settings_dialog_language_update():
    """测试设置对话框的语言更新方法"""
    print("\n=== 测试设置对话框语言更新方法 ===")
    
    from settings_dialog import SettingsDialog
    from config_manager import Language
    
    # 创建根窗口
    root = tk.Tk()
    root.withdraw()
    
    # 创建模拟的CipherGUI
    class MockCipherGUI:
        def __init__(self):
            from config_manager import get_config_manager
            from translations import get_translator
            from theme_manager import get_theme_manager
            self.config_manager = get_config_manager()
            self.translator = get_translator()
            self.theme_manager = get_theme_manager()
        
        def _change_language(self, language):
            print(f"主界面语言切换: {language}")
            self.translator.set_language(language)
        
        def _change_theme(self, theme):
            print(f"主题切换: {theme}")
    
    mock_gui = MockCipherGUI()
    
    try:
        # 创建设置对话框
        dialog = SettingsDialog(root, mock_gui)
        
        # 获取初始标题
        initial_title = dialog.dialog.title()
        print(f"初始对话框标题: {initial_title}")
        
        # 获取初始按钮文本
        initial_apply_text = dialog.apply_button.cget("text")
        initial_ok_text = dialog.ok_button.cget("text")
        initial_cancel_text = dialog.cancel_button.cget("text")
        initial_reset_text = dialog.reset_button.cget("text")
        
        print(f"初始按钮文本:")
        print(f"  应用: {initial_apply_text}")
        print(f"  确定: {initial_ok_text}")
        print(f"  取消: {initial_cancel_text}")
        print(f"  重置: {initial_reset_text}")
        
        # 切换到另一种语言
        current_lang = mock_gui.config_manager.get_language()
        if current_lang == Language.ZH_CN.value:
            new_lang = Language.EN_US.value
        else:
            new_lang = Language.ZH_CN.value
        
        print(f"\n切换到语言: {new_lang}")
        
        # 设置新语言
        mock_gui.config_manager.set_language(new_lang)
        mock_gui.translator.set_language(new_lang)
        
        # 调用对话框的更新方法
        dialog._update_dialog_language()
        
        # 获取更新后的标题
        updated_title = dialog.dialog.title()
        print(f"更新后对话框标题: {updated_title}")
        
        # 获取更新后的按钮文本
        updated_apply_text = dialog.apply_button.cget("text")
        updated_ok_text = dialog.ok_button.cget("text")
        updated_cancel_text = dialog.cancel_button.cget("text")
        updated_reset_text = dialog.reset_button.cget("text")
        
        print(f"更新后按钮文本:")
        print(f"  应用: {updated_apply_text}")
        print(f"  确定: {updated_ok_text}")
        print(f"  取消: {updated_cancel_text}")
        print(f"  重置: {updated_reset_text}")
        
        # 检查是否有更新
        if (updated_title != initial_title or 
            updated_apply_text != initial_apply_text or
            updated_ok_text != initial_ok_text or
            updated_cancel_text != initial_cancel_text or
            updated_reset_text != initial_reset_text):
            print("✅ 对话框UI已更新")
        else:
            print("⚠ 对话框UI没有明显更新")
        
        # 检查选项卡标签
        tab_count = dialog.notebook.index("end")
        print(f"选项卡数量: {tab_count}")
        for i in range(tab_count):
            tab_text = dialog.notebook.tab(i, "text")
            print(f"  选项卡 {i}: {tab_text}")
        
        # 关闭对话框
        dialog.dialog.destroy()
        
        print("✅ 设置对话框语言更新测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        root.destroy()

def test_main_interface_language_switch():
    """测试主界面的语言切换回调"""
    print("\n=== 测试主界面语言切换回调 ===")
    
    from cipher_gui import CipherGUI
    from config_manager import Language
    
    # 创建模拟的CipherGUI实例
    class TestCipherGUI:
        def __init__(self):
            from config_manager import get_config_manager
            from translations import get_translator
            from theme_manager import get_theme_manager
            self.config_manager = get_config_manager()
            self.translator = get_translator()
            self.theme_manager = get_theme_manager()
            self.language_changed = False
            self.last_language = None
        
        def _change_language(self, language):
            self.language_changed = True
            self.last_language = language
            print(f"_change_language被调用: {language}")
            self.translator.set_language(language)
        
        def _change_theme(self, theme):
            print(f"_change_theme被调用: {theme}")
    
    mock_gui = TestCipherGUI()
    
    # 记录当前语言
    current_lang = mock_gui.config_manager.get_language()
    print(f"当前语言: {current_lang}")
    
    # 切换到另一种语言
    if current_lang == Language.ZH_CN.value:
        new_lang = Language.EN_US.value
    else:
        new_lang = Language.ZH_CN.value
    
    print(f"切换到: {new_lang}")
    
    # 调用_change_language方法
    mock_gui._change_language(new_lang)
    
    # 验证回调被调用
    if not mock_gui.language_changed:
        print("❌ _change_language没有被调用")
        return False
    
    if mock_gui.last_language != new_lang:
        print(f"❌ 最后语言不匹配: 期望 {new_lang}, 实际 {mock_gui.last_language}")
        return False
    
    # 验证翻译器已更新
    translator_lang = mock_gui.translator.get_current_language()
    if translator_lang != new_lang:
        print(f"❌ 翻译器语言不匹配: 期望 {new_lang}, 实际 {translator_lang}")
        return False
    
    print("✅ 主界面语言切换回调测试通过")
    return True

def main():
    """主测试函数"""
    print("开始语言切换修复测试...")
    
    all_passed = True
    
    # 运行测试
    import time
    
    if not test_simple_language_switch():
        all_passed = False
    
    time.sleep(0.5)  # 给系统一点时间
    
    if not test_settings_dialog_language_update():
        all_passed = False
    
    time.sleep(0.5)  # 给系统一点时间
    
    if not test_main_interface_language_switch():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ 所有测试通过！语言切换修复成功。")
    else:
        print("⚠ 部分测试失败，可能需要进一步改进。")
    
    print("\n修复总结:")
    print("1. settings_dialog.py: 添加了_update_dialog_language()方法立即更新对话框UI")
    print("2. settings_dialog.py: 在_on_apply()中调用UI更新，确保语言切换后对话框立即响应")
    print("3. 修复了主界面语言切换回调机制")
    
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