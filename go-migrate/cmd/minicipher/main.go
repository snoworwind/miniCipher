package main

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"fyne.io/fyne/v2/app"

	"github.com/snoworwind/minicipher/internal/batch"
	"github.com/snoworwind/minicipher/internal/config"
	"github.com/snoworwind/minicipher/internal/crypto"
	"github.com/snoworwind/minicipher/internal/lang"
	"github.com/snoworwind/minicipher/internal/log"
	"github.com/snoworwind/minicipher/internal/platform"
	"github.com/snoworwind/minicipher/internal/ui"
)

func main() {
	// Detect mode: if arguments are provided, run CLI; otherwise run GUI
	if len(os.Args) > 1 {
		// CLI mode — attach to parent console (Windows) or use current terminal
		platform.AttachOrAllocConsole()
		runCLI()
	} else {
		// GUI mode — load config first to check debug setting
		runGUI()
	}
}

// ========== GUI mode ==========

func runGUI() {
	fApp := app.NewWithID("com.snoworwind.minicipher")
	cfgMgr := config.NewManager()
	cfg, err := cfgMgr.Load()
	if err != nil {
		cfg = config.DefaultConfig()
	}

	// If debug mode is enabled, open a console window (Windows only)
	if cfg.Debug {
		platform.AttachOrAllocConsole()
		log.Setup(cfg.Advanced.LogLevel, true)
		log.Debug("调试模式已启用")
	}
	// GUI mode without debug: DefaultLogger remains NoOpLogger (silent)

	guiApp := ui.NewApp(cfgMgr, fApp)
	guiApp.Run()
}

// ========== CLI mode (original minicipher CLI code, with fyne import removed from CLI path) ==========

var (
	cfgMgr     *config.Manager
	cfg        *config.Config
	translator *lang.Translator
)

func runCLI() {
	cfgMgr = config.NewManager()
	var err error
	cfg, err = cfgMgr.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "加载配置失败: %v\n", err)
		os.Exit(1)
	}

	// Initialize structured logger for CLI mode
	log.Setup(cfg.Advanced.LogLevel, cfg.Debug)

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

// readPassword reads password from the specified source.
// Returns []byte so the caller can zero the buffer after use.
func readPassword(passwordStdin bool, passwordEnv string, args []string) ([]byte, error) {
	// Priority 1: stdin (most secure, no shell history)
	if passwordStdin {
		reader := bufio.NewReader(os.Stdin)
		line, err := reader.ReadBytes('\n')
		if err != nil && err != io.EOF {
			return nil, fmt.Errorf("%s", translator.Tf("error.password_stdin", err))
		}
		// Trim trailing \r\n
		for len(line) > 0 && (line[len(line)-1] == '\n' || line[len(line)-1] == '\r') {
			line = line[:len(line)-1]
		}
		return line, nil
	}

	// Priority 2: environment variable
	if passwordEnv != "" {
		val := os.Getenv(passwordEnv)
		if val != "" {
			return []byte(val), nil
		}
		return nil, fmt.Errorf("%s", translator.Tf("error.password_env_empty", passwordEnv))
	}

	// Priority 3: deprecated --password= flag (kept for backwards compat with warning)
	for _, arg := range args {
		if strings.HasPrefix(arg, "--password=") {
			fmt.Fprintln(os.Stderr, translator.T("warn.password_cli"))
			fmt.Fprintln(os.Stderr, translator.T("warn.password_cli_hint"))
			return []byte(arg[11:]), nil
		}
	}

	return nil, fmt.Errorf("%s", translator.Tf("error.no_password"))
}

// clearBytes 清零字节切片，用于清除内存中的敏感数据（密码、密钥等）
func clearBytes(b []byte) {
	for i := range b {
		b[i] = 0
	}
}

