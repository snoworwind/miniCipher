#!/usr/bin/env python3
"""
配置文件管理器模块
支持跨平台配置文件管理，用于miniCipher工具
重构版本：明确区分基本配置和高级配置，确保所有配置项都有实际实现
"""

import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set
from enum import Enum

class AlgorithmType(str, Enum):
    """加密算法类型枚举"""
    OTP = "OTP"
    AES256 = "AES256"

class KeyType(str, Enum):
    """密钥类型枚举"""
    RANDOM = "random"
    PASSWORD = "password"

class ThemeType(str, Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"

class Language(str, Enum):
    """支持的语言枚举"""
    ZH_CN = "zh_CN"  # 简体中文
    EN_US = "en_US"  # 英文

class ConfigStatus(str, Enum):
    """配置项状态枚举"""
    IMPLEMENTED = "implemented"      # 已实现并可用
    DEVELOPMENT = "development"      # 开发中，部分功能可用
    DEPRECATED = "deprecated"       # 已弃用，保留兼容性
    REMOVED = "removed"             # 已移除，不再使用

class ConfigurationManager:
    """配置管理器类"""
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_config = self._get_default_config()
        self.config_status = self._get_config_status()
        
        # 初始化验证管理器
        from config_validator import get_validation_manager
        self.validation_manager = get_validation_manager(self)
        
        self.config = self._load_config()
        
        # 初始化日志系统（基于配置）
        self._init_logging()
    
    def _get_config_dir(self) -> Path:
        """获取配置目录（跨平台）"""
        if sys.platform == "win32":
            # Windows: %APPDATA%\miniCipher
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / "miniCipher"
            else:
                return Path.home() / "AppData" / "Roaming" / "miniCipher"
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/miniCipher
            return Path.home() / "Library" / "Application Support" / "miniCipher"
        else:
            # Linux和其他Unix系统: ~/.config/miniCipher
            return Path.home() / ".config" / "miniCipher"
    
    def _get_config_status(self) -> Dict[str, ConfigStatus]:
        """获取配置项状态映射"""
        return {
            # 基本配置 - 已实现
            "ui.language": ConfigStatus.IMPLEMENTED,
            "ui.theme": ConfigStatus.IMPLEMENTED,
            "ui.window_width": ConfigStatus.IMPLEMENTED,
            "ui.window_height": ConfigStatus.IMPLEMENTED,
            
            # 加密配置
            "encryption.default_algorithm": ConfigStatus.IMPLEMENTED,
            "encryption.default_key_type": ConfigStatus.IMPLEMENTED,
            "encryption.password_min_length": ConfigStatus.IMPLEMENTED,
            "encryption.require_strong_password": ConfigStatus.IMPLEMENTED,
            "encryption.otp_key_format": ConfigStatus.IMPLEMENTED,  # 已实现
            
            # 路径配置
            "paths.default_input_dir": ConfigStatus.IMPLEMENTED,
            "paths.default_output_dir": ConfigStatus.IMPLEMENTED,
            "paths.remember_last_folder": ConfigStatus.IMPLEMENTED,
            "paths.last_input_folder": ConfigStatus.IMPLEMENTED,
            "paths.last_output_folder": ConfigStatus.IMPLEMENTED,
            
            # 高级配置
            "advanced.debug_mode": ConfigStatus.IMPLEMENTED,        # 基本调试支持
            "advanced.log_level": ConfigStatus.IMPLEMENTED,         # 基本日志支持
            "advanced.buffer_size": ConfigStatus.IMPLEMENTED,       # 分块处理支持
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        # 从version_info模块获取版本信息
        try:
            from version_info import get_config_version
            config_version = get_config_version()
        except ImportError:
            # 如果version_info不可用，使用默认值
            config_version = "2.0"  # 更新版本号以标识配置结构变更
        
        return {
            "version": config_version,
            "basic": {
                "ui": {
                    "language": Language.ZH_CN.value,
                    "theme": ThemeType.LIGHT.value,
                    "window_width": 800,
                    "window_height": 600,
                },
                "encryption": {
                    "default_algorithm": AlgorithmType.OTP.value,
                    "default_key_type": KeyType.RANDOM.value,
                    "password_min_length": 8,
                    "require_strong_password": True,
                    "otp_key_format": "hex",  # hex 或 binary
                },
                "paths": {
                    "default_input_dir": "",
                    "default_output_dir": "",
                    "remember_last_folder": True,
                    "last_input_folder": "",
                    "last_output_folder": "",
                }
            },
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
                "buffer_size": 10,    # MB - 用于文件分块处理
            }
        }
    
    def _init_logging(self):
        """初始化日志系统"""
        log_level_str = self.get("advanced.log_level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        # 配置基础日志
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # 如果调试模式开启，增加详细日志
        if self.get("advanced.debug_mode", False):
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("调试模式已启用")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果配置文件不存在，创建默认配置
            if not self.config_file.exists():
                self._save_config(self.default_config)
                return self.default_config.copy()
            
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 检查版本，如果是旧版本配置，进行迁移
            if config.get("version", "1.0") == "1.0":
                config = self._migrate_v1_to_v2(config)
            
            # 合并默认配置，确保所有必要字段都存在
            merged_config = self._merge_configs(self.default_config, config)
            
            # 保存迁移后的配置
            self._save_config(merged_config)
            
            return merged_config
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件时出错: {e}，使用默认配置")
            return self.default_config.copy()
    
    def _migrate_v1_to_v2(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """将v1.0配置迁移到v2.0格式"""
        print("正在迁移配置文件从v1.0到v2.0格式...")
        
        # 创建新的v2.0配置结构
        new_config = self.default_config.copy()
        
        # 迁移基础配置
        if "ui" in old_config:
            new_config["basic"]["ui"] = old_config["ui"]
        
        # 迁移加密配置
        if "encryption" in old_config:
            encryption_config = old_config["encryption"]
            # 只迁移实际使用的配置
            for key in ["default_algorithm", "default_key_type", "password_min_length", "require_strong_password"]:
                if key in encryption_config:
                    new_config["basic"]["encryption"][key] = encryption_config[key]
            # OTP密钥格式需要特殊处理
            if "otp_key_format" in encryption_config:
                new_config["basic"]["encryption"]["otp_key_format"] = encryption_config["otp_key_format"]
        
        # 迁移路径配置
        if "paths" in old_config:
            new_config["basic"]["paths"] = old_config["paths"]
        
        # 迁移高级配置（只迁移实际实现的）
        if "advanced" in old_config:
            advanced_config = old_config["advanced"]
            if "debug_mode" in advanced_config:
                new_config["advanced"]["debug_mode"] = advanced_config["debug_mode"]
            if "log_level" in advanced_config:
                new_config["advanced"]["log_level"] = advanced_config["log_level"]
            if "buffer_size" in advanced_config:
                new_config["advanced"]["buffer_size"] = advanced_config["buffer_size"]
        
        return new_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置，确保所有字段都存在"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    # 对叶子节点进行验证和清理
                    config_key = self._find_full_config_key(key, result)
                    if config_key:
                        # 验证配置值
                        is_valid, error_msg = self.validation_manager.validate_key(config_key, value)
                        if not is_valid:
                            # 验证失败，使用默认值
                            default_value = self.validation_manager.get_default_value(config_key)
                            if default_value is not None:
                                result[key] = default_value
                            else:
                                # 没有默认值，保留原值（向后兼容）
                                result[key] = value
                        else:
                            result[key] = value
                    else:
                        result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _find_full_config_key(self, partial_key: str, config_dict: Dict[str, Any]) -> Optional[str]:
        """查找完整的配置键路径"""
        # 这是一个简化的实现，实际应该递归查找
        # 为了简化，我们假设partial_key是顶级键
        # 在完整的配置系统中，需要更复杂的查找逻辑
        return None
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件时出错: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔符（如 'basic.ui.language'）"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # 尝试旧版配置路径（向后兼容）
                if key.startswith("ui.") or key.startswith("encryption.") or key.startswith("paths."):
                    # 尝试在basic下查找
                    basic_key = f"basic.{key}"
                    basic_value = self.get(basic_key, None)
                    if basic_value is not None:
                        return basic_value
                return default
        
        return value
    
    def set(self, key: str, value: Any, skip_validation: bool = False) -> None:
        """设置配置值，支持点分隔符"""
        
        # 验证配置值（除非跳过验证）
        if not skip_validation:
            from config_validator import ValidationError
            is_valid, error_msg = self.validation_manager.validate_key(key, value)
            if not is_valid:
                raise ValidationError(key, value, error_msg)
        
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一个键的父字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 如果更改了日志相关配置，重新初始化日志
        if key in ["advanced.log_level", "advanced.debug_mode"]:
            self._init_logging()
        
        # 保存到文件
        self._save_config(self.config)
    
    def update(self, updates: Dict[str, Any], skip_validation: bool = False) -> None:
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value, skip_validation=skip_validation)
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self._save_config(self.config)
        self._init_logging()
    
    def get_config_status(self, key: str) -> ConfigStatus:
        """获取配置项状态"""
        return self.config_status.get(key, ConfigStatus.IMPLEMENTED)
    
    def get_implemented_keys(self) -> Set[str]:
        """获取所有已实现的配置键"""
        return {key for key, status in self.config_status.items() if status == ConfigStatus.IMPLEMENTED}
    
    def get_development_keys(self) -> Set[str]:
        """获取所有开发中的配置键"""
        return {key for key, status in self.config_status.items() if status == ConfigStatus.DEVELOPMENT}
    
    def get_deprecated_keys(self) -> Set[str]:
        """获取所有已弃用的配置键"""
        return {key for key, status in self.config_status.items() if status == ConfigStatus.DEPRECATED}
    
    # 便捷方法
    def get_language(self) -> str:
        """获取当前语言设置"""
        return self.get("basic.ui.language", Language.ZH_CN.value)
    
    def set_language(self, language: str) -> None:
        """设置语言"""
        # 验证语言是否有效
        if language in [lang.value for lang in Language]:
            self.set("basic.ui.language", language)
        else:
            raise ValueError(f"不支持的语言: {language}")
    
    def get_default_algorithm(self) -> str:
        """获取默认算法"""
        return self.get("basic.encryption.default_algorithm", AlgorithmType.OTP.value)
    
    def get_default_key_type(self) -> str:
        """获取默认密钥类型"""
        return self.get("basic.encryption.default_key_type", KeyType.RANDOM.value)
    
    def get_default_input_dir(self) -> str:
        """获取默认输入目录"""
        return self.get("basic.paths.default_input_dir", "")
    
    def get_default_output_dir(self) -> str:
        """获取默认输出目录"""
        return self.get("basic.paths.default_output_dir", "")
    
    def set_last_input_folder(self, path: str) -> None:
        """设置上次使用的输入文件夹"""
        self.set("basic.paths.last_input_folder", path)
    
    def set_last_output_folder(self, path: str) -> None:
        """设置上次使用的输出文件夹"""
        self.set("basic.paths.last_output_folder", path)
    
    def get_last_input_folder(self) -> str:
        """获取上次使用的输入文件夹"""
        return self.get("basic.paths.last_input_folder", "")
    
    def get_last_output_folder(self) -> str:
        """获取上次使用的输出文件夹"""
        return self.get("basic.paths.last_output_folder", "")
    
    def should_remember_last_folder(self) -> bool:
        """是否记住上次文件夹"""
        return self.get("basic.paths.remember_last_folder", True)
    
    def get_password_min_length(self) -> int:
        """获取密码最小长度"""
        return self.get("basic.encryption.password_min_length", 8)
    
    def requires_strong_password(self) -> bool:
        """是否要求强密码"""
        return self.get("basic.encryption.require_strong_password", True)
    
    def get_theme(self) -> str:
        """获取当前主题设置"""
        return self.get("basic.ui.theme", ThemeType.LIGHT.value)
    
    def set_theme(self, theme: str) -> None:
        """设置主题"""
        # 验证主题是否有效
        if theme in [theme.value for theme in ThemeType]:
            self.set("basic.ui.theme", theme)
        else:
            raise ValueError(f"不支持的主题: {theme}")
    
    def get_buffer_size(self) -> int:
        """获取缓冲区大小（MB）"""
        return self.get("advanced.buffer_size", 10)
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get("advanced.log_level", "INFO")
    
    def is_debug_mode(self) -> bool:
        """是否启用调试模式"""
        return self.get("advanced.debug_mode", False)
    
    def get_available_themes(self) -> Dict[str, str]:
        """获取可用主题列表"""
        return {
            ThemeType.LIGHT.value: "浅色主题",
            ThemeType.DARK.value: "深色主题",
        }


# 单例实例
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager() -> ConfigurationManager:
    """获取配置管理器单例实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


if __name__ == "__main__":
    # 测试配置管理器
    cm = get_config_manager()
    print(f"配置目录: {cm.config_dir}")
    print(f"配置文件: {cm.config_file}")
    print(f"当前语言: {cm.get_language()}")
    print(f"默认算法: {cm.get_default_algorithm()}")
    print(f"默认密钥类型: {cm.get_default_key_type()}")
    print(f"配置版本: {cm.get('version')}")
    print(f"已实现配置项: {len(cm.get_implemented_keys())}个")
    print(f"开发中配置项: {len(cm.get_development_keys())}个")
    print(f"已弃用配置项: {len(cm.get_deprecated_keys())}个")