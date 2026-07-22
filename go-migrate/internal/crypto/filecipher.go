package crypto

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"unicode"
)

// FileCipher 高级文件加密/解密API
// 整合所有文件操作、分块处理、密钥管理和错误处理逻辑
type FileCipher struct {
	bufferSizeMB         int
	passwordMinLength    int
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
	OtpKeyFormat    string // "hex" or "binary" for OTP key format
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

	count := 0
	for range password {
		count++
	}
	if count < fc.passwordMinLength {
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
// 根据文件大小自动选择小文件完整读取或大文件分块处理
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

	chunkSize := fc.bufferSizeMB * 1024 * 1024

	var result *EncryptionResult
	var encryptError error

	if req.Algorithm == AlgorithmOTP {
		otp := NewOTPAlgorithm()
		// 使用 BuildKeyFilePath 生成密钥文件路径
		outputDir := filepath.Dir(req.OutputPath)
		baseName := filepath.Base(req.InputPath)
		otpFormat := req.OtpKeyFormat
		if otpFormat == "" {
			otpFormat = "hex"
		}
		keyFilePath := BuildKeyFilePath(outputDir, baseName, AlgorithmOTP, KeyTypeRandom, otpFormat)

		// 创建进度包装器
		var progressFn ProgressFunc
		if req.ProgressFn != nil {
			progressFn = func(processed, total int64) {
				if total > 0 {
					pct := int(processed * 100 / total)
					req.ProgressFn(pct, fmt.Sprintf("加密中... %d%%", pct))
				}
			}
		}

		result, encryptError = otp.EncryptToFileWithProgress(req.InputPath, req.OutputPath, keyFilePath, chunkSize, progressFn)
	} else { // AES256
		if req.KeyType == KeyTypePassword {
			if req.Password == "" {
				return nil, fmt.Errorf("密码模式需要提供密码")
			}

			// 验证密码强度
			if valid, msg := fc.ValidatePassword(req.Password); !valid {
				return nil, fmt.Errorf("%s", msg)
			}

			aes := NewAES256Algorithm()
			var progressFn ProgressFunc
			if req.ProgressFn != nil {
				progressFn = func(processed, total int64) {
					if total > 0 {
						pct := int(processed * 100 / total)
						req.ProgressFn(pct, fmt.Sprintf("加密中... %d%%", pct))
					}
				}
			}
			result, encryptError = aes.EncryptToFileWithProgress(req.InputPath, req.OutputPath, KeyTypePassword, []byte(req.Password), nil, chunkSize, progressFn)
		} else {
			aes := NewAES256Algorithm()
			var progressFn ProgressFunc
			if req.ProgressFn != nil {
				progressFn = func(processed, total int64) {
					if total > 0 {
						pct := int(processed * 100 / total)
						req.ProgressFn(pct, fmt.Sprintf("加密中... %d%%", pct))
					}
				}
			}
			result, encryptError = aes.EncryptToFileWithProgress(req.InputPath, req.OutputPath, KeyTypeRandom, nil, nil, chunkSize, progressFn)
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

	chunkSize := fc.bufferSizeMB * 1024 * 1024

	// 创建进度包装器
	var progressFn ProgressFunc
	if req.ProgressFn != nil {
		progressFn = func(processed, total int64) {
			if total > 0 {
				pct := int(processed * 100 / total)
				req.ProgressFn(pct, fmt.Sprintf("解密中... %d%%", pct))
			}
		}
	}

	switch detectedAlgo {
	case AlgorithmOTP:
		if req.KeyPath == "" {
			return nil, fmt.Errorf("OTP解密需要密钥文件")
		}
		otp := NewOTPAlgorithm()
		_, decryptError = otp.DecryptFromFileWithProgress(req.InputPath, req.OutputPath, req.KeyPath, chunkSize, progressFn)

	case AlgorithmAES256:
		aes := NewAES256Algorithm()
		if req.KeyType == KeyTypePassword || req.Password != "" {
			if req.Password == "" {
				return nil, fmt.Errorf("密码模式需要密码")
			}
			_, decryptError = aes.DecryptFromFileWithProgress(req.InputPath, req.OutputPath,
				KeyTypePassword, nil, nil, nil, []byte(req.Password), nil, chunkSize, progressFn)
		} else {
			if req.KeyPath == "" {
				return nil, fmt.Errorf("需要密钥文件路径")
			}
			// 尝试智能加载密钥（兼容 Python 的 .key 文件和 Go 的 key+iv+tag 格式）
			key, iv, tag, err := fc.loadKeyForAES(req.KeyPath)
			if err != nil {
				return nil, fmt.Errorf("加载密钥文件失败: %w", err)
			}
			_, decryptError = aes.DecryptFromFileWithProgress(req.InputPath, req.OutputPath,
				KeyTypeRandom, key, iv, tag, nil, nil, chunkSize, progressFn)
		}

	default:
		return nil, fmt.Errorf("不支持的算法类型")
	}

	if decryptError != nil {
		return nil, fmt.Errorf("解密失败: %w", decryptError)
	}

	return &DecryptionResponse{Success: true}, nil
}

// loadKeyForAES 智能加载AES密钥文件
// 先尝试 LoadKeyWithIVTag (Go内部格式 60字节)，失败则尝试 LoadKey (纯key格式)
func (fc *FileCipher) loadKeyForAES(path string) (key, iv, tag []byte, err error) {
	// 优先尝试完整格式（key+iv+tag）
	key, iv, tag, err = LoadKeyWithIVTag(path)
	if err == nil {
		return key, iv, tag, nil
	}
	// 回退到纯key格式
	key, err = LoadKey(path)
	if err != nil {
		return nil, nil, nil, err
	}
	// 纯key格式不包含iv/tag，这些需要从加密文件中读取
	return key, nil, nil, nil
}

// SaveKey 保存密钥到文件
// 支持多种格式：十六进制 (.txt) 或 二进制 (.bin/.key)
func (fc *FileCipher) SaveKey(key []byte, outputDir, baseName string, algorithm AlgorithmType, keyType KeyType, format string) (string, error) {
	if len(key) == 0 {
		return "", fmt.Errorf("密钥为空")
	}

	// 确保输出目录存在
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("创建输出目录失败: %w", err)
	}

	// 使用统一的路径生成函数
	keyFilePath := BuildKeyFilePath(outputDir, baseName, algorithm, keyType, format)

	var err error
	if algorithm == AlgorithmOTP {
		if format == "binary" {
			// 二进制格式
			err = os.WriteFile(keyFilePath, key, 0600)
		} else {
			// 十六进制文本格式（默认）
			hexStr := fmt.Sprintf("%x", key)
			err = os.WriteFile(keyFilePath, []byte(hexStr), 0600)
		}
	} else {
		// AES 密钥保存为纯二进制
		err = SaveKeyFile(keyFilePath, key)
	}

	if err != nil {
		return "", fmt.Errorf("保存密钥文件失败: %w", err)
	}

	return keyFilePath, nil
}

// SaveAESKeyAll 保存AES密钥（包含key+iv+tag的完整格式）
func (fc *FileCipher) SaveAESKeyAll(key, iv, tag []byte, outputDir, baseName string) (string, error) {
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("创建输出目录失败: %w", err)
	}

	keyFilePath := BuildKeyFilePath(outputDir, baseName, AlgorithmAES256, KeyTypeRandom, "")

	if err := SaveKeyFileWithIVTag(keyFilePath, key, iv, tag); err != nil {
		return "", fmt.Errorf("保存密钥文件失败: %w", err)
	}

	return keyFilePath, nil
}

// detectAlgorithmByFileHeader 通过文件头检测算法类型
// 只读取前4字节，避免大文件完全加载到内存
func detectAlgorithmByFileHeader(filePath string) AlgorithmType {
	f, err := os.Open(filePath)
	if err != nil {
		return AlgorithmAES256
	}
	defer f.Close()

	header := make([]byte, 4)
	if _, err := io.ReadFull(f, header); err != nil {
		return AlgorithmAES256
	}

	// 检查 AES 文件头: b'AES\x00', b'AES\x01', b'AES\x02'
	if header[0] == 'A' && header[1] == 'E' && header[2] == 'S' {
		if header[3] == 0x00 || header[3] == 0x01 || header[3] == 0x02 {
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