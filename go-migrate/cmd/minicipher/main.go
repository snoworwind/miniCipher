package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/snoworwind/minicipher/internal/batch"
	"github.com/snoworwind/minicipher/internal/config"
	"github.com/snoworwind/minicipher/internal/crypto"
	"github.com/snoworwind/minicipher/internal/lang"
)

var (
	cfgMgr     *config.Manager
	cfg        *config.Config
	translator *lang.Translator
)

func main() {
	cfgMgr = config.NewManager()
	var err error
	cfg, err = cfgMgr.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	translator = lang.NewTranslator(cfg.UI.Language)

	if len(os.Args) < 2 {
		printUsage()
		os.Exit(0)
	}

	switch os.Args[1] {
	case "encrypt":
		handleEncrypt(os.Args[2:])
	case "decrypt":
		handleDecrypt(os.Args[2:])
	case "batch":
		handleBatch(os.Args[2:])
	case "test":
		runTests()
	case "help", "-h", "--help":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.unknown_command", os.Args[1]))
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Print(translator.T("usage.title"))
}

// readPassword reads password from the specified source
func readPassword(passwordStdin bool, passwordEnv string, args []string) (string, error) {
	// Priority 1: stdin (most secure, no shell history)
	if passwordStdin {
		reader := bufio.NewReader(os.Stdin)
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return "", fmt.Errorf("%s", translator.Tf("error.password_stdin", err))
		}
		return strings.TrimRight(line, "\r\n"), nil
	}

	// Priority 2: environment variable
	if passwordEnv != "" {
		val := os.Getenv(passwordEnv)
		if val != "" {
			return val, nil
		}
		return "", fmt.Errorf("%s", translator.Tf("error.password_env_empty", passwordEnv))
	}

	// Priority 3: deprecated --password= flag (kept for backwards compat with warning)
	for _, arg := range args {
		if strings.HasPrefix(arg, "--password=") {
			fmt.Fprintln(os.Stderr, translator.T("warn.password_cli"))
			fmt.Fprintln(os.Stderr, translator.T("warn.password_cli_hint"))
			return arg[11:], nil
		}
	}

	return "", fmt.Errorf("%s", translator.Tf("error.no_password"))
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

func handleEncrypt(args []string) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, translator.T("error.missing_args"))
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
			fmt.Fprintf(os.Stderr, "%v\n", err)
			fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("hint.password_usage", os.Args[0]))
			os.Exit(1)
		}
	}

	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.input_file_missing", inputFile))
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
		// 使用 BuildKeyFilePath 生成统一路径
		outputDir := filepath.Dir(outputFile)
		inputBase := filepath.Base(inputFile)
		otpFormat := cfg.Crypto.OTPKeyFormat
		if otpFormat == "" {
			otpFormat = "hex"
		}
		keyFilePath := crypto.BuildKeyFilePath(outputDir, inputBase, crypto.AlgorithmOTP, crypto.KeyTypeRandom, otpFormat)
		result, err = otp.EncryptToFile(inputFile, outputFile, keyFilePath, chunkSize)
	case "AES256":
		aes := crypto.NewAES256Algorithm()
		result, err = aes.EncryptToFile(inputFile, outputFile, kt, []byte(password), nil, chunkSize)
	default:
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.algo_not_supported", algo))
		os.Exit(1)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.encryption_failed", err.Error()))
		os.Exit(1)
	}

	fmt.Println(translator.Tf("success.encryption_stat", outputFile))

	// 保存密钥（随机密钥模式）
	if algo == "AES256" && kt == crypto.KeyTypeRandom {
		keyFile := crypto.BuildKeyFilePath(filepath.Dir(outputFile), filepath.Base(inputFile), crypto.AlgorithmAES256, crypto.KeyTypeRandom, "")
		if err := crypto.SaveKeyFileWithIVTag(keyFile, result.Key, result.IV, result.Tag); err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("warn.key_save", err))
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	} else if algo == "OTP" {
		outputDir := filepath.Dir(outputFile)
		inputBase := filepath.Base(inputFile)
		otpFormat := cfg.Crypto.OTPKeyFormat
		if otpFormat == "" {
			otpFormat = "hex"
		}
		keyFilePath := crypto.BuildKeyFilePath(outputDir, inputBase, crypto.AlgorithmOTP, crypto.KeyTypeRandom, otpFormat)
		fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFilePath)
	}
}

