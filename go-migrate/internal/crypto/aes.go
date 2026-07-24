package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"strings"

	"golang.org/x/crypto/pbkdf2"
)

// AES256Algorithm AES256-GCM算法实现
type AES256Algorithm struct{}

// NewAES256Algorithm 创建AES256算法实例
func NewAES256Algorithm() *AES256Algorithm {
	return &AES256Algorithm{}
}

// AlgorithmType 返回算法类型
func (a *AES256Algorithm) AlgorithmType() AlgorithmType {
	return AlgorithmAES256
}

// EncryptWithRandomKey 使用随机密钥进行AES256-GCM加密（内存模式-小文件）
func (a *AES256Algorithm) EncryptWithRandomKey(plaintext []byte) (*EncryptionResult, error) {
	key := make([]byte, AESKeyLength)
	if _, err := rand.Read(key); err != nil {
		return nil, fmt.Errorf("生成随机密钥失败: %w", err)
	}
	iv := make([]byte, AESIVLength)
	if _, err := rand.Read(iv); err != nil {
		return nil, fmt.Errorf("生成随机IV失败: %w", err)
	}
	return a.encrypt(plaintext, key, iv, nil, KeyTypeRandom)
}

// EncryptWithPassword 使用密码进行AES256-GCM加密（内存模式-小文件）
func (a *AES256Algorithm) EncryptWithPassword(plaintext, password []byte, salt []byte) (*EncryptionResult, error) {
	if len(password) == 0 {
		return nil, fmt.Errorf("密码不能为空")
	}
	if salt == nil {
		salt = make([]byte, SaltLength)
		if _, err := rand.Read(salt); err != nil {
			return nil, fmt.Errorf("生成随机salt失败: %w", err)
		}
	}
	key := pbkdf2.Key(password, salt, PBKDF2Iters, AESKeyLength, sha256.New)
	iv := make([]byte, AESIVLength)
	if _, err := rand.Read(iv); err != nil {
		return nil, fmt.Errorf("生成随机IV失败: %w", err)
	}
	return a.encrypt(plaintext, key, iv, salt, KeyTypePassword)
}

func (a *AES256Algorithm) encrypt(plaintext, key, iv, salt []byte, kt KeyType) (*EncryptionResult, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("创建AES密码器失败: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("创建GCM模式失败: %w", err)
	}
	// GCM Seal 返回 ciphertext + tag
	sealed := gcm.Seal(nil, iv, plaintext, nil)
	tagStart := len(sealed) - AESTagLength
	return &EncryptionResult{
		Ciphertext: sealed[:tagStart],
		Key:        key,
		IV:         iv,
		Tag:        sealed[tagStart:],
		Salt:       salt,
		Algorithm:  AlgorithmAES256,
		KeyType:    kt,
	}, nil
}

// DecryptWithRandomKey 使用随机密钥解密
func (a *AES256Algorithm) DecryptWithRandomKey(ciphertext, key, iv, tag []byte) (*DecryptionResult, error) {
	if len(tag) != AESTagLength {
		return nil, fmt.Errorf("认证标签长度不正确，应为%d字节，实际%d字节", AESTagLength, len(tag))
	}
	plaintext, err := a.decryptBytes(ciphertext, key, iv, tag)
	if err != nil {
		return nil, err
	}
	return &DecryptionResult{Plaintext: plaintext, Algorithm: AlgorithmAES256}, nil
}

// DecryptWithPassword 使用密码解密
func (a *AES256Algorithm) DecryptWithPassword(ciphertext, password, salt, iv, tag []byte) (*DecryptionResult, error) {
	if len(tag) != AESTagLength {
		return nil, fmt.Errorf("认证标签长度不正确，应为%d字节，实际%d字节", AESTagLength, len(tag))
	}
	// Try current iteration count first, fall back to legacy for backward compatibility
	key := pbkdf2.Key(password, salt, PBKDF2Iters, AESKeyLength, sha256.New)
	plaintext, err := a.decryptBytes(ciphertext, key, iv, tag)
	if err != nil {
		key = pbkdf2.Key(password, salt, PBKDF2ItersLegacy, AESKeyLength, sha256.New)
		plaintext, err = a.decryptBytes(ciphertext, key, iv, tag)
		if err != nil {
			return nil, err
		}
	}
	return &DecryptionResult{Plaintext: plaintext, Algorithm: AlgorithmAES256}, nil
}

