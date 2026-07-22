.PHONY: build test clean build-all build-macos build-windows build-linux install-deps-linux

APP_NAME=minicipher
BUILD_DIR=dist
LDFLAGS=-s -w

build:
	go build -o $(APP_NAME) -ldflags "$(LDFLAGS)" ./cmd/minicipher/

test:
	go run ./cmd/minicipher/ test

clean:
	rm -f $(APP_NAME)
	rm -rf $(BUILD_DIR)

# 跨平台构建
build-macos-arm64:
	GOOS=darwin GOARCH=arm64 go build -o $(BUILD_DIR)/$(APP_NAME)-macos-arm64 -ldflags "$(LDFLAGS)" ./cmd/minicipher/

build-macos-amd64:
	GOOS=darwin GOARCH=amd64 go build -o $(BUILD_DIR)/$(APP_NAME)-macos-amd64 -ldflags "$(LDFLAGS)" ./cmd/minicipher/

build-windows:
	GOOS=windows GOARCH=amd64 go build -o $(BUILD_DIR)/$(APP_NAME)-windows-amd64.exe -ldflags "$(LDFLAGS)" ./cmd/minicipher/

build-linux:
	GOOS=linux GOARCH=amd64 go build -o $(BUILD_DIR)/$(APP_NAME)-linux-amd64 -ldflags "$(LDFLAGS)" ./cmd/minicipher/

# 构建所有平台
build-all: clean
	mkdir -p $(BUILD_DIR)
	$(MAKE) build-macos-arm64
	$(MAKE) build-macos-amd64
	$(MAKE) build-windows
	$(MAKE) build-linux
	@echo ""
	@echo "构建完成! 产物在 $(BUILD_DIR)/ 目录:"
	@ls -lh $(BUILD_DIR)/

# 本地运行
run:
	go run ./cmd/minicipher/

# 格式化代码
fmt:
	go fmt ./...

# 代码检查
vet:
	go vet ./...

# 安装 Linux 系统依赖 (Fyne GUI 构建需要)
install-deps-linux:
	sudo apt-get update
	sudo apt-get install -y libgl1-mesa-dev xorg-dev libwayland-dev libxkbcommon-dev
