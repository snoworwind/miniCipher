#!/usr/bin/env python3
"""
配置验证器模块
为miniCipher配置系统提供验证和约束功能
支持多种验证类型：枚举值、数值范围、字符串长度、路径有效性等
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from pathlib import Path


class ValidationError(Exception):
    """配置验证错误异常"""
    
    def __init__(self, config_key: str, value: Any, message: str, validation_rule: Dict = None):
        self.config_key = config_key
        self.value = value
        self.message = message
        self.validation_rule = validation_rule or {}
        super().__init__(f"配置项 '{config_key}' 验证失败: {message} (值: {repr(value)})")


class ConfigValidator:
    """配置验证器类"""
    
    @staticmethod
    def validate_string(value: Any, min_len: int = None, max_len: int = None, 
                       pattern: str = None, allow_empty: bool = True) -> bool:
        """
        验证字符串值
        
        Args:
            value: 要验证的值
            min_len: 最小长度
            max_len: 最大长度
            pattern: 正则表达式模式
            allow_empty: 是否允许空字符串
            
        Returns:
            bool: 验证是否通过
        """
        # 转换为字符串
        if value is None:
            return allow_empty
        
        str_value = str(value)
        
        # 检查空字符串
        if not str_value and not allow_empty:
            return False
        
        # 检查长度
        if min_len is not None and len(str_value) < min_len:
            return False
        
        if max_len is not None and len(str_value) > max_len:
            return False
        
        # 检查正则表达式模式
        if pattern is not None:
            if not re.match(pattern, str_value):
                return False
        
        return True
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> bool:
        """
        验证整数值
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            bool: 验证是否通过
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False
        
        if min_val is not None and int_value < min_val:
            return False
        
        if max_val is not None and int_value > max_val:
            return False
        
        return True
    
    @staticmethod
    def validate_float(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """
        验证浮点数值
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            bool: 验证是否通过
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            return False
        
        if min_val is not None and float_value < min_val:
            return False
        
        if max_val is not None and float_value > max_val:
            return False
        
        return True
    
    @staticmethod
    def validate_boolean(value: Any) -> bool:
        """
        验证布尔值
        
        Args:
            value: 要验证的值
            
        Returns:
            bool: 验证是否通过
        """
        if isinstance(value, bool):
            return True
        elif isinstance(value, str):
            return value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n')
        elif isinstance(value, int):
            return value in (0, 1)
        else:
            return False
    
    @staticmethod
    def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
        """
        验证枚举值
        
        Args:
            value: 要验证的值
            allowed_values: 允许的值列表
            
        Returns:
            bool: 验证是否通过
        """
        return value in allowed_values
    
    @staticmethod
    def validate_path(value: str, must_exist: bool = False, must_be_dir: bool = False, 
                     must_be_file: bool = False, allow_empty: bool = True) -> bool:
        """
        验证路径值
        
        Args:
            value: 要验证的路径
            must_exist: 路径必须存在
            must_be_dir: 路径必须是目录
            must_be_file: 路径必须是文件
            allow_empty: 是否允许空路径
            
        Returns:
            bool: 验证是否通过
        """
        if not value:
            return allow_empty
        
        # 检查路径格式（基本格式检查）
        try:
            path = Path(value)
        except Exception:
            return False
        
        # 检查路径存在性
        if must_exist and not path.exists():
            return False
        
        # 检查路径类型
        if must_be_dir and path.exists() and not path.is_dir():
            return False
        
        if must_be_file and path.exists() and not path.is_file():
            return False
        
        # 检查是否可访问（如果存在）
        if path.exists():
            try:
                # 尝试访问路径
                path.stat()
            except (OSError, PermissionError):
                return False
        
        return True
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """
        验证电子邮件地址
        
        Args:
            value: 要验证的电子邮件地址
            
        Returns:
            bool: 验证是否通过
        """
        if not value:
            return True
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))
    
    @staticmethod
    def validate_url(value: str) -> bool:
        """
        验证URL地址
        
        Args:
            value: 要验证的URL
            
        Returns:
            bool: 验证是否通过
        """
        if not value:
            return True
        
        url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        return bool(re.match(url_pattern, value))
    
    @staticmethod
    def validate_regex(value: str, pattern: str) -> bool:
        """
        使用正则表达式验证值
        
        Args:
            value: 要验证的值
            pattern: 正则表达式模式
            
        Returns:
            bool: 验证是否通过
        """
        if value is None:
            return True
        
        return bool(re.match(pattern, str(value)))


class ConfigValidationRules:
    """配置验证规则定义"""
    
    # 验证规则字典
    # 格式: config_key -> validation_rule
    # validation_rule 包含:
    #   - type: 验证类型 (string, integer, float, boolean, enum, path, regex, email, url)
    #   - required: 是否必须（默认True）
    #   - 其他类型特定的参数
    
    @staticmethod
    def get_rules() -> Dict[str, Dict[str, Any]]:
        """获取所有配置验证规则"""
        from config_manager import Language, ThemeType, AlgorithmType, KeyType, ConfigStatus
        
        return {
            # 基本配置 - UI
            "version": {
                "type": "string",
                "min_len": 1,
                "max_len": 20,
                "required": True
            },
            
            # 语言设置
            "basic.ui.language": {
                "type": "enum",
                "allowed_values": [lang.value for lang in Language],
                "required": True,
                "default": Language.ZH_CN.value
            },
            
            # 主题设置
            "basic.ui.theme": {
                "type": "enum",
                "allowed_values": [theme.value for theme in ThemeType],
                "required": True,
                "default": ThemeType.LIGHT.value
            },
            
            # 窗口大小
            "basic.ui.window_width": {
                "type": "integer",
                "min_val": 400,
                "max_val": 3840,
                "required": True,
                "default": 800
            },
            
            "basic.ui.window_height": {
                "type": "integer",
                "min_val": 300,
                "max_val": 2160,
                "required": True,
                "default": 600
            },
            
            # 加密配置
            "basic.encryption.default_algorithm": {
                "type": "enum",
                "allowed_values": [alg.value for alg in AlgorithmType],
                "required": True,
                "default": AlgorithmType.OTP.value
            },
            
            "basic.encryption.default_key_type": {
                "type": "enum",
                "allowed_values": [kt.value for kt in KeyType],
                "required": True,
                "default": KeyType.RANDOM.value
            },
            
            "basic.encryption.password_min_length": {
                "type": "integer",
                "min_val": 4,
                "max_val": 32,
                "required": True,
                "default": 8
            },
            
            "basic.encryption.require_strong_password": {
                "type": "boolean",
                "required": True,
                "default": True
            },
            
            "basic.encryption.otp_key_format": {
                "type": "enum",
                "allowed_values": ["hex", "binary"],
                "required": True,
                "default": "hex"
            },
            
            # 路径配置
            "basic.paths.default_input_dir": {
                "type": "path",
                "must_exist": False,
                "must_be_dir": True,
                "allow_empty": True,
                "required": False,
                "default": ""
            },
            
            "basic.paths.default_output_dir": {
                "type": "path",
                "must_exist": False,
                "must_be_dir": True,
                "allow_empty": True,
                "required": False,
                "default": ""
            },
            
            "basic.paths.remember_last_folder": {
                "type": "boolean",
                "required": True,
                "default": True
            },
            
            "basic.paths.last_input_folder": {
                "type": "path",
                "must_exist": False,
                "must_be_dir": True,
                "allow_empty": True,
                "required": False,
                "default": ""
            },
            
            "basic.paths.last_output_folder": {
                "type": "path",
                "must_exist": False,
                "must_be_dir": True,
                "allow_empty": True,
                "required": False,
                "default": ""
            },
            
            # 高级配置
            "advanced.debug_mode": {
                "type": "boolean",
                "required": True,
                "default": False
            },
            
            "advanced.log_level": {
                "type": "enum",
                "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "required": True,
                "default": "INFO"
            },
            
            "advanced.buffer_size": {
                "type": "integer",
                "min_val": 1,
                "max_val": 100,
                "required": True,
                "default": 10
            },

            # 批量配置
            "batch.parallel_processing": {
                "type": "boolean",
                "required": True,
                "default": False
            },
            "batch.max_threads": {
                "type": "integer",
                "min_val": 1,
                "max_val": 16,
                "required": True,
                "default": 4
            },
            "batch.preserve_structure": {
                "type": "boolean",
                "required": True,
                "default": True
            }
        }
    
    @staticmethod
    def get_rule_for_key(config_key: str) -> Optional[Dict[str, Any]]:
        """获取指定配置键的验证规则"""
        rules = ConfigValidationRules.get_rules()
        return rules.get(config_key)
    
    @staticmethod
    def get_all_keys() -> List[str]:
        """获取所有有验证规则的配置键"""
        return list(ConfigValidationRules.get_rules().keys())


class ConfigValidationManager:
    """配置验证管理器"""
    
    def __init__(self, config_manager=None):
        """
        初始化验证管理器
        
        Args:
            config_manager: 配置管理器实例（可选）
        """
        self.config_manager = config_manager
        self.validator = ConfigValidator()
        self.rules = ConfigValidationRules.get_rules()
        
    def validate_key(self, config_key: str, value: Any) -> Tuple[bool, str]:
        """
        验证单个配置键的值
        
        Args:
            config_key: 配置键
            value: 要验证的值
            
        Returns:
            Tuple[bool, str]: (验证是否通过, 错误消息)
        """
        # 获取验证规则
        rule = self.rules.get(config_key)
        if not rule:
            # 没有验证规则，直接通过
            return True, "无验证规则"
        
        # 检查必需性
        required = rule.get("required", True)
        if value is None and required:
            return False, "配置项是必需的"
        
        # 如果值为None且非必需，通过验证
        if value is None:
            return True, ""
        
        # 根据类型验证
        validation_type = rule.get("type", "string")
        
        try:
            if validation_type == "string":
                if not self.validator.validate_string(
                    value,
                    min_len=rule.get("min_len"),
                    max_len=rule.get("max_len"),
                    pattern=rule.get("pattern"),
                    allow_empty=not required
                ):
                    return False, "字符串验证失败"
            
            elif validation_type == "integer":
                if not self.validator.validate_integer(
                    value,
                    min_val=rule.get("min_val"),
                    max_val=rule.get("max_val")
                ):
                    min_val = rule.get("min_val")
                    max_val = rule.get("max_val")
                    if min_val is not None and max_val is not None:
                        return False, f"整数值必须在 {min_val} 和 {max_val} 之间"
                    elif min_val is not None:
                        return False, f"整数值必须大于等于 {min_val}"
                    elif max_val is not None:
                        return False, f"整数值必须小于等于 {max_val}"
                    else:
                        return False, "无效的整数值"
            
            elif validation_type == "float":
                if not self.validator.validate_float(
                    value,
                    min_val=rule.get("min_val"),
                    max_val=rule.get("max_val")
                ):
                    min_val = rule.get("min_val")
                    max_val = rule.get("max_val")
                    if min_val is not None and max_val is not None:
                        return False, f"浮点数值必须在 {min_val} 和 {max_val} 之间"
                    elif min_val is not None:
                        return False, f"浮点数值必须大于等于 {min_val}"
                    elif max_val is not None:
                        return False, f"浮点数值必须小于等于 {max_val}"
                    else:
                        return False, "无效的浮点数值"
            
            elif validation_type == "boolean":
                if not self.validator.validate_boolean(value):
                    return False, "无效的布尔值"
            
            elif validation_type == "enum":
                allowed_values = rule.get("allowed_values", [])
                if not self.validator.validate_enum(value, allowed_values):
                    return False, f"值必须在允许的列表中: {allowed_values}"
            
            elif validation_type == "path":
                if not self.validator.validate_path(
                    value,
                    must_exist=rule.get("must_exist", False),
                    must_be_dir=rule.get("must_be_dir", False),
                    must_be_file=rule.get("must_be_file", False),
                    allow_empty=not required
                ):
                    constraints = []
                    if rule.get("must_exist"):
                        constraints.append("必须存在")
                    if rule.get("must_be_dir"):
                        constraints.append("必须是目录")
                    if rule.get("must_be_file"):
                        constraints.append("必须是文件")
                    
                    if constraints:
                        constraint_text = "，".join(constraints)
                        return False, f"路径无效: {constraint_text}"
                    else:
                        return False, "无效的路径格式"
            
            elif validation_type == "email":
                if not self.validator.validate_email(value):
                    return False, "无效的电子邮件地址格式"
            
            elif validation_type == "url":
                if not self.validator.validate_url(value):
                    return False, "无效的URL格式"
            
            elif validation_type == "regex":
                pattern = rule.get("pattern")
                if pattern and not self.validator.validate_regex(value, pattern):
                    return False, "值不符合正则表达式模式"
            
            else:
                # 未知验证类型
                return False, f"未知的验证类型: {validation_type}"
            
        except Exception as e:
            # 验证过程中发生异常
            return False, f"验证过程中发生错误: {str(e)}"
        
        return True, ""
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        验证整个配置字典
        
        Args:
            config: 配置字典
            
        Returns:
            Tuple[bool, Dict[str, str]]: (是否全部通过, 错误字典 {配置键: 错误消息})
        """
        errors = {}
        
        for key, rule in self.rules.items():
            # 使用点分隔符获取配置值
            value = self._get_nested_value(config, key)
            
            is_valid, error_msg = self.validate_key(key, value)
            
            if not is_valid:
                errors[key] = error_msg
        
        return len(errors) == 0, errors
    
    def validate_and_sanitize(self, config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        验证并清理配置，返回清理后的配置和错误信息
        
        Args:
            config: 原始配置字典
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, str]]: (清理后的配置, 错误字典)
        """
        sanitized_config = config.copy()
        errors = {}
        
        for key, rule in self.rules.items():
            # 获取当前值
            value = self._get_nested_value(sanitized_config, key)
            
            # 验证值
            is_valid, error_msg = self.validate_key(key, value)
            
            if not is_valid:
                # 如果验证失败但有默认值，使用默认值
                default_value = rule.get("default")
                if default_value is not None:
                    self._set_nested_value(sanitized_config, key, default_value)
                else:
                    errors[key] = error_msg
        
        return sanitized_config, errors
    
    def get_default_value(self, config_key: str) -> Any:
        """
        获取配置键的默认值
        
        Args:
            config_key: 配置键
            
        Returns:
            Any: 默认值，如果没有则返回None
        """
        rule = self.rules.get(config_key)
        if rule:
            return rule.get("default")
        return None
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """
        获取所有配置键的默认值
        
        Returns:
            Dict[str, Any]: 默认值字典
        """
        defaults = {}
        for key, rule in self.rules.items():
            default_value = rule.get("default")
            if default_value is not None:
                defaults[key] = default_value
        return defaults
    
    def _get_nested_value(self, config: Dict[str, Any], key: str) -> Any:
        """
        使用点分隔符从嵌套字典中获取值
        
        Args:
            config: 配置字典
            key: 点分隔符键（如 'basic.ui.language'）
            
        Returns:
            Any: 找到的值，如果没有则返回None
        """
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """
        使用点分隔符在嵌套字典中设置值
        
        Args:
            config: 配置字典
            key: 点分隔符键
            value: 要设置的值
        """
        keys = key.split('.')
        current = config
        
        # 导航到最后一个键的父字典
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value


# 单例实例
_validation_manager: Optional[ConfigValidationManager] = None

def get_validation_manager(config_manager=None) -> ConfigValidationManager:
    """获取配置验证管理器单例实例"""
    global _validation_manager
    if _validation_manager is None:
        _validation_manager = ConfigValidationManager(config_manager)
    return _validation_manager


if __name__ == "__main__":
    # 测试验证器
    print("测试配置验证器...")
    
    validator = ConfigValidator()
    
    # 测试字符串验证
    print("字符串验证测试:")
    print(f"  空字符串: {validator.validate_string('', allow_empty=True)}")
    print(f"  非空字符串: {validator.validate_string('test', allow_empty=False)}")
    print(f"  长度范围: {validator.validate_string('test', min_len=2, max_len=10)}")
    
    # 测试整数验证
    print("\n整数验证测试:")
    print(f"  有效整数: {validator.validate_integer(42, min_val=0, max_val=100)}")
    print(f"  超出范围: {validator.validate_integer(150, min_val=0, max_val=100)}")
    
    # 测试枚举验证
    print("\n枚举验证测试:")
    print(f"  有效枚举值: {validator.validate_enum('zh_CN', ['zh_CN', 'en_US'])}")
    print(f"  无效枚举值: {validator.validate_enum('fr_FR', ['zh_CN', 'en_US'])}")
    
    # 测试路径验证
    print("\n路径验证测试:")
    print(f"  当前目录: {validator.validate_path('.', must_exist=True)}")
    print(f"  不存在的路径: {validator.validate_path('/nonexistent/path', must_exist=False)}")
    
    # 测试验证管理器
    print("\n验证管理器测试:")
    validation_manager = get_validation_manager()
    
    test_config = {
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
    
    is_valid, errors = validation_manager.validate_config(test_config)
    print(f"  配置验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print(f"  错误信息: {errors}")
    
    # 测试无效配置
    invalid_config = test_config.copy()
    invalid_config["basic"]["ui"]["window_width"] = 100  # 太小
    
    is_valid, errors = validation_manager.validate_config(invalid_config)
    print(f"  无效配置验证结果: {'通过' if is_valid else '失败'}")
    if errors:
        print(f"  错误信息: {errors}")
    
    print("\n测试完成!")