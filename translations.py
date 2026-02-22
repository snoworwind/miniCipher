#!/usr/bin/env python3
"""
国际化翻译模块
支持中文和英文界面切换
"""

from enum import Enum
from typing import Dict, Any
from config_manager import get_config_manager, Language

class TranslationKeys(str, Enum):
    """翻译键枚举 - 定义所有需要翻译的字符串键"""
    # 窗口标题
    APP_TITLE = "app_title"
    
    # 算法设置
    ALGORITHM_SETTINGS = "algorithm_settings"
    ENCRYPTION_ALGORITHM = "encryption_algorithm"
    KEY_TYPE = "key_type"
    OTP_ALGORITHM_INFO = "otp_algorithm_info"
    AES_ALGORITHM_INFO = "aes_algorithm_info"
    PASSWORD = "password"
    
    # 加密部分
    ENCRYPTION = "encryption"
    INPUT_FILE_PATH = "input_file_path"
    OUTPUT_DIRECTORY_PATH = "output_directory_path"
    BROWSE = "browse"
    START_ENCRYPTION = "start_encryption"
    
    # 解密部分
    DECRYPTION = "decryption"
    INPUT_CIPHER_PATH = "input_cipher_path"
    KEY_FILE_PATH = "key_file_path"
    DECRYPTION_PASSWORD = "decryption_password"
    DECRYPTION_OUTPUT_PATH = "decryption_output_path"
    START_DECRYPTION = "start_decryption"
    
    # 提示信息
    TIPS = "tips"
    TIPS_ENCRYPT = "tips_encrypt"
    TIPS_DECRYPT = "tips_decrypt"
    
    # 状态栏
    READY = "ready"
    ENCRYPTION_COMPLETED = "encryption_completed"
    DECRYPTION_COMPLETED = "decryption_completed"
    ERROR = "error"
    
    # 按钮和操作
    OK = "ok"
    CANCEL = "cancel"
    APPLY = "apply"
    SAVE = "save"
    RESET = "reset"
    
    # 错误消息
    ERROR_INVALID_FILE = "error_invalid_file"
    ERROR_INVALID_DIRECTORY = "error_invalid_directory"
    ERROR_INVALID_PASSWORD = "error_invalid_password"
    ERROR_PASSWORD_TOO_SHORT = "error_password_too_short"
    ERROR_PASSWORD_STRENGTH = "error_password_strength"
    ERROR_ENCRYPTION_FAILED = "error_encryption_failed"
    ERROR_DECRYPTION_FAILED = "error_decryption_failed"
    ERROR_FILE_NOT_FOUND = "error_file_not_found"
    ERROR_PERMISSION_DENIED = "error_permission_denied"
    
    # 成功消息
    SUCCESS_ENCRYPTION = "success_encryption"
    SUCCESS_DECRYPTION = "success_decryption"
    
    # 菜单
    FILE_MENU = "file_menu"
    EDIT_MENU = "edit_menu"
    VIEW_MENU = "view_menu"
    HELP_MENU = "help_menu"
    SETTINGS_MENU = "settings_menu"
    EXIT = "exit"
    LANGUAGE_MENU = "language_menu"
    THEME_MENU = "theme_menu"
    ABOUT = "about"
    
    # 主题相关
    LIGHT_THEME = "light_theme"
    DARK_THEME = "dark_theme"
    THEME_SETTINGS = "theme_settings"


