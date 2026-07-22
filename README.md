# miniCipher - 文件加密/解密工具

# miniCipher - File Encryption/Decryption Tool

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Go-1.21%2B-00ADD8" alt="Go 1.21+">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green" alt="Cross-Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-2.0-orange" alt="Version 2.0">
</div>

## 📋 概述 / Overview

**miniCipher** 是一个简单易用的桌面文件加密/解密工具，提供图形界面，支持多种加密算法和密钥模式。专为需要保护文件隐私的用户设计，无需命令行知识即可使用。本工具大量使用AI编程，感受科技带来的便捷。

**miniCipher** is a user-friendly desktop file encryption/decryption tool with graphical interface, supporting multiple encryption algorithms and key modes. Designed for users who need to protect file privacy, no command-line knowledge required. This tool heavily uses AI programming to experience the convenience brought by technology.

## ✨ 核心特性 / Key Features

### 🔐 加密算法支持 / Encryption Algorithms

- **OTP (One-Time Pad)** - 一次性密码本，理论上不可破解的加密
- **AES256-GCM** - 高级加密标准，256位密钥，GCM认证模式

### 🔑 密钥模式 / Key Modes

- **随机密钥模式** - 生成随机密钥文件，需要妥善保管密钥
- **密码模式** - 使用用户密码，通过PBKDF2派生密钥，无需额外文件

### 🖥️ 用户界面 / User Interface

- 图形用户界面 (基于tkinter) / Graphical User Interface (based on tkinter)
- 中英文双语支持 / Chinese and English language support
- 配置文件管理 / Configuration file management

### ⚙️ 高级功能 / Advanced Features

- 跨平台配置文件系统 / Cross-platform configuration system
- 密码强度验证 / Password strength validation
- 记住上次使用的文件夹 / Remember last used folders
- 自定义加密设置 / Custom encryption settings

## 🚀 快速开始 / Quick Start

### 系统要求 / System Requirements

- **Python 3.7** 或更高版本 / or higher
- **tkinter** (通常Python自带) / (usually included with Python)
- **cryptography** 库 / library

### 安装与运行 / Installation & Running

#### 方法一：使用Python脚本运行 / Method 1: Run with Python Script

```bash
# 1. 克隆或下载项目 / Clone or download the project
git clone https://github.com/snoworwind/miniCipher.git
cd miniCipher

# 2. 安装依赖 / Install dependencies
pip install -r requirements.txt

# 3. 运行程序 / Run the program
python main.py
```

#### 方法二：使用预构建可执行文件 / Method 2: Use Pre-built Executable

