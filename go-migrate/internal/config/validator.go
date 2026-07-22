package config

import "fmt"

// ValidateConfig 验证配置的有效性
func ValidateConfig(cfg *Config) error {
	if cfg == nil {
		return fmt.Errorf("配置不能为空")
	}

	// 验证算法
	if cfg.Crypto.DefaultAlgorithm != "OTP" && cfg.Crypto.DefaultAlgorithm != "AES256" {
		return fmt.Errorf("不支持的默认算法: %s", cfg.Crypto.DefaultAlgorithm)
	}

	// 验证密钥类型
	if cfg.Crypto.DefaultKeyType != "random" && cfg.Crypto.DefaultKeyType != "password" {
		return fmt.Errorf("不支持的默认密钥类型: %s", cfg.Crypto.DefaultKeyType)
	}

	// 验证密码最小长度
	if cfg.Crypto.PasswordMinLength < 1 || cfg.Crypto.PasswordMinLength > 128 {
		return fmt.Errorf("密码最小长度必须在 1-128 之间，当前值: %d", cfg.Crypto.PasswordMinLength)
	}

	// 验证缓冲区大小
	if cfg.Advanced.BufferSize < 1 || cfg.Advanced.BufferSize > 100 {
		return fmt.Errorf("缓冲区大小必须在 1-100 MB 之间，当前值: %d", cfg.Advanced.BufferSize)
	}

	// 验证批量线程数
	if cfg.Batch.MaxThreads < 1 || cfg.Batch.MaxThreads > 64 {
		return fmt.Errorf("最大线程数必须在 1-64 之间，当前值: %d", cfg.Batch.MaxThreads)
	}

	// 验证语言
	if cfg.UI.Language != "zh_CN" && cfg.UI.Language != "en_US" {
		return fmt.Errorf("不支持的语言: %s", cfg.UI.Language)
	}

	// 验证主题
	if cfg.UI.Theme != "light" && cfg.UI.Theme != "dark" {
		return fmt.Errorf("不支持的主题: %s", cfg.UI.Theme)
	}

	// 验证 OTP 密钥格式
	if cfg.Crypto.OTPKeyFormat != "hex" && cfg.Crypto.OTPKeyFormat != "binary" && cfg.Crypto.OTPKeyFormat != "" {
		return fmt.Errorf("不支持的OTP密钥格式: %s", cfg.Crypto.OTPKeyFormat)
	}

	// 验证日志级别
	if cfg.Advanced.LogLevel != "" &&
		cfg.Advanced.LogLevel != "DEBUG" &&
		cfg.Advanced.LogLevel != "INFO" &&
		cfg.Advanced.LogLevel != "WARNING" &&
		cfg.Advanced.LogLevel != "ERROR" {
		return fmt.Errorf("不支持的日志级别: %s", cfg.Advanced.LogLevel)
	}

	return nil
}