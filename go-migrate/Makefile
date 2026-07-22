.PHONY: build build-cli build-gui test clean run-cli run-gui lint

# 默认目标
all: build

# 构建所有
build: build-cli

# 构建 CLI
build-cli:
	cd cmd/minicipher && go build -o ../../bin/minicipher .

# 构建 GUI
build-gui:
	cd cmd/gui && go build -o ../../bin/minicipher-gui .

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

# 交叉编译
build-all:
	GOOS=darwin GOARCH=amd64 go build -o bin/minicipher-darwin-amd64 ./cmd/minicipher/
	GOOS=darwin GOARCH=arm64 go build -o bin/minicipher-darwin-arm64 ./cmd/minicipher/
	GOOS=linux GOARCH=amd64 go build -o bin/minicipher-linux-amd64 ./cmd/minicipher/
	GOOS=windows GOARCH=amd64 go build -o bin/minicipher-windows-amd64.exe ./cmd/minicipher/