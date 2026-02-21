#!/usr/bin/env python3
"""
Version management script - for GitHub Actions automated builds
Auto-generates version numbers with incremental version management
Dynamic version system: Version is primarily derived from git tags
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

# For datetime.utcnow() deprecation - use timezone-aware UTC
try:
    # Python 3.11+ has datetime.UTC alias
    from datetime import UTC
except ImportError:
    # Python 3.9-3.10 use timezone.utc
    from datetime import timezone
    UTC = timezone.utc

# Default fallback version constants - used only when git is not available
# These should match the latest release tag to ensure consistency
DEFAULT_VERSION_MAJOR = 1
DEFAULT_VERSION_MINOR = 0
DEFAULT_VERSION_PATCH = 1  # Updated to match current tag v1.0.1
DEFAULT_VERSION = f"v{DEFAULT_VERSION_MAJOR}.{DEFAULT_VERSION_MINOR}.{DEFAULT_VERSION_PATCH}"

def get_git_info():
    """Get git repository information with improved error handling"""
    try:
        # Get current commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            text=True
        ).strip()
        
        # Get total commit count (for version increment)
        commit_count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            text=True
        ).strip()
        
        # Get current tag (if any)
        try:
            tag = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=0'],
                text=True
            ).strip()
        except subprocess.CalledProcessError:
            tag = None
        
        # Get current branch
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
        print(f"Warning: Failed to get git info: {e}")
        # Return sensible defaults instead of "unknown"
        return {
            'commit_hash': 'nogit',
            'commit_count': '0',
            'tag': None,
            'branch': 'nogit'
        }

def parse_version_from_tag(tag):
    """
    Parse version from git tag string
    Example: 'v1.0.1' -> (1, 0, 1)
    """
    if tag and tag.startswith('v'):
        tag_version = tag[1:]  # Remove 'v' prefix
        version_parts = tag_version.split('.')
        if len(version_parts) >= 3:
            try:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                patch = int(version_parts[2])
                return major, minor, patch
            except ValueError:
                pass
    return None

def get_version_from_git():
    """
    Get version from git tag, fallback to default if not available
    Returns version string like 'v1.0.1'
    """
    git_info = get_git_info()
    tag = git_info['tag']
    
    if tag:
        version_parts = parse_version_from_tag(tag)
        if version_parts:
            major, minor, patch = version_parts
            return f"v{major}.{minor}.{patch}"
    
    # Fallback to default version
    return DEFAULT_VERSION

def get_version_parts():
    """
    Get version parts (major, minor, patch) from git tag
    Returns tuple (major, minor, patch)
    """
    version_str = get_version_from_git()
    # Remove 'v' prefix if present
    if version_str.startswith('v'):
        version_str = version_str[1:]
    
    parts = version_str.split('.')
    if len(parts) >= 3:
        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            pass
    
    # Fallback to default parts
    return DEFAULT_VERSION_MAJOR, DEFAULT_VERSION_MINOR, DEFAULT_VERSION_PATCH

def generate_version_number(git_info, build_type='dev'):
    """
    Generate version number
    
    Format: v{major}.{minor}.{patch}+{build_type}.{build_date}.{commit_count}.{commit_hash}
    Example: v1.0.0+dev.2026-02-21.123.abc123
    
    Build types:
    - dev: Development version (CI build)
    - release: Release version (tag build)
    """
    # Get version from git tag first, fallback to defaults
    version_parts = parse_version_from_tag(git_info['tag'])
    if version_parts:
        major, minor, patch = version_parts
    else:
        major = DEFAULT_VERSION_MAJOR
        minor = DEFAULT_VERSION_MINOR
        patch = DEFAULT_VERSION_PATCH
    
    # Build metadata part
    build_date = datetime.datetime.now(UTC).strftime('%Y-%m-%d')
    commit_count = git_info['commit_count']
    commit_hash = git_info['commit_hash'][:8] if git_info['commit_hash'] != 'nogit' else 'nogit'
    
    # Determine build type
    if build_type == 'release':
        # Release version - use tag version without metadata
        version = f"v{major}.{minor}.{patch}"
    else:
        # Development version - incremental version number
        if build_type == 'dev':
            # Development version increments patch version based on commit count
            try:
                patch = int(commit_count) if commit_count.isdigit() else DEFAULT_VERSION_PATCH
            except ValueError:
                patch = DEFAULT_VERSION_PATCH
            version = f"v{major}.{minor}.{patch}+{build_type}.{build_date}.{commit_hash}"
        else:
            version = f"v{major}.{minor}.{patch}+{build_type}.{build_date}.{commit_hash}"
    
    return version

def write_version_file(version, platform_info=None):
    """Write version information file"""
    version_info = {
        'version': version,
        'build_date': datetime.datetime.now(UTC).isoformat() + 'Z',
        'build_type': 'release' if '+release' in version else 'dev'
    }
    
    # Add git information
    git_info = get_git_info()
    version_info.update(git_info)
    
    # Add platform information
    if platform_info:
        version_info['platform'] = platform_info.get('platform', 'unknown')
        version_info['architecture'] = platform_info.get('architecture', 'unknown')
    
    # Write to file
    output_file = Path(__file__).parent / 'version.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# MiniCipher Version Information\n")
        f.write("# ==============================\n\n")
        
        for key, value in version_info.items():
            if value is not None:
                f.write(f"{key}: {value}\n")
    
    print(f"Version file generated: {output_file}")
    print(f"Version: {version}")
    
    return version

def inject_version_into_executable():
    """
    Attempt to inject version information into the built executable
    This needs to be called during the build process
    """
    try:
        # Create version information file for build script use
        version_file = Path(__file__).parent / 'version_info.py'
        
        git_info = get_git_info()
        version = generate_version_number(git_info)
        
        # Get version parts for the injection
        major, minor, patch = get_version_parts()
        
        content = f'''"""
