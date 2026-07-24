package lang

import (
	"testing"
)

func TestNewTranslator(t *testing.T) {
	tr := NewTranslator("zh_CN")
	if tr == nil {
		t.Fatal("NewTranslator returned nil")
	}
	if tr.GetLanguage() != "zh_CN" {
		t.Errorf("unexpected language: got %s, want zh_CN", tr.GetLanguage())
	}
}

func TestTranslatorSetLanguage(t *testing.T) {
	tr := NewTranslator("zh_CN")
	tr.SetLanguage("en_US")
	if tr.GetLanguage() != "en_US" {
		t.Errorf("SetLanguage failed: got %s, want en_US", tr.GetLanguage())
	}
}

func TestTranslatorT(t *testing.T) {
	tr := NewTranslator("zh_CN")

	// Known key in zh_CN
	result := tr.T("app.title")
	if result != "MiniCipher - 文件加密工具" {
		t.Errorf("zh_CN app.title: got %q", result)
	}

	// Switch to English
	tr.SetLanguage("en_US")
	result = tr.T("app.title")
	if result != "MiniCipher - File Encryption Tool" {
		t.Errorf("en_US app.title: got %q", result)
	}
}

func TestTranslatorTFallbackToEnglish(t *testing.T) {
	// Unknown language should fall back to English
	tr := NewTranslator("ja_JP")
	result := tr.T("app.title")
	if result != "MiniCipher - File Encryption Tool" {
		t.Errorf("fallback to en_US failed: got %q", result)
	}
}

func TestTranslatorTMissingKeyReturnsKey(t *testing.T) {
	tr := NewTranslator("en_US")
	result := tr.T("nonexistent.key.xyz")
	if result != "nonexistent.key.xyz" {
		t.Errorf("missing key should return key itself: got %q", result)
	}
}

func TestTranslatorTf(t *testing.T) {
	tr := NewTranslator("en_US")

	// Format with args
	result := tr.Tf("error.encryption_failed", "something went wrong")
	expected := "Encryption failed: something went wrong"
	if result != expected {
		t.Errorf("Tf with args: got %q, want %q", result, expected)
	}

	// No args: should return format string as-is
	result = tr.Tf("app.title")
	if result != "MiniCipher - File Encryption Tool" {
		t.Errorf("Tf without args: got %q", result)
	}
}

func TestTranslatorTfChinese(t *testing.T) {
	tr := NewTranslator("zh_CN")

	result := tr.Tf("error.encryption_failed", "测试错误")
	expected := "加密失败: 测试错误"
	if result != expected {
		t.Errorf("zh_CN Tf with args: got %q, want %q", result, expected)
	}
}

func TestTranslatorTfMultipleArgs(t *testing.T) {
	tr := NewTranslator("en_US")

	// success.batch_result = "✅ %d/%d succeeded, %d failed, elapsed %s (%.1f%%)"
	result := tr.Tf("success.batch_result", 9, 10, 1, "5s", 90.0)
	expected := "✅ 9/10 succeeded, 1 failed, elapsed 5s (90.0%)"
	if result != expected {
		t.Errorf("Tf multiple args: got %q, want %q", result, expected)
	}
}

func TestTranslatorAllKeysExist(t *testing.T) {
	// Verify that all zh_CN keys have en_US counterparts and vice versa
	zhCN := defaultTranslations["zh_CN"]
	enUS := defaultTranslations["en_US"]

	for key := range zhCN {
		if _, ok := enUS[key]; !ok {
			t.Errorf("key %q exists in zh_CN but missing in en_US", key)
		}
	}
	for key := range enUS {
		if _, ok := zhCN[key]; !ok {
			t.Errorf("key %q exists in en_US but missing in zh_CN", key)
		}
	}
}

func TestTranslatorBatchProgressKey(t *testing.T) {
	tr := NewTranslator("zh_CN")
	progress := tr.T("batch.progress")
	if progress != "进度" {
		t.Errorf("zh_CN batch.progress: got %q, want 进度", progress)
	}
}

func TestTranslatorKnownKeys(t *testing.T) {
	// Smoke test a selection of keys in both languages
	tests := []struct {
		key     string
		zhCN    string
		enUS    string
	}{
		{"app.title", "MiniCipher - 文件加密工具", "MiniCipher - File Encryption Tool"},
		{"encryption", "加密", "Encryption"},
		{"decryption", "解密", "Decryption"},
		{"settings", "设置", "Settings"},
		{"ok", "确定", "OK"},
		{"cancel", "取消", "Cancel"},
		{"exit", "退出", "Exit"},
		{"status.ready", "就绪", "Ready"},
		{"error.no_key", "需要密钥文件", "Key file required"},
		{"error.no_password", "密码模式需要密码", "Password mode requires a password"},
	}

	for _, tt := range tests {
		t.Run(tt.key, func(t *testing.T) {
			tr := NewTranslator("zh_CN")
			if got := tr.T(tt.key); got != tt.zhCN {
				t.Errorf("zh_CN: got %q, want %q", got, tt.zhCN)
			}
			tr.SetLanguage("en_US")
			if got := tr.T(tt.key); got != tt.enUS {
				t.Errorf("en_US: got %q, want %q", got, tt.enUS)
			}
		})
	}
}
