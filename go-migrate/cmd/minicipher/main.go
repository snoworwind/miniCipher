package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/snoworwind/minicipher/internal/config"
	"github.com/snoworwind/minicipher/internal/crypto"
	"github.com/snoworwind/minicipher/internal/lang"
)

func main() {
	cfgMgr := config.NewManager()
	cfg, err := cfgMgr.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	translator := lang.NewTranslator(cfg.UI.Language)

	if len(os.Args) < 2 {
		printUsage(translator)
		os.Exit(0)
	}

	switch os.Args[1] {
	case "encrypt":
		handleEncrypt(os.Args[2:], cfg, translator, cfgMgr)
	case "decrypt":
		handleDecrypt(os.Args[2:], cfg, translator, cfgMgr)
	case "test":
		runTests()
	case "help", "-h", "--help":
		printUsage(translator)
	default:
		fmt.Fprintf(os.Stderr, "未知命令: %s\n", os.Args[1])
		printUsage(translator)
		os.Exit(1)
	}
}

func printUsage(t *lang.Translator) {
	fmt.Print(`
用法:
  minicipher encrypt <input_file> <output_file> [选项]
  minicipher decrypt <input_file> <output_file> [选项]
  minicipher test

加密选项:
  --algo=AES256|OTP        加密算法 (默认: 配置文件设置)
  --key-type=random|password  密钥类型 (默认: 配置文件设置)
  --password-stdin          从标准输入读取密码 (推荐)
  --password-env=VAR        从环境变量读取密码 (例如 --password-env=MINICIPHER_PASSWORD)

解密选项:
  --key-file=<path>         密钥文件路径
  --password-stdin          从标准输入读取密码
  --password-env=VAR        从环境变量读取密码

密码安全说明:
  推荐使用 --password-stdin 或环境变量方式提供密码，
  避免密码出现在命令行参数中（命令行参数会被记录到 shell 历史）。
  也可以通过设置环境变量 MINICIPHER_PASSWORD 来提供密码。

示例:
  # 加密（推荐：stdin 密码）
  echo "MySecret123" | minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-stdin

  # 加密（环境变量密码）
  MINICIPHER_PASSWORD=MySecret123 minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-env=MINICIPHER_PASSWORD

  # 加密（随机密钥 - 无需密码）
  minicipher encrypt doc.pdf doc.pdf.enc --algo=AES256 --key-type=random

  # OTP 加密
  minicipher encrypt data.bin data.bin.enc --algo=OTP

  # 解密
  echo "MySecret123" | minicipher decrypt secret.txt.enc output.txt --password-stdin
  minicipher decrypt doc.pdf.enc output.pdf --key-file=doc.pdf.enc.key
`)
}

// readPassword reads password from the specified source
func readPassword(passwordStdin bool, passwordEnv string, args []string) (string, error) {
	// Priority 1: stdin (most secure, no shell history)
	if passwordStdin {
		reader := bufio.NewReader(os.Stdin)
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return "", fmt.Errorf("从标准输入读取密码失败: %w", err)
		}
		return strings.TrimRight(line, "\r\n"), nil
	}

	// Priority 2: environment variable
	if passwordEnv != "" {
		val := os.Getenv(passwordEnv)
		if val != "" {
			return val, nil
		}
		return "", fmt.Errorf("环境变量 %s 为空或未设置", passwordEnv)
	}

	// Priority 3: deprecated --password= flag (kept for backwards compat with warning)
	for _, arg := range args {
		if strings.HasPrefix(arg, "--password=") {
			fmt.Fprintln(os.Stderr, "⚠️  警告: 使用 --password= 标志会将密码暴露在 shell 历史中。")
			fmt.Fprintln(os.Stderr, "   推荐使用 --password-stdin 或 --password-env=MINICIPHER_PASSWORD")
			return arg[11:], nil
		}
	}

	return "", fmt.Errorf("密码模式需要密码。使用 --password-stdin (推荐) 或 --password-env=VAR")
}