// EncryptToFile 加密到文件（使用分块 GCM 流式格式）
// 始终使用新格式 AES\x02，内存占用 ≤ ~2×chunkSize
// 文件格式:
//
//	[AES\x02 4B]                    ← 分块版本标识
//	[saltLen 1B] [salt NB]          ← 密码模式（随机密钥模式跳过）
//	[baseIV 12B]                    ← 基础 IV
//	[chunkSize 4B]                  ← 块大小
//	[chunk1: ciphertextLen(4B) | ciphertext(Var) | tag(16B)]
//	[chunk2: ciphertextLen(4B) | ciphertext(Var) | tag(16B)]
//	...
func (a *AES256Algorithm) EncryptToFile(inputFile, outputFile string, keyType KeyType, password, salt []byte, chunkSize int) (*EncryptionResult, error) {
	return a.EncryptToFileWithProgress(inputFile, outputFile, keyType, password, salt, chunkSize, nil)
}

// EncryptToFileWithProgress 带进度回调的加密到文件
func (a *AES256Algorithm) EncryptToFileWithProgress(inputFile, outputFile string, keyType KeyType, password, salt []byte, chunkSize int, progress ProgressFunc) (*EncryptionResult, error) {
	var key []byte
	var kt KeyType

	if chunkSize <= 0 {
		chunkSize = 10 * 1024 * 1024 // 默认 10MB
	}

	if keyType == KeyTypePassword {
		if salt == nil {
			salt = make([]byte, SaltLength)
			if _, err := rand.Read(salt); err != nil {
				return nil, fmt.Errorf("生成随机salt失败: %w", err)
			}
		}
		key = pbkdf2.Key(password, salt, PBKDF2Iters, AESKeyLength, sha256.New)
		kt = KeyTypePassword
	} else {
		key = make([]byte, AESKeyLength)
		if _, err := rand.Read(key); err != nil {
			return nil, fmt.Errorf("生成随机密钥失败: %w", err)
		}
		kt = KeyTypeRandom
	}

	// 生成基础 IV
	baseIV := make([]byte, AESIVLength)
	if _, err := rand.Read(baseIV); err != nil {
		return nil, fmt.Errorf("生成随机IV失败: %w", err)
	}

	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("创建AES密码器失败: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("创建GCM模式失败: %w", err)
	}

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

	// 写入文件头
	if _, err := outFile.Write([]byte{'A', 'E', 'S', byte(AESVersionChunked)}); err != nil {
		return nil, fmt.Errorf("写入文件头失败: %w", err)
	}
	if kt == KeyTypePassword {
		if _, err := outFile.Write([]byte{byte(len(salt))}); err != nil {
			return nil, fmt.Errorf("写入盐值长度失败: %w", err)
		}
		if _, err := outFile.Write(salt); err != nil {
			return nil, fmt.Errorf("写入盐值失败: %w", err)
		}
	}
	if _, err := outFile.Write(baseIV); err != nil {
		return nil, fmt.Errorf("写入IV失败: %w", err)
	}

	// 写入 chunkSize（4字节 big-endian）
	chunkSizeBuf := make([]byte, 4)
	binary.BigEndian.PutUint32(chunkSizeBuf, uint32(chunkSize))
	if _, err := outFile.Write(chunkSizeBuf); err != nil {
		return nil, fmt.Errorf("写入块大小失败: %w", err)
	}

	// 分块读取、加密、写入
	buf := make([]byte, chunkSize)
	chunkIndex := uint64(0)
	lenBuf := make([]byte, 4)
	var totalProcessed int64

	for {
		n, readErr := inFile.Read(buf)
		if n > 0 {
			// 生成当前块的 IV = baseIV XOR chunkIndex
			chunkIV := makeChunkIV(baseIV, chunkIndex)

			// GCM Seal
			sealed := gcm.Seal(nil, chunkIV, buf[:n], nil)
			// sealed = ciphertext + tag (tag 在最后 16 字节)

			// 写入块长度（仅密文长度，不含 tag）
			ciphertextLen := len(sealed) - AESTagLength
			binary.BigEndian.PutUint32(lenBuf, uint32(ciphertextLen))
			if _, err := outFile.Write(lenBuf); err != nil {
				return nil, fmt.Errorf("写入块长度失败: %w", err)
			}

			// 写入密文 + tag
			if _, err := outFile.Write(sealed); err != nil {
				return nil, fmt.Errorf("写入密文块失败: %w", err)
			}

			chunkIndex++
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
		Key:       key,
		IV:        baseIV,
		Tag:       nil, // 分块模式无统一 tag
		Salt:      salt,
		Algorithm: AlgorithmAES256,
		KeyType:   kt,
	}, nil
}

// DecryptFromFile 通用AES文件解密（自动检测格式）
// - 旧格式 (AES\x00 / AES\x01)：全量加载解密
// - 新格式 (AES\x02)：分块流式解密，内存 ≤ ~chunkSize
func (a *AES256Algorithm) DecryptFromFile(inputFile, outputFile string,
	keyType KeyType, key, iv, tag, password, salt []byte, chunkSize int) (*DecryptionResult, error) {
	return a.DecryptFromFileWithProgress(inputFile, outputFile, keyType, key, iv, tag, password, salt, chunkSize, nil)
}

// DecryptFromFileWithProgress 带进度回调的解密
func (a *AES256Algorithm) DecryptFromFileWithProgress(inputFile, outputFile string,
	keyType KeyType, key, iv, tag, password, salt []byte, chunkSize int, progress ProgressFunc) (*DecryptionResult, error) {

	if chunkSize <= 0 {
		chunkSize = 10 * 1024 * 1024 // 默认 10MB
	}

	// 读取文件头以判断格式版本
	f, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开文件失败: %w", err)
	}

	header := make([]byte, 4)
	if _, err := io.ReadFull(f, header); err != nil {
		f.Close()
		return nil, fmt.Errorf("读取文件头失败: %w", err)
	}

	version := AESFileVersion(header[3])
	if version.IsLegacyFormat() {
		f.Close()
		return a.decryptLegacy(inputFile, outputFile, keyType, key, iv, tag, password, salt, chunkSize, progress)
	}
	return a.decryptChunked(f, outputFile, keyType, key, password, chunkSize, progress)
}

