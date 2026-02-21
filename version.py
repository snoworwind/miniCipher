#!/usr/bin/env python3
"""
版本管理脚本 - 用于GitHub Actions自动构建
自动生成版本号，支持递增版本管理
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def get_git_info():
    """获取git仓库信息"""
    try:
        # 获取当前commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            text=True
        ).strip()
        
        # 获取commit总数（用于版本递增）
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            text=True
        ).strip()
        
        # 获取当前tag（如果有）
        try:
            tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0'],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            tag = None
        
        # 获取当前分支
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            text=True
        ).strip()
        
        return {
            'commit_hash': commit_hash,
            'commit_count': commit_count,
            'tag': tag,
            'branch': branch
        }
    except Exception as e:
        print(f"获取git信息失败: {e}")
        return {
            'commit_hash': 'unknown',
            'commit_count': '0',
            'tag': None,
            'branch': 'unknown'
        }

def generate_version_number(git_info, build_type='dev'):
    """
    生成版本号
    
    格式: v{主版本}.{次版本}.{补丁版本}+{构建类型}.{构建日期}.{提交次数}.{提交哈希}
    示例: v1.0.0+dev.2026-02-21.123.abc123
    
    构建类型:
    - dev: 开发版本（CI构建）
    - release: 发布版本（tag构建）
    """
    # 基础版本（可以从文件中读取，这里使用固定值）
    major = 1
    minor = 0
    patch = 0
    
    # 如果存在tag，使用tag作为版本基础
    if git_info['tag'] and git_info['tag'].startswith('v'):
        # 解析tag版本
        tag_version = git_info['tag'][1:]  # 移除'v'前缀
        version_parts = tag_version.split('.')
        if len(version_parts) >= 3:
            try:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                patch = int(version_parts[2])
            except ValueError:
                pass
    
    # 构建元数据部分
    build_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    commit_count = git_info['commit_count']
    commit_hash = git_info['commit_hash'][:8]  # 取前8位
    
    # 确定构建类型
    if build_type == 'release':
        # 发布版本
        version = f"v{major}.{minor}.{patch}"
    else:
        # 开发版本 - 递增版本号
        if build_type == 'dev':
            # 开发版本递增补丁版本
            patch = int(commit_count)
            version = f"v{major}.{minor}.{patch}+{build_type}.{build_date}.{commit_hash}"
        else:
            version = f"v{major}.{minor}.{patch}+{build_type}.{build_date}.{commit_hash}"
    
    return version

def write_version_file(version, platform_info=None):
    """写入版本信息文件"""
    version_info = {
        'version': version,
        'build_date': datetime.datetime.utcnow().isoformat() + 'Z',
        'build_type': 'release' if '+release' in version else 'dev'
    }
    
    # 添加git信息
    git_info = get_git_info()
    version_info.update(git_info)
    
    # 添加平台信息
    if platform_info:
        version_info['platform'] = platform_info.get('platform', 'unknown')
        version_info['architecture'] = platform_info.get('architecture', 'unknown')
    
    # 写入文件
    output_file = Path(__file__).parent / 'version.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# MiniCipher 版本信息\n")
        f.write("# ====================\n\n")
        
        for key, value in version_info.items():
            if value is not None:
                f.write(f"{key}: {value}\n")
    
    print(f"版本文件已生成: {output_file}")
    print(f"版本号: {version}")
    
    return version

def inject_version_into_executable():
    """
    尝试将版本信息注入到构建的可执行文件中
    这需要在构建过程中调用
    """
    try:
        # 创建版本信息文件，供构建脚本使用
        version_file = Path(__file__).parent / 'version_info.py'
        
        git_info = get_git_info()
        version = generate_version_number(git_info)
        
        content = f'''"""
自动生成的版本信息 - 用于注入到可执行文件中
"""

VERSION = "{version}"
BUILD_DATE = "{datetime.datetime.utcnow().isoformat()}Z"
COMMIT_HASH = "{git_info['commit_hash']}"
COMMIT_COUNT = "{git_info['commit_count']}"
BRANCH = "{git_info['branch']}"

def get_version():
    """获取版本信息"""
    return {{
        "version": VERSION,
        "build_date": BUILD_DATE,
        "commit_hash": COMMIT_HASH,
        "commit_count": COMMIT_COUNT,
        "branch": BRANCH
    }}

if __name__ == "__main__":
    print(VERSION)
'''
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"版本信息文件已生成: {version_file}")
        return version_file
        
    except Exception as e:
        print(f"生成版本信息文件失败: {e}")
        return None

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生成版本信息')
    parser.add_argument('--type', choices=['dev', 'release'], default='dev',
                       help='构建类型: dev(开发版本) 或 release(发布版本)')
    parser.add_argument('--platform', default=None,
                       help='目标平台: windows, macos, linux')
    parser.add_argument('--architecture', default='x64',
                       help='目标架构: x64, universal, arm64等')
    parser.add_argument('--inject', action='store_true',
                       help='生成版本信息文件供构建脚本使用')
    
    args = parser.parse_args()
    
    # 获取git信息
    git_info = get_git_info()
    
    # 生成版本号
    version = generate_version_number(git_info, args.type)
    
    # 平台信息
    platform_info = None
    if args.platform:
        platform_info = {
            'platform': args.platform,
            'architecture': args.architecture
        }
    
    # 写入版本文件
    write_version_file(version, platform_info)
    
    # 如果需要，生成注入文件
    if args.inject:
        inject_version_into_executable()
    
    # 输出版本号（供脚本使用）
    print(f"::set-output name=version::{version}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())