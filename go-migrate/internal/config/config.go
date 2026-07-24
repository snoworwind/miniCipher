package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"sync"
)

// Config 应用配置
type Config struct {
	Version  string         `json:"version"`
	UI       UIConfig       `json:"ui"`
	Crypto   CryptoConfig   `json:"crypto"`
	Paths    PathsConfig    `json:"paths"`
	Batch    BatchConfig    `json:"batch"`
	Debug    bool           `json:"debug"`
	Advanced AdvancedConfig `json:"advanced"`
}

// UIConfig 界面配置
type UIConfig struct {
	Language string `json:"language"` // "zh_CN" or "en_US"
	Theme    string `json:"theme"`    // "light" or "dark"
}

// AdvancedConfig 高级配置
type AdvancedConfig struct {
	BufferSize int    `json:"buffer_size"` // MB - 缓冲区大小
	LogLevel   string `json:"log_level"`   // 日志级别 DEBUG/INFO/WARNING/ERROR
}

// CryptoConfig 加密配置
type CryptoConfig struct {
	DefaultAlgorithm    string `json:"default_algorithm"`    // "OTP" or "AES256"
	DefaultKeyType      string `json:"default_key_type"`     // "random" or "password"
	PasswordMinLength   int    `json:"password_min_length"`
	RequireStrongPass   bool   `json:"require_strong_password"`
	OTPKeyFormat        string `json:"otp_key_format"`       // "hex" or "binary"
}

// PathsConfig 路径配置
type PathsConfig struct {
	DefaultInputDir    string `json:"default_input_dir"`
	DefaultOutputDir   string `json:"default_output_dir"`
	RememberLastFolder bool   `json:"remember_last_folder"`
	LastInputFolder    string `json:"last_input_folder"`
	LastOutputFolder   string `json:"last_output_folder"`
}

// BatchConfig 批量处理配置
type BatchConfig struct {
	ParallelProcessing bool `json:"parallel_processing"`
	MaxThreads         int  `json:"max_threads"`
	PreserveStructure  bool `json:"preserve_structure"`
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Version: "2.1.0",
		UI: UIConfig{
			Language: "zh_CN",
			Theme:    "light",
		},
		Crypto: CryptoConfig{
			DefaultAlgorithm:  "AES256",
			DefaultKeyType:    "random",
			PasswordMinLength: 8,
			RequireStrongPass: true,
			OTPKeyFormat:      "hex",
		},
		Paths: PathsConfig{
			RememberLastFolder: true,
		},
		Batch: BatchConfig{
			ParallelProcessing: false,
			MaxThreads:         4,
			PreserveStructure:  true,
		},
		Debug: false,
		Advanced: AdvancedConfig{
			BufferSize: 10,
			LogLevel:   "INFO",
		},
	}
}

// Manager 配置管理器（线程安全）
type Manager struct {
	mu         sync.RWMutex
	configDir  string
	configFile string
	config     *Config
}

// NewManager 创建配置管理器
func NewManager() *Manager {
	return &Manager{}
}