class Translator:
    """翻译管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.translations = self._load_translations()
        self.current_language = self.config_manager.get_language()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """加载所有语言的翻译"""
        return {
            Language.ZH_CN.value: self._get_chinese_translations(),
            Language.EN_US.value: self._get_english_translations(),
        }
    
    def _get_chinese_translations(self) -> Dict[str, str]:
        """获取中文翻译"""
        return {
            # 窗口标题
            TranslationKeys.APP_TITLE: "文件加密/解密工具 - Cipher",
            
            # 算法设置
            TranslationKeys.ALGORITHM_SETTINGS: "算法设置",
            TranslationKeys.ENCRYPTION_ALGORITHM: "加密算法：",
            TranslationKeys.KEY_TYPE: "密钥类型：",
            TranslationKeys.OTP_ALGORITHM_INFO: "OTP: 一次性密码本，密钥长度等于文件长度",
            TranslationKeys.AES_ALGORITHM_INFO: "AES256-GCM: 高级加密标准，256位密钥，GCM模式",
            TranslationKeys.PASSWORD: "密码：",
            
            # 加密部分
            TranslationKeys.ENCRYPTION: "加密",
            TranslationKeys.INPUT_FILE_PATH: "输入文件路径：",
            TranslationKeys.OUTPUT_DIRECTORY_PATH: "输出目录路径：",
            TranslationKeys.BROWSE: "浏览",
            TranslationKeys.START_ENCRYPTION: "开始加密",
            
            # 解密部分
            TranslationKeys.DECRYPTION: "解密",
            TranslationKeys.INPUT_CIPHER_PATH: "输入密文路径：",
            TranslationKeys.KEY_FILE_PATH: "密钥文件路径：",
            TranslationKeys.DECRYPTION_PASSWORD: "解密密码：",
            TranslationKeys.DECRYPTION_OUTPUT_PATH: "输出目录路径：",
            TranslationKeys.START_DECRYPTION: "开始解密",
            
            # 提示信息
            TranslationKeys.TIPS: "提示：",
            TranslationKeys.TIPS_ENCRYPT: "• 支持所有文件类型\n• 输出文件为.enc格式\n• 密钥文件与密文文件一同保存",
            TranslationKeys.TIPS_DECRYPT: "• 支持OTP和AES256-GCM算法\n• 密码模式无需密钥文件\n• 输出为原始文件格式",
            
            # 状态栏
            TranslationKeys.READY: "就绪",
            TranslationKeys.ENCRYPTION_COMPLETED: "加密完成",
            TranslationKeys.DECRYPTION_COMPLETED: "解密完成",
            TranslationKeys.ERROR: "错误",
            
            # 按钮和操作
            TranslationKeys.OK: "确定",
            TranslationKeys.CANCEL: "取消",
            TranslationKeys.APPLY: "应用",
            TranslationKeys.SAVE: "保存",
            TranslationKeys.RESET: "重置",
            
            # 错误消息
            TranslationKeys.ERROR_INVALID_FILE: "无效的文件",
            TranslationKeys.ERROR_INVALID_DIRECTORY: "无效的目录",
            TranslationKeys.ERROR_INVALID_PASSWORD: "无效的密码",
            TranslationKeys.ERROR_PASSWORD_TOO_SHORT: "密码至少需要{min_length}个字符",
            TranslationKeys.ERROR_PASSWORD_STRENGTH: "密码应包含大小写字母和数字",
            TranslationKeys.ERROR_ENCRYPTION_FAILED: "加密失败",
            TranslationKeys.ERROR_DECRYPTION_FAILED: "解密失败",
            TranslationKeys.ERROR_FILE_NOT_FOUND: "文件不存在：{path}",
            TranslationKeys.ERROR_PERMISSION_DENIED: "权限错误，无法访问文件",
            
            # 成功消息
            TranslationKeys.SUCCESS_ENCRYPTION: "加密完成！\n密文文件：{cipher_file}\n密钥文件：{key_file}\n算法：{algorithm}\n密钥类型：{key_type}",
            TranslationKeys.SUCCESS_DECRYPTION: "解密完成！\n明文文件：{plaintext_file}\n算法：{algorithm}",
            
            # 菜单
            TranslationKeys.FILE_MENU: "文件",
            TranslationKeys.EDIT_MENU: "编辑",
            TranslationKeys.VIEW_MENU: "视图",
            TranslationKeys.HELP_MENU: "帮助",
            TranslationKeys.SETTINGS_MENU: "设置",
            TranslationKeys.EXIT: "退出",
            TranslationKeys.LANGUAGE_MENU: "语言",
            TranslationKeys.THEME_MENU: "主题",
            TranslationKeys.ABOUT: "关于",
            
            # 主题相关
            TranslationKeys.LIGHT_THEME: "浅色主题",
            TranslationKeys.DARK_THEME: "深色主题",
            TranslationKeys.THEME_SETTINGS: "主题设置",
        }
    
    def _get_english_translations(self) -> Dict[str, str]:
        """获取英文翻译"""
        return {
            # 窗口标题
            TranslationKeys.APP_TITLE: "File Encryption/Decryption Tool - Cipher",
            
            # 算法设置
            TranslationKeys.ALGORITHM_SETTINGS: "Algorithm Settings",
            TranslationKeys.ENCRYPTION_ALGORITHM: "Encryption Algorithm:",
            TranslationKeys.KEY_TYPE: "Key Type:",
            TranslationKeys.OTP_ALGORITHM_INFO: "OTP: One-Time Pad, key length equals file length",
            TranslationKeys.AES_ALGORITHM_INFO: "AES256-GCM: Advanced Encryption Standard, 256-bit key, GCM mode",
            TranslationKeys.PASSWORD: "Password:",
            
            # 加密部分
            TranslationKeys.ENCRYPTION: "Encryption",
            TranslationKeys.INPUT_FILE_PATH: "Input File Path:",
            TranslationKeys.OUTPUT_DIRECTORY_PATH: "Output Directory Path:",
            TranslationKeys.BROWSE: "Browse",
            TranslationKeys.START_ENCRYPTION: "Start Encryption",
            
            # 解密部分
            TranslationKeys.DECRYPTION: "Decryption",
            TranslationKeys.INPUT_CIPHER_PATH: "Input Cipher Path:",
            TranslationKeys.KEY_FILE_PATH: "Key File Path:",
            TranslationKeys.DECRYPTION_PASSWORD: "Decryption Password:",
            TranslationKeys.DECRYPTION_OUTPUT_PATH: "Output Directory Path:",
            TranslationKeys.START_DECRYPTION: "Start Decryption",
            
            # 提示信息
            TranslationKeys.TIPS: "Tips:",
            TranslationKeys.TIPS_ENCRYPT: "• Supports all file types\n• Output files in .enc format\n• Key file saved with ciphertext",
            TranslationKeys.TIPS_DECRYPT: "• Supports OTP and AES256-GCM algorithms\n• Password mode requires no key file\n• Output in original file format",
            
            # 状态栏
            TranslationKeys.READY: "Ready",
            TranslationKeys.ENCRYPTION_COMPLETED: "Encryption Completed",
            TranslationKeys.DECRYPTION_COMPLETED: "Decryption Completed",
            TranslationKeys.ERROR: "Error",
            
            # 按钮和操作
            TranslationKeys.OK: "OK",
            TranslationKeys.CANCEL: "Cancel",
            TranslationKeys.APPLY: "Apply",
            TranslationKeys.SAVE: "Save",
            TranslationKeys.RESET: "Reset",
            
            # 错误消息
            TranslationKeys.ERROR_INVALID_FILE: "Invalid file",
            TranslationKeys.ERROR_INVALID_DIRECTORY: "Invalid directory",
            TranslationKeys.ERROR_INVALID_PASSWORD: "Invalid password",
            TranslationKeys.ERROR_PASSWORD_TOO_SHORT: "Password must be at least {min_length} characters",
            TranslationKeys.ERROR_PASSWORD_STRENGTH: "Password must contain uppercase, lowercase letters and numbers",
            TranslationKeys.ERROR_ENCRYPTION_FAILED: "Encryption failed",
            TranslationKeys.ERROR_DECRYPTION_FAILED: "Decryption failed",
            TranslationKeys.ERROR_FILE_NOT_FOUND: "File not found: {path}",
            TranslationKeys.ERROR_PERMISSION_DENIED: "Permission denied, cannot access file",
            
            # 成功消息
            TranslationKeys.SUCCESS_ENCRYPTION: "Encryption completed!\nCiphertext file: {cipher_file}\nKey file: {key_file}\nAlgorithm: {algorithm}\nKey type: {key_type}",
            TranslationKeys.SUCCESS_DECRYPTION: "Decryption completed!\nPlaintext file: {plaintext_file}\nAlgorithm: {algorithm}",
            
            # 菜单
            TranslationKeys.FILE_MENU: "File",
            TranslationKeys.EDIT_MENU: "Edit",
            TranslationKeys.VIEW_MENU: "View",
            TranslationKeys.HELP_MENU: "Help",
            TranslationKeys.SETTINGS_MENU: "Settings",
            TranslationKeys.EXIT: "Exit",
            TranslationKeys.LANGUAGE_MENU: "Language",
            TranslationKeys.THEME_MENU: "Theme",
            TranslationKeys.ABOUT: "About",
            
            # 主题相关
            TranslationKeys.LIGHT_THEME: "Light Theme",
            TranslationKeys.DARK_THEME: "Dark Theme",
            TranslationKeys.THEME_SETTINGS: "Theme Settings",
        }
    
    def translate(self, key: str, **kwargs) -> str:
        """翻译给定的键，支持参数格式化"""
        language = self.current_language
        
        # 如果语言不可用，使用中文作为后备
        if language not in self.translations:
            language = Language.ZH_CN.value
        
        # 获取翻译
        translation = self.translations[language].get(key, key)
        
        # 格式化参数
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                # 如果格式化失败，返回原始翻译
                pass
        
        return translation
    
    def set_language(self, language: str) -> None:
        """设置当前语言"""
        if language in self.translations:
            self.current_language = language
            self.config_manager.set_language(language)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def get_available_languages(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return {
            Language.ZH_CN.value: "简体中文",
            Language.EN_US.value: "English",
        }
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def get_current_language_display_name(self) -> str:
        """获取当前语言的显示名称"""
        display_names = {
            Language.ZH_CN.value: "简体中文",
            Language.EN_US.value: "English",
        }
        return display_names.get(self.current_language, self.current_language)


# 单例实例
_translator: "Translator" = None

def get_translator() -> Translator:
    """获取翻译器单例实例"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def _(key: str, **kwargs) -> str:
    """翻译函数，便于使用"""
    return get_translator().translate(key, **kwargs)


if __name__ == "__main__":
    # 测试翻译器
    translator = get_translator()
    
    print("=== 测试翻译器 ===")
    print(f"当前语言: {translator.get_current_language_display_name()}")
    
    # 测试一些翻译
    test_keys = [
        TranslationKeys.APP_TITLE,
        TranslationKeys.ENCRYPTION,
        TranslationKeys.DECRYPTION,
        TranslationKeys.START_ENCRYPTION,
    ]
    
    for key in test_keys:
        print(f"{key}: {translator.translate(key)}")
    
    # 测试参数格式化
    print("\n=== 测试参数格式化 ===")
    error_msg = translator.translate(
        TranslationKeys.ERROR_FILE_NOT_FOUND,
        path="/path/to/file.txt"
    )
    print(f"错误消息: {error_msg}")
    
    # 测试语言切换
    print("\n=== 测试语言切换 ===")
    translator.set_language(Language.EN_US.value)
    print(f"切换后语言: {translator.get_current_language_display_name()}")
    for key in test_keys:
        print(f"{key}: {translator.translate(key)}")