func parseArgs(args []string) map[string]string {
	result := make(map[string]string)
	for _, arg := range args {
		if strings.HasPrefix(arg, "--") {
			eqIdx := strings.Index(arg, "=")
			if eqIdx > 0 {
				key := arg[:eqIdx]
				value := arg[eqIdx+1:]
				result[key] = value
			} else {
				result[arg] = "true" // boolean flag
			}
		}
	}
	return result
}

func handleEncrypt(args []string, cfg *config.Config, t *lang.Translator, cfgMgr *config.Manager) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "错误: 需要输入文件路径和输出文件路径")
		os.Exit(1)
	}

	inputFile := args[0]
	outputFile := args[1]

	parsed := parseArgs(args[2:])

	algo := cfg.Crypto.DefaultAlgorithm
	if v, ok := parsed["--algo"]; ok {
		algo = v
	}

	keyTypeStr := cfg.Crypto.DefaultKeyType
	if v, ok := parsed["--key-type"]; ok {
		keyTypeStr = v
	}

	var kt crypto.KeyType
	if keyTypeStr == "password" {
		kt = crypto.KeyTypePassword
	} else {
		kt = crypto.KeyTypeRandom
	}

	// Read password via secure channel
	var password string
	if kt == crypto.KeyTypePassword {
		passwordStdin := false
		if _, ok := parsed["--password-stdin"]; ok {
			passwordStdin = true
		}
		passwordEnv := parsed["--password-env"]
		if passwordEnv == "" {
			// auto-detect MINICIPHER_PASSWORD if no explicit env var name
			if v := os.Getenv("MINICIPHER_PASSWORD"); v != "" && !passwordStdin {
				passwordEnv = "MINICIPHER_PASSWORD"
			}
		}

		var err error
		password, err = readPassword(passwordStdin, passwordEnv, args[2:])
		if err != nil || password == "" {
			fmt.Fprintf(os.Stderr, "错误: %v\n", err)
			fmt.Fprintf(os.Stderr, "使用: echo <密码> | %s encrypt ... --password-stdin\n", os.Args[0])
			os.Exit(1)
		}
	}

	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "错误: 输入文件不存在: %s\n", inputFile)
		os.Exit(1)
	}

	fmt.Printf("加密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("算法: %s, 密钥类型: %s\n\n", algo, keyTypeStr)

	chunkSize := cfgMgr.GetBufferSizeMB() * 1024 * 1024

	var result *crypto.EncryptionResult
	var err error

	switch algo {
	case "OTP":
		otp := crypto.NewOTPAlgorithm()
		result, err = otp.EncryptToFile(inputFile, outputFile, chunkSize)
	case "AES256":
		aes := crypto.NewAES256Algorithm()
		result, err = aes.EncryptToFile(inputFile, outputFile, kt, []byte(password), nil, chunkSize)
	default:
		fmt.Fprintf(os.Stderr, "不支持的算法: %s\n", algo)
		os.Exit(1)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "加密失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("✅ 加密成功!")
	fmt.Printf("输出文件: %s\n", outputFile)

	// 保存密钥（随机密钥模式）
	if algo == "AES256" && kt == crypto.KeyTypeRandom {
		keyFile := outputFile + ".key"
		// 保存 key+iv+tag 完整格式
		if err := crypto.SaveKeyFileWithIVTag(keyFile, result.Key, result.IV, result.Tag); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 保存密钥文件失败: %v\n", err)
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	} else if algo == "OTP" && result.Key != nil {
		keyFile := outputFile + ".key"
		// OTP 密钥：保存为纯二进制（与 Python 兼容）
		if err := crypto.SaveKeyFile(keyFile, result.Key); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 保存密钥文件失败: %v\n", err)
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	}
}

func handleDecrypt(args []string, cfg *config.Config, t *lang.Translator, cfgMgr *config.Manager) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "错误: 需要加密文件路径和输出文件路径")
		os.Exit(1)
	}

	inputFile := args[0]
	outputFile := args[1]
	parsed := parseArgs(args[2:])

	keyFile := parsed["--key-file"]
	passwordStdin := false
	if _, ok := parsed["--password-stdin"]; ok {
		passwordStdin = true
	}
	passwordEnv := parsed["--password-env"]
	if passwordEnv == "" {
		if v := os.Getenv("MINICIPHER_PASSWORD"); v != "" && !passwordStdin {
			passwordEnv = "MINICIPHER_PASSWORD"
		}
	}

	// Read password via secure channel
	var password string
	if passwordStdin || passwordEnv != "" {
		var err error
		password, err = readPassword(passwordStdin, passwordEnv, args[2:])
		if err != nil {
			fmt.Fprintf(os.Stderr, "错误: %v\n", err)
			os.Exit(1)
		}
	}

	algo := "AES256"

	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "错误: 加密文件不存在: %s\n", inputFile)
		os.Exit(1)
	}

	// 从文件头自动检测算法
	data, err := os.ReadFile(inputFile)
	if err == nil && len(data) >= 4 {
		switch {
		case data[0] == 'A' && data[1] == 'E' && data[2] == 'S':
			algo = "AES256"
		case data[0] == 'O' && data[1] == 'T' && data[2] == 'P':
			algo = "OTP"
		}
	}

	fmt.Printf("解密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("检测算法: %s\n\n", algo)

	chunkSize := cfgMgr.GetBufferSizeMB() * 1024 * 1024

	switch algo {
	case "OTP":
		if keyFile == "" {
			fmt.Fprintln(os.Stderr, "错误: OTP解密需要 --key-file=")
			os.Exit(1)
		}
		// 使用智能加载（兼容 hex 和二进制格式）
		key, err := crypto.LoadKey(keyFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "读取密钥文件失败: %v\n", err)
			os.Exit(1)
		}
		otp := crypto.NewOTPAlgorithm()
		_, err = otp.DecryptFromFile(inputFile, outputFile, key, chunkSize)
		if err != nil {
			fmt.Fprintf(os.Stderr, "解密失败: %v\n", err)
			os.Exit(1)
		}

	case "AES256":
		aes := crypto.NewAES256Algorithm()
		if password != "" {
			_, err = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypePassword, nil, nil, nil, []byte(password), nil, chunkSize)
		} else if keyFile != "" {
			// 智能加载 AES 密钥（兼容完整格式和纯key格式）
			key, iv, tag, e := crypto.LoadKeyWithIVTag(keyFile)
			if e != nil {
				// 回退到纯key格式
				key, err = crypto.LoadKey(keyFile)
				if err != nil {
					fmt.Fprintf(os.Stderr, "读取密钥文件失败: %v\n", err)
					os.Exit(1)
				}
				iv = nil
				tag = nil
			}
			_, err = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypeRandom, key, iv, tag, nil, nil, chunkSize)
		} else {
			fmt.Fprintln(os.Stderr, "错误: 需要 --key-file= 或提供密码 (--password-stdin / --password-env)")
			os.Exit(1)
		}
		if err != nil {
			fmt.Fprintf(os.Stderr, "解密失败: %v\n", err)
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "不支持的算法: %s\n", algo)
		os.Exit(1)
	}

	fmt.Println("✅ 解密成功!")
	fmt.Printf("输出文件: %s\n", outputFile)
}

