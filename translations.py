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
    
    # 设置对话框
    SETTINGS_GENERAL = "settings_general"
    SETTINGS_ENCRYPTION = "settings_encryption"
    SETTINGS_PATHS = "settings_paths"
    SETTINGS_ADVANCED = "settings_advanced"
    SETTINGS_LANGUAGE = "settings_language"
    SETTINGS_THEME = "settings_theme"
    SETTINGS_LANGUAGE_CHINESE = "settings_language_chinese"
    SETTINGS_LANGUAGE_ENGLISH = "settings_language_english"
    SETTINGS_ALGORITHM = "settings_algorithm"
    SETTINGS_KEY_TYPE = "settings_key_type"
    SETTINGS_PASSWORD = "settings_password"
    SETTINGS_PASSWORD_MIN_LENGTH = "settings_password_min_length"
    SETTINGS_REQUIRE_STRONG_PASSWORD = "settings_require_strong_password"
    SETTINGS_OTP = "settings_otp"
    SETTINGS_AES = "settings_aes"
    SETTINGS_FILE_FORMAT = "settings_file_format"
    SETTINGS_COMPRESSION = "settings_compression"
    SETTINGS_DEFAULT_PATHS = "settings_default_paths"
    SETTINGS_REMEMBER_LAST_FOLDER = "settings_remember_last_folder"
    SETTINGS_CLEAR_HISTORY = "settings_clear_history"
    SETTINGS_UPDATE = "settings_update"
    SETTINGS_DEBUG = "settings_debug"
    SETTINGS_PERFORMANCE = "settings_performance"
    SETTINGS_THEME_PREVIEW = "settings_theme_preview"
    SETTINGS_WINDOW = "settings_window"
    SETTINGS_OTP_KEY_FORMAT = "settings_otp_key_format"
    SETTINGS_OTP_HEX = "settings_otp_hex"
    SETTINGS_OTP_BINARY = "settings_otp_binary"
    SETTINGS_AES_AUTO_IV = "settings_aes_auto_iv"
    SETTINGS_AUTO_UPDATE = "settings_auto_update"
    SETTINGS_UPDATE_FREQUENCY = "settings_update_frequency"
    SETTINGS_DEBUG_MODE = "settings_debug_mode"
    SETTINGS_LOG_LEVEL = "settings_log_level"
    SETTINGS_PARALLEL_PROCESSING = "settings_parallel_processing"
    SETTINGS_BUFFER_SIZE = "settings_buffer_size"
    SETTINGS_UPDATE_DAILY = "settings_update_daily"
    SETTINGS_UPDATE_WEEKLY = "settings_update_weekly"
    SETTINGS_UPDATE_MONTHLY = "settings_update_monthly"
    SETTINGS_UPDATE_NEVER = "settings_update_never"
    SETTINGS_SUCCESS = "settings_success"
    SETTINGS_ERROR = "settings_error"
    SETTINGS_RESET = "settings_reset"
    SETTINGS_CLEAR = "settings_clear"
    SETTINGS_HISTORY_CLEARED = "settings_history_cleared"
    SETTINGS_RESET_TO_DEFAULTS = "settings_reset_to_defaults"
    
    # 配置验证相关
    VALIDATION_REQUIRED = "validation_required"
    VALIDATION_INVALID_STRING = "validation_invalid_string"
    VALIDATION_INVALID_INTEGER = "validation_invalid_integer"
    VALIDATION_INVALID_FLOAT = "validation_invalid_float"
    VALIDATION_INVALID_BOOLEAN = "validation_invalid_boolean"
    VALIDATION_INVALID_ENUM = "validation_invalid_enum"
    VALIDATION_INVALID_PATH = "validation_invalid_path"
    VALIDATION_INVALID_EMAIL = "validation_invalid_email"
    VALIDATION_INVALID_URL = "validation_invalid_url"
    VALIDATION_INVALID_REGEX = "validation_invalid_regex"
    VALIDATION_STRING_MIN_LENGTH = "validation_string_min_length"
    VALIDATION_STRING_MAX_LENGTH = "validation_string_max_length"
    VALIDATION_INTEGER_MIN = "validation_integer_min"
    VALIDATION_INTEGER_MAX = "validation_integer_max"
    VALIDATION_INTEGER_RANGE = "validation_integer_range"
    VALIDATION_FLOAT_MIN = "validation_float_min"
    VALIDATION_FLOAT_MAX = "validation_float_max"
    VALIDATION_FLOAT_RANGE = "validation_float_range"
    VALIDATION_PATH_NOT_EXIST = "validation_path_not_exist"
    VALIDATION_PATH_NOT_DIR = "validation_path_not_dir"
    VALIDATION_PATH_NOT_FILE = "validation_path_not_file"
    VALIDATION_CONFIG_KEY = "validation_config_key"


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
            
            # 设置对话框
            TranslationKeys.SETTINGS_GENERAL: "常规",
            TranslationKeys.SETTINGS_ENCRYPTION: "加密",
            TranslationKeys.SETTINGS_PATHS: "路径",
            TranslationKeys.SETTINGS_ADVANCED: "高级",
            TranslationKeys.SETTINGS_LANGUAGE: "语言设置",
            TranslationKeys.SETTINGS_THEME: "主题设置",
            TranslationKeys.SETTINGS_LANGUAGE_CHINESE: "简体中文",
            TranslationKeys.SETTINGS_LANGUAGE_ENGLISH: "English",
            TranslationKeys.SETTINGS_ALGORITHM: "算法设置",
            TranslationKeys.SETTINGS_KEY_TYPE: "密钥类型设置",
            TranslationKeys.SETTINGS_PASSWORD: "密码设置",
            TranslationKeys.SETTINGS_PASSWORD_MIN_LENGTH: "密码最小长度：",
            TranslationKeys.SETTINGS_REQUIRE_STRONG_PASSWORD: "要求强密码（大小写字母+数字）",
            TranslationKeys.SETTINGS_OTP: "OTP设置",
            TranslationKeys.SETTINGS_AES: "AES设置",
            TranslationKeys.SETTINGS_FILE_FORMAT: "文件格式设置",
            TranslationKeys.SETTINGS_COMPRESSION: "压缩设置",
            TranslationKeys.SETTINGS_DEFAULT_PATHS: "默认路径",
            TranslationKeys.SETTINGS_REMEMBER_LAST_FOLDER: "记住上次使用的文件夹",
            TranslationKeys.SETTINGS_CLEAR_HISTORY: "清空历史记录",
            TranslationKeys.SETTINGS_UPDATE: "更新设置",
            TranslationKeys.SETTINGS_DEBUG: "调试设置",
            TranslationKeys.SETTINGS_PERFORMANCE: "性能设置",
            TranslationKeys.SETTINGS_THEME_PREVIEW: "主题预览：",
            TranslationKeys.SETTINGS_WINDOW: "窗口设置",
            TranslationKeys.SETTINGS_OTP_KEY_FORMAT: "OTP密钥文件格式：",
            TranslationKeys.SETTINGS_OTP_HEX: "十六进制 (.txt)",
            TranslationKeys.SETTINGS_OTP_BINARY: "二进制 (.bin)",
            TranslationKeys.SETTINGS_AES_AUTO_IV: "自动生成IV（初始化向量）",
            TranslationKeys.SETTINGS_AUTO_UPDATE: "自动检查更新",
            TranslationKeys.SETTINGS_UPDATE_FREQUENCY: "检查频率：",
            TranslationKeys.SETTINGS_DEBUG_MODE: "启用调试模式",
            TranslationKeys.SETTINGS_LOG_LEVEL: "日志级别：",
            TranslationKeys.SETTINGS_PARALLEL_PROCESSING: "启用多线程处理",
            TranslationKeys.SETTINGS_BUFFER_SIZE: "缓冲区大小 (MB)：",
            TranslationKeys.SETTINGS_UPDATE_DAILY: "每天",
            TranslationKeys.SETTINGS_UPDATE_WEEKLY: "每周",
            TranslationKeys.SETTINGS_UPDATE_MONTHLY: "每月",
            TranslationKeys.SETTINGS_UPDATE_NEVER: "从不",
            TranslationKeys.SETTINGS_SUCCESS: "成功",
            TranslationKeys.SETTINGS_ERROR: "错误",
            TranslationKeys.SETTINGS_RESET: "重置",
            TranslationKeys.SETTINGS_CLEAR: "清空",
            TranslationKeys.SETTINGS_HISTORY_CLEARED: "历史记录已清空",
            TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "设置已重置为默认值",
            
            # 配置验证相关翻译
            TranslationKeys.VALIDATION_REQUIRED: "配置项是必需的",
            TranslationKeys.VALIDATION_INVALID_STRING: "字符串验证失败",
            TranslationKeys.VALIDATION_INVALID_INTEGER: "无效的整数值",
            TranslationKeys.VALIDATION_INVALID_FLOAT: "无效的浮点数值",
            TranslationKeys.VALIDATION_INVALID_BOOLEAN: "无效的布尔值",
            TranslationKeys.VALIDATION_INVALID_ENUM: "值必须在允许的列表中: {allowed_values}",
            TranslationKeys.VALIDATION_INVALID_PATH: "无效的路径格式",
            TranslationKeys.VALIDATION_INVALID_EMAIL: "无效的电子邮件地址格式",
            TranslationKeys.VALIDATION_INVALID_URL: "无效的URL格式",
            TranslationKeys.VALIDATION_INVALID_REGEX: "值不符合正则表达式模式",
            TranslationKeys.VALIDATION_STRING_MIN_LENGTH: "字符串长度不能小于 {min_len}",
            TranslationKeys.VALIDATION_STRING_MAX_LENGTH: "字符串长度不能大于 {max_len}",
            TranslationKeys.VALIDATION_INTEGER_MIN: "整数值必须大于等于 {min_val}",
            TranslationKeys.VALIDATION_INTEGER_MAX: "整数值必须小于等于 {max_val}",
            TranslationKeys.VALIDATION_INTEGER_RANGE: "整数值必须在 {min_val} 和 {max_val} 之间",
            TranslationKeys.VALIDATION_FLOAT_MIN: "浮点数值必须大于等于 {min_val}",
            TranslationKeys.VALIDATION_FLOAT_MAX: "浮点数值必须小于等于 {max_val}",
            TranslationKeys.VALIDATION_FLOAT_RANGE: "浮点数值必须在 {min_val} 和 {max_val} 之间",
            TranslationKeys.VALIDATION_PATH_NOT_EXIST: "路径必须存在",
            TranslationKeys.VALIDATION_PATH_NOT_DIR: "路径必须是目录",
            TranslationKeys.VALIDATION_PATH_NOT_FILE: "路径必须是文件",
            TranslationKeys.VALIDATION_CONFIG_KEY: "配置项 '{config_key}' 验证失败: {message} (值: {repr_value})",
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
            
            # 设置对话框
            TranslationKeys.SETTINGS_GENERAL: "General",
            TranslationKeys.SETTINGS_ENCRYPTION: "Encryption",
            TranslationKeys.SETTINGS_PATHS: "Paths",
            TranslationKeys.SETTINGS_ADVANCED: "Advanced",
            TranslationKeys.SETTINGS_LANGUAGE: "Language Settings",
            TranslationKeys.SETTINGS_THEME: "Theme Settings",
            TranslationKeys.SETTINGS_LANGUAGE_CHINESE: "Chinese",
            TranslationKeys.SETTINGS_LANGUAGE_ENGLISH: "English",
            TranslationKeys.SETTINGS_ALGORITHM: "Algorithm Settings",
            TranslationKeys.SETTINGS_KEY_TYPE: "Key Type Settings",
            TranslationKeys.SETTINGS_PASSWORD: "Password Settings",
            TranslationKeys.SETTINGS_PASSWORD_MIN_LENGTH: "Password Minimum Length:",
            TranslationKeys.SETTINGS_REQUIRE_STRONG_PASSWORD: "Require strong password (uppercase + lowercase + digits)",
            TranslationKeys.SETTINGS_OTP: "OTP Settings",
            TranslationKeys.SETTINGS_AES: "AES Settings",
            TranslationKeys.SETTINGS_FILE_FORMAT: "File Format Settings",
            TranslationKeys.SETTINGS_COMPRESSION: "Compression Settings",
            TranslationKeys.SETTINGS_DEFAULT_PATHS: "Default Paths",
            TranslationKeys.SETTINGS_REMEMBER_LAST_FOLDER: "Remember last used folder",
            TranslationKeys.SETTINGS_CLEAR_HISTORY: "Clear History",
            TranslationKeys.SETTINGS_UPDATE: "Update Settings",
            TranslationKeys.SETTINGS_DEBUG: "Debug Settings",
            TranslationKeys.SETTINGS_PERFORMANCE: "Performance Settings",
            TranslationKeys.SETTINGS_THEME_PREVIEW: "Theme Preview:",
            TranslationKeys.SETTINGS_WINDOW: "Window Settings",
            TranslationKeys.SETTINGS_OTP_KEY_FORMAT: "OTP Key File Format:",
            TranslationKeys.SETTINGS_OTP_HEX: "Hexadecimal (.txt)",
            TranslationKeys.SETTINGS_OTP_BINARY: "Binary (.bin)",
            TranslationKeys.SETTINGS_AES_AUTO_IV: "Auto-generate IV (Initialization Vector)",
            TranslationKeys.SETTINGS_AUTO_UPDATE: "Auto-check for updates",
            TranslationKeys.SETTINGS_UPDATE_FREQUENCY: "Check Frequency:",
            TranslationKeys.SETTINGS_DEBUG_MODE: "Enable debug mode",
            TranslationKeys.SETTINGS_LOG_LEVEL: "Log Level:",
            TranslationKeys.SETTINGS_PARALLEL_PROCESSING: "Enable multi-threading",
            TranslationKeys.SETTINGS_BUFFER_SIZE: "Buffer Size (MB):",
            TranslationKeys.SETTINGS_UPDATE_DAILY: "Daily",
            TranslationKeys.SETTINGS_UPDATE_WEEKLY: "Weekly",
            TranslationKeys.SETTINGS_UPDATE_MONTHLY: "Monthly",
            TranslationKeys.SETTINGS_UPDATE_NEVER: "Never",
            TranslationKeys.SETTINGS_SUCCESS: "Success",
            TranslationKeys.SETTINGS_ERROR: "Error",
            TranslationKeys.SETTINGS_RESET: "Reset",
            TranslationKeys.SETTINGS_CLEAR: "Clear",
            TranslationKeys.SETTINGS_HISTORY_CLEARED: "History cleared",
            TranslationKeys.SETTINGS_RESET_TO_DEFAULTS: "Settings reset to defaults",
            
            # Configuration validation related translations
            TranslationKeys.VALIDATION_REQUIRED: "Configuration item is required",
            TranslationKeys.VALIDATION_INVALID_STRING: "String validation failed",
            TranslationKeys.VALIDATION_INVALID_INTEGER: "Invalid integer value",
            TranslationKeys.VALIDATION_INVALID_FLOAT: "Invalid float value",
            TranslationKeys.VALIDATION_INVALID_BOOLEAN: "Invalid boolean value",
            TranslationKeys.VALIDATION_INVALID_ENUM: "Value must be in allowed list: {allowed_values}",
            TranslationKeys.VALIDATION_INVALID_PATH: "Invalid path format",
            TranslationKeys.VALIDATION_INVALID_EMAIL: "Invalid email address format",
            TranslationKeys.VALIDATION_INVALID_URL: "Invalid URL format",
            TranslationKeys.VALIDATION_INVALID_REGEX: "Value does not match regex pattern",
            TranslationKeys.VALIDATION_STRING_MIN_LENGTH: "String length cannot be less than {min_len}",
            TranslationKeys.VALIDATION_STRING_MAX_LENGTH: "String length cannot be greater than {max_len}",
            TranslationKeys.VALIDATION_INTEGER_MIN: "Integer value must be greater than or equal to {min_val}",
            TranslationKeys.VALIDATION_INTEGER_MAX: "Integer value must be less than or equal to {max_val}",
            TranslationKeys.VALIDATION_INTEGER_RANGE: "Integer value must be between {min_val} and {max_val}",
            TranslationKeys.VALIDATION_FLOAT_MIN: "Float value must be greater than or equal to {min_val}",
            TranslationKeys.VALIDATION_FLOAT_MAX: "Float value must be less than or equal to {max_val}",
            TranslationKeys.VALIDATION_FLOAT_RANGE: "Float value must be between {min_val} and {max_val}",
            TranslationKeys.VALIDATION_PATH_NOT_EXIST: "Path must exist",
            TranslationKeys.VALIDATION_PATH_NOT_DIR: "Path must be a directory",
            TranslationKeys.VALIDATION_PATH_NOT_FILE: "Path must be a file",
            TranslationKeys.VALIDATION_CONFIG_KEY: "Configuration item '{config_key}' validation failed: {message} (value: {repr_value})",
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