package batch

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/snoworwind/minicipher/internal/crypto"
)

func TestNew(t *testing.T) {
	bp := New(0, 0)
	if bp.maxWorkers != 4 {
		t.Errorf("default maxWorkers: got %d, want 4", bp.maxWorkers)
	}
	if bp.chunkSize != 10*1024*1024 {
		t.Errorf("default chunkSize: got %d, want %d", bp.chunkSize, 10*1024*1024)
	}

	bp2 := New(8, 20)
	if bp2.maxWorkers != 8 {
		t.Errorf("custom maxWorkers: got %d, want 8", bp2.maxWorkers)
	}
	if bp2.chunkSize != 20*1024*1024 {
		t.Errorf("custom chunkSize: got %d, want %d", bp2.chunkSize, 20*1024*1024)
	}
}

func TestBuildOutputPathEncrypt(t *testing.T) {
	bp := New(4, 10)

	// Without preserve structure
	bp.preserveStruct = false
	result := bp.buildOutputPath("/data/docs/report.pdf", "/out", OpEncrypt)
	expected := filepath.Join("/out", "report.pdf.enc")
	if result != expected {
		t.Errorf("encrypt output path: got %s, want %s", result, expected)
	}
}

func TestBuildOutputPathDecrypt(t *testing.T) {
	bp := New(4, 10)
	bp.preserveStruct = false

	// Decrypt .enc file
	result := bp.buildOutputPath("/data/docs/report.pdf.enc", "/out", OpDecrypt)
	expected := filepath.Join("/out", "report.pdf")
	if result != expected {
		t.Errorf("decrypt output path: got %s, want %s", result, expected)
	}
}

func TestBuildOutputPathPreserveStructure(t *testing.T) {
	tmpDir := t.TempDir()
	bp := New(4, 10)
	bp.preserveStruct = true
	bp.baseInputPath = tmpDir

	// Create input subdirectory structure so the relative path is valid.
	// buildOutputPath internally calls os.MkdirAll on the output subdirectory,
	// which requires the parent to be writable (t.TempDir() satisfies this).
	inputSubDir := filepath.Join(tmpDir, "sub")
	inputPath := filepath.Join(inputSubDir, "report.pdf")
	outputDir := filepath.Join(tmpDir, "out")

	result := bp.buildOutputPath(inputPath, outputDir, OpEncrypt)

	expectedPrefix := filepath.Join(outputDir, "sub")
	if !strings.HasPrefix(result, expectedPrefix) {
		t.Errorf("preserve structure: got %s, expected prefix %s", result, expectedPrefix)
	}
	if !strings.HasSuffix(result, ".pdf.enc") {
		t.Errorf("preserve structure: output should end with .pdf.enc, got %s", result)
	}
}

func TestShouldIncludeFile(t *testing.T) {
	bp := New(4, 10)

	excludeExts := map[string]bool{
		".tmp": true, ".temp": true, ".swp": true, ".DS_Store": true, ".lnk": true,
	}
	excludeNames := map[string]bool{
		"thumbs.db": true, ".gitignore": true,
	}

	// Helper to create a temp file and get its FileInfo
	tmpDir := t.TempDir()

	t.Run("exclude tmp files", func(t *testing.T) {
		path := filepath.Join(tmpDir, "test.tmp")
		os.WriteFile(path, []byte("data"), 0644)
		info, _ := os.Stat(path)
		if bp.shouldIncludeFile(path, info, OpEncrypt, excludeExts, excludeNames) {
			t.Error(".tmp files should be excluded")
		}
	})

	t.Run("exclude .enc when encrypting", func(t *testing.T) {
		path := filepath.Join(tmpDir, "already.enc")
		os.WriteFile(path, []byte("encrypted data here"), 0644)
		info, _ := os.Stat(path)
		if bp.shouldIncludeFile(path, info, OpEncrypt, excludeExts, excludeNames) {
			t.Error(".enc files should be excluded when encrypting")
		}
	})

	t.Run("include .enc when decrypting", func(t *testing.T) {
		path := filepath.Join(tmpDir, "file.enc")
		os.WriteFile(path, []byte("encrypted data here"), 0644)
		info, _ := os.Stat(path)
		if !bp.shouldIncludeFile(path, info, OpDecrypt, excludeExts, excludeNames) {
			t.Error(".enc files should be included when decrypting")
		}
	})

	t.Run("exclude non-enc when decrypting", func(t *testing.T) {
		path := filepath.Join(tmpDir, "readme.txt")
		os.WriteFile(path, []byte("hello"), 0644)
		info, _ := os.Stat(path)
		if bp.shouldIncludeFile(path, info, OpDecrypt, excludeExts, excludeNames) {
			t.Error("non-.enc files should be excluded when decrypting")
		}
	})

	t.Run("exclude empty files", func(t *testing.T) {
		path := filepath.Join(tmpDir, "empty.txt")
		os.WriteFile(path, []byte{}, 0644)
		info, _ := os.Stat(path)
		if bp.shouldIncludeFile(path, info, OpEncrypt, excludeExts, excludeNames) {
			t.Error("empty files should be excluded")
		}
	})

	t.Run("exclude key files when decrypting", func(t *testing.T) {
		path := filepath.Join(tmpDir, "secret.key")
		os.WriteFile(path, []byte("keydata"), 0644)
		info, _ := os.Stat(path)
		if bp.shouldIncludeFile(path, info, OpDecrypt, excludeExts, excludeNames) {
			t.Error(".key files should be excluded when decrypting")
		}
	})

	t.Run("include normal files for encryption", func(t *testing.T) {
		path := filepath.Join(tmpDir, "doc.pdf")
		os.WriteFile(path, []byte("pdf content"), 0644)
		info, _ := os.Stat(path)
		if !bp.shouldIncludeFile(path, info, OpEncrypt, excludeExts, excludeNames) {
			t.Error("normal files should be included for encryption")
		}
	})
}