// decryptLegacy 旧格式解密（全量加载）
func (a *AES256Algorithm) decryptLegacy(inputFile, outputFile string,
	keyType KeyType, key, iv, tag, password, salt []byte, chunkSize int, progress ProgressFunc) (*DecryptionResult, error) {

	info, ciphertext, err := readAESFile(inputFile)
	if err != nil {
		return nil, err
	}

	useIV := iv
	if useIV == nil {
		useIV = info.IV
	}
	useTag := tag
	if useTag == nil {
		useTag = info.Tag
	}
	useSalt := salt
	if useSalt == nil {
		useSalt = info.Salt
	}

	var finalKey []byte
	if keyType == KeyTypePassword {
		if useSalt == nil {
			return nil, fmt.Errorf("密码模式解密需要salt")
		}
		finalKey = pbkdf2.Key(password, useSalt, PBKDF2Iters, AESKeyLength, sha256.New)
	} else {
		finalKey = key
	}

	plaintext, err := a.decryptBytes(ciphertext, finalKey, useIV, useTag)
	if err != nil && keyType == KeyTypePassword {
		// Fall back to legacy iteration count for backward compatibility
		finalKey = pbkdf2.Key(password, useSalt, PBKDF2ItersLegacy, AESKeyLength, sha256.New)
		plaintext, err = a.decryptBytes(ciphertext, finalKey, useIV, useTag)
	}
	if err != nil {
		return nil, err
	}
	// 立即释放密文内存
	ciphertext = nil

	// 分块写入输出文件
	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	totalLen := int64(len(plaintext))
	writeChunkSize := chunkSize
	if writeChunkSize > len(plaintext) {
		writeChunkSize = len(plaintext)
	}
	var written int64
	for offset := 0; offset < len(plaintext); offset += writeChunkSize {
		end := offset + writeChunkSize
		if end > len(plaintext) {
			end = len(plaintext)
		}
		if _, err := outFile.Write(plaintext[offset:end]); err != nil {
			return nil, fmt.Errorf("写入输出文件失败: %w", err)
		}
		written += int64(end - offset)
		if progress != nil {
			progress(written, totalLen)
		}
	}

	return &DecryptionResult{Algorithm: AlgorithmAES256}, nil
}

