#!/usr/bin/env python3
"""
配置文件管理器模块
支持跨平台配置文件管理，用于miniCipher工具
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

class AlgorithmType(str, Enum):
    """加密算法类型枚举"""
    OTP = "OTP"
    AES256 = "AES256"

class KeyType(str, Enum):
    """密钥类型枚举"""
    RANDOM = "random"
    PASSWORD = "password"

class Language(str, Enum):
    """支持的语言枚举"""
    ZH_CN = "zh_CN"  # 简体中文
    EN_US = "en_US"  # 英文

class ConfigurationManager:
    """配置管理器类"""
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_config = self._get_default_config()
        self.config = self._load_config()
    
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
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        # 从version_info模块获取版本信息
        try:
            from version_info import get_config_version
            config_version = get_config_version()
        except ImportError:
            # 如果version_info不可用，使用默认值
            config_version = "1.0"
        
        return {
            "version": config_version,
            "ui": {
                "language": Language.ZH_CN.value,
                "theme": "default",
                "window_width": 800,
                "window_height": 600,
            },
            "encryption": {
                "default_algorithm": AlgorithmType.OTP.value,
                "default_key_type": KeyType.RANDOM.value,
                "password_min_length": 8,
                "require_strong_password": True,
            },
            "paths": {
                "default_input_dir": "",
                "default_output_dir": "",
                "remember_last_folder": True,
                "last_input_folder": "",
                "last_output_folder": "",
            },
            "advanced": {
                "auto_update_check": True,
                "debug_mode": False,
                "log_level": "INFO",
            }
        }
    
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
            
            # 合并默认配置，确保所有必要字段都存在
            merged_config = self._merge_configs(self.default_config, config)
            
            # 如果版本不一致，可能需要迁移配置
            if config.get("version") != self.default_config.get("version"):
                merged_config["version"] = self.default_config.get("version")
                self._save_config(merged_config)
            
            return merged_config
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件时出错: {e}，使用默认配置")
            return self.default_config.copy()
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置，确保所有字段都存在"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件时出错: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点分隔符（如 'ui.language'）"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点分隔符"""
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一个键的父字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存到文件
        self._save_config(self.config)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """批量更新配置"""
        for key, value in updates.items():
            self.set(key, value)
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self._save_config(self.config)
    
    def get_language(self) -> str:
        """获取当前语言设置"""
        return self.get("ui.language", Language.ZH_CN.value)
    
    def set_language(self, language: str) -> None:
        """设置语言"""
        # 验证语言是否有效
        if language in [lang.value for lang in Language]:
            self.set("ui.language", language)
        else:
            raise ValueError(f"不支持的语言: {language}")
    
    def get_default_algorithm(self) -> str:
        """获取默认算法"""
        return self.get("encryption.default_algorithm", AlgorithmType.OTP.value)
    
    def get_default_key_type(self) -> str:
        """获取默认密钥类型"""
        return self.get("encryption.default_key_type", KeyType.RANDOM.value)
    
    def get_default_input_dir(self) -> str:
        """获取默认输入目录"""
        return self.get("paths.default_input_dir", "")
    
    def get_default_output_dir(self) -> str:
        """获取默认输出目录"""
        return self.get("paths.default_output_dir", "")
    
    def set_last_input_folder(self, path: str) -> None:
        """设置上次使用的输入文件夹"""
        self.set("paths.last_input_folder", path)
    
    def set_last_output_folder(self, path: str) -> None:
        """设置上次使用的输出文件夹"""
        self.set("paths.last_output_folder", path)
    
    def get_last_input_folder(self) -> str:
        """获取上次使用的输入文件夹"""
        return self.get("paths.last_input_folder", "")
    
    def get_last_output_folder(self) -> str:
        """获取上次使用的输出文件夹"""
        return self.get("paths.last_output_folder", "")
    
    def should_remember_last_folder(self) -> bool:
        """是否记住上次文件夹"""
        return self.get("paths.remember_last_folder", True)
    
    def get_password_min_length(self) -> int:
        """获取密码最小长度"""
        return self.get("encryption.password_min_length", 8)
    
    def requires_strong_password(self) -> bool:
        """是否要求强密码"""
        return self.get("encryption.require_strong_password", True)


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