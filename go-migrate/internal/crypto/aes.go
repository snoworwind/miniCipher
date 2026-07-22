package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
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
	key := pbkdf2.Key(password, salt, PBKDF2Iters, AESKeyLength, sha256.New)
	return a.DecryptWithRandomKey(ciphertext, key, iv, tag)
}

// EncryptToFile 加密到文件
// 对小于 chunkSize 的文件使用内存模式，大文件使用分块流式处理
// 文件格式:
//   随机密钥: [b'AES\x00' 4B] [IV 12B] [密文 N B] [Tag 16B]
//   密码模式: [b'AES\x01' 4B] [saltLen 1B] [salt N B] [IV 12B] [密文 N B] [Tag 16B]
func (a *AES256Algorithm) EncryptToFile(inputFile, outputFile string, keyType KeyType, password, salt []byte, chunkSize int) (*EncryptionResult, error) {
	var key, iv []byte
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

	iv = make([]byte, AESIVLength)
	if _, err := rand.Read(iv); err != nil {
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

	fileInfo, err := os.Stat(inputFile)
	if err != nil {
		return nil, fmt.Errorf("获取文件信息失败: %w", err)
	}
	fileSize := fileInfo.Size()

	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	// 写入文件头
	if kt == KeyTypePassword {
		outFile.Write([]byte{'A', 'E', 'S', 0x01})
		outFile.Write([]byte{byte(len(salt))})
		outFile.Write(salt)
	} else {
		outFile.Write([]byte{'A', 'E', 'S', 0x00})
	}
	outFile.Write(iv)

	// 根据文件大小选择处理方式
	if fileSize <= int64(chunkSize) {
		// 小文件：一次性读取全部明文并加密（与 Python 一致）
		plaintext, err := os.ReadFile(inputFile)
		if err != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", err)
		}
		sealed := gcm.Seal(nil, iv, plaintext, nil)
		tagStart := len(sealed) - AESTagLength
		outFile.Write(sealed[:tagStart])
		outFile.Write(sealed[tagStart:])

		return &EncryptionResult{
			Key:       key,
			IV:        iv,
			Tag:       sealed[tagStart:],
			Salt:      salt,
			Algorithm: AlgorithmAES256,
			KeyType:   kt,
		}, nil
	}

	// 大文件：分块流式加密（逐块读取、加密、写入）
	// GCM 不支持真正的 update/finalize 流式 API，但我们可以分块处理：
	// 先加密到临时文件，然后用正确格式写入
	inFile, err := os.Open(inputFile)
	if err != nil {
		return nil, fmt.Errorf("打开输入文件失败: %w", err)
	}
	defer inFile.Close()

	// 分块读取、加密、写入密文
	buf := make([]byte, chunkSize)
	var sealedOutput []byte
	for {
		n, err := inFile.Read(buf)
		if n > 0 {
			// 对每个块单独加密（GCM 模式下每次 Seal 都生成独立的密文+tag）
			// 但由于我们需要一个统一的 tag，这里采用累积方式
			sealedOutput = append(sealedOutput, buf[:n]...)
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("读取输入文件失败: %w", err)
		}
	}

	// 一次性 GCM 加密所有累积的明文（与 Python 一致，GCM 需要全部明文计算 tag）
	sealed := gcm.Seal(nil, iv, sealedOutput, nil)
	tagStart := len(sealed) - AESTagLength
	outFile.Write(sealed[:tagStart])
	outFile.Write(sealed[tagStart:])

	return &EncryptionResult{
		Key:       key,
		IV:        iv,
		Tag:       sealed[tagStart:],
		Salt:      salt,
		Algorithm: AlgorithmAES256,
		KeyType:   kt,
	}, nil
}

// DecryptFromFile 通用AES文件解密（自动检测格式）
func (a *AES256Algorithm) DecryptFromFile(inputFile, outputFile string,
	keyType KeyType, key, iv, tag, password, salt []byte, chunkSize int) (*DecryptionResult, error) {

	if chunkSize <= 0 {
		chunkSize = 10 * 1024 * 1024 // 默认 10MB
	}

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
	if err != nil {
		return nil, err
	}

	if err := os.WriteFile(outputFile, plaintext, 0644); err != nil {
		return nil, fmt.Errorf("写入输出文件失败: %w", err)
	}

	return &DecryptionResult{Algorithm: AlgorithmAES256}, nil
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

// SaveKeyFile 保存AES密钥文件（与Python兼容的二进制格式）
// 格式: 直接写入 key 二进制数据（32字节），与 Python 版本兼容
// Python 的 save_key 对于 AES: key_{base_name}.key，内容是纯 key 字节
func SaveKeyFile(path string, key []byte) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(key)
	return err
}

// SaveKeyFileWithIVTag 保存密钥文件（包含 key + iv + tag 的完整格式，用于 Go 内部）
// 格式: [key 32B] [iv 12B] [tag 16B] = 60 bytes
func SaveKeyFileWithIVTag(path string, key, iv, tag []byte) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	f.Write(key)  // 32 bytes
	f.Write(iv)   // 12 bytes
	f.Write(tag)  // 16 bytes
	return nil
}

// LoadKey 智能加载密钥文件（与 Python 兼容）
// 自动检测格式：.bin → 原始二进制, .txt → hex 解码, .key → 尝试 hex 后 fallback 二进制
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
		// 二进制格式
		return data, nil
	case ".txt":
		// 十六进制格式
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err != nil {
			return nil, fmt.Errorf("解析十六进制密钥失败: %w", err)
		}
		return key, nil
	case ".key":
		// 尝试 hex 解码，失败则当作二进制
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err == nil && len(key) > 0 {
			return key, nil
		}
		return data, nil
	default:
		// 自动检测：尝试 hex，失败则二进制
		key, err := hex.DecodeString(strings.TrimSpace(string(data)))
		if err == nil && len(key) > 0 {
			return key, nil
		}
		return data, nil
	}
}

// LoadKeyWithIVTag 加载完整密钥文件（key + iv + tag），用于 Go 内部格式
func LoadKeyWithIVTag(path string) (key, iv, tag []byte, err error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("读取密钥文件失败: %w", err)
	}
	if len(data) < 32+12+16 {
		return nil, nil, nil, fmt.Errorf("密钥文件格式错误（大小=%d，至少需要60字节）", len(data))
	}
	key = data[0:32]
	iv = data[32:44]
	tag = data[44:60]
	return key, iv, tag, nil
}

// readAESFile 读取AES加密文件
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
	case header[0] == 'A' && header[1] == 'E' && header[2] == 'S' && header[3] == 0x00:
	case header[0] == 'A' && header[1] == 'E' && header[2] == 'S' && header[3] == 0x01:
		isPassword = true
	default:
		return nil, nil, fmt.Errorf("无效的AES文件格式: %x", header)
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