// Load 加载配置（如果不存在则使用默认配置）
// 采用深度合并策略：先用默认配置填充，再用文件内容覆盖非零字段
func (m *Manager) Load() (*Config, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	configDir, err := getConfigDir()
	if err != nil {
		return nil, fmt.Errorf("获取配置目录失败: %w", err)
	}
	m.configDir = configDir
	m.configFile = filepath.Join(configDir, "config.json")

	// 确保配置目录存在
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return nil, fmt.Errorf("创建配置目录失败: %w", err)
	}

	// 尝试读取配置
	data, err := os.ReadFile(m.configFile)
	if err != nil {
		if os.IsNotExist(err) {
			// 配置文件不存在，使用默认配置
			m.config = DefaultConfig()
			if err := m.Save(); err != nil {
				return nil, fmt.Errorf("保存默认配置失败: %w", err)
			}
			return m.config, nil
		}
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	// 深度合并：先设置默认值，再应用文件中的非零值
	config := DefaultConfig()
	if err := deepMergeJSON(config, data); err != nil {
		// 配置文件损坏，使用默认配置。输出警告到 stderr 因为此时日志系统可能未初始化。
		fmt.Fprintf(os.Stderr, "WARNING: 配置文件已损坏 (%v)，已恢复为默认配置\n", err)
		m.config = DefaultConfig()
		if saveErr := m.saveLocked(); saveErr != nil {
			fmt.Fprintf(os.Stderr, "WARNING: 保存默认配置失败: %v\n", saveErr)
		}
		return m.config, nil
	}

	m.config = config

	// 验证配置
	if err := ValidateConfig(config); err != nil {
		// 配置无效，使用默认配置
		fmt.Fprintf(os.Stderr, "WARNING: 配置验证失败 (%v)，已恢复为默认配置\n", err)
		m.config = DefaultConfig()
		if saveErr := m.saveLocked(); saveErr != nil {
			fmt.Fprintf(os.Stderr, "WARNING: 保存默认配置失败: %v\n", saveErr)
		}
		return m.config, nil
	}

	return config, nil
}

// deepMergeJSON 深度合并 JSON 数据到配置结构体
// config 已由 DefaultConfig() 预填充默认值；仅覆盖文件中明确指定的字段。
// 对于 bool 字段，检查 JSON 键是否存在以区分"未设置"和"设置为 false"。
func deepMergeJSON(config *Config, data []byte) error {
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil {
		return err
	}

	// keyExists checks whether a key is present in a raw JSON object.
	keyExists := func(rawJSON json.RawMessage, key string) bool {
		var m map[string]json.RawMessage
		if err := json.Unmarshal(rawJSON, &m); err != nil {
			return false
		}
		_, ok := m[key]
		return ok
	}

	// Top-level fields
	if v, ok := raw["version"]; ok {
		json.Unmarshal(v, &config.Version)
	}
	if v, ok := raw["debug"]; ok {
		json.Unmarshal(v, &config.Debug)
	}

	// UI section
	if v, ok := raw["ui"]; ok {
		var ui UIConfig
		if json.Unmarshal(v, &ui) == nil {
			if ui.Language != "" {
				config.UI.Language = ui.Language
			}
			if ui.Theme != "" {
				config.UI.Theme = ui.Theme
			}
		}
	}

	// Crypto section
	if v, ok := raw["crypto"]; ok {
		var c CryptoConfig
		if json.Unmarshal(v, &c) == nil {
			if c.DefaultAlgorithm != "" {
				config.Crypto.DefaultAlgorithm = c.DefaultAlgorithm
			}
			if c.DefaultKeyType != "" {
				config.Crypto.DefaultKeyType = c.DefaultKeyType
			}
			if c.PasswordMinLength > 0 {
				config.Crypto.PasswordMinLength = c.PasswordMinLength
			}
			if c.OTPKeyFormat != "" {
				config.Crypto.OTPKeyFormat = c.OTPKeyFormat
			}
			if keyExists(v, "require_strong_password") {
				config.Crypto.RequireStrongPass = c.RequireStrongPass
			}
		}
	}

	// Paths section
	if v, ok := raw["paths"]; ok {
		var p PathsConfig
		if json.Unmarshal(v, &p) == nil {
			if p.DefaultInputDir != "" {
				config.Paths.DefaultInputDir = p.DefaultInputDir
			}
			if p.DefaultOutputDir != "" {
				config.Paths.DefaultOutputDir = p.DefaultOutputDir
			}
			if p.LastInputFolder != "" {
				config.Paths.LastInputFolder = p.LastInputFolder
			}
			if p.LastOutputFolder != "" {
				config.Paths.LastOutputFolder = p.LastOutputFolder
			}
			if keyExists(v, "remember_last_folder") {
				config.Paths.RememberLastFolder = p.RememberLastFolder
			}
		}
	}

	// Batch section
	if v, ok := raw["batch"]; ok {
		var b BatchConfig
		if json.Unmarshal(v, &b) == nil {
			if b.MaxThreads > 0 {
				config.Batch.MaxThreads = b.MaxThreads
			}
			if keyExists(v, "parallel_processing") {
				config.Batch.ParallelProcessing = b.ParallelProcessing
			}
			if keyExists(v, "preserve_structure") {
				config.Batch.PreserveStructure = b.PreserveStructure
			}
		}
	}

	// Advanced section
	if v, ok := raw["advanced"]; ok {
		var a AdvancedConfig
		if json.Unmarshal(v, &a) == nil {
			if a.BufferSize > 0 {
				config.Advanced.BufferSize = a.BufferSize
			}
			if a.LogLevel != "" {
				config.Advanced.LogLevel = a.LogLevel
			}
		}
	}

	return nil
}

