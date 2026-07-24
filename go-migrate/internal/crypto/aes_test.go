package crypto

import (
	"os"
	"path/filepath"
	"testing"
)

func TestAES256EncryptDecryptRandomKey(t *testing.T) {
	aes := NewAES256Algorithm()
	plaintext := []byte("Hello, MiniCipher! 你好，加密世界！This is a test message.")

	result, err := aes.EncryptWithRandomKey(plaintext)
	if err != nil {
		t.Fatalf("加密失败: %v", err)
	}

	if len(result.Key) != AESKeyLength {
		t.Errorf("密钥长度错误: got %d, want %d", len(result.Key), AESKeyLength)
	}
	if len(result.IV) != AESIVLength {
		t.Errorf("IV长度错误: got %d, want %d", len(result.IV), AESIVLength)
	}
	if len(result.Tag) != AESTagLength {
		t.Errorf("Tag长度错误: got %d, want %d", len(result.Tag), AESTagLength)
	}

	decrypted, err := aes.DecryptWithRandomKey(result.Ciphertext, result.Key, result.IV, result.Tag)
	if err != nil {
		t.Fatalf("解密失败: %v", err)
	}

	if string(decrypted.Plaintext) != string(plaintext) {
		t.Errorf("解密内容不匹配: got %q, want %q", string(decrypted.Plaintext), string(plaintext))
	}
}

func TestAES256EncryptDecryptPassword(t *testing.T) {
	aes := NewAES256Algorithm()
	plaintext := []byte("Password protected data")
	password := []byte("MySecurePassword123!")

	result, err := aes.EncryptWithPassword(plaintext, password, nil)
	if err != nil {
		t.Fatalf("密码加密失败: %v", err)
	}

	if result.Salt == nil {
		t.Error("盐值不能为空")
	}

	decrypted, err := aes.DecryptWithPassword(result.Ciphertext, password, result.Salt, result.IV, result.Tag)
	if err != nil {
		t.Fatalf("密码解密失败: %v", err)
	}

	if string(decrypted.Plaintext) != string(plaintext) {
		t.Errorf("解密内容不匹配")
	}
}

func TestAES256EncryptDecryptFile(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "aes_test")
	if err != nil {
		t.Fatalf("创建临时目录失败: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	inputPath := filepath.Join(tmpDir, "test.txt")
	encPath := filepath.Join(tmpDir, "test.txt.enc")
	decPath := filepath.Join(tmpDir, "test_decrypted.txt")

	testContent := []byte("This is a file encryption test!\n第二行中文内容。\nMultiple lines of data.")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	aes := NewAES256Algorithm()

	// 加密
	result, err := aes.EncryptToFile(inputPath, encPath, KeyTypeRandom, nil, nil, 1*1024*1024)
	if err != nil {
		t.Fatalf("文件加密失败: %v", err)
	}

	if result.Key == nil {
		t.Error("加密结果缺少密钥")
	}

	// 保存密钥文件
	keyPath := filepath.Join(tmpDir, "test.key")
	if err := SaveKeyFileWithIVTag(keyPath, result.Key, result.IV, result.Tag); err != nil {
		t.Fatalf("保存密钥文件失败: %v", err)
	}

	// 解密
	_, err = aes.DecryptFromFile(encPath, decPath, KeyTypeRandom, result.Key, result.IV, result.Tag, nil, nil, 1*1024*1024)
	if err != nil {
		t.Fatalf("文件解密失败: %v", err)
	}

	// 验证
	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}

	if string(decContent) != string(testContent) {
		t.Errorf("解密内容不匹配: got %q, want %q", string(decContent), string(testContent))
	}
}

