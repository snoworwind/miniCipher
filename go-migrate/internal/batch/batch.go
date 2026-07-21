package batch

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/snoworwind/minicipher/internal/crypto"
)

// OperationType 操作类型
type OperationType int

const (
	OpEncrypt OperationType = iota
	OpDecrypt
)

// Mode 批量处理模式
type Mode int

const (
	ModeFiles          Mode = iota
	ModeFolder
	ModeFolderRecursive
)

// FileResult 单个文件处理结果
type FileResult struct {
	InputPath    string
	OutputPath   string
	Success      bool
	ErrorMessage string
	FileSize     int64
	Duration     time.Duration
}

// BatchResult 批量处理结果
type BatchResult struct {
	TotalFiles     int
	SuccessFiles   int
	FailedFiles    int
	TotalBytes     int64
	ProcessedBytes int64
	StartTime      time.Time
	EndTime        time.Time
	FileResults    []FileResult
}

// Progress 进度信息
type Progress struct {
	TotalFiles    int
	CurrentFile   int
	CurrentName   string
	ProcessedSize int64
	TotalSize     int64
	Done          bool
}

// BatchProcessor 批量处理器
type BatchProcessor struct {
	maxWorkers  int
	chunkSize   int
	isCancelled atomic.Bool
	progressFn  func(Progress)
}

// New 创建批量处理器
func New(maxWorkers int, chunkSizeMB int) *BatchProcessor {
	if maxWorkers <= 0 {
		maxWorkers = 4
	}
	if chunkSizeMB <= 0 {
		chunkSizeMB = 10
	}
	return &BatchProcessor{
		maxWorkers: maxWorkers,
		chunkSize:  chunkSizeMB * 1024 * 1024,
	}
}

// SetProgressCallback 设置进度回调
func (bp *BatchProcessor) SetProgressCallback(fn func(Progress)) {
	bp.progressFn = fn
}

// Cancel 取消处理
func (bp *BatchProcessor) Cancel() {
	bp.isCancelled.Store(true)
}

// Process 执行批量处理
func (bp *BatchProcessor) Process(op OperationType, paths []string, outputDir string,
	preserveStructure bool, algo string, keyType crypto.KeyType,
	key, password, iv, tag, salt []byte) (*BatchResult, error) {

	bp.isCancelled.Store(false)

	files, totalSize, err := bp.collectFiles(paths)
	if err != nil {
		return nil, err
	}

	if len(files) == 0 {
		return nil, fmt.Errorf("未找到可处理的文件")
	}

	result := &BatchResult{
		TotalFiles: len(files),
		TotalBytes: totalSize,
		StartTime:  time.Now(),
	}

	progressCh := make(chan Progress, 100)

	type task struct {
		index int
		path  string
	}
	taskCh := make(chan task, len(files))
	var mu sync.Mutex

	var wgProgress sync.WaitGroup
	wgProgress.Add(1)
	go func() {
		defer wgProgress.Done()
		var current int
		for p := range progressCh {
			current++
			if bp.progressFn != nil {
				p.CurrentFile = current
				p.TotalFiles = len(files)
				p.TotalSize = totalSize
				bp.progressFn(p)
			}
		}
	}()

	var wg sync.WaitGroup
	for i := 0; i < bp.maxWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for t := range taskCh {
				if bp.isCancelled.Load() {
					return
				}

				startTime := time.Now()
				fr := FileResult{InputPath: t.path}
				outputPath := bp.buildOutputPath(t.path, outputDir, preserveStructure, op)
				err := bp.processFile(op, t.path, outputPath, algo, keyType,
					key, password, iv, tag, salt)

				fr.Duration = time.Since(startTime)
				if err != nil {
					fr.Success = false
					fr.ErrorMessage = err.Error()
				} else {
					fr.Success = true
					fr.OutputPath = outputPath
					if info, e := os.Stat(t.path); e == nil {
						fr.FileSize = info.Size()
					}
				}

				mu.Lock()
				if fr.Success {
					result.SuccessFiles++
					result.ProcessedBytes += fr.FileSize
				} else {
					result.FailedFiles++
				}
				result.FileResults = append(result.FileResults, fr)
				mu.Unlock()

				progressCh <- Progress{
					CurrentName:   filepath.Base(t.path),
					ProcessedSize: fr.FileSize,
					Done:          false,
				}
			}
		}()
	}

	for i, f := range files {
		taskCh <- task{index: i, path: f}
	}
	close(taskCh)

	wg.Wait()
	close(progressCh)
	wgProgress.Wait()

	result.EndTime = time.Now()

	if bp.progressFn != nil {
		bp.progressFn(Progress{Done: true, TotalFiles: len(files), CurrentFile: len(files)})
	}

	return result, nil
}

