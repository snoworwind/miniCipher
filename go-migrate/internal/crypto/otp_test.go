package crypto

import (
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestOTPEncryptDecrypt(t *testing.T) {
	otp := NewOTPAlgorithm()
	plaintext := []byte("Hello, OTP! 一次性密码本测试数据。")

	result, err := otp.Encrypt(plaintext)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	if len(result.Key) != len(plaintext) {
		t.Errorf("密钥长度错误: got %d, want %d", len(result.Key), len(plaintext))
	}
	if len(result.Ciphertext) != len(plaintext) {
		t.Errorf("密文长度错误: got %d, want %d", len(result.Ciphertext), len(plaintext))
	}

	decrypted, err := otp.Decrypt(result.Ciphertext, result.Key)
	if err != nil {
		t.Fatalf("OTP解密失败: %v", err)
	}

	if string(decrypted.Plaintext) != string(plaintext) {
		t.Errorf("解密内容不匹配: got %q, want %q", string(decrypted.Plaintext), string(plaintext))
	}
}

func TestOTPDecryptKeyLengthMismatch(t *testing.T) {
	otp := NewOTPAlgorithm()
	ciphertext := []byte("short")
	key := []byte("toolongkey")

	_, err := otp.Decrypt(ciphertext, key)
	if err == nil {
		t.Error("密钥长度不匹配应返回错误")
	}
}

func TestOTPEncryptDecryptEmpty(t *testing.T) {
	otp := NewOTPAlgorithm()
	plaintext := []byte{}

	result, err := otp.Encrypt(plaintext)
	if err != nil {
		t.Fatalf("空数据OTP加密失败: %v", err)
	}

	if len(result.Key) != 0 {
		t.Errorf("空数据密钥长度应为0: got %d", len(result.Key))
	}

	decrypted, err := otp.Decrypt(result.Ciphertext, result.Key)
	if err != nil {
		t.Fatalf("空数据OTP解密失败: %v", err)
	}

	if len(decrypted.Plaintext) != 0 {
		t.Errorf("空数据解密结果应为空: got %d bytes", len(decrypted.Plaintext))
	}
}

func TestOTPEncryptDecryptFileSmall(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	keyPath := filepath.Join(tmpDir, "test.bin.key.txt")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := []byte("Small OTP file test content.")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()

	// 加密
	result, err := otp.EncryptToFile(inputPath, encPath, keyPath, 4*1024) // small chunk to test multi-chunk
	if err != nil {
		t.Fatalf("OTP文件加密失败: %v", err)
	}

	if result.Algorithm != AlgorithmOTP {
		t.Errorf("算法类型错误: got %s", result.Algorithm)
	}

	// 验证密钥文件存在且有正确大小（hex 格式 = 2×文件长度）
	keyInfo, err := os.Stat(keyPath)
	if err != nil {
		t.Fatalf("密钥文件不存在: %v", err)
	}
	expectedKeySize := int64(len(testContent) * 2) // hex encoding
	if keyInfo.Size() != expectedKeySize {
		t.Errorf("密钥文件大小错误: got %d, want %d", keyInfo.Size(), expectedKeySize)
	}

	// 解密
	_, err = otp.DecryptFromFile(encPath, decPath, keyPath, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP文件解密失败: %v", err)
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

func TestOTPEncryptDecryptFileLargeChunk(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test_large.bin")
	encPath := filepath.Join(tmpDir, "test_large.bin.enc")
	keyPath := filepath.Join(tmpDir, "test_large.bin.key.txt")
	decPath := filepath.Join(tmpDir, "test_large_decrypted.bin")

	// Create slightly larger than default chunk test data
	testContent := make([]byte, 1024*100) // 100KB
	for i := range testContent {
		testContent[i] = byte(i % 256)
	}
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()

	// 加密（使用较小的chunk size测试多块场景）
	_, err := otp.EncryptToFile(inputPath, encPath, keyPath, 1024) // 1KB chunks
	if err != nil {
		t.Fatalf("OTP文件加密失败: %v", err)
	}

	// 解密
	_, err = otp.DecryptFromFile(encPath, decPath, keyPath, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP文件解密失败: %v", err)
	}

	// 验证二进制内容
	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}

	if len(decContent) != len(testContent) {
		t.Fatalf("解密文件大小不匹配: got %d, want %d", len(decContent), len(testContent))
	}

	for i := range testContent {
		if decContent[i] != testContent[i] {
			t.Errorf("解密内容在偏移 %d 处不匹配: got 0x%02x, want 0x%02x", i, decContent[i], testContent[i])
			break
		}
	}
}

func TestOTPBinaryKeyFormat(t *testing.T) {
	// Note: OTP EncryptToFile currently always writes keys in hex format
	// regardless of file extension. The .bin extension detection in
	// detectOTPKeyFormat would treat it as raw binary and fail to decrypt.
	// In practice, BuildKeyFilePath with format="hex" creates .txt files
	// and format="binary" creates .bin files. Binary format key output
	// is not yet implemented in EncryptToFile.
	// This test verifies detection works for manually-created binary key files.

	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := []byte("Binary key format test!")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()

	// Use hex key path so the key is saved in hex format
	keyPathHex := filepath.Join(tmpDir, "key_test.txt")
	_, err := otp.EncryptToFile(inputPath, encPath, keyPathHex, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	// Read the hex key and convert to raw binary, then save as .bin
	keyData, err := os.ReadFile(keyPathHex)
	if err != nil {
		t.Fatalf("读取密钥文件失败: %v", err)
	}
	binKey, err := hex.DecodeString(strings.TrimSpace(string(keyData)))
	if err != nil {
		t.Fatalf("解码hex密钥失败: %v", err)
	}
	keyPathBin := filepath.Join(tmpDir, "key_test.bin")
	if err := os.WriteFile(keyPathBin, binKey, 0644); err != nil {
		t.Fatalf("写入二进制密钥文件失败: %v", err)
	}

	// Verify .bin key file has correct size
	keyInfo, err := os.Stat(keyPathBin)
	if err != nil {
		t.Fatalf("密钥文件不存在: %v", err)
	}
	if keyInfo.Size() != int64(len(testContent)) {
		t.Errorf("二进制密钥文件大小错误: got %d, want %d", keyInfo.Size(), len(testContent))
	}

	// Decrypt with binary key
	_, err = otp.DecryptFromFile(encPath, decPath, keyPathBin, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP二进制密钥解密失败: %v", err)
	}

	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}
	if string(decContent) != string(testContent) {
		t.Errorf("解密内容不匹配")
	}
}
func TestOTPKeyFormatDetection(t *testing.T) {
	tmpDir := t.TempDir()

	// Create a hex key file (.txt)
	hexPath := filepath.Join(tmpDir, "key.txt")
	hexData := []byte("aabbccdd")
	os.WriteFile(hexPath, hexData, 0644)

	format, byteSize, err := detectOTPKeyFormat(hexPath)
	if err != nil {
		t.Fatalf("检测hex密钥格式失败: %v", err)
	}
	if format != otpKeyHex {
		t.Error("应该检测为hex格式")
	}
	if byteSize != 4 {
		t.Errorf("hex密钥字节大小错误: got %d, want 4", byteSize)
	}

	// Create a binary key file (.bin)
	binPath := filepath.Join(tmpDir, "key.bin")
	binData := []byte{0xAA, 0xBB, 0xCC, 0xDD}
	os.WriteFile(binPath, binData, 0644)

	format, byteSize, err = detectOTPKeyFormat(binPath)
	if err != nil {
		t.Fatalf("检测binary密钥格式失败: %v", err)
	}
	if format != otpKeyBinary {
		t.Error("应该检测为binary格式")
	}
	if byteSize != 4 {
		t.Errorf("binary密钥字节大小错误: got %d, want 4", byteSize)
	}

	// Create a file with no extension that has hex-only content
	noExtPath := filepath.Join(tmpDir, "keyfile")
	os.WriteFile(noExtPath, hexData, 0644)

	format, byteSize, err = detectOTPKeyFormat(noExtPath)
	if err != nil {
		t.Fatalf("检测无扩展名密钥格式失败: %v", err)
	}
	if format != otpKeyHex {
		t.Error("全hex字符文件应检测为hex格式")
	}
	if byteSize != 4 {
		t.Errorf("hex密钥字节大小错误: got %d, want 4", byteSize)
	}

	// Create a file with no extension that has binary content
	noExtBinPath := filepath.Join(tmpDir, "keyfile_bin")
	os.WriteFile(noExtBinPath, binData, 0644)

	format, byteSize, err = detectOTPKeyFormat(noExtBinPath)
	if err != nil {
		t.Fatalf("检测无扩展名binary密钥格式失败: %v", err)
	}
	// Binary content like 0xAA is NOT a hex character, so should be detected as binary
	if format != otpKeyBinary {
		t.Error("非hex字符文件应检测为binary格式")
	}
	if byteSize != 4 {
		t.Errorf("binary密钥字节大小错误: got %d, want 4", byteSize)
	}
}

func TestOTPHexKeyWithWhitespace(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := []byte("Test with whitespace in key!")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()

	// Encrypt to get the key
	keyPathHex := filepath.Join(tmpDir, "key_test.txt")
	_, err := otp.EncryptToFile(inputPath, encPath, keyPathHex, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	// Read the hex key and add trailing newline (simulating real-world editing)
	keyData, err := os.ReadFile(keyPathHex)
	if err != nil {
		t.Fatalf("读取密钥文件失败: %v", err)
	}
	keyWithNewline := append(keyData, '\n')
	keyPathNewline := filepath.Join(tmpDir, "key_with_newline.txt")
	os.WriteFile(keyPathNewline, keyWithNewline, 0644)

	// Decrypt with key file that has trailing whitespace
	_, err = otp.DecryptFromFile(encPath, decPath, keyPathNewline, 10*1024*1024)
	if err != nil {
		t.Fatalf("带空白字符的密钥文件解密失败: %v", err)
	}

	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}
	if string(decContent) != string(testContent) {
		t.Errorf("解密内容不匹配")
	}
}

func TestOTPHeaderDetection(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	keyPath := filepath.Join(tmpDir, "key_test.txt")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := []byte("Header detection test data.")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()
	_, err := otp.EncryptToFile(inputPath, encPath, keyPath, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	// Verify the OTP header is present
	encData, err := os.ReadFile(encPath)
	if err != nil {
		t.Fatalf("读取加密文件失败: %v", err)
	}
	if len(encData) < 4 || encData[0] != 'O' || encData[1] != 'T' || encData[2] != 'P' || encData[3] != 0x00 {
		t.Errorf("OTP文件头错误: got %x", encData[:4])
	}

	// DetectAlgorithmByFileHeader should return OTP
	algo := DetectAlgorithmByFileHeader(encPath)
	if algo != AlgorithmOTP {
		t.Errorf("算法检测错误: got %s, want OTP", algo)
	}

	// Decrypt
	_, err = otp.DecryptFromFile(encPath, decPath, keyPath, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP解密失败: %v", err)
	}

	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}
	if string(decContent) != string(testContent) {
		t.Errorf("解密内容不匹配")
	}
}

func TestOTPKeyFileSizeMismatch(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := []byte("Key size mismatch test!")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()
	_, err := otp.EncryptToFile(inputPath, encPath, filepath.Join(tmpDir, "key.txt"), 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	// Create a deliberately wrong-sized key file
	wrongKeyPath := filepath.Join(tmpDir, "wrong_key.txt")
	os.WriteFile(wrongKeyPath, []byte("aabb"), 0644) // 2 bytes, but need len(testContent) bytes

	_, err = otp.DecryptFromFile(encPath, decPath, wrongKeyPath, 10*1024*1024)
	if err == nil {
		t.Error("密钥大小不匹配应返回错误")
	}
	if !strings.Contains(err.Error(), "不匹配") {
		t.Errorf("错误信息应包含'不匹配': got %v", err)
	}
}

func TestOTPAlgorithmType(t *testing.T) {
	otp := NewOTPAlgorithm()
	if otp.AlgorithmType() != AlgorithmOTP {
		t.Errorf("算法类型错误: got %s, want OTP", otp.AlgorithmType())
	}
}

// Test that key buffer is zeroed after encryption
func TestOTPKeyNotPreservedInResult(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	keyPath := filepath.Join(tmpDir, "key.txt")

	testContent := []byte("Key zeroing test data.")
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()
	result, err := otp.EncryptToFile(inputPath, encPath, keyPath, 10*1024*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	// Key should be nil in result (streamed to separate file)
	if result.Key != nil {
		t.Error("大文件加密后 Key 应为 nil（密钥已写入独立文件）")
	}
	if result.Ciphertext != nil {
		t.Error("大文件加密后 Ciphertext 应为 nil（密文已流式写入文件）")
	}
}

func TestXORBytes(t *testing.T) {
	a := []byte{0x01, 0x02, 0x03, 0xFF}
	b := []byte{0x01, 0x03, 0x03, 0x0F}
	result := xorBytes(a, b)
	expected := []byte{0x00, 0x01, 0x00, 0xF0}

	if len(result) != len(expected) {
		t.Fatalf("XOR结果长度错误: got %d, want %d", len(result), len(expected))
	}
	for i := range expected {
		if result[i] != expected[i] {
			t.Errorf("XOR在偏移 %d 处错误: got 0x%02x, want 0x%02x", i, result[i], expected[i])
		}
	}
}

func TestOTPEncryptFileWithProgress(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	keyPath := filepath.Join(tmpDir, "key.txt")

	testContent := make([]byte, 1024)
	for i := range testContent {
		testContent[i] = byte(i % 256)
	}
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()

	var progressCalls int
	var lastProcessed int64

	_, err := otp.EncryptToFileWithProgress(inputPath, encPath, keyPath, 256, func(processed, total int64) {
		progressCalls++
		lastProcessed = processed
		if total != 1024 {
			t.Errorf("进度回调 total 错误: got %d, want 1024", total)
		}
	})
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	if progressCalls == 0 {
		t.Error("进度回调未被调用")
	}
	if lastProcessed != 1024 {
		t.Errorf("最后进度 processed 错误: got %d, want 1024", lastProcessed)
	}
}

func TestOTPDecryptFromFileWithProgress(t *testing.T) {
	tmpDir := t.TempDir()

	inputPath := filepath.Join(tmpDir, "test.bin")
	encPath := filepath.Join(tmpDir, "test.bin.enc")
	keyPath := filepath.Join(tmpDir, "key.txt")
	decPath := filepath.Join(tmpDir, "test_decrypted.bin")

	testContent := make([]byte, 512)
	for i := range testContent {
		testContent[i] = byte(i % 256)
	}
	if err := os.WriteFile(inputPath, testContent, 0644); err != nil {
		t.Fatalf("写入测试文件失败: %v", err)
	}

	otp := NewOTPAlgorithm()
	_, err := otp.EncryptToFile(inputPath, encPath, keyPath, 10*1024)
	if err != nil {
		t.Fatalf("OTP加密失败: %v", err)
	}

	var progressCalls int
	_, err = otp.DecryptFromFileWithProgress(encPath, decPath, keyPath, 128, func(processed, total int64) {
		progressCalls++
	})
	if err != nil {
		t.Fatalf("OTP解密失败: %v", err)
	}

	if progressCalls == 0 {
		t.Error("解密进度回调未被调用")
	}

	decContent, err := os.ReadFile(decPath)
	if err != nil {
		t.Fatalf("读取解密文件失败: %v", err)
	}
	for i := range testContent {
		if decContent[i] != testContent[i] {
			t.Errorf("解密内容在偏移 %d 处不匹配", i)
			break
		}
	}
}

func TestOTPKeyHexEncodingRoundTrip(t *testing.T) {
	// Verify that hex-encoded keys decode correctly
	originalKey := []byte{0x00, 0x01, 0x0A, 0xFF, 0xAB, 0xCD, 0xEF, 0x00}
	hexStr := hex.EncodeToString(originalKey)
	decoded, err := hex.DecodeString(hexStr)
	if err != nil {
		t.Fatalf("hex解码失败: %v", err)
	}
	if len(decoded) != len(originalKey) {
		t.Errorf("hex解码长度错误: got %d, want %d", len(decoded), len(originalKey))
	}
	for i := range originalKey {
		if decoded[i] != originalKey[i] {
			t.Errorf("hex解码在偏移 %d 处错误", i)
			break
		}
	}
}
