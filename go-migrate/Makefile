.PHONY: build build-cli build-gui test clean run-cli run-test lint deps install build-all build-macos-app

# 共享 ldflags
GO_LDFLAGS := -s -w

# 默认目标
all: build

# 构建统一入口（根据当前 OS 自动选择）
build:
	cd cmd/minicipher && go build -trimpath -ldflags="$(GO_LDFLAGS)" -o ../../bin/minicipher .

# 构建 CLI（仅命令行，保留控制台）
build-cli:
	cd cmd/minicipher && go build -trimpath -ldflags="$(GO_LDFLAGS)" -o ../../bin/minicipher .

# 构建 GUI 模式（Windows: 隐藏控制台；其他平台: 正常构建）
# Windows 使用 -H windowsgui 编译为 GUI 子系统，双击启动时不弹控制台
build-gui:
	@case "$$(go env GOOS)" in \
		windows) cd cmd/minicipher && go build -trimpath -ldflags="$(GO_LDFLAGS) -H windowsgui" -o ../../bin/minicipher.exe . ;; \
		*)       cd cmd/minicipher && go build -trimpath -ldflags="$(GO_LDFLAGS)" -o ../../bin/minicipher . ;; \
	esac

# 构建 macOS .app 捆绑包（Finder 双击无终端）
build-macos-app: build
	mkdir -p bin/MiniCipher.app/Contents/MacOS
	mkdir -p bin/MiniCipher.app/Contents/Resources
	cp bin/minicipher bin/MiniCipher.app/Contents/MacOS/MiniCipher
	@echo '<?xml version="1.0" encoding="UTF-8"?>' > bin/MiniCipher.app/Contents/Info.plist
	@echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '<plist version="1.0">' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '<dict>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>CFBundleExecutable</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>MiniCipher</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>CFBundleIdentifier</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>com.snoworwind.minicipher</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>CFBundleName</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>miniCipher</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>CFBundleVersion</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>2.1.0</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>CFBundleShortVersionString</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>2.1.0</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>LSMinimumSystemVersion</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <string>10.14</string>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <key>NSHighResolutionCapable</key>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '    <true/>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '</dict>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo '</plist>' >> bin/MiniCipher.app/Contents/Info.plist
	@echo "✅ macOS .app bundle created at bin/MiniCipher.app"

# 运行 CLI 帮助
run-cli: build-cli
	./bin/minicipher help

# 运行 CLI 测试
run-test: build-cli
	./bin/minicipher test

# 运行单元测试
test:
	go test ./internal/... -v -count=1

# 运行测试并显示覆盖率
test-cover:
	go test ./internal/... -v -cover -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html

# 代码检查
lint:
	go vet ./...
	go fmt ./...

# 下载依赖
deps:
	go mod download
	go mod tidy

# 清理
clean:
	rm -rf bin/
	go clean -cache -testcache

# 安装到 GOPATH/bin
install: build-cli
	cp bin/minicipher $(shell go env GOPATH)/bin/minicipher

# 交叉编译（每步失败立即停止）
build-all:
	GOOS=darwin GOARCH=amd64 go build -trimpath -ldflags="$(GO_LDFLAGS)" -o bin/minicipher-darwin-amd64 ./cmd/minicipher/ && \
	GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags="$(GO_LDFLAGS)" -o bin/minicipher-darwin-arm64 ./cmd/minicipher/ && \
	GOOS=linux GOARCH=amd64 go build -trimpath -ldflags="$(GO_LDFLAGS)" -o bin/minicipher-linux-amd64 ./cmd/minicipher/ && \
	GOOS=windows GOARCH=amd64 go build -trimpath -ldflags="$(GO_LDFLAGS) -H windowsgui" -o bin/minicipher-windows-amd64.exe ./cmd/minicipher/
