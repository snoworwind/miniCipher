package crypto

import (
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode"
	"unicode/utf8"

	"golang.org/x/crypto/pbkdf2"
	"crypto/sha256"
)

// FileCipher 高级文件加密/解密API
// 整合所有文件操作、分块处理、密钥管理和错误处理逻辑
type FileCipher struct {
	bufferSizeMB int
	passwordMinLength int
	requireStrongPassword bool
}

// NewFileCipher 创建 FileCipher 实例
func NewFileCipher(bufferSizeMB, passwordMinLength int, requireStrongPassword bool) *FileCipher {
	if bufferSizeMB <= 0 {
		bufferSizeMB = 10
	}
	if passwordMinLength <= 0 {
		passwordMinLength = 8
	}
	return &FileCipher{
		bufferSizeMB:         bufferSizeMB,
		passwordMinLength:    passwordMinLength,
		requireStrongPassword: requireStrongPassword,
	}
}

// EncryptionRequest 加密请求参数
type EncryptionRequest struct {
	InputPath       string
	OutputPath      string
	Algorithm       AlgorithmType
	KeyType         KeyType
	Password        string
	ProgressFn      func(percent int, message string)
}

// EncryptionResponse 加密响应
type EncryptionResponse struct {
	Key     []byte
	IV      []byte
	Tag     []byte
	Salt    []byte
	KeyFileNeeded bool
	Success  bool
	Error    string
}

// DecryptionRequest 解密请求参数
type DecryptionRequest struct {
	InputPath       string
	OutputPath      string
	Algorithm       AlgorithmType
	KeyType         KeyType
	KeyPath         string
	Password        string
	ProgressFn      func(percent int, message string)
}

// DecryptionResponse 解密响应
type DecryptionResponse struct {
	Success bool
	Error   string
}

// ValidatePassword 验证密码强度
// 返回 (是否有效, 错误消息)
func (fc *FileCipher) ValidatePassword(password string) (bool, string) {
	if password == "" {
		return false, "密码不能为空"
	}
	
	if utf8.RuneCountInString(password) < fc.passwordMinLength {
		return false, fmt.Sprintf("密码太短，至少需要%d个字符", fc.passwordMinLength)
	}
	
	if fc.requireStrongPassword {
		hasUpper := false
		hasLower := false
		hasDigit := false
		
		for _, ch := range password {
			switch {
			case unicode.IsUpper(ch):
				hasUpper = true
			case unicode.IsLower(ch):
				hasLower = true
			case unicode.IsDigit(ch):
				hasDigit = true
			}
		}
		
		if !hasUpper || !hasLower || !hasDigit {
			return false, "密码强度不足，需要包含大写字母、小写字母和数字"
		}
	}
	
	return true, ""
}

// EncryptFile 加密文件 - 统一入口
// 自动选择分块或完整处理，支持进度回调
func (fc *FileCipher) EncryptFile(req EncryptionRequest) (*EncryptionResponse, error) {
	// 检查输入文件
	fileInfo, err := os.Stat(req.InputPath)
	if err != nil {
		return nil, fmt.Errorf("输入文件不存在: %w", err)
	}
	fileSize := fileInfo.Size()

	if req.ProgressFn != nil {
		req.ProgressFn(0, fmt.Sprintf("开始加密，文件大小: %d 字节", fileSize))
	}

	chunkSize := int64(fc.bufferSizeMB) * 1024 * 1024

	var result *EncryptionResult
	var encryptError error

	if req.Algorithm == AlgorithmOTP {
		otp := NewOTPAlgorithm()
		result, encryptError = otp.EncryptToFile(req.InputPath, req.OutputPath, int(chunkSize))
	} else { // AES256
		if req.KeyType == KeyTypePassword {
			if req.Password == "" {
				return nil, fmt.Errorf("密码模式需要提供密码")
			}
			
			// 验证密码强度
			if valid, msg := fc.ValidatePassword(req.Password); !valid {
				return nil, fmt.Errorf(msg)
			}
			
			aes := NewAES256Algorithm()
			result, encryptError = aes.EncryptToFile(req.InputPath, req.OutputPath, KeyTypePassword, []byte(req.Password), nil)
		} else {
			aes := NewAES256Algorithm()
			result, encryptError = aes.EncryptToFile(req.InputPath, req.OutputPath, KeyTypeRandom, nil, nil)
		}
	}

	if encryptError != nil {
		return nil, fmt.Errorf("加密失败: %w", encryptError)
	}

	if req.ProgressFn != nil {
		req.ProgressFn(70, "写入密文文件...")
	}

	needsKey := false
	if req.Algorithm == AlgorithmOTP || (req.Algorithm == AlgorithmAES256 && req.KeyType == KeyTypeRandom) {
		needsKey = true
	}

	if req.ProgressFn != nil {
		req.ProgressFn(100, "加密完成")
	}

	return &EncryptionResponse{
		Key:           result.Key,
		IV:            result.IV,
		Tag:           result.Tag,
		Salt:          result.Salt,
		KeyFileNeeded: needsKey,
		Success:       true,
	}, nil
}

