#!/usr/bin/env python3
"""
配置验证系统测试脚本
测试新添加的配置验证功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from config_manager import get_config_manager, AlgorithmType, KeyType, ThemeType, Language
from config_validator import ConfigValidator, ConfigValidationManager, ValidationError, get_validation_manager

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_validator():
    """测试配置验证器"""
    print("=" * 50)
    print("测试配置验证器")
    print("=" * 50)
    
    validator = ConfigValidator()
    
    # 测试字符串验证
    print("\n1. 测试字符串验证:")
    print(f"  空字符串 (允许空): {validator.validate_string('', allow_empty=True)}")
    print(f"  空字符串 (不允许空): {validator.validate_string('', allow_empty=False)}")
    print(f"  有效字符串: {validator.validate_string('test', min_len=2, max_len=10)}")
    print(f"  太短字符串: {validator.validate_string('a', min_len=2, max_len=10)}")
    print(f"  太长字符串: {validator.validate_string('toolongstring', min_len=2, max_len=10)}")
    
    # 测试整数验证
    print("\n2. 测试整数验证:")
    print(f"  有效整数: {validator.validate_integer(42, min_val=0, max_val=100)}")
    print(f"  超出范围 (太小): {validator.validate_integer(-5, min_val=0, max_val=100)}")
    print(f"  超出范围 (太大): {validator.validate_integer(150, min_val=0, max_val=100)}")
    print(f"  无效整数 (字符串): {validator.validate_integer('notanumber', min_val=0, max_val=100)}")
    
    # 测试布尔值验证
    print("\n3. 测试布尔值验证:")
    print(f"  True: {validator.validate_boolean(True)}")
    print(f"  False: {validator.validate_boolean(False)}")
    print(f"  'true': {validator.validate_boolean('true')}")
    print(f"  'false': {validator.validate_boolean('false')}")
    print(f"  1: {validator.validate_boolean(1)}")
    print(f"  0: {validator.validate_boolean(0)}")
    print(f"  无效布尔值: {validator.validate_boolean('invalid')}")
    
    # 测试枚举验证
    print("\n4. 测试枚举验证:")
    allowed_values = ['zh_CN', 'en_US', 'fr_FR']
    print(f"  有效枚举值: {validator.validate_enum('zh_CN', allowed_values)}")
    print(f"  无效枚举值: {validator.validate_enum('de_DE', allowed_values)}")
    
    # 测试路径验证
    print("\n5. 测试路径验证:")
    print(f"  当前目录 (必须存在): {validator.validate_path('.', must_exist=True)}")
    print(f"  不存在的路径 (不要求存在): {validator.validate_path('/nonexistent/path', must_exist=False)}")
    
    print("\n配置验证器测试完成!")

def test_validation_manager():
    """测试验证管理器"""
    print("\n" + "=" * 50)
    print("测试验证管理器")
    print("=" * 50)
    
    validation_manager = get_validation_manager()
    
    # 测试单个配置键验证
    print("\n1. 测试单个配置键验证:")
    
    # 有效配置
    test_cases = [
        ("basic.ui.language", "zh_CN", True),
        ("basic.ui.language", "en_US", True),
        ("basic.ui.language", "fr_FR", False),  # 无效语言
        ("basic.encryption.password_min_length", 8, True),
        ("basic.encryption.password_min_length", 3, False),  # 太小
        ("basic.encryption.password_min_length", 33, False),  # 太大
        ("basic.encryption.otp_key_format", "hex", True),
        ("basic.encryption.otp_key_format", "binary", True),
        ("basic.encryption.otp_key_format", "invalid", False),
        ("advanced.log_level", "INFO", True),
        ("advanced.log_level", "DEBUG", True),
        ("advanced.log_level", "WARNING", True),
        ("advanced.log_level", "ERROR", True),
        ("advanced.log_level", "CRITICAL", True),
        ("advanced.log_level", "INVALID", False),
        ("advanced.buffer_size", 10, True),
        ("advanced.buffer_size", 1, True),
        ("advanced.buffer_size", 100, True),
        ("advanced.buffer_size", 0, False),  # 太小
        ("advanced.buffer_size", 101, False),  # 太大
    ]
    
    for config_key, value, expected_valid in test_cases:
        is_valid, error_msg = validation_manager.validate_key(config_key, value)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"  {status} {config_key} = {repr(value)}: {is_valid} (预期: {expected_valid}) {'' if is_valid else f'错误: {error_msg}'}")
    
    # 测试配置验证
    print("\n2. 测试整个配置验证:")
    
    valid_config = {
        "version": "2.0",
        "basic": {
            "ui": {
                "language": "zh_CN",
                "theme": "light",
                "window_width": 800,
                "window_height": 600
            },
            "encryption": {
                "default_algorithm": "OTP",
                "default_key_type": "random",
                "password_min_length": 8,
                "require_strong_password": True,
                "otp_key_format": "hex"
            },
            "paths": {
                "default_input_dir": "",
                "default_output_dir": "",
                "remember_last_folder": True,
                "last_input_folder": "",
                "last_output_folder": ""
            }
        },
        "advanced": {
            "debug_mode": False,
            "log_level": "INFO",
            "buffer_size": 10
        }
    }
    
    is_valid, errors = validation_manager.validate_config(valid_config)
    print(f"  有效配置验证: {'通过' if is_valid else '失败'}")
    if errors:
        for key, error in errors.items():
            print(f"    错误: {key} - {error}")
    
    # 测试无效配置
    invalid_config = valid_config.copy()
    invalid_config["basic"]["encryption"]["password_min_length"] = 2  # 太小
    
    is_valid, errors = validation_manager.validate_config(invalid_config)
    print(f"  无效配置验证: {'通过' if is_valid else '失败'}")
    if errors:
        for key, error in errors.items():
            print(f"    错误: {key} - {error}")
    
    # 测试验证和清理
    print("\n3. 测试验证和清理:")
    test_config = {
        "basic": {
            "ui": {
                "language": "invalid_language",  # 无效，应使用默认值
                "theme": "light"
            },
            "encryption": {
                "password_min_length": 200  # 无效，应使用默认值
            }
        }
    }
    
    sanitized_config, errors = validation_manager.validate_and_sanitize(test_config)
    print(f"  清理后配置: {sanitized_config.get('basic', {}).get('ui', {}).get('language')}")
    print(f"  错误: {errors}")
    
    print("\n验证管理器测试完成!")

def test_config_manager_integration():
    """测试ConfigManager集成"""
    print("\n" + "=" * 50)
    print("测试ConfigManager集成")
    print("=" * 50)
    
    config_manager = get_config_manager()
    
    print(f"\n1. 获取配置管理器:")
    print(f"  配置目录: {config_manager.config_dir}")
    print(f"  配置文件: {config_manager.config_file}")
    print(f"  当前语言: {config_manager.get_language()}")
    print(f"  验证管理器: {config_manager.validation_manager}")
    
    # 测试设置方法（带验证）
    print("\n2. 测试设置方法（带验证）:")
    
    # 有效设置
    try:
        config_manager.set("basic.encryption.password_min_length", 12)
        print(f"  ✓ 有效设置: 密码最小长度 = 12")
    except ValidationError as e:
        print(f"  ✗ 意外错误: {e}")
    
    # 无效设置（应抛出异常）
    try:
        config_manager.set("basic.encryption.password_min_length", 2)  # 太小
        print(f"  ✗ 无效设置应抛出异常但未抛出")
    except ValidationError as e:
        print(f"  ✓ 无效设置正确抛出异常: {e}")
    
    # 测试跳过验证的设置
    try:
        config_manager.set("basic.encryption.password_min_length", 2, skip_validation=True)
        print(f"  ✓ 跳过验证的设置: 密码最小长度 = 2 (跳过验证)")
    except ValidationError as e:
        print(f"  ✗ 跳过验证的设置不应抛出异常但抛出了: {e}")
    
    # 测试更新方法
    print("\n3. 测试更新方法:")
    
    valid_updates = {
        "basic.ui.theme": "dark",
        "advanced.debug_mode": True,
        "advanced.buffer_size": 20
    }
    
    try:
        config_manager.update(valid_updates)
        print(f"  ✓ 批量更新: 主题={config_manager.get_theme()}, 调试模式={config_manager.is_debug_mode()}, 缓冲区大小={config_manager.get_buffer_size()}")
    except ValidationError as e:
        print(f"  ✗ 批量更新失败: {e}")
    
    invalid_updates = {
        "basic.ui.theme": "invalid_theme",  # 无效主题
        "advanced.buffer_size": 200  # 太大
    }
    
    try:
        config_manager.update(invalid_updates)
        print(f"  ✗ 无效批量更新应抛出异常但未抛出")
    except ValidationError as e:
        print(f"  ✓ 无效批量更新正确抛出异常: {e}")
    
    # 测试重置为默认值
    print("\n4. 测试重置为默认值:")
    config_manager.reset_to_defaults()
    print(f"  ✓ 重置为默认值完成")
    
    print("\nConfigManager集成测试完成!")

def test_settings_dialog_integration():
    """测试SettingsDialog集成"""
    print("\n" + "=" * 50)
    print("测试SettingsDialog集成")
    print("=" * 50)
    
    print("\n说明: SettingsDialog集成测试需要GUI环境")
    print("可以通过运行settings_dialog.py的测试函数来测试")
    print("或者运行应用程序并打开设置对话框")
    
    print("\nSettingsDialog集成测试完成 (GUI测试需手动)")

def main():
    """主测试函数"""
    print("开始配置验证系统测试")
    print("=" * 50)
    
    try:
        # 测试基本验证器
        test_validator()
        
        # 测试验证管理器
        test_validation_manager()
        
        # 测试ConfigManager集成
        test_config_manager_integration()
        
        # 测试SettingsDialog集成 (信息性)
        test_settings_dialog_integration()
        
        print("\n" + "=" * 50)
        print("所有测试完成!")
        print("=" * 50)
        
        # 运行示例配置文件
        print("\n示例使用:")
        print("1. 导入配置验证器: from config_validator import get_validation_manager")
        print("2. 获取验证管理器: vm = get_validation_manager()")
        print("3. 验证配置键: is_valid, error = vm.validate_key('basic.ui.language', 'zh_CN')")
        print("4. 验证整个配置: is_valid, errors = vm.validate_config(config_dict)")
        print("5. 清理配置: sanitized_config, errors = vm.validate_and_sanitize(config_dict)")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())