// decryptChunked 分块 GCM 流式解密
// 内存占用 ≈ chunkSize（每个块独立解密后立即写入输出文件）
// For password mode, automatically falls back to legacy PBKDF2 iteration count
// if decryption fails with the current count (backward compatibility).
func (a *AES256Algorithm) decryptChunked(f *os.File, outputFile string,
	keyType KeyType, key, password []byte, chunkSize int, progress ProgressFunc) (*DecryptionResult, error) {
	defer f.Close()

	// 获取文件总大小用于进度估算
	fileInfo, err := f.Stat()
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}
	totalSize := fileInfo.Size()

	// Read header fields that are common to both attempts
	type headerData struct {
		salt           []byte
		baseIV         []byte
		fileChunkSize  uint32
	}
	var hdr headerData

	// 读取密码模式的 salt
	var saltForDerivation []byte
	if keyType == KeyTypePassword {
		saltLenBuf := make([]byte, 1)
		if _, err := io.ReadFull(f, saltLenBuf); err != nil {
			return nil, fmt.Errorf("读取盐值长度失败: %w", err)
		}
		hdr.salt = make([]byte, saltLenBuf[0])
		if _, err := io.ReadFull(f, hdr.salt); err != nil {
			return nil, fmt.Errorf("读取盐值失败: %w", err)
		}
		saltForDerivation = hdr.salt
	}

	// 读取基础 IV
	hdr.baseIV = make([]byte, AESIVLength)
	if _, err := io.ReadFull(f, hdr.baseIV); err != nil {
		return nil, fmt.Errorf("读取IV失败: %w", err)
	}

	// 读取文件中的 chunkSize
	fileChunkSizeBuf := make([]byte, 4)
	if _, err := io.ReadFull(f, fileChunkSizeBuf); err != nil {
		return nil, fmt.Errorf("读取块大小失败: %w", err)
	}
	hdr.fileChunkSize = binary.BigEndian.Uint32(fileChunkSizeBuf)
	_ = hdr.fileChunkSize

	// Save position right before chunk data for potential retry
	chunkDataStart, _ := f.Seek(0, io.SeekCurrent)

	// Try decryption with current iteration count; fall back to legacy on failure
	itersToTry := []int{PBKDF2Iters}
	if keyType == KeyTypePassword {
		itersToTry = append(itersToTry, PBKDF2ItersLegacy)
	}

	var lastErr error
	for attempt, iters := range itersToTry {
		if attempt > 0 {
			// Retry: seek back to start of chunk data
			if _, err := f.Seek(chunkDataStart, io.SeekStart); err != nil {
				return nil, fmt.Errorf("重试定位失败: %w", err)
			}
		}

		var finalKey []byte
		if keyType == KeyTypePassword {
			finalKey = pbkdf2.Key(password, saltForDerivation, iters, AESKeyLength, sha256.New)
		} else {
			finalKey = key
		}

		block, err := aes.NewCipher(finalKey)
		if err != nil {
			return nil, fmt.Errorf("创建AES密码器失败: %w", err)
		}
		gcm, err := cipher.NewGCM(block)
		if err != nil {
			return nil, fmt.Errorf("创建GCM模式失败: %w", err)
		}

		outFile, err := os.Create(outputFile)
		if err != nil {
			return nil, fmt.Errorf("创建输出文件失败: %w", err)
		}

		// 分块解密
		chunkIndex := uint64(0)
		lenBuf := make([]byte, 4)
		tryCount := 0
		reportEvery := 10
		var totalProcessed int64
		decryptOK := true

		for {
			if _, err := io.ReadFull(f, lenBuf); err != nil {
				if err == io.EOF || err == io.ErrUnexpectedEOF {
					break
				}
				decryptOK = false
				lastErr = fmt.Errorf("读取块长度失败: %w", err)
				break
			}
			ciphertextLen := binary.BigEndian.Uint32(lenBuf)

			// Sanity check: chunk ciphertext must not exceed expected bounds
			// (plaintext + GCM overhead). Reject obviously malformed input.
			if ciphertextLen > uint32(chunkSize)+AESTagLength {
				decryptOK = false
				lastErr = fmt.Errorf("块 %d 长度异常 (%d 字节)，文件可能已损坏", chunkIndex, ciphertextLen)
				break
			}

			chunkBuf := make([]byte, int(ciphertextLen)+AESTagLength)
			if _, err := io.ReadFull(f, chunkBuf); err != nil {
				decryptOK = false
				lastErr = fmt.Errorf("读取密文块失败: %w", err)
				break
			}

			chunkIV := makeChunkIV(hdr.baseIV, chunkIndex)
			plaintext, err := gcm.Open(nil, chunkIV, chunkBuf, nil)
			if err != nil {
				decryptOK = false
				lastErr = fmt.Errorf("块 %d 解密失败（密钥或文件可能已损坏）: %w", chunkIndex, err)
				break
			}

			if _, writeErr := outFile.Write(plaintext); writeErr != nil {
				outFile.Close()
				return nil, fmt.Errorf("写入输出文件失败: %w", writeErr)
			}

			chunkIndex++
			totalProcessed += int64(len(plaintext))
			tryCount++

			if progress != nil && tryCount%reportEvery == 0 {
				progress(totalProcessed, totalSize)
			}
		}

		outFile.Close()

		if decryptOK {
			// 最后一次进度汇报
			if progress != nil {
				progress(totalProcessed, totalSize)
			}
			return &DecryptionResult{Algorithm: AlgorithmAES256}, nil
		}

		// Clean up partial output file before retry
		os.Remove(outputFile)

		// If not password mode or last attempt, don't retry
		if keyType != KeyTypePassword || attempt == len(itersToTry)-1 {
			return nil, lastErr
		}
		// Otherwise retry with legacy iteration count
	}

	return nil, lastErr
}