func (bp *BatchProcessor) collectFiles(paths []string) ([]string, int64, error) {
	var files []string
	var totalSize int64
	for _, path := range paths {
		info, err := os.Stat(path)
		if err != nil {
			continue
		}
		if info.IsDir() {
			filepath.Walk(path, func(p string, fi os.FileInfo, err error) error {
				if err != nil || fi.IsDir() {
					return nil
				}
				files = append(files, p)
				totalSize += fi.Size()
				return nil
			})
		} else {
			files = append(files, path)
			totalSize += info.Size()
		}
	}
	return files, totalSize, nil
}

func (bp *BatchProcessor) buildOutputPath(inputPath, outputDir string, preserveStructure bool, op OperationType) string {
	baseName := filepath.Base(inputPath)
	if op == OpEncrypt {
		baseName += ".enc"
	} else {
		baseName = strings.TrimSuffix(baseName, ".enc")
	}
	if preserveStructure {
		absInput, err := filepath.Abs(inputPath)
		if err != nil {
			return filepath.Join(outputDir, baseName)
		}
		return filepath.Join(outputDir, filepath.Dir(absInput), baseName)
	}
	return filepath.Join(outputDir, baseName)
}

func (bp *BatchProcessor) processFile(op OperationType, inputPath, outputPath string,
	algo string, keyType crypto.KeyType, key, password, iv, tag, salt []byte) error {

	outputDir := filepath.Dir(outputPath)
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("创建输出目录失败: %w", err)
	}

	switch op {
	case OpEncrypt:
		return bp.encryptFile(inputPath, outputPath, algo, keyType, password, salt)
	case OpDecrypt:
		return bp.decryptFile(inputPath, outputPath, algo, keyType, key, password, iv, tag, salt)
	}
	return fmt.Errorf("不支持的操作类型")
}

func (bp *BatchProcessor) encryptFile(inputPath, outputPath string,
	algo string, keyType crypto.KeyType, password, salt []byte) error {

	switch algo {
	case "OTP":
		otp := crypto.NewOTPAlgorithm()
		result, err := otp.EncryptToFile(inputPath, outputPath, bp.chunkSize)
		if err != nil {
			return err
		}
		// 保存 OTP 密钥文件
		keyPath := outputPath + ".key"
		if err := os.WriteFile(keyPath, result.Key, 0600); err != nil {
			return fmt.Errorf("保存OTP密钥文件失败: %w", err)
		}
		return nil
	case "AES256":
		aes := crypto.NewAES256Algorithm()
		result, err := aes.EncryptToFile(inputPath, outputPath, keyType, password, salt)
		if err != nil {
			return err
		}
		// 保存 AES 随机密钥文件
		if keyType == crypto.KeyTypeRandom {
			keyPath := outputPath + ".key"
			if err := crypto.SaveKeyFile(keyPath, result.Key, result.IV, result.Tag); err != nil {
				return fmt.Errorf("保存AES密钥文件失败: %w", err)
			}
		}
		return nil
	}
	return fmt.Errorf("不支持的算法: %s", algo)
}

func (bp *BatchProcessor) decryptFile(inputPath, outputPath string,
	algo string, keyType crypto.KeyType, key, password, iv, tag, salt []byte) error {

	switch algo {
	case "OTP":
		otp := crypto.NewOTPAlgorithm()
		_, err := otp.DecryptFromFile(inputPath, outputPath, key, bp.chunkSize)
		return err
	case "AES256":
		aes := crypto.NewAES256Algorithm()
		_, err := aes.DecryptFromFile(inputPath, outputPath, keyType, key, iv, tag, password, salt)
		return err
	}
	return fmt.Errorf("不支持的算法: %s", algo)
}

// Duration 返回处理耗时
func (r *BatchResult) Duration() time.Duration {
	return r.EndTime.Sub(r.StartTime)
}

// SuccessRate 返回成功率
func (r *BatchResult) SuccessRate() float64 {
	if r.TotalFiles == 0 {
		return 0
	}
	return float64(r.SuccessFiles) / float64(r.TotalFiles) * 100
}