func handleDecrypt(args []string) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, translator.T("error.missing_encrypt_args"))
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
		var pwdErr error
		password, pwdErr = readPassword(passwordStdin, passwordEnv, args[2:])
		if pwdErr != nil {
			fmt.Fprintf(os.Stderr, "%v\n", pwdErr)
			os.Exit(1)
		}
	}

	if _, statErr := os.Stat(inputFile); os.IsNotExist(statErr) {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.input_file_missing", inputFile))
		os.Exit(1)
	}

	// 从文件头自动检测算法（只读4字节，避免大文件加载到内存）
	algo := detectAlgorithmFromHeader(inputFile)

	fmt.Printf("解密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("检测算法: %s\n\n", algo)

	chunkSize := cfgMgr.GetBufferSizeMB() * 1024 * 1024
	var decryptErr error

	switch algo {
	case "OTP":
		if keyFile == "" {
			fmt.Fprintln(os.Stderr, translator.T("error.no_key"))
			os.Exit(1)
		}
		// OTP 流式解密：分块读取密钥文件
		otp := crypto.NewOTPAlgorithm()
		_, decryptErr = otp.DecryptFromFile(inputFile, outputFile, keyFile, chunkSize)

	case "AES256":
		aes := crypto.NewAES256Algorithm()
		if password != "" {
			_, decryptErr = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypePassword, nil, nil, nil, []byte(password), nil, chunkSize)
		} else if keyFile != "" {
			// 智能加载 AES 密钥（兼容完整格式和纯key格式）
			key, iv, tag, e := crypto.LoadKeyWithIVTag(keyFile)
			if e != nil {
				// 回退到纯key格式
				key, decryptErr = crypto.LoadKey(keyFile)
				if decryptErr != nil {
					fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.decryption_failed", decryptErr.Error()))
					os.Exit(1)
				}
				iv = nil
				tag = nil
			}
			_, decryptErr = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypeRandom, key, iv, tag, nil, nil, chunkSize)
		} else {
			fmt.Fprintln(os.Stderr, translator.T("error.no_key"))
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.algo_not_supported", algo))
		os.Exit(1)
	}

	if decryptErr != nil {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.decryption_failed", decryptErr.Error()))
		os.Exit(1)
	}

	fmt.Println(translator.Tf("success.decryption_stat", outputFile))
}

// detectAlgorithmFromHeader 从文件头检测算法类型（只读4字节）
func detectAlgorithmFromHeader(filePath string) string {
	f, err := os.Open(filePath)
	if err != nil {
		return "AES256"
	}
	defer f.Close()

	header := make([]byte, 4)
	if _, err := io.ReadFull(f, header); err != nil {
		return "AES256"
	}

	if header[0] == 'O' && header[1] == 'T' && header[2] == 'P' {
		return "OTP"
	}
	if header[0] == 'A' && header[1] == 'E' && header[2] == 'S' {
		return "AES256"
	}
	return "AES256"
}

// handleBatch 批量加密/解密 CLI 入口
func handleBatch(args []string) {
	if len(args) < 3 {
		fmt.Fprintln(os.Stderr, "用法: minicipher batch <encrypt|decrypt> <input_dir> <output_dir> [选项]")
		os.Exit(1)
	}

	opStr := args[0]
	if opStr != "encrypt" && opStr != "decrypt" {
		fmt.Fprintf(os.Stderr, "无效的操作: %s (应为 encrypt 或 decrypt)\n", opStr)
		os.Exit(1)
	}

	inputDir := args[1]
	outputDir := args[2]
	parsed := parseArgs(args[3:])

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

	// 密码处理
	var password []byte
	if kt == crypto.KeyTypePassword {
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

		pwd, err := readPassword(passwordStdin, passwordEnv, args[3:])
		if err != nil || pwd == "" {
			fmt.Fprintf(os.Stderr, "%v\n", err)
			os.Exit(1)
		}
		password = []byte(pwd)
	}

	// 处理模式
	modeStr := parsed["--mode"]
	if modeStr == "" {
		modeStr = "recursive"
	}
	var mode batch.Mode
	switch modeStr {
	case "files":
		mode = batch.ModeFiles
	case "folder":
		mode = batch.ModeFolder
	default:
		mode = batch.ModeFolderRecursive
	}

	preserveStruct := false
	if _, ok := parsed["--preserve-structure"]; ok {
		preserveStruct = true
	}

	parallel := false
	if _, ok := parsed["--parallel"]; ok {
		parallel = true
	}

	maxThreads := 4
	if v, ok := parsed["--max-threads"]; ok {
		fmt.Sscanf(v, "%d", &maxThreads)
	}
	if !parallel {
		maxThreads = 1
	}

	var op batch.OperationType
	if opStr == "encrypt" {
		op = batch.OpEncrypt
	} else {
		op = batch.OpDecrypt
	}

	bp := batch.New(maxThreads, cfgMgr.GetBufferSizeMB())

	startTime := time.Now()
	fmt.Printf("批量%s: %s -> %s\n", opStr, inputDir, outputDir)
	fmt.Printf("算法: %s, 模式: %s, 并行: %v\n", algo, modeStr, parallel)

	result, err := bp.Process(op, mode, []string{inputDir}, outputDir, preserveStruct,
		algo, kt, nil, password, nil, nil, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.decryption_failed", err.Error()))
		os.Exit(1)
	}

	elapsed := time.Since(startTime).Round(time.Millisecond)
	fmt.Printf("\n✅ 批量%s完成!\n", opStr)
	fmt.Printf("总文件: %d, 成功: %d, 失败: %d\n", result.TotalFiles, result.SuccessFiles, result.FailedFiles)
	fmt.Printf("耗时: %s\n", elapsed)

	if result.FailedFiles > 0 {
		fmt.Println("\n失败详情:")
		for _, fr := range result.FileResults {
			if !fr.Success {
				fmt.Printf("  ❌ %s: %s\n", filepath.Base(fr.InputPath), fr.ErrorMessage)
			}
		}
	}

	fmt.Print(result.StatisticsReport())
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

	// 密钥文件保存/加载（完整格式 key+iv+tag）
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
	_ = tag2
	if len(k2) == 32 && len(iv2) == 12 {
		fmt.Println("✅ 密钥文件保存/加载: 通过")
	} else {
		fmt.Printf("❌ 密钥文件保存/加载: 格式错误 (key=%d iv=%d)\n", len(k2), len(iv2))
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