package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

// Config 应用配置
type Config struct {
	Version string         `json:"version"`
	UI      UIConfig       `json:"ui"`
	Crypto  CryptoConfig   `json:"crypto"`
	Paths   PathsConfig    `json:"paths"`
	Batch   BatchConfig    `json:"batch"`
	Debug   bool           `json:"debug"`
}

// UIConfig 界面配置
type UIConfig struct {
	Language string `json:"language"` // "zh_CN" or "en_US"
	Theme    string `json:"theme"`    // "light" or "dark"
}

// CryptoConfig 加密配置
type CryptoConfig struct {
	DefaultAlgorithm    string `json:"default_algorithm"`    // "OTP" or "AES256"
	DefaultKeyType      string `json:"default_key_type"`     // "random" or "password"
	PasswordMinLength   int    `json:"password_min_length"`
	RequireStrongPass   bool   `json:"require_strong_password"`
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
		Version: "2.0",
		UI: UIConfig{
			Language: "zh_CN",
			Theme:    "light",
		},
		Crypto: CryptoConfig{
			DefaultAlgorithm:  "AES256",
			DefaultKeyType:    "random",
			PasswordMinLength: 8,
			RequireStrongPass: true,
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
	}
}

// Manager 配置管理器
type Manager struct {
	configDir  string
	configFile string
	config     *Config
}

// NewManager 创建配置管理器
func NewManager() *Manager {
	return &Manager{}
}

// Load 加载配置（如果不存在则使用默认配置）
func (m *Manager) Load() (*Config, error) {
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

	config := DefaultConfig()
	if err := json.Unmarshal(data, config); err != nil {
		// 配置文件损坏，使用默认配置
		m.config = DefaultConfig()
		m.Save()
		return m.config, nil
	}

	m.config = config
	return config, nil
}

// Save 保存配置
func (m *Manager) Save() error {
	if m.config == nil {
		return fmt.Errorf("配置未加载")
	}

	data, err := json.MarshalIndent(m.config, "", "  ")
	if err != nil {
		return fmt.Errorf("序列化配置失败: %w", err)
	}

	if err := os.WriteFile(m.configFile, data, 0644); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}
	return nil
}

// Get 获取当前配置
func (m *Manager) Get() *Config {
	return m.config
}

// GetDefaultAlgorithm 获取默认算法
func (m *Manager) GetDefaultAlgorithm() string {
	if m.config != nil {
		return m.config.Crypto.DefaultAlgorithm
	}
	return "AES256"
}

// GetDefaultKeyType 获取默认密钥类型
func (m *Manager) GetDefaultKeyType() string {
	if m.config != nil {
		return m.config.Crypto.DefaultKeyType
	}
	return "random"
}

// GetBufferSizeMB 获取缓冲区大小（MB）
func (m *Manager) GetBufferSizeMB() int {
	return 10 // 默认10MB
}

// GetLanguage 获取当前语言
func (m *Manager) GetLanguage() string {
	if m.config != nil && m.config.UI.Language != "" {
		return m.config.UI.Language
	}
	return "zh_CN"
}

// SetLanguage 设置语言
func (m *Manager) SetLanguage(lang string) error {
	if m.config == nil {
		return fmt.Errorf("配置未加载")
	}
	m.config.UI.Language = lang
	return m.Save()
}

// GetTheme 获取当前主题
func (m *Manager) GetTheme() string {
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