func runTests() {
	fmt.Println("运行加密模块测试...")
	testData := []byte("Hello, MiniCipher! 你好，加密世界！")
	aes := crypto.NewAES256Algorithm()

	// AES256 随机密钥
	encResult, err := aes.EncryptWithRandomKey(testData)
	if err != nil {
		fmt.Printf("❌ AES256 加密失败: %v\n", err)
		return
	}
	decResult, err := aes.DecryptWithRandomKey(encResult.Ciphertext, encResult.Key, encResult.IV, encResult.Tag)
	if err != nil {
		fmt.Printf("❌ AES256 解密失败: %v\n", err)
		return
	}
	if string(decResult.Plaintext) == string(testData) {
		fmt.Println("✅ AES256 随机密钥: 通过")
	} else {
		fmt.Println("❌ AES256 随机密钥: 数据不匹配")
	}

	// AES256 密码模式
	password := []byte("MySecurePassword123!")
	encResult2, err := aes.EncryptWithPassword(testData, password, nil)
	if err != nil {
		fmt.Printf("❌ AES256 密码加密失败: %v\n", err)
		return
	}
	decResult2, err := aes.DecryptWithPassword(encResult2.Ciphertext, password, encResult2.Salt, encResult2.IV, encResult2.Tag)
	if err != nil {
		fmt.Printf("❌ AES256 密码解密失败: %v\n", err)
		return
	}
	if string(decResult2.Plaintext) == string(testData) {
		fmt.Println("✅ AES256 密码模式: 通过")
	} else {
		fmt.Println("❌ AES256 密码模式: 数据不匹配")
	}

	// OTP
	otp := crypto.NewOTPAlgorithm()
	otpEnc, err := otp.Encrypt(testData)
	if err != nil {
		fmt.Printf("❌ OTP 加密失败: %v\n", err)
		return
	}
	otpDec, err := otp.Decrypt(otpEnc.Ciphertext, otpEnc.Key)
	if err != nil {
		fmt.Printf("❌ OTP 解密失败: %v\n", err)
		return
	}
	if string(otpDec.Plaintext) == string(testData) {
		fmt.Println("✅ OTP: 通过")
	} else {
		fmt.Println("❌ OTP: 数据不匹配")
	}

	// 文件加密/解密
	tmpDir, _ := os.MkdirTemp("", "minicipher_test")
	defer os.RemoveAll(tmpDir)

	testFilePath := filepath.Join(tmpDir, "test.txt")
	testContent := []byte("This is a file encryption test!\n第二行中文内容。")
	os.WriteFile(testFilePath, testContent, 0644)

	encFilePath := filepath.Join(tmpDir, "test.txt.enc")
	fileResult, err := aes.EncryptToFile(testFilePath, encFilePath, crypto.KeyTypeRandom, nil, nil, 10*1024*1024)
	if err != nil {
		fmt.Printf("❌ 文件加密失败: %v\n", err)
		return
	}

	decFilePath := filepath.Join(tmpDir, "test_decrypted.txt")
	_, err = aes.DecryptFromFile(encFilePath, decFilePath,
		crypto.KeyTypeRandom, fileResult.Key, fileResult.IV, fileResult.Tag, nil, nil, 10*1024*1024)
	if err != nil {
		fmt.Printf("❌ 文件解密失败: %v\n", err)
		return
	}

	decContent, _ := os.ReadFile(decFilePath)
	if string(decContent) == string(testContent) {
		fmt.Println("✅ 文件加解密: 通过")
	} else {
		fmt.Println("❌ 文件加解密: 数据不匹配")
	}

	// 密钥文件保存/加载 (新的 API)
	keyFilePath := filepath.Join(tmpDir, "test.key")
	if err := crypto.SaveKeyFileWithIVTag(keyFilePath, fileResult.Key, fileResult.IV, fileResult.Tag); err != nil {
		fmt.Printf("❌ 保存密钥文件失败: %v\n", err)
		return
	}
	k2, iv2, tag2, err := crypto.LoadKeyWithIVTag(keyFilePath)
	if err != nil {
		fmt.Printf("❌ 加载密钥文件失败: %v\n", err)
		return
	}
	if len(k2) == 32 && len(iv2) == 12 && len(tag2) == 16 {
		fmt.Println("✅ 密钥文件保存/加载: 通过")
	} else {
		fmt.Println("❌ 密钥文件保存/加载: 格式错误")
	}

	// 测试智能加载密钥 (LoadKey)
	keyOnlyPath := filepath.Join(tmpDir, "test_key_only.key")
	if err := crypto.SaveKeyFile(keyOnlyPath, fileResult.Key); err != nil {
		fmt.Printf("❌ 保存纯key文件失败: %v\n", err)
	} else {
		k3, err := crypto.LoadKey(keyOnlyPath)
		if err != nil || len(k3) != 32 {
			fmt.Printf("❌ 加载纯key文件失败: %v\n", err)
		} else {
			fmt.Println("✅ 纯key加载: 通过")
		}
	}

	fmt.Println("\n所有测试完成!")
}