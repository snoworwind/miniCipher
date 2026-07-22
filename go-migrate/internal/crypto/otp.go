package crypto

import (
	"crypto/rand"
	"encoding/hex"
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
		Algorithm: AlgorithmOTP,
	}, nil
}

// EncryptToFile OTP流式加密到文件
// 密钥分块生成并直接写入密钥文件，不保留完整密钥在内存中
// keyFilePath: 密钥文件输出路径（hex 文本格式）
func (o *OTPAlgorithm) EncryptToFile(inputFile, outputFile, keyFilePath string, chunkSize int) (*EncryptionResult, error) {
	return o.EncryptToFileWithProgress(inputFile, outputFile, keyFilePath, chunkSize, nil)
}

// EncryptToFileWithProgress OTP流式加密到文件（带进度回调）
func (o *OTPAlgorithm) EncryptToFileWithProgress(inputFile, outputFile, keyFilePath string, chunkSize int, progress ProgressFunc) (*EncryptionResult, error) {
	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	// 获取文件总大小
	fileInfo, err := inFile.Stat()
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}
	totalSize := fileInfo.Size()

	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	keyFile, err := os.Create(keyFilePath)
	if err != nil {
		return nil, fmt.Errorf("创建密钥文件失败: %w", err)
	}
	defer keyFile.Close()

	// 分块生成密钥、读取、加密、写入
	// 不保留完整密钥在内存中
	buf := make([]byte, chunkSize)
	keyBuf := make([]byte, chunkSize)
	hexBuf := make([]byte, chunkSize*2) // hex 编码缓冲区（每个字节 = 2 hex 字符）
	var totalProcessed int64

	for {
		n, readErr := inFile.Read(buf)
		if n > 0 {
			// 分块生成随机密钥
			chunkKey := keyBuf[:n]
			if _, randErr := rand.Read(chunkKey); randErr != nil {
				return nil, fmt.Errorf("生成OTP密钥块失败: %w", randErr)
			}

			// XOR 加密
			encryptedChunk := xorBytes(buf[:n], chunkKey)
			if _, writeErr := outFile.Write(encryptedChunk); writeErr != nil {
				return nil, fmt.Errorf("写入加密数据失败: %w", writeErr)
			}

			// 将密钥块以 hex 格式追加到密钥文件
			hexLen := hex.Encode(hexBuf, chunkKey)
			if _, writeErr := keyFile.Write(hexBuf[:hexLen]); writeErr != nil {
				return nil, fmt.Errorf("写入密钥文件失败: %w", writeErr)
			}

			totalProcessed += int64(n)
			if progress != nil {
				progress(totalProcessed, totalSize)
			}
		}
		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", readErr)
		}
	}

	return &EncryptionResult{
		Ciphertext: nil, // 大文件不保存完整密文
		Key:        nil, // 密钥已写入独立文件，不在内存中保留
		Algorithm:  AlgorithmOTP,
		KeyType:    KeyTypeRandom,
	}, nil
}

// DecryptFromFile OTP流式解密从文件
// 分块读取密钥文件，不将完整密钥加载到内存
// keyPath: 密钥文件路径（支持 hex 文本 .txt 和二进制 .bin 格式）
func (o *OTPAlgorithm) DecryptFromFile(inputFile, outputFile, keyPath string, chunkSize int) (*DecryptionResult, error) {
	return o.DecryptFromFileWithProgress(inputFile, outputFile, keyPath, chunkSize, nil)
}