Auto-generated version information - for injection into executable
Dynamic version system: Version derived from git tags or defaults
"""

# Core version information - dynamically determined
VERSION = "{version}"
MAJOR_VERSION = {major}
MINOR_VERSION = {minor}
PATCH_VERSION = {patch}
BUILD_DATE = "{datetime.datetime.now(UTC).isoformat()}Z"
COMMIT_HASH = "{git_info['commit_hash']}"
COMMIT_COUNT = "{git_info['commit_count']}"
BRANCH = "{git_info['branch']}"

def get_version():
    """Get version information"""
    return {{
        "version": VERSION,
        "major": MAJOR_VERSION,
        "minor": MINOR_VERSION,
        "patch": PATCH_VERSION,
        "build_date": BUILD_DATE,
        "commit_hash": COMMIT_HASH,
        "commit_count": COMMIT_COUNT,
        "branch": BRANCH
    }}

def get_version_string():
    """Get version string for display"""
    return VERSION

def get_version_info():
    """Get complete version info for UI display"""
    return get_version()

if __name__ == "__main__":
    print(VERSION)
'''
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Version information file generated: {version_file}")
        return version_file
        
    except Exception as e:
        print(f"Failed to generate version information file: {e}")
        return None

def main():
    """Command line entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate version information')
    parser.add_argument('--type', choices=['dev', 'release'], default='dev',
                       help='Build type: dev (development version) or release (release version)')
    parser.add_argument('--platform', default=None,
                       help='Target platform: windows, macos, linux')
    parser.add_argument('--architecture', default='x64',
                       help='Target architecture: x64, universal, arm64, etc.')
    parser.add_argument('--inject', action='store_true',
                       help='Generate version information file for build script use')
    
    args = parser.parse_args()
    
    # Get git information
    git_info = get_git_info()
    
    # Generate version number
    version = generate_version_number(git_info, args.type)
    
    # Platform information
    platform_info = None
    if args.platform:
        platform_info = {
            'platform': args.platform,
            'architecture': args.architecture
        }
    
    # Write version file
    write_version_file(version, platform_info)
    
    # If needed, generate injection file
    if args.inject:
        inject_version_into_executable()
    
    # Output version number (for script use)
    # GitHub Actions deprecated ::set-output in October 2022
    # Use environment file method if GITHUB_OUTPUT is available
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f'version={version}\n')
    else:
        # Keep backward compatibility for local testing
        print(f"::set-output name=version::{version}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())