func TestAES256EncryptDecryptFilePassword(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "aes_test_password")
	if err != nil {
		t.Fatalf("创建临时目录失败: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	inputPath := filepath.Join(tmpDir, "test.txt")
	encPath := filepath.Join(tmpDir, "test.txt.enc")
	decPath := filepath.Join(tmpDir, "test_decrypted.txt")

	testContent := []byte("Password-protected file content.")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	aes := NewAES256Algorithm()
	password := []byte("SecurePass123!")

	// 加密
	result, err := aes.EncryptToFile(inputPath, encPath, KeyTypePassword, password, nil, 1*1024*1024)
	if err != nil {
		t.Fatalf("密码文件加密失败: %v", err)
	}

	if result.Salt == nil {
		t.Error("密码模式加密结果缺少盐值")
	}

	// 解密
	_, err = aes.DecryptFromFile(encPath, decPath, KeyTypePassword, nil, nil, nil, password, result.Salt, 1*1024*1024)
	if err != nil {
		t.Fatalf("密码文件解密失败: %v", err)
	}

	// 验证
	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}

	if string(decContent) != string(testContent) {
		t.Errorf("解密内容不匹配")
	}
}

func TestSaveLoadKeyWithIVTag(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "key_test")
	if err != nil {
		t.Fatalf("创建临时目录失败: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	key := make([]byte, AESKeyLength)
	iv := make([]byte, AESIVLength)
	tag := make([]byte, AESTagLength)

	for i := range key {
		key[i] = byte(i)
	}
	for i := range iv {
		iv[i] = byte(i + 32)
	}
	for i := range tag {
		tag[i] = byte(i + 44)
	}

	keyPath := filepath.Join(tmpDir, "test.key")

	// 保存完整格式
	if err := SaveKeyFileWithIVTag(keyPath, key, iv, tag); err != nil {
		t.Fatalf("保存密钥文件失败: %v", err)
	}

	// 检查文件大小
	info, err := os.Stat(keyPath)
	if err != nil {
		t.Fatalf("检查密钥文件失败: %v", err)
	}
	if info.Size() != 60 {
		t.Errorf("密钥文件大小错误: got %d, want 60", info.Size())
	}

	// 加载
	k, iv2, tg2, err := LoadKeyWithIVTag(keyPath)
	if err != nil {
		t.Fatalf("加载密钥文件失败: %v", err)
	}
	if len(k) != AESKeyLength {
		t.Errorf("加载的密钥长度错误: %d", len(k))
	}
	if len(iv2) != AESIVLength {
		t.Errorf("加载的IV长度错误: %d", len(iv2))
	}
	if len(tg2) != AESTagLength {
		t.Errorf("加载的Tag长度错误: %d", len(tg2))
	}
}

func TestLoadKeyFormats(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "key_format_test")
	if err != nil {
		t.Fatalf("创建临时目录失败: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	key := make([]byte, 32)
	for i := range key {
		key[i] = byte(i)
	}
	expectedHex := "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"

	// 测试纯二进制 .key
	keyPath := filepath.Join(tmpDir, "test.key")
	if err := SaveKeyFile(keyPath, key); err != nil {
		t.Fatalf("保存纯key失败: %v", err)
	}
	k, err := LoadKey(keyPath)
	if err != nil {
		t.Fatalf("加载纯key失败: %v", err)
	}
	if len(k) != 32 {
		t.Errorf("加载纯key长度错误: %d", len(k))
	}

	// 测试hex .txt
	txtPath := filepath.Join(tmpDir, "test.txt")
	if err := os.WriteFile(txtPath, []byte(expectedHex), 0644); err != nil {
		t.Fatalf("写入hex文件失败: %v", err)
	}
	k2, err := LoadKey(txtPath)
	if err != nil {
		t.Fatalf("加载hex key失败: %v", err)
	}
	if len(k2) != 32 {
		t.Errorf("加载hex key长度错误: %d", len(k2))
	}
}

func TestValidatePassword(t *testing.T) {
	fc := NewFileCipher(10, 8, true)

	tests := []struct {
		name     string
		password []byte
		valid    bool
	}{
		{"空密码", []byte(""), false},
		{"太短", []byte("Ab1"), false},
		{"缺少数字", []byte("Abcdefgh"), false},
		{"缺少大写", []byte("abc12345"), false},
		{"缺少小写", []byte("ABC12345"), false},
		{"有效强密码", []byte("MyPass123"), true},
		{"刚刚好", []byte("Abcd1234"), true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			valid, _ := fc.ValidatePassword(tt.password)
			if valid != tt.valid {
				t.Errorf("密码 %s: got valid=%v, want %v", tt.password, valid, tt.valid)
			}
		})
	}
}