从 [GitHub Releases](https://github.com/snoworwind/miniCipher/releases) 页面下载对应平台的可执行文件：

- **Windows**: `Cipher-windows-x64.exe`
- **macOS**: `Cipher-macos-arm64` (仅支持Arm64)
- **Linux**: `Cipher-linux-x64`

#### 方法三：本地构建 / Method 3: Local Build

```bash
# 完整构建流程（安装依赖、构建、测试）
python build.py --all

# 运行构建的可执行文件
# Windows: 双击 launch.bat 或 dist\Cipher.exe
# macOS/Linux: ./launch.command 或 ./dist/Cipher
```

## 📖 详细使用指南 / Detailed Usage Guide

### 1. 启动程序 / Starting the Program

启动后，您将看到主界面，包含以下部分：

- **算法设置** - 选择加密算法和密钥类型
- **加密区域** - 文件加密操作
- **解密区域** - 文件解密操作

### 2. 加密文件 / Encrypting Files

1. **选择算法**：OTP 或 AES256
2. **选择密钥类型**：随机密钥 或 密码
3. **选择输入文件**：点击"浏览"选择要加密的文件
4. **选择输出目录**：指定加密文件保存位置
5. **开始加密**：点击"开始加密"按钮

**注意**：

- OTP算法只支持随机密钥模式
- 密码模式需要设置至少8位密码（可配置）
- 随机密钥模式会生成密钥文件，请妥善保管

### 3. 解密文件 / Decrypting Files

1. **选择输入文件**：选择要解密的.enc文件
2. **提供密钥**：
   - 随机密钥模式：选择对应的密钥文件
   - 密码模式：输入加密时使用的密码
3. **选择输出目录**：指定解密文件保存位置
4. **开始解密**：点击"开始解密"按钮

### 4. 界面功能 / Interface Features

- **语言切换**：通过菜单栏的"语言"菜单切换中英文
- **设置管理**：通过"文件"→"设置"访问配置选项
- **关于信息**：查看版本信息和构建详情

## 🌐 多语言支持 / Multi-language Support

miniCipher支持以下语言：

- **简体中文 (zh_CN)** - 默认语言
- **English (en_US)**

**切换语言**：

1. 点击菜单栏的"语言" (Language)
2. 选择"简体中文"或"English"
3. 界面将立即切换，设置会自动保存

## 📁 文件格式说明 / File Format Specification

### 加密文件格式 / Encrypted File Formats

- **OTP加密文件**：`.enc`扩展名，纯密文数据
- **AES加密文件**：`.enc`扩展名，包含算法标识、IV和认证标签

### 密钥文件格式 / Key File Formats

- **OTP密钥**：`.txt`格式，十六进制字符串
- **AES随机密钥**：`.key`格式，二进制数据

### 密码模式 / Password Mode

盐值存储在加密文件中，只需记住密码即可解密。

## 🛠️ 构建与开发 / Building & Development

### 构建可执行文件 / Building Executable

使用PyInstaller打包为独立可执行文件：

```bash
# 完整构建流程
python build.py --all

# 或分步构建
python build.py --install-deps   # 安装依赖
python build.py --build          # 执行构建
python build.py --test           # 测试构建结果
```

### 项目结构 / Project Structure

```
miniCipher/
├── main.py                    # Python 主程序入口
├── cipher_gui.py              # Python GUI主界面（支持多语言）
├── cipher_algorithms.py       # 加密算法实现
├── config_manager.py          # 配置文件管理系统
├── translations.py            # 多语言翻译模块
├── requirements.txt           # Python依赖
├── build.py                   # 构建脚本
├── test_cipher.py             # 核心加密测试
├── launch.bat                 # Windows启动脚本
├── launch.command             # macOS/Linux启动脚本
├── go-migrate/                # Go v2.0 版本
│   ├── cmd/gui/               # GUI 程序入口
│   ├── cmd/minicipher/        # 命令行程序入口
│   ├── internal/
│   │   ├── batch/             # 批量处理模块
│   │   ├── config/            # 配置管理 + 验证器
│   │   ├── crypto/            # 加密算法 (OTP/AES256/FileCipher)
│   │   ├── lang/              # 多语言翻译 (中/英)
│   │   ├── theme/             # 主题管理 (浅色/深色)
│   │   └── ui/                # GUI 界面 (设置/加密/解密/批量)
│   ├── go.mod / go.sum        # Go 依赖管理
│   └── Makefile               # 构建脚本
├── README.md                  # 说明文档
└── LICENSE                    # 许可证文件
```

### 测试 / Testing

```bash
# 运行核心加密测试
python test_cipher.py
```

## 🔄 持续集成 / Continuous Integration

项目使用GitHub Actions实现自动化构建和发布：

### 自动构建工作流 / Automated Build Workflow

- **CI构建**：每次推送到main分支或创建pull request时自动运行
- **多平台构建**：在Windows、macOS和Linux上构建可执行文件
- **自动测试**：运行单元测试确保功能正确性

### 发布工作流 / Release Workflow

- **自动发布**：创建git tag时自动发布新版本
- **预构建文件**：可从GitHub Releases页面下载

## 🐹 Go 版本 (v2.0) / Go Version (v2.0)

项目已从 Python/tkinter 迁移至 Go/Fyne，全新 v2.0 版本提供现代化的用户界面和更好的跨平台体验。

The project has been migrated from Python/tkinter to Go/Fyne, the new v2.0 version provides a modern user interface and better cross-platform experience.

### 系统要求 / System Requirements

- **Go 1.21** 或更高版本 / or higher
- **Fyne** GUI 框架 (自动安装依赖)
- 操作系统：Windows / macOS / Linux

### 安装与运行 / Installation & Running

```bash
# 1. 进入 Go 项目目录
cd go-migrate

# 2. 安装依赖
go mod tidy

# 3. 编译并运行 GUI 版本
go run ./cmd/gui

# 4. 或编译为可执行文件
go build -o minicipher ./cmd/gui
./minicipher
```

### 命令行版本 / CLI Version

```bash
# 编译命令行工具
go build -o minicipher-cli ./cmd/minicipher

# 加密文件
./minicipher-cli encrypt -i input.txt -o output.enc -a AES256 -k password -p "mypassword"

# 解密文件
./minicipher-cli decrypt -i output.enc -o decrypted.txt -p "mypassword"
```

### Python vs Go 版本对比 / Comparison

| 特性 | Python (v1.0) | Go (v2.0) |
|------|--------------|-----------|
| GUI 框架 | tkinter | Fyne |
| 启动速度 | 较慢 | 快速 |
| 内存占用 | 较高 | 较低 |
| 单文件分发 | 需 PyInstaller | 原生静态编译 |
| 主题支持 | 手动实现 (深/浅) | Fyne 内置 |
| 加密算法 | OTP / AES256-GCM | OTP / AES256-GCM |
| 批量处理 | 支持 | 支持 |
| 配置文件 | JSON | JSON (兼容) |
| 加密文件格式 | 二进制兼容 | 二进制兼容 |
| 密钥文件格式 | hex/binary 可选 | hex/binary 可选 |

### Go 项目结构 / Go Project Structure

```
go-migrate/
├── cmd/
│   ├── gui/main.go            # GUI 应用程序入口
│   └── minicipher/main.go     # 命令行工具入口
├── internal/
│   ├── batch/batch.go         # 批量加密/解密处理
│   ├── config/config.go       # 配置管理器
│   ├── config/validator.go    # 配置验证器
│   ├── crypto/aes.go          # AES256-GCM 算法实现
│   ├── crypto/otp.go          # OTP 一次性密码本实现
│   ├── crypto/filecipher.go   # 文件加解密高级API
│   ├── crypto/types.go        # 类型定义
│   ├── lang/i18n.go           # 多语言翻译
│   ├── theme/theme.go         # 主题管理
│   ├── ui/app.go              # 主界面 (加密/解密/批量)
│   └── ui/settings.go         # 设置对话框
├── go.mod / go.sum            # Go 模块定义
└── Makefile                   # 构建脚本
```

## ❓ 常见问题 / FAQ

### Q: OTP和AES256哪个更安全？

**A**: OTP在理论上不可破解，但要求密钥长度等于文件长度。AES256是行业标准，性能更好，适用于各种文件大小。

### Q: 忘记密码或丢失密钥文件怎么办？

**A**: 如果使用密码模式忘记密码，或使用随机密钥模式丢失密钥文件，**无法恢复**加密文件。请务必妥善保管密码或密钥文件。

### Q: 支持哪些文件类型？

**A**: 支持所有文件类型，包括文档、图片、视频等。miniCipher将文件视为二进制数据处理。

### Q: 加密大文件时需要注意什么？

**A**: OTP算法对大文件可能较慢（密钥长度等于文件长度）。对于大文件，建议使用AES256算法。

### Q: 如何验证加密是否正确？

**A**: 使用测试文件进行加密，然后立即解密验证原始文件是否能够完全恢复。

### Q: 为什么macOS版无法启动？

**A**: 可能是苹果的签名安全机制阻止了程序运行。

## 📄 许可证 / License

本项目采用 **MIT许可证**。详见 [LICENSE](LICENSE) 文件。

## 📞 支持与联系 / Support & Contact

- **项目主页**: [https://github.com/snoworwind/miniCipher](https://github.com/snoworwind/miniCipher)
- **问题反馈**: 通过GitHub Issues报告问题
- **作者**: snoworwind

## 📋 版本历史 / Version History

- **v2.0** (2026-07) - Go/Fyne 重写版本，现代化 UI，静态编译，性能提升
  - Go 1.21+ / Fyne GUI 框架
  - 支持批量处理模式选择（文件/文件夹/递归）
  - 并行处理 + 最大线程数配置
  - OTP 密钥格式可选 (hex/binary)
  - 主题深色/浅色切换
  - 命令行版支持 (cmd/minicipher)
- **v1.0** (2026-02) - 初始稳定版本，支持配置系统和多语言
  - 主要功能：配置文件管理、中英文界面、增强错误处理

---

<div align="center">
  <sub>使用 ❤️ 构建 | Built with ❤️</sub><br>
  <sub>© 2026 miniCipher项目 | © 2026 miniCipher Project</sub>
</div>
