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
// keyFilePath: 密钥文件输出路径（根据扩展名自动选择 hex 或 binary 格式）
func (o *OTPAlgorithm) EncryptToFile(inputFile, outputFile, keyFilePath string, chunkSize int) (*EncryptionResult, error) {
	return o.EncryptToFileWithProgress(inputFile, outputFile, keyFilePath, chunkSize, nil)
}

// EncryptToFileWithProgress OTP流式加密到文件（带进度回调）
// keyFilePath 扩展名决定密钥格式: .bin → 二进制, 其他 → hex 文本
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

	// 写入 OTP 文件头，用于算法自动检测
	if _, err := outFile.Write([]byte{'O', 'T', 'P', 0x00}); err != nil {
		return nil, fmt.Errorf("写入OTP文件头失败: %w", err)
	}

	keyFile, err := os.OpenFile(keyFilePath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return nil, fmt.Errorf("创建密钥文件失败: %w", err)
	}
	defer keyFile.Close()

	// 根据密钥文件扩展名选择格式
	useBinaryKey := false
	if len(keyFilePath) > 4 && keyFilePath[len(keyFilePath)-4:] == ".bin" {
		useBinaryKey = true
	}

	// 分块生成密钥、读取、加密、写入
	// 不保留完整密钥在内存中
	buf := make([]byte, chunkSize)
	keyBuf := make([]byte, chunkSize)
	var hexBuf []byte
	if !useBinaryKey {
		hexBuf = make([]byte, chunkSize*2) // hex 编码缓冲区（每个字节 = 2 hex 字符）
	}
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

			// 将密钥块写入密钥文件（根据格式选择 hex 或 binary）
			if useBinaryKey {
				if _, writeErr := keyFile.Write(chunkKey); writeErr != nil {
					return nil, fmt.Errorf("写入密钥文件失败: %w", writeErr)
				}
			} else {
				hexLen := hex.Encode(hexBuf, chunkKey)
				if _, writeErr := keyFile.Write(hexBuf[:hexLen]); writeErr != nil {
					return nil, fmt.Errorf("写入密钥文件失败: %w", writeErr)
				}
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

	// 清零缓冲区以清除内存中的敏感数据
	for i := range buf {
		buf[i] = 0
	}
	for i := range keyBuf {
		keyBuf[i] = 0
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
	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	// Detect and skip OTP header if present (new format: OTP\x00)
	// Also supports old format files that have no header
	header := make([]byte, 4)
	hasHeader := false
	if n, _ := io.ReadFull(inFile, header); n == 4 {
		if header[0] == 'O' && header[1] == 'T' && header[2] == 'P' && header[3] == 0x00 {
			hasHeader = true
		}
	}
	if !hasHeader {
		// Old format: no header, rewind to beginning
		if _, err := inFile.Seek(0, io.SeekStart); err != nil {
			return nil, fmt.Errorf("定位文件开头失败: %w", err)
		}
	}

	// The ciphertext size is file size minus header (if present)
	fileInfo, err := inFile.Stat()
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}
	ciphertextSize := fileInfo.Size()
	if hasHeader {
		ciphertextSize -= 4
	}

	// 判断密钥文件格式并验证大小
	keyFormat, keyByteSize, err := detectOTPKeyFormat(keyPath)
	if err != nil {
		return nil, err
	}
	if keyByteSize != ciphertextSize {
		return nil, fmt.Errorf("密钥长度(%d)与文件大小(%d)不匹配", keyByteSize, ciphertextSize)
	}

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
				progress(totalProcessed, ciphertextSize)
			}
		}
		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", readErr)
		}
	}

	// 清零缓冲区以清除内存中的敏感数据
	for i := range buf {
		buf[i] = 0
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
// 优先根据文件扩展名判断，其次使用内容试探法。
// 对于 hex 格式（.txt 及试探法检测到的 hex 文件），读取实际内容计算
// hex 字符数，以正确处理文件末尾的空白字符（换行、空格等）。
// 返回 (格式, 密钥字节数, 错误)
func detectOTPKeyFormat(keyPath string) (otpKeyFormat, int64, error) {
	info, err := os.Stat(keyPath)
	if err != nil {
		return 0, 0, fmt.Errorf("读取密钥文件信息失败: %w", err)
	}
	fileSize := info.Size()

	// 优先根据文件扩展名判断
	ext := ""
	if len(keyPath) > 4 {
		ext = keyPath[len(keyPath)-4:]
	}
	if ext == ".bin" {
		return otpKeyBinary, fileSize, nil
	}

	// 对于 .txt 和未知扩展名的文件，读取内容进行精确检测
	f, err := os.Open(keyPath)
	if err != nil {
		return 0, 0, fmt.Errorf("打开密钥文件失败: %w", err)
	}
	defer f.Close()

	// 读取整个文件内容以精确计算 hex 字符数
	// 对于 .txt 格式，文件大小 = 明文长度 × 2，通常不大
	data, err := io.ReadAll(f)
	if err != nil {
		// 无法读取则根据扩展名做最佳猜测
		if ext == ".txt" {
			return otpKeyHex, fileSize / 2, nil
		}
		return otpKeyBinary, fileSize, nil
	}

	// 统计有效的 hex 字符数（跳过空白字符）
	hexCharCount := 0
	allHex := true
	for _, b := range data {
		if b == '\n' || b == '\r' || b == ' ' || b == '\t' {
			continue
		}
		if (b >= '0' && b <= '9') || (b >= 'a' && b <= 'f') || (b >= 'A' && b <= 'F') {
			hexCharCount++
		} else {
			allHex = false
			break
		}
	}

	// 如果是 .txt 扩展名且全部为 hex 字符，按 hex 处理
	if ext == ".txt" && allHex && hexCharCount > 0 {
		return otpKeyHex, int64(hexCharCount) / 2, nil
	}

	// 对于未知扩展名：只有当所有非空白字符都是 hex 且 hex 字符数占比足够高时才视为 hex
	// 这样可以避免将恰好含 hex 字节的二进制文件误判为 hex
	if allHex && hexCharCount > 0 {
		totalNonSpace := 0
		for _, b := range data {
			if b != '\n' && b != '\r' && b != ' ' && b != '\t' {
				totalNonSpace++
			}
		}
		// 至少 80% 的非空白字符是 hex 才视为 hex 格式
		// （全部非空白字符都应该是 hex 因为 allHex=true）
		if totalNonSpace > 0 && hexCharCount == totalNonSpace {
			return otpKeyHex, int64(hexCharCount) / 2, nil
		}
	}

	// .txt 文件但内容不是 hex → 视为二进制
	// 未知扩展名且内容不是 hex → 视为二进制
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