func (a *AES256Algorithm) decryptBytes(ciphertext, key, iv, tag []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, fmt.Errorf("创建AES密码器失败: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("创建GCM模式失败: %w", err)
	}
	full := make([]byte, len(ciphertext)+len(tag))
	copy(full, ciphertext)
	copy(full[len(ciphertext):], tag)
	return gcm.Open(nil, iv, full, nil)
}

// makeChunkIV 生成分块 IV：baseIV XOR chunkIndex（大端序，低8字节参与XOR）
func makeChunkIV(baseIV []byte, chunkIndex uint64) []byte {
	chunkIV := make([]byte, AESIVLength)
	copy(chunkIV, baseIV)
	// 将 chunkIndex 写入后 8 字节进行 XOR
	idxBuf := make([]byte, 8)
	binary.BigEndian.PutUint64(idxBuf, chunkIndex)
	// XOR 到 IV 的后部（IV 12 字节，从 offset 4 开始 XOR 8 字节）
	for i := 0; i < 8; i++ {
		chunkIV[4+i] ^= idxBuf[i]
	}
	return chunkIV
}

// SaveKeyFile 保存AES密钥文件（与Python兼容的二进制格式）
// 格式: 直接写入 key 二进制数据（32字节），与 Python 版本兼容
func SaveKeyFile(path string, key []byte) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(key)
	return err
}

// SaveKeyFileWithIVTag 保存密钥文件（包含 key + iv + tag 的完整格式）
// 格式:
//
//	有 tag: [key 32B] [iv 12B] [tag 16B] = 60 bytes
//	无 tag: [key 32B] [iv 12B]              = 44 bytes（分块 GCM 格式）
func SaveKeyFileWithIVTag(path string, key, iv, tag []byte) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(key); err != nil {
		return fmt.Errorf("写入密钥失败: %w", err)
	}
	if _, err := f.Write(iv); err != nil {
		return fmt.Errorf("写入IV失败: %w", err)
	}
	if len(tag) == AESTagLength {
		if _, err := f.Write(tag); err != nil {
			return fmt.Errorf("写入标签失败: %w", err)
		}
	}
	return nil
}

// LoadKey 智能加载密钥文件（与 Python 兼容）
// 自动检测格式：.bin → 原始二进制, .txt → hex 解码, .key → 尝试 hex 后 fallback 二进制
// 当 .key 后缀文件为 60 字节时，返回完整 32 字节 key（含 IV/Tag 的完整格式由 LoadKeyWithIVTag 处理）
func LoadKey(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取密钥文件失败: %w", err)
	}

	if len(data) == 0 {
		return nil, fmt.Errorf("密钥文件为空")
	}

	// 根据扩展名判断格式
	ext := ""
	if len(path) > 4 {
		ext = path[len(path)-4:]
	}

	switch ext {
	case ".bin":
		return data, nil
	case ".txt":
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err != nil {
			return nil, fmt.Errorf("解析十六进制密钥失败: %w", err)
		}
		return key, nil
	case ".key":
		// .key 文件可能是 32 字节纯key 或 60 字节完整格式
		// LoadKey 只返回纯 key；完整格式由 LoadKeyWithIVTag 处理
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err == nil && len(key) > 0 {
			return key, nil
		}
		if len(data) >= 32 {
			return data[:32], nil
		}
		return data, nil
	default:
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err == nil && len(key) > 0 {
			return key, nil
		}
		return data, nil
	}
}