// Save 保存配置到磁盘（线程安全）
func (m *Manager) Save() error {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.saveLocked()
}

// saveLocked 保存配置（调用者必须持有至少读锁）
func (m *Manager) saveLocked() error {
	if m.config == nil {
		return fmt.Errorf("配置未加载")
	}

	data, err := json.MarshalIndent(m.config, "", "  ")
	if err != nil {
		return fmt.Errorf("序列化配置失败: %w", err)
	}

	if err := os.WriteFile(m.configFile, data, 0600); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}
	return nil
}

// Get 获取当前配置（返回指针，调用者不应修改）
func (m *Manager) Get() *Config {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.config
}

// Replace 原子替换当前配置（线程安全，用于设置对话框）
func (m *Manager) Replace(newConfig *Config) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.config = newConfig
}

// GetDefaultAlgorithm 获取默认算法
func (m *Manager) GetDefaultAlgorithm() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.config != nil {
		return m.config.Crypto.DefaultAlgorithm
	}
	return "AES256"
}

// GetDefaultKeyType 获取默认密钥类型
func (m *Manager) GetDefaultKeyType() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.config != nil {
		return m.config.Crypto.DefaultKeyType
	}
	return "random"
}

// GetBufferSizeMB 获取缓冲区大小（MB）
func (m *Manager) GetBufferSizeMB() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.config != nil && m.config.Advanced.BufferSize > 0 {
		return m.config.Advanced.BufferSize
	}
	return 10 // 默认10MB
}

// SetBufferSizeMB 设置缓冲区大小（MB）
func (m *Manager) SetBufferSizeMB(size int) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.config == nil {
		return fmt.Errorf("配置未加载")
	}
	if size < 1 || size > 100 {
		return fmt.Errorf("缓冲区大小必须在 1-100 MB 之间")
	}
	m.config.Advanced.BufferSize = size
	return m.saveLocked()
}

// GetLanguage 获取当前语言
func (m *Manager) GetLanguage() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.config != nil && m.config.UI.Language != "" {
		return m.config.UI.Language
	}
	return "zh_CN"
}

// SetLanguage 设置语言
func (m *Manager) SetLanguage(lang string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.config == nil {
		return fmt.Errorf("配置未加载")
	}
	m.config.UI.Language = lang
	return m.saveLocked()
}

// GetTheme 获取当前主题
func (m *Manager) GetTheme() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if m.config != nil && m.config.UI.Theme != "" {
		return m.config.UI.Theme
	}
	return "light"
}

// getConfigDir 获取配置目录（跨平台）
func getConfigDir() (string, error) {
	var base string
	switch runtime.GOOS {
	case "windows":
		appData := os.Getenv("APPDATA")
		if appData == "" {
			home, err := os.UserHomeDir()
			if err != nil {
				return "", err
			}
			base = filepath.Join(home, "AppData", "Roaming")
		} else {
			base = appData
		}
	case "darwin":
		home, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		base = filepath.Join(home, "Library", "Application Support")
	default:
		home, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		base = filepath.Join(home, ".config")
	}
	return filepath.Join(base, "miniCipher"), nil
}