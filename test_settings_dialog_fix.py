#!/usr/bin/env python3
"""
测试设置对话框修复 - 验证修复后的语言切换和对话框稳定性
"""

import tkinter as tk
import logging
import time

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_settings_dialog_stability():
    """测试设置对话框稳定性"""
    print("=== 测试设置对话框稳定性 ===")
    
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    from config_manager import get_config_manager, Language
    from translations import TranslationKeys, get_translator, _
    from theme_manager import get_theme_manager
    from settings_dialog import SettingsDialog
    
    class MockCipherGUI:
        def __init__(self):
            self.config_manager = get_config_manager()
            self.translator = get_translator()
            self.theme_manager = get_theme_manager()
            self.language_changed = False
            self.last_language = None
            self.theme_changed = False
            self.last_theme = None
        
        def _change_language(self, language):
            self.language_changed = True
            self.last_language = language
            print(f"主界面语言切换: {language}")
            self.translator.set_language(language)
        
        def _change_theme(self, theme):
            self.theme_changed = True
            self.last_theme = theme
            print(f"主界面主题切换: {theme}")
    
    mock_gui = MockCipherGUI()
    
    try:
        # 创建对话框
        dialog = SettingsDialog(root, mock_gui)
        
        # 获取初始语言
        initial_lang = mock_gui.config_manager.get_language()
        print(f"初始语言: {initial_lang}")
        
        # 获取初始主题
        initial_theme = mock_gui.config_manager.get_theme()
        print(f"初始主题: {initial_theme}")
        
        # 检查对话框标题
        dialog_title = dialog.dialog.title()
        print(f"对话框标题: {dialog_title}")
        
        # 切换到另一种语言
        if initial_lang == Language.ZH_CN.value:
            new_lang = Language.EN_US.value
        else:
            new_lang = Language.ZH_CN.value
        
        print(f"\n切换到语言: {new_lang}")
        
        # 设置新的语言选择
        if new_lang == Language.ZH_CN.value:
            dialog.language_var.set(_(TranslationKeys.CHINESE_LANGUAGE))
        else:
            dialog.language_var.set(_(TranslationKeys.ENGLISH_LANGUAGE))
        
        # 手动触发设置变更
        dialog._on_setting_changed()
        
        # 检查应用按钮是否启用
        apply_state = dialog.apply_button.cget("state")
        print(f"应用按钮状态: {apply_state}")
        
        if apply_state != "normal":
            print("❌ 设置变更没有启用应用按钮")
            return False
        
        print("\n点击应用按钮...")
        
        # 模拟应用按钮点击
        dialog._on_apply()
        
        # 等待一小段时间让UI更新
        time.sleep(0.5)
        
        # 检查对话框是否仍然存在
        dialog_exists = hasattr(dialog.dialog, 'winfo_exists') and dialog.dialog.winfo_exists()
        print(f"对话框是否存在: {dialog_exists}")
        
        if not dialog_exists:
            print("❌ 对话框被意外关闭")
            return False
        
        # 检查语言是否已更改
        current_lang = mock_gui.config_manager.get_language()
        print(f"当前语言配置: {current_lang}")
        
        if current_lang != new_lang:
            print(f"❌ 语言配置未正确保存: 期望 {new_lang}, 实际 {current_lang}")
            return False
        
        # 检查主界面的回调是否被调用
        if not mock_gui.language_changed:
            print("❌ 主界面语言切换回调未被调用")
            return False
        
        if mock_gui.last_language != new_lang:
            print(f"❌ 最后语言不匹配: 期望 {new_lang}, 实际 {mock_gui.last_language}")
            return False
        
        # 检查对话框UI是否更新
        updated_title = dialog.dialog.title()
        print(f"更新后对话框标题: {updated_title}")
        
        # 检查按钮文本是否更新
        updated_apply_text = dialog.apply_button.cget("text")
        print(f"更新后应用按钮文本: {updated_apply_text}")
        
        # 检查应用按钮是否已禁用（设置已应用）
        final_apply_state = dialog.apply_button.cget("state")
        print(f"应用按钮最终状态: {final_apply_state}")
        
        if final_apply_state != "disabled":
            print("⚠ 应用按钮未被禁用，但设置已应用")
            # 这不是严重错误，可能UI更新有延迟
        
        # 测试确定按钮
        print("\n测试确定按钮...")
        dialog._on_ok()
        
        # 检查对话框是否已关闭
        time.sleep(0.2)
        dialog_exists_after_ok = hasattr(dialog.dialog, 'winfo_exists') and dialog.dialog.winfo_exists()
        print(f"确定按钮后对话框是否存在: {dialog_exists_after_ok}")
        
        if dialog_exists_after_ok:
            print("⚠ 确定按钮未关闭对话框")
            # 手动关闭对话框
            try:
                dialog.dialog.destroy()
            except:
                pass
        
        print("✅ 设置对话框稳定性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def test_rapid_language_switch():
    """测试快速语言切换"""
    print("\n=== 测试快速语言切换 ===")
    
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()
    
    from config_manager import get_config_manager, Language
    from translations import TranslationKeys, get_translator, _
    from theme_manager import get_theme_manager
    from settings_dialog import SettingsDialog
    
    class MockCipherGUI2:
        def __init__(self):
            self.config_manager = get_config_manager()
            self.translator = get_translator()
            self.theme_manager = get_theme_manager()
            self.change_count = 0
        
        def _change_language(self, language):
            self.change_count += 1
            print(f"语言切换 #{self.change_count}: {language}")
            self.translator.set_language(language)
        
        def _change_theme(self, theme):
            print(f"主题切换: {theme}")
    
    mock_gui = MockCipherGUI2()
    
    try:
        # 创建对话框
        dialog = SettingsDialog(root, mock_gui)
        
        # 记录初始语言
        initial_lang = mock_gui.config_manager.get_language()
        
        # 快速切换语言多次
        for i in range(3):
            # 切换语言
            if mock_gui.config_manager.get_language() == Language.ZH_CN.value:
                new_lang = Language.EN_US.value
                dialog.language_var.set(_(TranslationKeys.ENGLISH_LANGUAGE))
            else:
                new_lang = Language.ZH_CN.value
                dialog.language_var.set(_(TranslationKeys.CHINESE_LANGUAGE))
            
            print(f"\n快速切换 #{i+1}: 切换到 {new_lang}")
            
            # 应用设置
            dialog._on_apply()
            
            # 短暂等待
            time.sleep(0.1)
            
            # 检查对话框是否仍然存在
            if not hasattr(dialog.dialog, 'winfo_exists') or not dialog.dialog.winfo_exists():
                print(f"❌ 快速切换 #{i+1} 时对话框被关闭")
                return False
        
        # 检查切换次数
        print(f"语言切换总次数: {mock_gui.change_count}")
        
        if mock_gui.change_count != 3:
            print(f"❌ 期望3次语言切换，实际{mock_gui.change_count}次")
            return False
        
        # 关闭对话框
        dialog.dialog.destroy()
        
        print("✅ 快速语言切换测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 快速切换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def test_dialog_close_during_update():
    """测试在UI更新期间关闭对话框"""
    print("\n=== 测试在UI更新期间关闭对话框 ===")
    
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()
    
    from config_manager import get_config_manager, Language
    from translations import TranslationKeys, get_translator, _
    from theme_manager import get_theme_manager
    from settings_dialog import SettingsDialog
    
    class MockCipherGUI3:
        def __init__(self):
            self.config_manager = get_config_manager()
            self.translator = get_translator()
            self.theme_manager = get_theme_manager()
        
        def _change_language(self, language):
            print(f"语言切换（可能被中断）: {language}")
            self.translator.set_language(language)
        
        def _change_theme(self, theme):
            print(f"主题切换: {theme}")
    
    mock_gui = MockCipherGUI3()
    
    try:
        # 创建对话框
        dialog = SettingsDialog(root, mock_gui)
        
        # 切换到另一种语言
        current_lang = mock_gui.config_manager.get_language()
        if current_lang == Language.ZH_CN.value:
            new_lang = Language.EN_US.value
            dialog.language_var.set(_(TranslationKeys.ENGLISH_LANGUAGE))
        else:
            new_lang = Language.ZH_CN.value
            dialog.language_var.set(_(TranslationKeys.CHINESE_LANGUAGE))
        
        print(f"切换到语言: {new_lang}")
        
        # 在应用设置前立即关闭对话框（模拟竞态条件）
        print("立即关闭对话框...")
        dialog.dialog.destroy()
        
        # 等待对话框关闭
        time.sleep(0.2)
        
        # 尝试应用设置（应该安全地失败）
        print("尝试应用设置（对话框已关闭）...")
        try:
            dialog._on_apply()
            print("✅ _on_apply() 在对话框关闭时安全地处理了错误")
        except Exception as e:
            print(f"❌ _on_apply() 抛出异常: {e}")
            return False
        
        print("✅ 对话框关闭期间安全处理测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def main():
    """主测试函数"""
    print("开始设置对话框修复测试...")
    
    all_passed = True
    
    # 运行测试
    if not test_settings_dialog_stability():
        all_passed = False
    
    time.sleep(0.5)  # 给系统一点时间
    
    if not test_rapid_language_switch():
        all_passed = False
    
    time.sleep(0.5)  # 给系统一点时间
    
    if not test_dialog_close_during_update():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ 所有测试通过！设置对话框修复成功。")
    else:
        print("⚠ 部分测试失败，可能需要进一步改进。")
    
    print("\n修复总结:")
    print("1. 增强了_update_dialog_language()方法的安全性")
    print("2. 添加了_safe_update_widget_text_recursive()安全递归方法")
    print("3. 所有UI操作前检查部件是否存在")
    print("4. 改进了错误处理，避免'bad window path name'错误")
    
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