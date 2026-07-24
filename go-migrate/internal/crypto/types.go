package crypto

import (
	"fmt"
	"path/filepath"
)

// AlgorithmType 加密算法类型
type AlgorithmType string

const (
	AlgorithmOTP    AlgorithmType = "OTP"
	AlgorithmAES256 AlgorithmType = "AES256"
)

// KeyType 密钥类型
type KeyType string

const (
	KeyTypeRandom   KeyType = "random"
	KeyTypePassword KeyType = "password"
)

// ProgressFunc 进度回调函数类型
// processed: 已处理字节数, total: 总字节数 (-1 表示未知)
type ProgressFunc func(processed, total int64)

// EncryptionResult 加密结果
type EncryptionResult struct {
	Ciphertext []byte        // 密文（大文件加密后可能为空）
	Key        []byte        // 密钥（随机密钥模式）
	IV         []byte        // 初始化向量（AES模式）
	Tag        []byte        // 认证标签（GCM模式）
	Salt       []byte        // 盐值（密码模式）
	Algorithm  AlgorithmType // 算法类型
	KeyType    KeyType       // 密钥类型
}

// DecryptionResult 解密结果
type DecryptionResult struct {
	Plaintext []byte        // 明文
	Algorithm AlgorithmType // 算法类型
}

// 常量定义
const (
	AESKeyLength  = 32 // AES256 密钥 32 字节
	AESIVLength   = 12 // GCM 推荐 12 字节 IV
	AESTagLength  = 16 // GCM 认证标签 16 字节
	PBKDF2Iters       = 600000 // OWASP recommended minimum for PBKDF2-SHA256
	PBKDF2ItersLegacy = 100000 // backward compatibility for files encrypted with older versions
	SaltLength    = 16
	ChunkLenBytes = 4 // 分块长度字段占用字节数
)

// AESFileVersion AES 文件格式版本
type AESFileVersion byte

const (
	AESVersionRandomKey AESFileVersion = 0x00 // 原始格式：随机密钥
	AESVersionPassword  AESFileVersion = 0x01 // 原始格式：密码模式
	AESVersionChunked   AESFileVersion = 0x02 // 分块 GCM 流式格式
)

// IsLegacyFormat 判断是否为旧格式（需要全量加载）
func (v AESFileVersion) IsLegacyFormat() bool {
	return v == AESVersionRandomKey || v == AESVersionPassword
}

// BuildKeyFilePath 生成统一的密钥文件路径
// dir: 输出目录, baseName: 原始文件名（不含路径）, algorithm: 算法类型, keyType: 密钥类型, otpFormat: OTP 密钥格式 ("hex"→.txt, "binary"→.bin)
func BuildKeyFilePath(dir, baseName string, algorithm AlgorithmType, keyType KeyType, otpFormat string) string {
	switch algorithm {
	case AlgorithmOTP:
		if otpFormat == "binary" {
			return filepath.Join(dir, fmt.Sprintf("key_%s.bin", baseName))
		}
		return filepath.Join(dir, fmt.Sprintf("key_%s.txt", baseName))
	case AlgorithmAES256:
		if keyType == KeyTypeRandom {
			return filepath.Join(dir, fmt.Sprintf("key_%s.key", baseName))
		}
		// 密码模式不需要密钥文件
		return ""
	default:
		return filepath.Join(dir, fmt.Sprintf("key_%s.key", baseName))
	}
}