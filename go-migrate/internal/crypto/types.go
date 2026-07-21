package crypto

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
	AESKeyLength = 32 // AES256 密钥 32 字节
	AESIVLength  = 12 // GCM 推荐 12 字节 IV
	AESTagLength = 16 // GCM 认证标签 16 字节
	PBKDF2Iters  = 100000
	SaltLength   = 16
)