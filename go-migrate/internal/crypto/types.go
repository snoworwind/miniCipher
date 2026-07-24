package crypto

import (
	"fmt"
	"path/filepath"
	"runtime"
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

// EncryptionResult holds the result of an encryption operation.
// For large files, Ciphertext may be nil (streamed to disk).
// Callers should clear Key, IV, and Tag when no longer needed.
type EncryptionResult struct {
	Ciphertext []byte        // 密文（大文件加密后可能为空）
	Key        []byte        // 密钥（随机密钥模式）
	IV         []byte        // 初始化向量（AES模式）
	Tag        []byte        // 认证标签（GCM模式）
	Salt       []byte        // 盐值（密码模式）
	Algorithm  AlgorithmType // 算法类型
	KeyType    KeyType       // 密钥类型
}

// DecryptionResult holds the result of a decryption operation.
// For large files, Plaintext may be nil (streamed to disk).
type DecryptionResult struct {
	Plaintext []byte        // 明文（大文件解密后可能为空）
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

// ClearBytes 清零字节切片，用于清除内存中的敏感数据（密码、密钥等）
func ClearBytes(b []byte) {
	for i := range b {
		b[i] = 0
	}
	// Prevent the compiler from optimizing away the zeroing loop.
	// Without this barrier the compiler may prove that b is dead after
	// the function returns and eliminate the writes entirely.
	runtime.KeepAlive(b)
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