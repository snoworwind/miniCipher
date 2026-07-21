package main

import (
	"fmt"
	"os"
	"path/filepath"

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
		handleEncrypt(os.Args[2:], cfg, translator)
	case "decrypt":
		handleDecrypt(os.Args[2:], cfg, translator)
	case "test":
		runTests()
	case "help", "-h", "--help":
		printUsage(translator)
	default:
		fmt.Printf("未知命令: %s\n", os.Args[1])
		printUsage(translator)
		os.Exit(1)
	}
}

func printUsage(t *lang.Translator) {
	fmt.Println(`
用法:
  minicipher encrypt <input_file> <output_file> [--algo=AES256|OTP] [--key-type=random|password] [--password=<pwd>]
  minicipher decrypt <input_file> <output_file> [--key-file=<path>] [--password=<pwd>]
  minicipher test

示例:
  minicipher encrypt doc.pdf doc.pdf.enc --algo=AES256 --key-type=random
  minicipher encrypt secret.txt secret.txt.enc --key-type=password --password=MySecret123
  minicipher encrypt data.bin data.bin.enc --algo=OTP
  minicipher decrypt doc.pdf.enc output.pdf --key-file=doc.pdf.enc.key
  minicipher decrypt secret.txt.enc output.txt --password=MySecret123
`)
}

func handleEncrypt(args []string, cfg *config.Config, t *lang.Translator) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "错误: 需要输入文件路径和输出文件路径")
		os.Exit(1)
	}

	inputFile := args[0]
	outputFile := args[1]
	algo := cfg.Crypto.DefaultAlgorithm
	keyTypeStr := cfg.Crypto.DefaultKeyType
	var password string

	for _, arg := range args[2:] {
		if len(arg) > 7 && arg[:7] == "--algo=" {
			algo = arg[7:]
		}
		if len(arg) > 11 && arg[:11] == "--key-type=" {
			keyTypeStr = arg[11:]
		}
		if len(arg) > 11 && arg[:11] == "--password=" {
			password = arg[11:]
		}
	}

	var kt crypto.KeyType
	if keyTypeStr == "password" {
		kt = crypto.KeyTypePassword
	} else {
		kt = crypto.KeyTypeRandom
	}

	if kt == crypto.KeyTypePassword && password == "" {
		fmt.Fprintln(os.Stderr, "错误: 密码模式需要 --password=")
		os.Exit(1)
	}

	if _, err := os.Stat(inputFile); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "错误: 输入文件不存在: %s\n", inputFile)
		os.Exit(1)
	}

	fmt.Printf("加密: %s -> %s\n", inputFile, outputFile)
	fmt.Printf("算法: %s, 密钥类型: %s\n\n", algo, keyTypeStr)

	var result *crypto.EncryptionResult
	var err error

	switch algo {
	case "OTP":
		otp := crypto.NewOTPAlgorithm()
		result, err = otp.EncryptToFile(inputFile, outputFile, 10*1024*1024)
	case "AES256":
		aes := crypto.NewAES256Algorithm()
		result, err = aes.EncryptToFile(inputFile, outputFile, kt, []byte(password), nil)
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
		if err := crypto.SaveKeyFile(keyFile, result.Key, result.IV, result.Tag); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 保存密钥文件失败: %v\n", err)
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	} else if algo == "OTP" && result.Key != nil {
		keyFile := outputFile + ".key"
		if err := os.WriteFile(keyFile, result.Key, 0600); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 保存密钥文件失败: %v\n", err)
		} else {
			fmt.Printf("密钥文件: %s (请妥善保管！)\n", keyFile)
		}
	}
}

func handleDecrypt(args []string, cfg *config.Config, t *lang.Translator) {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "错误: 需要加密文件路径和输出文件路径")
		os.Exit(1)
	}

	inputFile := args[0]
	outputFile := args[1]
	var keyFile string
	var password string
	algo := "AES256"

	for _, arg := range args[2:] {
		if len(arg) > 11 && arg[:11] == "--key-file=" {
			keyFile = arg[11:]
		}
		if len(arg) > 11 && arg[:11] == "--password=" {
			password = arg[11:]
		}
		if len(arg) > 7 && arg[:7] == "--algo=" {
			algo = arg[7:]
		}
	}

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

	switch algo {
	case "OTP":
		if keyFile == "" {
			fmt.Fprintln(os.Stderr, "错误: OTP解密需要 --key-file=")
			os.Exit(1)
		}
		key, err := os.ReadFile(keyFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "读取密钥文件失败: %v\n", err)
			os.Exit(1)
		}
		otp := crypto.NewOTPAlgorithm()
		_, err = otp.DecryptFromFile(inputFile, outputFile, key, 10*1024*1024)
		if err != nil {
			fmt.Fprintf(os.Stderr, "解密失败: %v\n", err)
			os.Exit(1)
		}

	case "AES256":
		aes := crypto.NewAES256Algorithm()
		if password != "" {
			_, err = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypePassword, nil, nil, nil, []byte(password), nil)
		} else if keyFile != "" {
			key, iv, tag, e := crypto.LoadKeyFile(keyFile)
			if e != nil {
				fmt.Fprintf(os.Stderr, "读取密钥文件失败: %v\n", e)
				os.Exit(1)
			}
			_, err = aes.DecryptFromFile(inputFile, outputFile,
				crypto.KeyTypeRandom, key, iv, tag, nil, nil)
		} else {
			fmt.Fprintln(os.Stderr, "错误: 需要 --key-file= 或 --password=")
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
	fileResult, err := aes.EncryptToFile(testFilePath, encFilePath, crypto.KeyTypeRandom, nil, nil)
	if err != nil {
		fmt.Printf("❌ 文件加密失败: %v\n", err)
		return
	}

	decFilePath := filepath.Join(tmpDir, "test_decrypted.txt")
	_, err = aes.DecryptFromFile(encFilePath, decFilePath,
		crypto.KeyTypeRandom, fileResult.Key, fileResult.IV, fileResult.Tag, nil, nil)
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

	// 密钥文件保存/加载
	keyFilePath := filepath.Join(tmpDir, "test.key")
	if err := crypto.SaveKeyFile(keyFilePath, fileResult.Key, fileResult.IV, fileResult.Tag); err != nil {
		fmt.Printf("❌ 保存密钥文件失败: %v\n", err)
		return
	}
	k2, iv2, tag2, err := crypto.LoadKeyFile(keyFilePath)
	if err != nil {
		fmt.Printf("❌ 加载密钥文件失败: %v\n", err)
		return
	}
	if len(k2) == 32 && len(iv2) == 12 && len(tag2) == 16 {
		fmt.Println("✅ 密钥文件保存/加载: 通过")
	} else {
		fmt.Println("❌ 密钥文件保存/加载: 格式错误")
	}

	fmt.Println("\n所有测试完成!")
}