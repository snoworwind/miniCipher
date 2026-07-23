#!/bin/bash

# Cipher tool launch script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "========================================"
echo "Cipher Encryption Tool Launch"
echo "========================================"
echo ""

if [ -f "$DIR/dist/Cipher" ]; then
    echo "Starting Cipher tool..."
    "$DIR/dist/Cipher"
    echo ""
    echo "Cipher tool has exited"
else
    echo "Error: Executable not found"
    echo ""
    echo "Please build first with:"
    echo "  python build.py --all"
    echo "or:"
    echo "  python build.py --install-deps --build"
    exit 1
fi
