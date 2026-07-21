package crypto

import (
	"crypto/rand"
	"fmt"
	"io"
	"os"
)

// OTPAlgorithm OTP（一次性密码本）算法实现
type OTPAlgorithm struct{}

// NewOTPAlgorithm 创建OTP算法实例
func NewOTPAlgorithm() *OTPAlgorithm {
	return &OTPAlgorithm{}
}

// AlgorithmType 返回算法类型
func (o *OTPAlgorithm) AlgorithmType() AlgorithmType {
	return AlgorithmOTP
}

// Encrypt OTP加密（内存模式）
// 生成与明文等长的随机密钥，进行XOR加密
func (o *OTPAlgorithm) Encrypt(plaintext []byte) (*EncryptionResult, error) {
	// 生成随机密钥
	key := make([]byte, len(plaintext))
	if _, err := rand.Read(key); err != nil {
		return nil, fmt.Errorf("生成OTP密钥失败: %w", err)
	}

	// XOR加密
	ciphertext := make([]byte, len(plaintext))
	for i := range plaintext {
		ciphertext[i] = plaintext[i] ^ key[i]
	}

	return &EncryptionResult{
		Ciphertext: ciphertext,
		Key:        key,
		Algorithm:  AlgorithmOTP,
		KeyType:    KeyTypeRandom,
	}, nil
}

// Decrypt OTP解密（内存模式）
func (o *OTPAlgorithm) Decrypt(ciphertext, key []byte) (*DecryptionResult, error) {
	if len(ciphertext) != len(key) {
		return nil, fmt.Errorf("密文长度(%d)与密钥长度(%d)不匹配", len(ciphertext), len(key))
	}

	// XOR解密
	plaintext := make([]byte, len(ciphertext))
	for i := range ciphertext {
		plaintext[i] = ciphertext[i] ^ key[i]
	}

	return &DecryptionResult{
		Plaintext: plaintext,
		Algorithm:  AlgorithmOTP,
	}, nil
}

// EncryptToFile OTP分块加密到文件
// inputFile: 输入文件路径
// outputFile: 输出文件路径
// chunkSize: 块大小（字节）
func (o *OTPAlgorithm) EncryptToFile(inputFile, outputFile string, chunkSize int) (*EncryptionResult, error) {
	fileSize, err := getFileSize(inputFile)
	if err != nil {
		return nil, err
	}

	// 生成与文件等长的随机密钥
	key := make([]byte, fileSize)
	if _, err := rand.Read(key); err != nil {
		return nil, fmt.Errorf("生成OTP密钥失败: %w", err)
	}

	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	// 分块读取、加密、写入
	buf := make([]byte, chunkSize)
	totalRead := 0
	for {
		n, err := inFile.Read(buf)
		if n > 0 {
			keyChunk := key[totalRead : totalRead+n]
			encryptedChunk := xorBytes(buf[:n], keyChunk)
			if _, writeErr := outFile.Write(encryptedChunk); writeErr != nil {
				return nil, fmt.Errorf("写入加密数据失败: %w", writeErr)
			}
			totalRead += n
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", err)
		}
	}

	return &EncryptionResult{
		Ciphertext: nil, // 大文件不保存完整密文
		Key:        key,
		Algorithm:  AlgorithmOTP,
		KeyType:    KeyTypeRandom,
	}, nil
}

// DecryptFromFile OTP分块解密从文件
func (o *OTPAlgorithm) DecryptFromFile(inputFile, outputFile string, key []byte, chunkSize int) (*DecryptionResult, error) {
	fileSize, err := getFileSize(inputFile)
	if err != nil {
		return nil, err
	}

	if len(key) != int(fileSize) {
		return nil, fmt.Errorf("密钥长度(%d)与文件大小(%d)不匹配", len(key), fileSize)
	}

	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	// 分块读取、解密、写入
	buf := make([]byte, chunkSize)
	totalRead := 0
	for {
		n, err := inFile.Read(buf)
		if n > 0 {
			keyChunk := key[totalRead : totalRead+n]
			plainChunk := xorBytes(buf[:n], keyChunk)
			if _, writeErr := outFile.Write(plainChunk); writeErr != nil {
				return nil, fmt.Errorf("写入解密数据失败: %w", writeErr)
			}
			totalRead += n
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", err)
		}
	}

	return &DecryptionResult{
		Plaintext: nil, // 大文件不保存完整明文
		Algorithm:  AlgorithmOTP,
	}, nil
}

// xorBytes 两个字节切片的XOR运算
func xorBytes(a, b []byte) []byte {
	result := make([]byte, len(a))
	for i := range a {
		result[i] = a[i] ^ b[i]
	}
	return result
}

// getFileSize 获取文件大小
func getFileSize(path string) (int64, error) {
	info, err := os.Stat(path)
	if err != nil {
		return 0, fmt.Errorf("获取文件信息失败: %w", err)
	}
	return info.Size(), nil
}