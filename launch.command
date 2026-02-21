#!/bin/bash

# Cipher工具启动脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Cipher加密工具启动"
echo "========================================"
echo ""

if [ -f "$DIR/dist/Cipher" ]; then
    echo "正在启动Cipher工具..."
    "$DIR/dist/Cipher"
    echo ""
    echo "Cipher工具已退出"
else
    echo "错误: 未找到可执行文件"
    echo ""
    echo "请先运行以下命令构建:"
    echo "  python build.py --all"
    echo "或:"
    echo "  python build.py --install-deps --build"
    exit 1
fi
