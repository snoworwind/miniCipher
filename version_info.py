#!/usr/bin/env python3
"""
版本信息模块 - 提供统一的版本信息访问接口
作为项目版本信息的单一事实来源
动态版本系统：版本主要从git标签获取
"""

import os
import sys
from pathlib import Path

def _import_dynamic_version():
    """
    动态导入版本信息
    优先从version.py获取，失败时使用默认值
    """
    try:
        from version import (
            get_version_from_git,
            get_version_parts,
            DEFAULT_VERSION_MAJOR,
            DEFAULT_VERSION_MINOR,
            DEFAULT_VERSION_PATCH,
            DEFAULT_VERSION,
            get_git_info
        )
        
        # 获取动态版本
        version_str = get_version_from_git()
        major, minor, patch = get_version_parts()
        
        return {
            'VERSION': version_str,
            'MAJOR_VERSION': major,
            'MINOR_VERSION': minor,
            'PATCH_VERSION': patch,
            'DEFAULT_VERSION': DEFAULT_VERSION,
            'get_git_info': get_git_info
        }
    except ImportError as e:
        # 如果导入失败，使用硬编码的默认值
        print(f"Warning: Failed to import dynamic version functions: {e}")
        return {
            'VERSION': "v1.0.1",
            'MAJOR_VERSION': 1,
            'MINOR_VERSION': 0,
            'PATCH_VERSION': 1,
            'DEFAULT_VERSION': "v1.0.1",
            'get_git_info': None
        }

# 导入动态版本信息
_dynamic_version = _import_dynamic_version()

# 版本常量 - 从动态版本系统获取
VERSION = _dynamic_version['VERSION']
MAJOR_VERSION = _dynamic_version['MAJOR_VERSION']
MINOR_VERSION = _dynamic_version['MINOR_VERSION']
PATCH_VERSION = _dynamic_version['PATCH_VERSION']
DEFAULT_VERSION = _dynamic_version['DEFAULT_VERSION']

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
        except Exception as e:
            print(f"Warning: Failed to read build info: {e}")
            pass
    return None

def get_git_info():
    """
    获取git信息，如果动态版本系统不可用则返回默认值
    """
    if _dynamic_version['get_git_info']:
        try:
            return _dynamic_version['get_git_info']()
        except Exception as e:
            print(f"Warning: Failed to get git info: {e}")
    
    # 返回默认值
    return {
        'commit_hash': 'unknown',
        'commit_count': '0',
        'tag': None,
        'branch': 'unknown'
    }

def get_version_info():
    """
    获取完整的版本信息
    返回包含项目版本和构建信息的字典
    """
    info = {
        "version": VERSION,
        "major": MAJOR_VERSION,
        "minor": MINOR_VERSION,
        "patch": PATCH_VERSION,
        "version_string": VERSION
    }
    
    # 添加构建信息（如果可用）
    build_info = get_build_info()
    if build_info:
        info.update(build_info)
    
    # 添加git信息
    git_info = get_git_info()
    info.update(git_info)
    
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
    return f"{MAJOR_VERSION}.{MINOR_VERSION}"

def get_display_version():
    """
    获取显示版本字符串
    简洁版本：主版本.次版本.修订号
    """
    return f"{MAJOR_VERSION}.{MINOR_VERSION}.{PATCH_VERSION}"

if __name__ == "__main__":
    # 测试输出
    print("版本信息:")
    print(f"  项目版本: {VERSION}")
    print(f"  主版本: {MAJOR_VERSION}")
    print(f"  次版本: {MINOR_VERSION}")
    print(f"  修订号: {PATCH_VERSION}")
    print(f"  显示版本: {get_display_version()}")
    print(f"  配置版本: {get_config_version()}")
    
    build_info = get_build_info()
    if build_info:
        print("\n构建信息:")
        for key, value in build_info.items():
            if key not in ['version', 'major', 'minor', 'patch']:  # 避免重复
                print(f"  {key}: {value}")
    else:
        print("\n未找到构建信息文件 (version.txt)")
    
    git_info = get_git_info()
    print("\nGit信息:")
    print(f"  提交哈希: {git_info['commit_hash']}")
    print(f"  提交数量: {git_info['commit_count']}")
    print(f"  标签: {git_info['tag'] or '无'}")
    print(f"  分支: {git_info['branch']}")
    
    print(f"\n版本字符串 (供显示): {get_version_string()}")