func parseArgs(args []string) map[string]string {
	result := make(map[string]string)
	for i := 0; i < len(args); i++ {
		arg := args[i]
		if strings.HasPrefix(arg, "--") {
			eqIdx := strings.Index(arg, "=")
			if eqIdx > 0 {
				// --key=value syntax
				key := arg[:eqIdx]
				value := arg[eqIdx+1:]
				result[key] = value
			} else if i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {
				// --key value syntax (next arg is not a flag)
				result[arg] = args[i+1]
				i++ // skip next arg
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
	var password []byte
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
		if err != nil || len(password) == 0 {
			fmt.Fprintf(os.Stderr, "%v\n", err)
			fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("hint.password_usage", os.Args[0]))
			os.Exit(1)
		}
		defer clearBytes(password)
	}

	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.input_file_missing", inputFile))
		os.Exit(1)
	}

	fmt.Printf("加密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("算法: %s, 密钥类型: %s\n\n", algo, keyTypeStr)

	chunkSize := cfgMgr.GetBufferSizeMB() * 1024 * 1024

	outputDir := filepath.Dir(outputFile)
	inputBase := filepath.Base(inputFile)

	var result *crypto.EncryptionResult
	var err error
	var otpKeyPath string // OTP key path, reused for notification

	switch crypto.AlgorithmType(algo) {
	case crypto.AlgorithmOTP:
		otpFormat := cfg.Crypto.OTPKeyFormat
		if otpFormat == "" {
			otpFormat = "hex"
		}
		otpKeyPath = crypto.BuildKeyFilePath(outputDir, inputBase, crypto.AlgorithmOTP, crypto.KeyTypeRandom, otpFormat)
		otp := crypto.NewOTPAlgorithm()
		result, err = otp.EncryptToFile(inputFile, outputFile, otpKeyPath, chunkSize)
	case crypto.AlgorithmAES256:
		aes := crypto.NewAES256Algorithm()
		result, err = aes.EncryptToFile(inputFile, outputFile, kt, password, nil, chunkSize)
	default:
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.algo_not_supported", algo))
		os.Exit(1)
	}

	if err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.encryption_failed", err.Error()))
		os.Exit(1)
	}

	fmt.Println(translator.Tf("success.encryption_stat", outputFile))

	// Save key (random key mode)
	if crypto.AlgorithmType(algo) == crypto.AlgorithmAES256 && kt == crypto.KeyTypeRandom {
		keyFile := crypto.BuildKeyFilePath(outputDir, inputBase, crypto.AlgorithmAES256, crypto.KeyTypeRandom, "")
		if err := crypto.SaveKeyFileWithIVTag(keyFile, result.Key, result.IV, result.Tag); err != nil {
			fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("warn.key_save", err))
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	} else if crypto.AlgorithmType(algo) == crypto.AlgorithmOTP {
		fmt.Printf("密钥文件: %s (请妥善保管！)\n", otpKeyPath)
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
	var password []byte
	if passwordStdin || passwordEnv != "" {
		var pwdErr error
		password, pwdErr = readPassword(passwordStdin, passwordEnv, args[2:])
		if pwdErr != nil {
			fmt.Fprintf(os.Stderr, "%v\n", pwdErr)
			os.Exit(1)
		}
		defer clearBytes(password)
	}

	if _, statErr := os.Stat(inputFile); os.IsNotExist(statErr) {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.input_file_missing", inputFile))
		os.Exit(1)
	}

	// Auto-detect algorithm from file header (only read 4 bytes, avoid loading large files into memory)
	algo := crypto.DetectAlgorithmByFileHeader(inputFile)

	fmt.Printf("解密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("检测算法: %s\n\n", algo)

	chunkSize := cfgMgr.GetBufferSizeMB() * 1024 * 1024
	var decryptErr error

	switch algo {
	case crypto.AlgorithmOTP:
		if keyFile == "" {
			fmt.Fprintln(os.Stderr, translator.T("error.no_key"))
			os.Exit(1)
		}
		// OTP streaming decrypt: read key file in chunks
		otp := crypto.NewOTPAlgorithm()
		_, decryptErr = otp.DecryptFromFile(inputFile, outputFile, keyFile, chunkSize)

	case crypto.AlgorithmAES256:
		aes := crypto.NewAES256Algorithm()
		if len(password) > 0 {
			_, decryptErr = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypePassword, nil, nil, nil, password, nil, chunkSize)
		} else if keyFile != "" {
			// Smart load AES key (compatible with full format and plain key format)
			key, iv, tag, e := crypto.LoadKeyWithIVTag(keyFile)
			if e != nil {
				// Fall back to plain key format
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

// handleBatch batch encrypt/decrypt CLI entry
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

	// Password handling
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
		if err != nil || len(pwd) == 0 {
			fmt.Fprintf(os.Stderr, "%v\n", err)
			os.Exit(1)
		}
		password = pwd
		defer clearBytes(password)
	}

	// Processing mode
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
		if n, err := strconv.Atoi(v); err == nil && n >= 1 && n <= 64 {
			maxThreads = n
		} else {
			fmt.Fprintf(os.Stderr, "警告: 无效的 --max-threads 值 %q，使用默认值 %d\n", v, maxThreads)
		}
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
		crypto.AlgorithmType(algo), kt, nil, password, nil, nil, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", translator.Tf("error.batch_failed", err.Error()))
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

	// AES256 random key
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

	// AES256 password mode
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

	// File encrypt/decrypt
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

	// Key file save/load (full format key+iv+tag)
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

	// Test smart key loading (LoadKey)
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
