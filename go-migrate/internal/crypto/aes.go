package crypto

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"io"
	"os"

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

// EncryptWithRandomKey 使用随机密钥进行AES256-GCM加密（内存模式）
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

// EncryptWithPassword 使用密码进行AES256-GCM加密（内存模式）
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

// EncryptToFile 随机密钥模式加密到文件（支持大文件流式处理）
// 文件格式: [b'AES\x00' 4B] [IV 12B] [密文 N B] [Tag 16B]
func (a *AES256Algorithm) EncryptToFile(inputFile, outputFile string, keyType KeyType, password, salt []byte) (*EncryptionResult, error) {
	var key, iv []byte
	var kt KeyType

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

	// 流式加密：先读全部明文，GCM加密，再写入
	// GCM本身不支持真正的流式（需要finalize获得tag），但读入内存后一次性加密是正确的
	plaintext, err := os.ReadFile(inputFile)
	if err != nil {
		return nil, fmt.Errorf("读取输入文件失败: %w", err)
	}

	sealed := gcm.Seal(nil, iv, plaintext, nil)
	tagStart := len(sealed) - AESTagLength
	ciphertext := sealed[:tagStart]
	tag := sealed[tagStart:]

	// 写入文件
	outFile, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("创建输出文件失败: %w", err)
	}
	defer outFile.Close()

	if kt == KeyTypePassword {
		outFile.Write([]byte{'A', 'E', 'S', 0x01})
		outFile.Write([]byte{byte(len(salt))})
		outFile.Write(salt)
	} else {
		outFile.Write([]byte{'A', 'E', 'S', 0x00})
	}
	outFile.Write(iv)
	outFile.Write(ciphertext)
	outFile.Write(tag)

	return &EncryptionResult{
		Key:       key,
		IV:        iv,
		Tag:       tag,
		Salt:      salt,
		Algorithm: AlgorithmAES256,
		KeyType:   kt,
	}, nil
}

// DecryptFromFile 通用AES文件解密（自动检测格式）
func (a *AES256Algorithm) DecryptFromFile(inputFile, outputFile string,
	keyType KeyType, key, iv, tag, password, salt []byte) (*DecryptionResult, error) {

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

// SaveKeyFile 保存密钥文件（包含key+iv+tag，用于传输）
// 格式: [magic 4B "K001"] [key 32B] [iv 12B] [tag 16B] = 64 bytes
func SaveKeyFile(path string, key, iv, tag []byte) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	// 魔数 + 版本号
	f.Write([]byte{'K', '0', '0', '1'})
	f.Write(key)  // 32 bytes
	f.Write(iv)   // 12 bytes
	f.Write(tag)  // 16 bytes
	return nil
}

// LoadKeyFile 加载密钥文件
func LoadKeyFile(path string) (key, iv, tag []byte, err error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, nil, fmt.Errorf("读取密钥文件失败: %w", err)
	}
	if len(data) < 4+32+12+16 {
		return nil, nil, nil, fmt.Errorf("密钥文件格式错误（大小=%d）", len(data))
	}
	if data[0] != 'K' || data[1] != '0' || data[2] != '0' || data[3] != '1' {
		return nil, nil, nil, fmt.Errorf("密钥文件格式错误（魔数不匹配）")
	}
	key = data[4:36]
	iv = data[36:48]
	tag = data[48:64]
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

	f.Seek(currentPos, io.SeekStart)
	ciphertext := make([]byte, ciphertextSize)
	if _, err := io.ReadFull(f, ciphertext); err != nil {
		return nil, nil, fmt.Errorf("读取密文失败: %w", err)
	}

	info.Tag = make([]byte, AESTagLength)
	f.Seek(-int64(AESTagLength), io.SeekEnd)
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

// 保留 encoding/binary 引用
var _ = binary.NativeEndian