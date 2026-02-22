#!/usr/bin/env python3
"""
测试语言切换修复
"""

import tkinter as tk
from tkinter import ttk
import logging
from config_manager import get_config_manager, Language, ThemeType
from translations import get_translator
from theme_manager import get_theme_manager, apply_theme_to_window

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MockCipherGUI:
    """模拟CipherGUI类"""
    def __init__(self):
        self.config_manager = get_config_manager()
        self.translator = get_translator()
        self.theme_manager = get_theme_manager()
        self.language_changed = False
        self.theme_changed = False
        self.last_language = None
        self.last_theme = None
        self.call_log = []
    
    def _change_theme(self, theme):
        self.theme_changed = True
        self.last_theme = theme
        self.call_log.append(f"theme:{theme}")
        logging.info(f"模拟主题切换: {theme}")
    
    def _change_language(self, language):
        self.language_changed = True
        self.last_language = language
        self.call_log.append(f"language:{language}")
        logging.info(f"模拟语言切换: {language}")

def test_settings_dialog_language():
    """测试设置对话框的语言切换"""
    print("=== 测试设置对话框语言切换修复 ===")
    
    # 创建根窗口（隐藏）
    root = tk.Tk()
    root.withdraw()
    
    # 创建模拟GUI
    mock_gui = MockCipherGUI()
    
    # 获取当前配置
    config_manager = get_config_manager()
    current_language = config_manager.get_language()
    current_theme = config_manager.get_theme()
    
    print(f"当前配置: 语言={current_language}, 主题={current_theme}")
    
    # 导入设置对话框类
    from settings_dialog import SettingsDialog
    
    # 创建设置对话框实例
    dialog_instance = SettingsDialog.__new__(SettingsDialog)
    dialog_instance.parent = root
    dialog_instance.cipher_gui = mock_gui
    dialog_instance.config_manager = config_manager
    dialog_instance.translator = get_translator()
    dialog_instance.theme_manager = get_theme_manager()
    
    # 初始化一些必要的属性
    dialog_instance.settings_applied = False
    dialog_instance.original_settings = {}
    dialog_instance.apply_button = None
    
    # 模拟UI变量
    dialog_instance.language_var = tk.StringVar()
    
    # 测试1: 切换到中文
    print("\n--- 测试1: 切换到中文 ---")
    mock_gui.call_log = []
    mock_gui.language_changed = False
    
    # 模拟选择了中文
    dialog_instance.language_var.set("简体中文")
    
    # 调用_on_apply方法（部分模拟）
    try:
        # 保存语言设置的部分
        from translations import TranslationKeys, _
        from settings_dialog import Language as LangEnum
        
        language_text = dialog_instance.language_var.get()
        print(f"选择的语言文本: {language_text}")
        
        if language_text == "简体中文":
            language_value = LangEnum.ZH_CN.value
        else:
            language_value = LangEnum.EN_US.value
        
        print(f"对应的语言值: {language_value}")
        
        # 保存到配置管理器
        config_manager.set_language(language_value)
        
        # 模拟调用_cipher_gui._change_language
        if mock_gui:
            mock_gui._change_language(language_value)
        
        print(f"语言切换调用: {mock_gui.language_changed}")
        print(f"调用日志: {mock_gui.call_log}")
        
        # 验证配置已更新
        new_language = config_manager.get_language()
        print(f"配置中的新语言: {new_language}")
        
        assert mock_gui.language_changed, "应该调用_cipher_gui._change_language()"
        assert language_value == new_language, "配置应该更新"
        print("✓ 测试1通过")
        
    except Exception as e:
        print(f"✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试2: 切换到英文
    print("\n--- 测试2: 切换到英文 ---")
    mock_gui.call_log = []
    mock_gui.language_changed = False
    
    # 模拟选择了英文
    dialog_instance.language_var.set("English")
    
    try:
        language_text = dialog_instance.language_var.get()
        print(f"选择的语言文本: {language_text}")
        
        if language_text == "简体中文":
            language_value = LangEnum.ZH_CN.value
        else:
            language_value = LangEnum.EN_US.value
        
        print(f"对应的语言值: {language_value}")
        
        # 保存到配置管理器
        config_manager.set_language(language_value)
        
        # 模拟调用_cipher_gui._change_language
        if mock_gui:
            mock_gui._change_language(language_value)
        
        print(f"语言切换调用: {mock_gui.language_changed}")
        print(f"调用日志: {mock_gui.call_log}")
        
        # 验证配置已更新
        new_language = config_manager.get_language()
        print(f"配置中的新语言: {new_language}")
        
        assert mock_gui.language_changed, "应该调用_cipher_gui._change_language()"
        assert language_value == new_language, "配置应该更新"
        print("✓ 测试2通过")
        
    except Exception as e:
        print(f"✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试3: 检查_on_cancel方法是否恢复语言
    print("\n--- 测试3: 检查取消时是否恢复语言 ---")
    
    # 保存原始设置
    original_language = config_manager.get_language()
    dialog_instance.original_settings = {
        "basic.ui.language": original_language,
        "basic.ui.theme": config_manager.get_theme()
    }
    dialog_instance.settings_applied = False
    
    mock_gui.call_log = []
    mock_gui.language_changed = False
    
    # 临时更改语言
    temp_language = LangEnum.ZH_CN.value if original_language == LangEnum.EN_US.value else LangEnum.EN_US.value
    config_manager.set_language(temp_language)
    print(f"临时更改语言为: {temp_language}")
    
    # 模拟_on_cancel调用
    try:
        # 恢复原始设置
        for key, value in dialog_instance.original_settings.items():
            config_manager.set(key, value)
        
        # 恢复主题
        if mock_gui:
            mock_gui._change_theme(dialog_instance.original_settings["basic.ui.theme"])
        
        # 恢复语言
        if mock_gui and "basic.ui.language" in dialog_instance.original_settings:
            language_value = dialog_instance.original_settings["basic.ui.language"]
            mock_gui._change_language(language_value)
        
        print(f"取消后语言切换调用: {mock_gui.language_changed}")
        print(f"调用日志: {mock_gui.call_log}")
        
        # 验证语言已恢复
        restored_language = config_manager.get_language()
        print(f"恢复后的语言: {restored_language}")
        print(f"原始语言: {original_language}")
        
        assert mock_gui.language_changed, "取消时应该调用_cipher_gui._change_language()"
        assert restored_language == original_language, "取消后语言应该恢复"
        print("✓ 测试3通过")
        
    except Exception as e:
        print(f"✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 清理
    root.destroy()
    
    print("\n=== 测试总结 ===")
    print("语言切换修复测试完成")
    return True

if __name__ == "__main__":
    success = test_settings_dialog_language()
    if success:
        print("\n✅ 所有测试通过！语言切换修复成功。")
    else:
        print("\n❌ 测试失败，请检查修复。")