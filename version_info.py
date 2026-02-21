#!/usr/bin/env python3
"""
版本信息模块 - 提供统一的版本信息访问接口
作为项目版本信息的单一事实来源
"""

import os
import sys
from pathlib import Path

# 尝试从version.py导入项目版本常量
try:
    from version import (
        PROJECT_VERSION_MAJOR,
        PROJECT_VERSION_MINOR,
        PROJECT_VERSION_PATCH,
        PROJECT_VERSION
    )
    VERSION_MAJOR = PROJECT_VERSION_MAJOR
    VERSION_MINOR = PROJECT_VERSION_MINOR
    VERSION_PATCH = PROJECT_VERSION_PATCH
    VERSION = PROJECT_VERSION
except ImportError:
    # 如果version.py不可用，使用硬编码的默认值
    # 这些值应与version.py中的常量保持一致
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0
    VERSION = f"v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

# 尝试从version.txt文件读取构建信息
def get_build_info():
    """
    读取version.txt文件获取构建信息
    返回包含版本信息的字典，如果文件不存在则返回None
    """
    version_file = Path(__file__).parent / "version.txt"
    if version_file.exists():
        try:
            build_info = {}
            with open(version_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            build_info[key.strip()] = value.strip()
            return build_info
        except Exception:
            pass
    return None

def get_version_info():
    """
    获取完整的版本信息
    返回包含项目版本和构建信息的字典
    """
    info = {
        "version": VERSION,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "version_string": VERSION
    }
    
    # 添加构建信息（如果可用）
    build_info = get_build_info()
    if build_info:
        info.update(build_info)
    
    return info

def get_version_string():
    """获取版本字符串（主要供显示使用）"""
    build_info = get_build_info()
    if build_info and 'version' in build_info:
        return build_info['version']
    return VERSION

def get_config_version():
    """
    获取配置版本字符串
    返回适合配置文件使用的版本字符串（无'v'前缀）
    """
    return f"{VERSION_MAJOR}.{VERSION_MINOR}"

if __name__ == "__main__":
    # 测试输出
    print("版本信息:")
    print(f"  项目版本: {VERSION}")
    print(f"  主版本: {VERSION_MAJOR}")
    print(f"  次版本: {VERSION_MINOR}")
    print(f"  修订号: {VERSION_PATCH}")
    print(f"  配置版本: {get_config_version()}")
    
    build_info = get_build_info()
    if build_info:
        print("\n构建信息:")
        for key, value in build_info.items():
            print(f"  {key}: {value}")
    else:
        print("\n未找到构建信息文件 (version.txt)")
    
    print(f"\n版本字符串 (供显示): {get_version_string()}")