// DecryptFromFileWithProgress OTP流式解密从文件（带进度回调）
func (o *OTPAlgorithm) DecryptFromFileWithProgress(inputFile, outputFile, keyPath string, chunkSize int, progress ProgressFunc) (*DecryptionResult, error) {
	fileSize, err := getFileSize(inputFile)
	if err != nil {
		return nil, err
	}

	// 判断密钥文件格式并验证大小
	keyFormat, keyByteSize, err := detectOTPKeyFormat(keyPath)
	if err != nil {
		return nil, err
	}
	if keyByteSize != fileSize {
		return nil, fmt.Errorf("密钥长度(%d)与文件大小(%d)不匹配", keyByteSize, fileSize)
	}

	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	keyFile, err := os.Open(keyPath)
	if err != nil {
		return nil, fmt.Errorf("打开密钥文件失败: %w", err)
	}
	defer keyFile.Close()

	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	// 分块读取、解密、写入
	buf := make([]byte, chunkSize)
	hexKeyBuf := make([]byte, chunkSize*2) // hex 格式时使用
	var totalProcessed int64

	for {
		n, readErr := inFile.Read(buf)
		if n > 0 {
			// 分块读取密钥
			var keyChunk []byte
			if keyFormat == otpKeyHex {
				// hex 文本格式：读取 2*n 个字符，解码为 n 字节
				hexToRead := n * 2
				if hexToRead > len(hexKeyBuf) {
					hexKeyBuf = make([]byte, hexToRead)
				}
				hexBytes := hexKeyBuf[:hexToRead]
				if _, kerr := io.ReadFull(keyFile, hexBytes); kerr != nil {
					return nil, fmt.Errorf("读取密钥文件失败: %w", kerr)
				}
				keyChunk = make([]byte, n)
				if _, decErr := hex.Decode(keyChunk, hexBytes); decErr != nil {
					return nil, fmt.Errorf("解码hex密钥失败: %w", decErr)
				}
			} else {
				// 二进制格式：直接读取 n 字节
				keyChunk = make([]byte, n)
				if _, kerr := io.ReadFull(keyFile, keyChunk); kerr != nil {
					return nil, fmt.Errorf("读取密钥文件失败: %w", kerr)
				}
			}

			plainChunk := xorBytes(buf[:n], keyChunk)
			if _, writeErr := outFile.Write(plainChunk); writeErr != nil {
				return nil, fmt.Errorf("写入解密数据失败: %w", writeErr)
			}

			totalProcessed += int64(n)
			if progress != nil {
				progress(totalProcessed, fileSize)
			}
		}
		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", readErr)
		}
	}

	return &DecryptionResult{
		Plaintext: nil, // 大文件不保存完整明文
		Algorithm: AlgorithmOTP,
	}, nil
}

// otpKeyFormat OTP密钥文件格式
type otpKeyFormat int

const (
	otpKeyBinary otpKeyFormat = iota
	otpKeyHex
)

// detectOTPKeyFormat 检测OTP密钥文件格式并返回密钥字节数
// 返回 (格式, 密钥字节数, 错误)
func detectOTPKeyFormat(keyPath string) (otpKeyFormat, int64, error) {
	info, err := os.Stat(keyPath)
	if err != nil {
		return 0, 0, fmt.Errorf("读取密钥文件信息失败: %w", err)
	}
	fileSize := info.Size()

	// 读前几个字节判断格式
	f, err := os.Open(keyPath)
	if err != nil {
		return 0, 0, fmt.Errorf("打开密钥文件失败: %w", err)
	}
	defer f.Close()

	// 尝试读少量数据判断是否为 hex
	peek := make([]byte, 128)
	if fileSize < int64(len(peek)) {
		peek = make([]byte, fileSize)
	}
	n, _ := f.Read(peek)
	peek = peek[:n]

	// 检查是否全为 hex 字符（0-9, a-f, A-F, 可能包含换行符）
	isHex := true
	hexCharCount := 0
	for _, b := range peek {
		if b == '\n' || b == '\r' || b == ' ' || b == '\t' {
			continue
		}
		if (b >= '0' && b <= '9') || (b >= 'a' && b <= 'f') || (b >= 'A' && b <= 'F') {
			hexCharCount++
		} else {
			isHex = false
			break
		}
	}

	if isHex && hexCharCount > 0 {
		// hex 格式：每2个hex字符 = 1字节密钥
		// 去除换行等空白字符估算实际hex字符总数
		// 由于文件可能很大，估算：文件大小 ≈ 2*密钥字节数 + 少量换行
		keyBytes := fileSize / 2
		return otpKeyHex, keyBytes, nil
	}

	// 二进制格式
	return otpKeyBinary, fileSize, nil
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