// LoadKeyWithIVTag 加载完整密钥文件（key + iv + tag），用于 Go 内部格式
// 兼容两种格式:
//   - 60 bytes: key(32) + iv(12) + tag(16)
//   - 44 bytes: key(32) + iv(12)（分块 GCM 无全局 tag）
func LoadKeyWithIVTag(path string) (key, iv, tag []byte, err error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("读取密钥文件失败: %w", err)
	}
	if len(data) < 32+12 {
		return nil, nil, nil, fmt.Errorf("密钥文件格式错误（大小=%d，至少需要44字节）", len(data))
	}
	key = data[0:32]
	iv = data[32:44]
	if len(data) >= 60 {
		tag = data[44:60]
	}
	// tag 可能为 nil（分块格式）
	return key, iv, tag, nil
}

// readAESFile 读取AES加密文件（仅用于旧格式）
func readAESFile(filePath string) (*AESFileInfo, []byte, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return nil, nil, fmt.Errorf("打开文件失败: %w", err)
	}
	defer f.Close()

	header := make([]byte, 4)
	if _, err := io.ReadFull(f, header); err != nil {
		return nil, nil, fmt.Errorf("读取文件头失败: %w", err)
	}

	info := &AESFileInfo{Header: header}
	isPassword := false

	switch {
	case header[0] == 'A' && header[1] == 'E' && header[2] == 'S' && header[3] == byte(AESVersionRandomKey):
	case header[0] == 'A' && header[1] == 'E' && header[2] == 'S' && header[3] == byte(AESVersionPassword):
		isPassword = true
	default:
		return nil, nil, fmt.Errorf("无效的旧AES文件格式: %x", header)
	}

	if isPassword {
		saltLenBuf := make([]byte, 1)
		if _, err := io.ReadFull(f, saltLenBuf); err != nil {
			return nil, nil, fmt.Errorf("读取盐值长度失败: %w", err)
		}
		saltLen := int(saltLenBuf[0])
		info.Salt = make([]byte, saltLen)
		if _, err := io.ReadFull(f, info.Salt); err != nil {
			return nil, nil, fmt.Errorf("读取盐值失败: %w", err)
		}
	}

	info.IV = make([]byte, AESIVLength)
	if _, err := io.ReadFull(f, info.IV); err != nil {
		return nil, nil, fmt.Errorf("读取IV失败: %w", err)
	}

	currentPos := int64(4)
	if isPassword {
		currentPos = 4 + 1 + int64(len(info.Salt))
	}
	currentPos += int64(AESIVLength)

	fileInfo, err := f.Stat()
	if err != nil {
		return nil, nil, fmt.Errorf("获取文件信息失败: %w", err)
	}
	fileSize := fileInfo.Size()

	ciphertextSize := fileSize - currentPos - int64(AESTagLength)
	if ciphertextSize < 0 {
		return nil, nil, fmt.Errorf("文件损坏：缺少认证标签")
	}

	ciphertext := make([]byte, ciphertextSize)
	if _, err := io.ReadFull(f, ciphertext); err != nil {
		return nil, nil, fmt.Errorf("读取密文失败: %w", err)
	}

	info.Tag = make([]byte, AESTagLength)
	if _, err := f.Seek(-int64(AESTagLength), io.SeekEnd); err != nil {
		return nil, nil, fmt.Errorf("定位认证标签失败: %w", err)
	}
	if _, err := io.ReadFull(f, info.Tag); err != nil {
		return nil, nil, fmt.Errorf("读取认证标签失败: %w", err)
	}

	return info, ciphertext, nil
}

// AESFileInfo AES文件解析信息
type AESFileInfo struct {
	Header []byte
	IV     []byte
	Salt   []byte
	Tag    []byte
}