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
    
    # 设置对话框新增翻译键
    UI_LANGUAGE = "ui_language"
    UI_THEME = "ui_theme"
    DEFAULT_ALGORITHM_LABEL = "default_algorithm_label"
    DEFAULT_KEY_TYPE_LABEL = "default_key_type_label"
    OTP_FORMAT_INFO = "otp_format_info"
    DEFAULT_INPUT_DIRECTORY = "default_input_directory"
    DEFAULT_OUTPUT_DIRECTORY = "default_output_directory"
    FEATURE_DESCRIPTION = "feature_description"
    ADVANCED_SETTINGS_INFO = "advanced_settings_info"
    TAB_GENERAL = "tab_general"
    TAB_ENCRYPTION = "tab_encryption"
    TAB_PATHS = "tab_paths"
    TAB_ADVANCED = "tab_advanced"
    LOG_LEVEL_LABEL = "log_level_label"
    BUFFER_SIZE_LABEL = "buffer_size_label"
    CHINESE_LANGUAGE = "chinese_language"
    ENGLISH_LANGUAGE = "english_language"
    SETTINGS_SUCCESS_TITLE = "settings_success_title"
    SETTINGS_SUCCESS_MESSAGE = "settings_success_message"
    VALIDATION_ERROR_TITLE = "validation_error_title"
    VALIDATION_ERROR_MESSAGE = "validation_error_message"
    ERROR_TITLE = "error_title"
    ERROR_MESSAGE_TEMPLATE = "error_message_template"
    RESET_TITLE = "reset_title"
    RESET_MESSAGE = "reset_message"
    CLEAR_TITLE = "clear_title"
    CLEAR_MESSAGE = "clear_message"

    # 重启提示翻译键
    RESTART_REQUIRED_TITLE = "restart_required_title"
    RESTART_REQUIRED_INTRO = "restart_required_intro"
    RESTART_LANGUAGE_CHANGED = "restart_language_changed"
    RESTART_THEME_CHANGED = "restart_theme_changed"
    RESTART_REQUIRED_INSTRUCTIONS = "restart_required_instructions"
    RESTART_NOW_BUTTON = "restart_now_button"
    RESTART_LATER_BUTTON = "restart_later_button"

    # 批量操作翻译键
    BATCH_OPERATION = "batch_operation"
    BATCH_TAB_TITLE = "batch_tab_title"
    BATCH_SELECT_FILES = "batch_select_files"
    BATCH_SELECT_FOLDER = "batch_select_folder"
    BATCH_SELECT_RECURSIVE = "batch_select_recursive"
    BATCH_SELECTED_FILES = "batch_selected_files"
    BATCH_SELECTED_FOLDER = "batch_selected_folder"
    BATCH_SELECTED_RECURSIVE = "batch_selected_recursive"
    BATCH_PROCESSING_MODE = "batch_processing_mode"
    BATCH_PROCESSING_MODE_FILES = "batch_processing_mode_files"
    BATCH_PROCESSING_MODE_FOLDER = "batch_processing_mode_folder"
    BATCH_PROCESSING_MODE_RECURSIVE = "batch_processing_mode_recursive"
    BATCH_OUTPUT_DIRECTORY = "batch_output_directory"
    BATCH_PRESERVE_STRUCTURE = "batch_preserve_structure"
    BATCH_ENABLE_PARALLEL = "batch_enable_parallel"
    BATCH_MAX_THREADS = "batch_max_threads"
    BATCH_START_ENCRYPTION = "batch_start_encryption"
    BATCH_START_DECRYPTION = "batch_start_decryption"
    BATCH_CANCEL_PROCESSING = "batch_cancel_processing"
    BATCH_PROGRESS_TOTAL = "batch_progress_total"
    BATCH_PROGRESS_CURRENT = "batch_progress_current"
    BATCH_PROGRESS_FILE = "batch_progress_file"
    BATCH_PROGRESS_SUCCESS = "batch_progress_success"
    BATCH_PROGRESS_FAILED = "batch_progress_failed"
    BATCH_PROGRESS_ELAPSED = "batch_progress_elapsed"
    BATCH_PROGRESS_SPEED = "batch_progress_speed"
    BATCH_STATUS_COLLECTING = "batch_status_collecting"
    BATCH_STATUS_PROCESSING = "batch_status_processing"
    BATCH_STATUS_COMPLETED = "batch_status_completed"
    BATCH_STATUS_CANCELLED = "batch_status_cancelled"
    BATCH_RESULTS_TITLE = "batch_results_title"
    BATCH_RESULTS_SUCCESS = "batch_results_success"
    BATCH_RESULTS_FAILED = "batch_results_failed"
    BATCH_RESULTS_SKIPPED = "batch_results_skipped"
    BATCH_RESULTS_SUCCESS_RATE = "batch_results_success_rate"
    BATCH_RESULTS_TOTAL_SIZE = "batch_results_total_size"
    BATCH_RESULTS_PROCESSED_SIZE = "batch_results_processed_size"
    BATCH_RESULTS_ELAPSED_TIME = "batch_results_elapsed_time"
    BATCH_RESULTS_AVG_SPEED = "batch_results_avg_speed"
    BATCH_NO_FILES_SELECTED = "batch_no_files_selected"
    BATCH_INVALID_OUTPUT_DIR = "batch_invalid_output_dir"
    BATCH_OPERATION_STARTED = "batch_operation_started"
    BATCH_OPERATION_COMPLETED = "batch_operation_completed"
    BATCH_OPERATION_CANCELLED = "batch_operation_cancelled"
    BATCH_OPERATION_FAILED = "batch_operation_failed"
    BATCH_ERROR_INVALID_PATHS = "batch_error_invalid_paths"
    BATCH_ERROR_NO_OUTPUT = "batch_error_no_output"
    BATCH_ERROR_PROCESSING_ACTIVE = "batch_error_processing_active"
    BATCH_TIPS_TITLE = "batch_tips_title"
    BATCH_TIPS_ENCRYPT = "batch_tips_encrypt"
    BATCH_TIPS_DECRYPT = "batch_tips_decrypt"

    # 批量操作对话框标题
    BATCH_SELECT_FILES_DIALOG_TITLE = "batch_select_files_dialog_title"
    BATCH_SELECT_FOLDER_DIALOG_TITLE = "batch_select_folder_dialog_title"


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
            
            # 设置对话框新增翻译
            TranslationKeys.UI_LANGUAGE: "界面语言：",
            TranslationKeys.UI_THEME: "界面主题：",
            TranslationKeys.DEFAULT_ALGORITHM_LABEL: "默认算法：",
            TranslationKeys.DEFAULT_KEY_TYPE_LABEL: "默认密钥类型：",
            TranslationKeys.OTP_FORMAT_INFO: "选择密钥文件保存格式，十六进制便于查看，二进制更节省空间",
            TranslationKeys.DEFAULT_INPUT_DIRECTORY: "默认输入目录：",
            TranslationKeys.DEFAULT_OUTPUT_DIRECTORY: "默认输出目录：",
            TranslationKeys.FEATURE_DESCRIPTION: "功能说明",
            TranslationKeys.ADVANCED_SETTINGS_INFO: "当前版本的高级设置仅包含已实现的功能：\n• 调试模式：控制控制台输出详细程度\n• 日志级别：控制日志信息的详细程度\n• 缓冲区大小：控制文件分块处理的大小\n\n其他高级功能将在未来版本中添加。",
            TranslationKeys.TAB_GENERAL: "常规",
            TranslationKeys.TAB_ENCRYPTION: "加密",
            TranslationKeys.TAB_PATHS: "路径",
            TranslationKeys.TAB_ADVANCED: "高级",
            TranslationKeys.LOG_LEVEL_LABEL: "日志级别：",
            TranslationKeys.BUFFER_SIZE_LABEL: "缓冲区大小 (MB)：",
            TranslationKeys.CHINESE_LANGUAGE: "简体中文",
            TranslationKeys.ENGLISH_LANGUAGE: "English",
            TranslationKeys.SETTINGS_SUCCESS_TITLE: "成功",
            TranslationKeys.SETTINGS_SUCCESS_MESSAGE: "设置已成功应用",
            TranslationKeys.VALIDATION_ERROR_TITLE: "验证错误",
            TranslationKeys.VALIDATION_ERROR_MESSAGE: "设置验证失败: {error}",
            TranslationKeys.ERROR_TITLE: "错误",
            TranslationKeys.ERROR_MESSAGE_TEMPLATE: "应用设置时出错: {error}",
            TranslationKeys.RESET_TITLE: "重置",
            TranslationKeys.RESET_MESSAGE: "设置已重置为默认值",
            TranslationKeys.CLEAR_TITLE: "清空",
            TranslationKeys.CLEAR_MESSAGE: "历史记录已清空",

            # 重启提示翻译
            TranslationKeys.RESTART_REQUIRED_TITLE: "需要重启界面",
            TranslationKeys.RESTART_REQUIRED_INTRO: "您已更改了需要重启界面才能完全生效的设置：",
            TranslationKeys.RESTART_LANGUAGE_CHANGED: "语言已更改",
            TranslationKeys.RESTART_THEME_CHANGED: "主题已更改",
            TranslationKeys.RESTART_REQUIRED_INSTRUCTIONS: "请重启界面以使更改生效。点击\"立即重启\"按钮关闭设置对话框并重启界面。",
            TranslationKeys.RESTART_NOW_BUTTON: "立即重启",
            TranslationKeys.RESTART_LATER_BUTTON: "稍后重启",

            # 批量操作翻译
            TranslationKeys.BATCH_OPERATION: "批量操作",
            TranslationKeys.BATCH_TAB_TITLE: "批量加密/解密",
            TranslationKeys.BATCH_SELECT_FILES: "选择文件",
            TranslationKeys.BATCH_SELECT_FOLDER: "选择文件夹",
            TranslationKeys.BATCH_SELECT_RECURSIVE: "递归选择文件夹",
            TranslationKeys.BATCH_SELECTED_FILES: "已选文件：{count} 个文件",
            TranslationKeys.BATCH_SELECTED_FOLDER: "已选文件夹：{path}",
            TranslationKeys.BATCH_SELECTED_RECURSIVE: "已选文件夹（递归）：{path}",
            TranslationKeys.BATCH_PROCESSING_MODE: "处理模式：",
            TranslationKeys.BATCH_PROCESSING_MODE_FILES: "多个文件",
            TranslationKeys.BATCH_PROCESSING_MODE_FOLDER: "文件夹内容",
            TranslationKeys.BATCH_PROCESSING_MODE_RECURSIVE: "文件夹内容（递归）",
            TranslationKeys.BATCH_OUTPUT_DIRECTORY: "输出目录：",
            TranslationKeys.BATCH_PRESERVE_STRUCTURE: "保持目录结构",
            TranslationKeys.BATCH_ENABLE_PARALLEL: "启用并行处理",
            TranslationKeys.BATCH_MAX_THREADS: "最大线程数：",
            TranslationKeys.BATCH_START_ENCRYPTION: "开始批量加密",
            TranslationKeys.BATCH_START_DECRYPTION: "开始批量解密",
            TranslationKeys.BATCH_CANCEL_PROCESSING: "取消处理",
            TranslationKeys.BATCH_PROGRESS_TOTAL: "总文件数：{total}",
            TranslationKeys.BATCH_PROGRESS_CURRENT: "当前进度：{current}/{total}",
            TranslationKeys.BATCH_PROGRESS_FILE: "正在处理：{filename}",
            TranslationKeys.BATCH_PROGRESS_SUCCESS: "成功：{success}",
            TranslationKeys.BATCH_PROGRESS_FAILED: "失败：{failed}",
            TranslationKeys.BATCH_PROGRESS_ELAPSED: "耗时：{elapsed}",
            TranslationKeys.BATCH_PROGRESS_SPEED: "速度：{speed} MB/秒",
            TranslationKeys.BATCH_STATUS_COLLECTING: "正在收集文件...",
            TranslationKeys.BATCH_STATUS_PROCESSING: "正在处理...",
            TranslationKeys.BATCH_STATUS_COMPLETED: "处理完成",
            TranslationKeys.BATCH_STATUS_CANCELLED: "处理已取消",
            TranslationKeys.BATCH_RESULTS_TITLE: "批量处理结果",
            TranslationKeys.BATCH_RESULTS_SUCCESS: "成功：{count} 个文件",
            TranslationKeys.BATCH_RESULTS_FAILED: "失败：{count} 个文件",
            TranslationKeys.BATCH_RESULTS_SKIPPED: "跳过：{count} 个文件",
            TranslationKeys.BATCH_RESULTS_SUCCESS_RATE: "成功率：{rate}%",
            TranslationKeys.BATCH_RESULTS_TOTAL_SIZE: "总大小：{size}",
            TranslationKeys.BATCH_RESULTS_PROCESSED_SIZE: "已处理：{size}",
            TranslationKeys.BATCH_RESULTS_ELAPSED_TIME: "耗时：{time}",
            TranslationKeys.BATCH_RESULTS_AVG_SPEED: "平均速度：{speed} MB/秒",
            TranslationKeys.BATCH_NO_FILES_SELECTED: "未选择任何文件",
            TranslationKeys.BATCH_INVALID_OUTPUT_DIR: "无效的输出目录",
            TranslationKeys.BATCH_OPERATION_STARTED: "批量操作已开始",
            TranslationKeys.BATCH_OPERATION_COMPLETED: "批量操作完成",
            TranslationKeys.BATCH_OPERATION_CANCELLED: "批量操作已取消",
            TranslationKeys.BATCH_OPERATION_FAILED: "批量操作失败：{error}",
            TranslationKeys.BATCH_ERROR_INVALID_PATHS: "无效的路径",
            TranslationKeys.BATCH_ERROR_NO_OUTPUT: "请指定输出目录",
            TranslationKeys.BATCH_ERROR_PROCESSING_ACTIVE: "已有处理正在进行",
            TranslationKeys.BATCH_TIPS_TITLE: "批量操作提示",
            TranslationKeys.BATCH_TIPS_ENCRYPT: "• 支持批量加密多个文件或整个文件夹\n• 加密后文件会添加.enc扩展名\n• 可启用并行处理加快速度",
            TranslationKeys.BATCH_TIPS_DECRYPT: "• 支持批量解密多个文件或整个文件夹\n• 自动识别.enc扩展名\n• 密码模式需要输入正确密码",
            TranslationKeys.BATCH_SELECT_FILES_DIALOG_TITLE: "选择文件",
            TranslationKeys.BATCH_SELECT_FOLDER_DIALOG_TITLE: "选择文件夹",
            TranslationKeys.BATCH_SELECT_RECURSIVE: "选择文件夹（递归）",
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
            
            # Settings dialog new translations
            TranslationKeys.UI_LANGUAGE: "Interface Language:",
            TranslationKeys.UI_THEME: "Interface Theme:",
            TranslationKeys.DEFAULT_ALGORITHM_LABEL: "Default Algorithm:",
            TranslationKeys.DEFAULT_KEY_TYPE_LABEL: "Default Key Type:",
            TranslationKeys.OTP_FORMAT_INFO: "Select key file format, hexadecimal for easy viewing, binary for space efficiency",
            TranslationKeys.DEFAULT_INPUT_DIRECTORY: "Default Input Directory:",
            TranslationKeys.DEFAULT_OUTPUT_DIRECTORY: "Default Output Directory:",
            TranslationKeys.FEATURE_DESCRIPTION: "Feature Description",
            TranslationKeys.ADVANCED_SETTINGS_INFO: "Current version of advanced settings only includes implemented features:\n• Debug mode: Controls console output verbosity\n• Log level: Controls log message verbosity\n• Buffer size: Controls file chunk processing size\n\nOther advanced features will be added in future versions.",
            TranslationKeys.TAB_GENERAL: "General",
            TranslationKeys.TAB_ENCRYPTION: "Encryption",
            TranslationKeys.TAB_PATHS: "Paths",
            TranslationKeys.TAB_ADVANCED: "Advanced",
            TranslationKeys.LOG_LEVEL_LABEL: "Log Level:",
            TranslationKeys.BUFFER_SIZE_LABEL: "Buffer Size (MB):",
            TranslationKeys.CHINESE_LANGUAGE: "Chinese",
            TranslationKeys.ENGLISH_LANGUAGE: "English",
            TranslationKeys.SETTINGS_SUCCESS_TITLE: "Success",
            TranslationKeys.SETTINGS_SUCCESS_MESSAGE: "Settings successfully applied",
            TranslationKeys.VALIDATION_ERROR_TITLE: "Validation Error",
            TranslationKeys.VALIDATION_ERROR_MESSAGE: "Settings validation failed: {error}",
            TranslationKeys.ERROR_TITLE: "Error",
            TranslationKeys.ERROR_MESSAGE_TEMPLATE: "Error applying settings: {error}",
            TranslationKeys.RESET_TITLE: "Reset",
            TranslationKeys.RESET_MESSAGE: "Settings reset to defaults",
            TranslationKeys.CLEAR_TITLE: "Clear",
            TranslationKeys.CLEAR_MESSAGE: "History cleared",

            # Restart prompt translations
            TranslationKeys.RESTART_REQUIRED_TITLE: "Restart Required",
            TranslationKeys.RESTART_REQUIRED_INTRO: "You have changed settings that require a restart to take full effect:",
            TranslationKeys.RESTART_LANGUAGE_CHANGED: "Language changed",
            TranslationKeys.RESTART_THEME_CHANGED: "Theme changed",
            TranslationKeys.RESTART_REQUIRED_INSTRUCTIONS: "Please restart the interface for the changes to take effect. Click \"Restart Now\" to close the settings dialog and restart the interface.",
            TranslationKeys.RESTART_NOW_BUTTON: "Restart Now",
            TranslationKeys.RESTART_LATER_BUTTON: "Restart Later",

            # Batch operation translations
            TranslationKeys.BATCH_OPERATION: "Batch Operation",
            TranslationKeys.BATCH_TAB_TITLE: "Batch Encryption/Decryption",
            TranslationKeys.BATCH_SELECT_FILES: "Select Files",
            TranslationKeys.BATCH_SELECT_FOLDER: "Select Folder",
            TranslationKeys.BATCH_SELECT_RECURSIVE: "Select Folder Recursively",
            TranslationKeys.BATCH_SELECTED_FILES: "Selected files: {count} files",
            TranslationKeys.BATCH_SELECTED_FOLDER: "Selected folder: {path}",
            TranslationKeys.BATCH_SELECTED_RECURSIVE: "Selected folder (recursive): {path}",
            TranslationKeys.BATCH_PROCESSING_MODE: "Processing mode:",
            TranslationKeys.BATCH_PROCESSING_MODE_FILES: "Multiple files",
            TranslationKeys.BATCH_PROCESSING_MODE_FOLDER: "Folder contents",
            TranslationKeys.BATCH_PROCESSING_MODE_RECURSIVE: "Folder contents (recursive)",
            TranslationKeys.BATCH_OUTPUT_DIRECTORY: "Output directory:",
            TranslationKeys.BATCH_PRESERVE_STRUCTURE: "Preserve directory structure",
            TranslationKeys.BATCH_ENABLE_PARALLEL: "Enable parallel processing",
            TranslationKeys.BATCH_MAX_THREADS: "Max threads:",
            TranslationKeys.BATCH_START_ENCRYPTION: "Start Batch Encryption",
            TranslationKeys.BATCH_START_DECRYPTION: "Start Batch Decryption",
            TranslationKeys.BATCH_CANCEL_PROCESSING: "Cancel Processing",
            TranslationKeys.BATCH_PROGRESS_TOTAL: "Total files: {total}",
            TranslationKeys.BATCH_PROGRESS_CURRENT: "Current progress: {current}/{total}",
            TranslationKeys.BATCH_PROGRESS_FILE: "Processing: {filename}",
            TranslationKeys.BATCH_PROGRESS_SUCCESS: "Success: {success}",
            TranslationKeys.BATCH_PROGRESS_FAILED: "Failed: {failed}",
            TranslationKeys.BATCH_PROGRESS_ELAPSED: "Elapsed: {elapsed}",
            TranslationKeys.BATCH_PROGRESS_SPEED: "Speed: {speed} MB/s",
            TranslationKeys.BATCH_STATUS_COLLECTING: "Collecting files...",
            TranslationKeys.BATCH_STATUS_PROCESSING: "Processing...",
            TranslationKeys.BATCH_STATUS_COMPLETED: "Processing completed",
            TranslationKeys.BATCH_STATUS_CANCELLED: "Processing cancelled",
            TranslationKeys.BATCH_RESULTS_TITLE: "Batch Processing Results",
            TranslationKeys.BATCH_RESULTS_SUCCESS: "Success: {count} files",
            TranslationKeys.BATCH_RESULTS_FAILED: "Failed: {count} files",
            TranslationKeys.BATCH_RESULTS_SKIPPED: "Skipped: {count} files",
            TranslationKeys.BATCH_RESULTS_SUCCESS_RATE: "Success rate: {rate}%",
            TranslationKeys.BATCH_RESULTS_TOTAL_SIZE: "Total size: {size}",
            TranslationKeys.BATCH_RESULTS_PROCESSED_SIZE: "Processed: {size}",
            TranslationKeys.BATCH_RESULTS_ELAPSED_TIME: "Elapsed time: {time}",
            TranslationKeys.BATCH_RESULTS_AVG_SPEED: "Average speed: {speed} MB/s",
            TranslationKeys.BATCH_NO_FILES_SELECTED: "No files selected",
            TranslationKeys.BATCH_INVALID_OUTPUT_DIR: "Invalid output directory",
            TranslationKeys.BATCH_OPERATION_STARTED: "Batch operation started",
            TranslationKeys.BATCH_OPERATION_COMPLETED: "Batch operation completed",
            TranslationKeys.BATCH_OPERATION_CANCELLED: "Batch operation cancelled",
            TranslationKeys.BATCH_OPERATION_FAILED: "Batch operation failed: {error}",
            TranslationKeys.BATCH_ERROR_INVALID_PATHS: "Invalid paths",
            TranslationKeys.BATCH_ERROR_NO_OUTPUT: "Please specify output directory",
            TranslationKeys.BATCH_ERROR_PROCESSING_ACTIVE: "Processing already in progress",
            TranslationKeys.BATCH_TIPS_TITLE: "Batch Operation Tips",
            TranslationKeys.BATCH_TIPS_ENCRYPT: "• Supports batch encryption of multiple files or entire folders\n• Encrypted files get .enc extension\n• Enable parallel processing for faster speed",
            TranslationKeys.BATCH_TIPS_DECRYPT: "• Supports batch decryption of multiple files or entire folders\n• Automatically recognizes .enc extension\n• Password mode requires correct password",
            TranslationKeys.BATCH_SELECT_FILES_DIALOG_TITLE: "Select Files",
            TranslationKeys.BATCH_SELECT_FOLDER_DIALOG_TITLE: "Select Folder",
            TranslationKeys.BATCH_SELECT_RECURSIVE: "Select Folder Recursively",
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