// DecryptFile 解密文件 - 统一入口
// 支持算法自动检测和密钥文件自动加载
func (fc *FileCipher) DecryptFile(req DecryptionRequest) (*DecryptionResponse, error) {
	// 检查输入文件
	if _, err := os.Stat(req.InputPath); err != nil {
		return nil, fmt.Errorf("输入文件不存在: %w", err)
	}

	var decryptError error

	// 自动检测算法
	detectedAlgo := req.Algorithm
	if detectedAlgo == "" {
		detectedAlgo = detectAlgorithmByFileHeader(req.InputPath)
	}

	switch detectedAlgo {
	case AlgorithmOTP:
		if req.KeyPath == "" {
			return nil, fmt.Errorf("OTP解密需要密钥文件")
		}
		key, err := os.ReadFile(req.KeyPath)
		if err != nil {
			return nil, fmt.Errorf("读取密钥文件失败: %w", err)
		}
		otp := NewOTPAlgorithm()
		chunkSize := int64(fc.bufferSizeMB) * 1024 * 1024
		_, decryptError = otp.DecryptFromFile(req.InputPath, req.OutputPath, key, int(chunkSize))

	case AlgorithmAES256:
		aes := NewAES256Algorithm()
		if req.KeyType == KeyTypePassword || req.Password != "" {
			if req.Password == "" {
				return nil, fmt.Errorf("密码模式需要密码")
			}
			_, decryptError = aes.DecryptFromFile(req.InputPath, req.OutputPath,
				KeyTypePassword, nil, nil, nil, []byte(req.Password), nil)
		} else {
			if req.KeyPath == "" {
				return nil, fmt.Errorf("需要密钥文件路径")
			}
			key, iv, tag, err := LoadKeyFile(req.KeyPath)
			if err != nil {
				return nil, fmt.Errorf("加载密钥文件失败: %w", err)
			}
			_, decryptError = aes.DecryptFromFile(req.InputPath, req.OutputPath,
				KeyTypeRandom, key, iv, tag, nil, nil)
		}

	default:
		return nil, fmt.Errorf("不支持的算法类型")
	}

	if decryptError != nil {
		return nil, fmt.Errorf("解密失败: %w", decryptError)
	}

	return &DecryptionResponse{Success: true}, nil
}

// SaveKey 保存密钥到文件
// 支持多种格式：十六进制 (.key) 或 二进制 (.bin)
func (fc *FileCipher) SaveKey(key []byte, outputDir, baseName string, algorithm AlgorithmType, keyType KeyType, format string) (string, error) {
	if len(key) == 0 {
		return "", fmt.Errorf("密钥为空")
	}

	// 确保输出目录存在
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("创建输出目录失败: %w", err)
	}

	// 确定密钥文件扩展名
	var ext string
	if algorithm == AlgorithmOTP {
		if format == "binary" {
			ext = ".bin"
		} else {
			ext = ".txt" // OTP hex format
		}
	} else {
		ext = ".key" // AES binary format
	}

	// 生成密钥文件名: key_<baseName><ext>
	keyFileName := fmt.Sprintf("key_%s%s", baseName, ext)
	keyFilePath := filepath.Join(outputDir, keyFileName)

	var err error
	if algorithm == AlgorithmOTP {
		if format == "binary" {
			err = os.WriteFile(keyFilePath, key, 0600)
		} else {
			// 十六进制文本格式
			hexStr := hex.EncodeToString(key)
			err = os.WriteFile(keyFilePath, []byte(hexStr), 0600)
		}
	} else {
		// AES 使用标准 SaveKeyFile
		err = SaveKeyFile(keyFilePath, key, nil, nil)
	}

	if err != nil {
		return "", fmt.Errorf("保存密钥文件失败: %w", err)
	}

	return keyFilePath, nil
}

// SaveAESKeyAll 保存AES密钥（包含key+iv+tag）
func (fc *FileCipher) SaveAESKeyAll(key, iv, tag []byte, outputDir, baseName string) (string, error) {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("创建输出目录失败: %w", err)
	}

	keyFileName := fmt.Sprintf("key_%s.key", baseName)
	keyFilePath := filepath.Join(outputDir, keyFileName)

	if err := SaveKeyFile(keyFilePath, key, iv, tag); err != nil {
		return "", fmt.Errorf("保存密钥文件失败: %w", err)
	}

	return keyFilePath, nil
}

// detectAlgorithmByFileHeader 通过文件头检测算法类型
func detectAlgorithmByFileHeader(filePath string) AlgorithmType {
	data, err := os.ReadFile(filePath)
	if err != nil || len(data) < 4 {
		return AlgorithmAES256
	}
	
	header := data[:4]
	
	// 检查 AES 文件头: b'AES\x00' 或 b'AES\x01'
	if header[0] == 'A' && header[1] == 'E' && header[2] == 'S' {
		if header[3] == 0x00 || header[3] == 0x01 {
			return AlgorithmAES256
		}
	}
	
	// 检查 OTP 文件头: b'OTP\x00'
	if header[0] == 'O' && header[1] == 'T' && header[2] == 'P' && header[3] == 0x00 {
		return AlgorithmOTP
	}
	
	// 默认根据扩展名判断
	if strings.HasSuffix(filePath, ".enc") {
		return AlgorithmOTP // 向后兼容：无文件头的.enc文件视为OTP
	}
	
	return AlgorithmAES256
}

// 保留 pbkdf2 和 sha256 引用
var _ = pbkdf2.Key
var _ = sha256.New