func TestFilepathBaseExt(t *testing.T) {
	tests := []struct {
		filename string
		name     string
		ext      string
	}{
		{"report.pdf", "report", ".pdf"},
		{"archive.tar.gz", "archive.tar", ".gz"},
		{"Makefile", "Makefile", ""},
		{"file.enc", "file", ".enc"},
		{".hidden", "", ".hidden"}, // Go filepath.Ext treats leading dot as extension
		{"data.", "data", "."},
	}

	for _, tt := range tests {
		t.Run(tt.filename, func(t *testing.T) {
			name, ext := filepathBaseExt(tt.filename)
			if name != tt.name {
				t.Errorf("name: got %q, want %q", name, tt.name)
			}
			if ext != tt.ext {
				t.Errorf("ext: got %q, want %q", ext, tt.ext)
			}
		})
	}
}

func TestCancel(t *testing.T) {
	bp := New(4, 10)
	if bp.isCancelled.Load() {
		t.Error("should not be cancelled initially")
	}
	bp.Cancel()
	if !bp.isCancelled.Load() {
		t.Error("should be cancelled after Cancel()")
	}
}

func TestCollectFiles(t *testing.T) {
	tmpDir := t.TempDir()

	// Create test files
	files := map[string]string{
		"doc1.txt":   "content1",
		"doc2.txt":   "content2",
		"secret.enc": "already encrypted",
		"temp.tmp":   "temp data",
		"empty.txt":  "",
	}
	for name, content := range files {
		os.WriteFile(filepath.Join(tmpDir, name), []byte(content), 0644)
	}

	bp := New(4, 10)
	bp.processMode = ModeFolder

	collected, totalSize, err := bp.collectFiles([]string{tmpDir}, OpEncrypt, ModeFolder)
	if err != nil {
		t.Fatalf("collectFiles failed: %v", err)
	}

	// Should only include doc1.txt and doc2.txt (non-enc, non-tmp, non-empty)
	if len(collected) != 2 {
		t.Errorf("expected 2 files, got %d: %v", len(collected), collected)
	}
	if totalSize == 0 {
		t.Error("totalSize should be > 0")
	}
}

func TestBatchResultStatistics(t *testing.T) {
	r := &BatchResult{
		TotalFiles:     10,
		SuccessFiles:   9,
		FailedFiles:    1,
		TotalBytes:     1024 * 1024, // 1 MB
		ProcessedBytes: 1024 * 1024,
	}

	if r.SuccessRate() != 90.0 {
		t.Errorf("success rate: got %.1f, want 90.0", r.SuccessRate())
	}

	report := r.StatisticsReport()
	if !strings.Contains(report, "10") {
		t.Error("report should contain total file count")
	}
	if !strings.Contains(report, "90.0%") {
		t.Error("report should contain success rate")
	}
}

func TestFindMatchingKeyFile(t *testing.T) {
	tmpDir := t.TempDir()

	// Create a test encrypted file and matching key
	encPath := filepath.Join(tmpDir, "secret.txt.enc")
	os.WriteFile(encPath, []byte("encrypted"), 0644)

	// Create the key file using the standard naming
	keyPath := crypto.BuildKeyFilePath(tmpDir, "secret.txt", crypto.AlgorithmOTP, crypto.KeyTypeRandom, "hex")
	os.WriteFile(keyPath, []byte("aabbccdd"), 0644)

	result := findMatchingKeyFile(encPath, tmpDir, crypto.AlgorithmOTP, crypto.KeyTypeRandom)
	if result == "" {
		t.Error("should find the matching OTP key file")
	}
}
