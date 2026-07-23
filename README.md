# miniCipher

<div align="center">
  <img src="https://img.shields.io/badge/Go-1.23%2B-00ADD8" alt="Go 1.23+">
  <img src="https://img.shields.io/badge/Fyne-v2.8-blue" alt="Fyne v2.8">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green" alt="Cross-Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
  <img src="https://img.shields.io/badge/Version-2.1.0-orange" alt="Version 2.1.0">
</div>

## 概述

**miniCipher** 是一个简单易用的桌面文件加密工具，基于 Go + Fyne 构建。

双击即可启动图形界面，也支持命令行模式。无需联网，不收集任何数据。

> v2.1 将 CLI 和 GUI 合并为统一入口，Windows 双击无控制台弹出，在设置中可开启调试模式查看日志。

> 🤖 本项目完全由 AI 开发。

## 核心特性

| 功能 | 说明 |
|---|---|
| OTP 一次性密码本 | 理论上不可破解，密钥长度等于文件长度 |
| AES256-GCM | 行业标准加密，支持随机密钥和密码两种模式 |
| 批量处理 | 文件夹递归加密/解密，支持多线程并行 |
| 统一入口 | 一个二进制同时包含 GUI 和 CLI |
| Windows 无控制台 | `-H windowsgui` 编译，双击只显示 GUI |
| 调试模式 | 设置中开启后弹出控制台窗口查看日志 |
| 多语言 | 简体中文 / English |
| 主题 | 浅色 / 深色 |

## 快速开始

### 下载预构建版本

从 [Releases](https://github.com/snoworwind/miniCipher/releases) 下载对应平台的可执行文件：

| 平台 | 文件 |
|---|---|
| Windows (x64) | `minicipher-windows-amd64.exe` |
| macOS (Apple Silicon) | `minicipher-macos-arm64` |
| Linux (x64) | `minicipher-linux-amd64` |

**Windows**：双击 `.exe` 启动 GUI（无控制台）。在终端带参数运行则进入 CLI 模式。

**macOS**：首次运行可能需要右键 → "打开"。从终端运行可直接使用 CLI。

**Linux**：`chmod +x minicipher-linux-amd64 && ./minicipher-linux-amd64`

### 从源码构建

```bash
# 要求: Go 1.23+, GCC (Windows 需 MSYS2/MinGW-w64)

cd go-migrate

# Windows
build.bat gui      # GUI 子系统（双击无控制台）
build.bat          # 控制台子系统

# macOS / Linux
make build         # 默认构建
make build-macos-app  # macOS .app 捆绑包

# 交叉编译所有平台
build.bat all      # Windows
make build-all     # macOS / Linux
```

## 使用指南

### GUI 模式（双击启动）

- **加密**：选择文件 → 选择算法（OTP / AES256）→ 选择密钥类型 → 开始加密
- **解密**：选择 `.enc` 文件 → 提供密钥文件或密码 → 开始解密
- **批量处理**：选择目录 → 选择模式（文件/文件夹/递归） → 批量加密/解密
- **设置**：菜单栏 → 文件 → 设置（语言、主题、算法默认值、缓冲区大小等）

### CLI 模式（终端带参数）

```bash
# 加密
minicipher encrypt input.txt output.enc --algo AES256 --key-type password --password-stdin

# 解密
minicipher decrypt output.enc decrypted.txt --key-file my.key

# 批量加密
minicipher batch encrypt ./docs ./encrypted --mode recursive --parallel --max-threads 4

# 帮助
minicipher help
```

### 密码输入方式（按优先级）

1. `--password-stdin` — 通过管道传入（最安全）
2. `MINICIPHER_PASSWORD` — 环境变量
3. `--password=` — 命令行参数（不推荐，会记录在 shell 历史中）

## 项目结构

```
miniCipher/
├── go-migrate/                  # Go v2 实现（主力）
│   ├── cmd/
│   │   └── minicipher/main.go   # 统一入口（GUI + CLI）
│   ├── internal/
│   │   ├── batch/               # 批量处理
│   │   ├── config/              # 配置管理 + 验证
│   │   ├── crypto/              # AES256 / OTP / FileCipher
│   │   ├── lang/                # 多语言翻译
│   │   ├── log/                 # 日志模块
│   │   ├── platform/            # 平台相关（控制台附加）
│   │   ├── theme/               # 主题管理
│   │   └── ui/                  # GUI 界面
│   ├── build.bat                # Windows 构建脚本
│   ├── Makefile                 # macOS / Linux 构建脚本
│   └── go.mod / go.sum
├── python-legacy/               # Python v1 实现（已归档）
├── .github/workflows/          # CI/CD
│   ├── build-go.yml            # Go CI 构建
│   └── release-go.yml          # Go 自动发布
└── README.md
```

## CI / CD

| Workflow | 触发条件 |
|---|---|
| `build-go.yml` | push / PR 到 main 分支 |
| `release-go.yml` | 推送 `v*` tag（如 `v2.1.0`） |

CI 交叉编译 Windows/macOS/Linux，UPX 压缩后上传为 Release 资产。

## 常见问题

**Q: OTP 和 AES256 哪个更好？**

OTP 理论上不可破解但密钥等于文件长度，大文件较慢。AES256 是行业标准，对所有文件大小均适用。

**Q: 忘记密码或丢失密钥文件？**

无法恢复。请务必妥善保管。

**Q: 如何开启控制台查看日志？**

设置 → 高级 → 勾选"调试模式"，重启程序后控制台窗口会自动弹出（仅 Windows）。

**Q: 为什么 macOS 版本可能无法启动？**

macOS Gatekeeper 可能阻止未签名应用。右键点击 → "打开" 即可绕过，或将 `.app` 拖入"应用程序"文件夹。

## 版本历史

- **v2.1.0** — 统一 CLI/GUI 入口、Windows `-H windowsgui`、调试模式控制台、UPX 压缩、CI 完善
- **v2.0.0** — Go/Fyne 重写，现代化 UI，原生静态编译
- **v1.0** — Python/tkinter 初始版本

## 🤖 AI 开发声明

本项目所有代码完全由 AI 生成，包括设计、实现、测试、文档和 CI/CD 配置。

## 许可证

[MIT License](LICENSE) © 2026 miniCipher Project
