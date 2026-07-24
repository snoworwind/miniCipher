package batch

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
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
	mu             sync.Mutex // 保护 FileResults 切片
}

// AddResult 线程安全地添加一个结果
func (r *BatchResult) AddResult(fr FileResult) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if fr.Success {
		r.SuccessFiles++
		r.ProcessedBytes += fr.FileSize
	} else {
		r.FailedFiles++
	}
	r.FileResults = append(r.FileResults, fr)
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

// Clone 深拷贝一个 FileResult（避免并发读时底层 slice 被修改）
func (p Progress) Clone() Progress {
	return p
}

// BatchProcessor 批量处理器
type BatchProcessor struct {
	maxWorkers     int
	chunkSize      int
	isCancelled    atomic.Bool
	progressFn     func(Progress)
	preserveStruct bool          // 是否保持目录结构
	baseInputPath  string        // 基础输入路径（用于计算相对路径）
	processMode    Mode          // 处理模式
	opType         OperationType // 操作类型
	mu             sync.Mutex    // 保护非原子字段
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
	bp.mu.Lock()
	defer bp.mu.Unlock()
	bp.progressFn = fn
}

// Cancel 取消处理
func (bp *BatchProcessor) Cancel() {
	bp.isCancelled.Store(true)
}

// Process 执行批量处理
func (bp *BatchProcessor) Process(op OperationType, mode Mode, paths []string, outputDir string,
	preserveStructure bool, algo crypto.AlgorithmType, keyType crypto.KeyType,
	key, password, iv, tag, salt []byte) (*BatchResult, error) {

	bp.isCancelled.Store(false)
	bp.mu.Lock()
	bp.preserveStruct = preserveStructure
	bp.opType = op
	bp.processMode = mode
	bp.mu.Unlock()

	// 确定基础路径（用于保持目录结构）
	if preserveStructure && len(paths) > 0 {
		for _, p := range paths {
			if info, err := os.Stat(p); err == nil && info.IsDir() {
				bp.baseInputPath = p
				break
			}
		}
		// 如果所有路径都是文件，使用第一个文件的父目录
		if bp.baseInputPath == "" {
			bp.baseInputPath = filepath.Dir(paths[0])
		}
	}

	files, totalSize, err := bp.collectFiles(paths, op)
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

	var wgProgress sync.WaitGroup
	wgProgress.Add(1)
	go func() {
		defer wgProgress.Done()
		var current int
		for p := range progressCh {
			current++
			bp.mu.Lock()
			cb := bp.progressFn
			bp.mu.Unlock()
			if cb != nil {
				p.CurrentFile = current
				p.TotalFiles = len(files)
				p.TotalSize = totalSize
				cb(p.Clone())
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
				outputPath := bp.buildOutputPath(t.path, outputDir, op)

				// 对于解密操作，自动查找密钥文件
				actualKeyPath := ""
				if op == OpDecrypt {
					actualKeyPath = findMatchingKeyFile(t.path, outputDir, algo, keyType)
				}

				err := bp.processFile(op, t.path, outputPath, actualKeyPath,
					algo, keyType, key, password, iv, tag, salt)

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

				// 在线程安全的 AddResult 之前发送进度，避免持有锁时发送 channel
				result.AddResult(fr)

				// 发送进度（不持有锁）
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

	bp.mu.Lock()
	cb := bp.progressFn
	bp.mu.Unlock()
	if cb != nil {
		cb(Progress{Done: true, TotalFiles: len(files), CurrentFile: result.SuccessFiles})
	}

	return result, nil
}

// collectFiles 收集要处理的文件，并进行过滤
func (bp *BatchProcessor) collectFiles(paths []string, op OperationType) ([]string, int64, error) {
	var files []string
	var totalSize int64

	// 排除扩展名和文件名（仅排除明确的临时文件和系统文件）
	excludeExtensions := map[string]bool{
		".tmp": true, ".temp": true, ".swp": true, ".DS_Store": true, ".lnk": true,
	}
	excludeNames := map[string]bool{
		"thumbs.db": true, ".gitignore": true,
	}

	// 根据操作类型添加额外排除条件：只排除密钥文件本身，不排除正常数据文件
	if op == OpDecrypt {
		excludeExtensions[".key"] = true
	} else {
		excludeExtensions[".enc"] = true
		excludeExtensions[".key"] = true // 加密时不处理密钥文件
	}

	for _, path := range paths {
		info, err := os.Stat(path)
		if err != nil {
			continue
		}
		if info.IsDir() {
			if bp.processMode == ModeFolderRecursive || bp.processMode == ModeFolder {
				filepath.Walk(path, func(p string, fi os.FileInfo, err error) error {
					if err != nil || fi.IsDir() {
						return nil
					}

					// ModeFolder：只处理一级子文件，不递归
					if bp.processMode == ModeFolder {
						parentDir := filepath.Dir(p)
						if parentDir != path {
							return nil
						}
					}

					// 文件过滤
					if !bp.shouldIncludeFile(p, fi, op, excludeExtensions, excludeNames) {
						return nil
					}

					files = append(files, p)
					totalSize += fi.Size()
					return nil
				})
			}
		} else {
			if bp.shouldIncludeFile(path, info, op, excludeExtensions, excludeNames) {
				files = append(files, path)
				totalSize += info.Size()
			}
		}
	}

	// 按文件大小降序排序（大文件优先，有助于并行处理）
	type fileWithSize struct {
		path string
		size int64
	}
	fws := make([]fileWithSize, len(files))
	for i, f := range files {
		if info, err := os.Stat(f); err == nil {
			fws[i] = fileWithSize{path: f, size: info.Size()}
		} else {
			fws[i] = fileWithSize{path: f, size: 0}
		}
	}
	sort.Slice(fws, func(i, j int) bool {
		return fws[i].size > fws[j].size // 降序
	})
	for i := range fws {
		files[i] = fws[i].path
	}

	return files, totalSize, nil
}

// shouldIncludeFile 判断文件是否应该被包含
func (bp *BatchProcessor) shouldIncludeFile(path string, info os.FileInfo, op OperationType,
	excludeExts map[string]bool, excludeNames map[string]bool) bool {

	if !info.Mode().IsRegular() {
		return false
	}

	name := info.Name()
	ext := strings.ToLower(filepath.Ext(name))

	// 检查排除扩展名
	if excludeExts[ext] {
		return false
	}

	// 检查排除文件名
	if excludeNames[strings.ToLower(name)] {
		return false
	}

	// 根据操作类型过滤
	if op == OpDecrypt {
		// 解密时只处理 .enc 文件
		if ext != ".enc" && !strings.HasSuffix(strings.ToLower(name), ".enc") {
			return false
		}
	} else { // OpEncrypt
		// 加密时跳过已加密的文件
		if ext == ".enc" || strings.HasSuffix(strings.ToLower(name), ".enc") {
			return false
		}
	}

	// 跳过空文件
	if info.Size() == 0 {
		return false
	}

	return true
}

// buildOutputPath 计算输出文件路径
func (bp *BatchProcessor) buildOutputPath(inputPath, outputDir string, op OperationType) string {
	baseName := filepath.Base(inputPath)
	name, ext := filepathBaseExt(baseName)

	var outputName string
	if op == OpEncrypt {
		outputName = name + ext + ".enc"
	} else {
		// 去除 .enc 扩展名
		if strings.HasSuffix(name, ".enc") {
			name = name[:len(name)-4]
		} else if ext == ".enc" {
			ext = ""
		} else {
			name = name + "_decrypted"
		}
		outputName = name + ext
	}

	if bp.preserveStruct && bp.baseInputPath != "" {
		// 使用 relpath 计算相对路径
		inputDir := filepath.Dir(inputPath)
		relPath, err := filepath.Rel(bp.baseInputPath, inputDir)
		if err == nil && relPath != "." {
			outputSubdir := filepath.Join(outputDir, relPath)
			os.MkdirAll(outputSubdir, 0755)
			return filepath.Join(outputSubdir, outputName)
		}
	}

	// 确保输出目录存在
	os.MkdirAll(outputDir, 0755)
	return filepath.Join(outputDir, outputName)
}

// filepathBaseExt 获取文件名和扩展名
func filepathBaseExt(filename string) (string, string) {
	ext := filepath.Ext(filename)
	name := filename[:len(filename)-len(ext)]
	return name, ext
}

// findMatchingKeyFile 查找与输入文件匹配的密钥文件
func findMatchingKeyFile(inputPath, outputDir string, algorithm crypto.AlgorithmType, keyType crypto.KeyType) string {
	baseName := filepath.Base(inputPath)

	// 处理文件名，去除.enc扩展名获取原始文件名
	originalName := baseName
	if strings.HasSuffix(originalName, ".enc") {
		originalName = originalName[:len(originalName)-4]
	}

	// 获取不包含扩展名的基本名称
	baseNameNoExt := originalName
	if ext := filepath.Ext(baseNameNoExt); ext != "" {
		baseNameNoExt = baseNameNoExt[:len(baseNameNoExt)-len(ext)]
	}

	inputDir := filepath.Dir(inputPath)
	searchDirs := []string{inputDir, outputDir}

	// 收集可能的密钥文件路径
	var possibleKeyFiles []string

	for _, searchDir := range searchDirs {
		if _, err := os.Stat(searchDir); err != nil {
			continue
		}

		if algorithm == crypto.AlgorithmOTP {
			// 使用 BuildKeyFilePath 生成标准路径
			possibleKeyFiles = append(possibleKeyFiles,
				crypto.BuildKeyFilePath(searchDir, originalName, crypto.AlgorithmOTP, crypto.KeyTypeRandom, "hex"),
				crypto.BuildKeyFilePath(searchDir, originalName, crypto.AlgorithmOTP, crypto.KeyTypeRandom, "binary"),
				crypto.BuildKeyFilePath(searchDir, baseNameNoExt, crypto.AlgorithmOTP, crypto.KeyTypeRandom, "hex"),
				crypto.BuildKeyFilePath(searchDir, baseNameNoExt, crypto.AlgorithmOTP, crypto.KeyTypeRandom, "binary"),
			)
		} else if keyType == crypto.KeyTypeRandom {
			// AES 随机密钥模式
			possibleKeyFiles = append(possibleKeyFiles,
				crypto.BuildKeyFilePath(searchDir, originalName, crypto.AlgorithmAES256, crypto.KeyTypeRandom, ""),
				crypto.BuildKeyFilePath(searchDir, baseNameNoExt, crypto.AlgorithmAES256, crypto.KeyTypeRandom, ""),
			)
		}

		// 遍历目录搜索更多模式
		entries, err := os.ReadDir(searchDir)
		if err != nil {
			continue
		}
		lowerOrig := strings.ToLower(originalName)
		lowerNoExt := strings.ToLower(baseNameNoExt)
		for _, entry := range entries {
			if entry.IsDir() {
				continue
			}
			name := entry.Name()
			lower := strings.ToLower(name)
			if strings.HasPrefix(lower, "key_"+lowerOrig+".") ||
				strings.HasPrefix(lower, "key_"+lowerNoExt+".") ||
				(strings.Contains(lower, "_"+lowerOrig+".") &&
					(strings.HasSuffix(lower, ".txt") || strings.HasSuffix(lower, ".bin") || strings.HasSuffix(lower, ".key"))) {
				possibleKeyFiles = append(possibleKeyFiles, filepath.Join(searchDir, name))
			}
		}
	}

	// 去重并查找存在的文件
	seen := make(map[string]bool)
	for _, keyFile := range possibleKeyFiles {
		if seen[keyFile] {
			continue
		}
		seen[keyFile] = true
		if info, err := os.Stat(keyFile); err == nil && !info.IsDir() {
			return keyFile
		}
	}

	// 在父目录中搜索
	parentDir := filepath.Dir(inputDir)
	if parentDir != "" && parentDir != inputDir {
		entries, err := os.ReadDir(parentDir)
		if err == nil {
			lowerOrig := strings.ToLower(originalName)
			lowerNoExt := strings.ToLower(baseNameNoExt)
			for _, entry := range entries {
				if entry.IsDir() {
					continue
				}
				name := entry.Name()
				lower := strings.ToLower(name)
				if strings.HasPrefix(lower, "key_"+lowerOrig+".") ||
					strings.HasPrefix(lower, "key_"+lowerNoExt+".") {
					keyFile := filepath.Join(parentDir, name)
					if info, err := os.Stat(keyFile); err == nil && !info.IsDir() {
						return keyFile
					}
				}
			}
		}
	}

	return ""
}

// processFile 处理单个文件
func (bp *BatchProcessor) processFile(op OperationType, inputPath, outputPath, keyPath string,
	algo crypto.AlgorithmType, keyType crypto.KeyType, key, password, iv, tag, salt []byte) error {

	outputDir := filepath.Dir(outputPath)
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("创建输出目录失败: %w", err)
	}

	switch op {
	case OpEncrypt:
		return bp.encryptFile(inputPath, outputPath, algo, keyType, password, salt)
	case OpDecrypt:
		return bp.decryptFile(inputPath, outputPath, keyPath, algo, keyType, key, password, iv, tag, salt)
	}
	return fmt.Errorf("不支持的操作类型")
}

func (bp *BatchProcessor) encryptFile(inputPath, outputPath string,
	algo crypto.AlgorithmType, keyType crypto.KeyType, password, salt []byte) error {

	switch algo {
	case crypto.AlgorithmOTP:
		// OTP 流式加密：使用 BuildKeyFilePath 生成统一路径
		baseName := filepath.Base(inputPath)
		keyPath := crypto.BuildKeyFilePath(filepath.Dir(outputPath), baseName, crypto.AlgorithmOTP, crypto.KeyTypeRandom, "hex")
		otp := crypto.NewOTPAlgorithm()
		_, err := otp.EncryptToFile(inputPath, outputPath, keyPath, bp.chunkSize)
		return err
	case crypto.AlgorithmAES256:
		aes := crypto.NewAES256Algorithm()
		result, err := aes.EncryptToFile(inputPath, outputPath, keyType, password, salt, bp.chunkSize)
		if err != nil {
			return err
		}
		// 保存 AES 随机密钥文件（完整格式：key + iv + tag）
		if keyType == crypto.KeyTypeRandom {
			baseName := filepath.Base(inputPath)
			keyPath := crypto.BuildKeyFilePath(filepath.Dir(outputPath), baseName, crypto.AlgorithmAES256, crypto.KeyTypeRandom, "")
			if err := crypto.SaveKeyFileWithIVTag(keyPath, result.Key, result.IV, result.Tag); err != nil {
				return fmt.Errorf("保存AES密钥文件失败: %w", err)
			}
		}
		return nil
	}
	return fmt.Errorf("不支持的算法: %s", algo)
}

func (bp *BatchProcessor) decryptFile(inputPath, outputPath, keyPath string,
	algo crypto.AlgorithmType, keyType crypto.KeyType, key, password, iv, tag, salt []byte) error {

	switch algo {
	case crypto.AlgorithmOTP:
		if keyPath == "" {
			return fmt.Errorf("OTP解密需要密钥文件")
		}
		// OTP 流式解密：分块读取密钥文件，不加载完整密钥到内存
		otp := crypto.NewOTPAlgorithm()
		_, err := otp.DecryptFromFile(inputPath, outputPath, keyPath, bp.chunkSize)
		return err
	case crypto.AlgorithmAES256:
		aes := crypto.NewAES256Algorithm()
		if keyType == crypto.KeyTypePassword || len(password) > 0 {
			_, err := aes.DecryptFromFile(inputPath, outputPath, keyType, nil, nil, nil, password, nil, bp.chunkSize)
			return err
		}
		if keyPath == "" {
			return fmt.Errorf("AES解密需要密钥文件")
		}
		// 智能加载密钥（支持纯key和完整格式）
		aesKey, aesIV, aesTag, err := crypto.LoadKeyWithIVTag(keyPath)
		if err != nil {
			// 回退到纯key格式
			aesKey, err = crypto.LoadKey(keyPath)
			if err != nil {
				return fmt.Errorf("加载AES密钥文件失败: %w", err)
			}
			aesIV = nil
			aesTag = nil
		}
		_, err = aes.DecryptFromFile(inputPath, outputPath, crypto.KeyTypeRandom, aesKey, aesIV, aesTag, nil, nil, bp.chunkSize)
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

// ElapsedSeconds 返回耗时（秒）
func (r *BatchResult) ElapsedSeconds() float64 {
	return r.EndTime.Sub(r.StartTime).Seconds()
}

// AverageSpeed 返回平均处理速度（字节/秒）
func (r *BatchResult) AverageSpeed() float64 {
	elapsed := r.ElapsedSeconds()
	if elapsed == 0 {
		return 0
	}
	return float64(r.ProcessedBytes) / elapsed
}

// StatisticsReport 生成统计报告
func (r *BatchResult) StatisticsReport() string {
	elapsed := r.Duration()
	minutes := int(elapsed.Minutes())
	seconds := elapsed.Seconds() - float64(minutes*60)

	return fmt.Sprintf(
		"\n=== 批量处理统计报告 ===\n"+
			"总文件数: %d\n"+
			"成功: %d\n"+
			"失败: %d\n"+
			"成功率: %.1f%%\n"+
			"总大小: %s (%s)\n"+
			"处理大小: %s (%s)\n"+
			"耗时: %d分%.1f秒\n"+
			"平均速度: %s/秒\n"+
			"========================\n",
		r.TotalFiles,
		r.SuccessFiles,
		r.FailedFiles,
		r.SuccessRate(),
		formatBytes(r.TotalBytes),
		formatMB(r.TotalBytes),
		formatBytes(r.ProcessedBytes),
		formatMB(r.ProcessedBytes),
		minutes, seconds,
		formatMB(int64(r.AverageSpeed())),
	)
}

func formatBytes(b int64) string {
	const unit = 1024
	if b < unit {
		return fmt.Sprintf("%d 字节", b)
	}
	div, exp := int64(unit), 0
	for n := b / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(b)/float64(div), "KMGTPE"[exp])
}

func formatMB(b int64) string {
	return fmt.Sprintf("%.2f MB", float64(b)/(1024*1024))
}