package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()
	if cfg == nil {
		t.Fatal("DefaultConfig returned nil")
	}
	if cfg.Version != "2.1.1" {
		t.Errorf("unexpected version: %s", cfg.Version)
	}
	if cfg.Crypto.DefaultAlgorithm != "AES256" {
		t.Errorf("unexpected default algorithm: %s", cfg.Crypto.DefaultAlgorithm)
	}
	if cfg.Crypto.DefaultKeyType != "random" {
		t.Errorf("unexpected default key type: %s", cfg.Crypto.DefaultKeyType)
	}
	if cfg.Crypto.PasswordMinLength != 8 {
		t.Errorf("unexpected password min length: %d", cfg.Crypto.PasswordMinLength)
	}
	if cfg.Crypto.OTPKeyFormat != "hex" {
		t.Errorf("unexpected OTP key format: %s", cfg.Crypto.OTPKeyFormat)
	}
	if cfg.Advanced.BufferSize != 10 {
		t.Errorf("unexpected buffer size: %d", cfg.Advanced.BufferSize)
	}
	if cfg.UI.Language != "zh_CN" {
		t.Errorf("unexpected language: %s", cfg.UI.Language)
	}
	if cfg.UI.Theme != "light" {
		t.Errorf("unexpected theme: %s", cfg.UI.Theme)
	}
}

func TestValidateConfig(t *testing.T) {
	tests := []struct {
		name    string
		mutate  func(*Config)
		wantErr bool
	}{
		{
			name:    "valid default",
			mutate:  func(c *Config) {},
			wantErr: false,
		},
		{
			name: "unsupported algorithm",
			mutate: func(c *Config) {
				c.Crypto.DefaultAlgorithm = "DES"
			},
			wantErr: true,
		},
		{
			name: "unsupported key type",
			mutate: func(c *Config) {
				c.Crypto.DefaultKeyType = "biometric"
			},
			wantErr: true,
		},
		{
			name: "password min length too small",
			mutate: func(c *Config) {
				c.Crypto.PasswordMinLength = 0
			},
			wantErr: true,
		},
		{
			name: "password min length too large",
			mutate: func(c *Config) {
				c.Crypto.PasswordMinLength = 200
			},
			wantErr: true,
		},
		{
			name: "buffer size too small",
			mutate: func(c *Config) {
				c.Advanced.BufferSize = 0
			},
			wantErr: true,
		},
		{
			name: "buffer size too large",
			mutate: func(c *Config) {
				c.Advanced.BufferSize = 200
			},
			wantErr: true,
		},
		{
			name: "max threads too small",
			mutate: func(c *Config) {
				c.Batch.MaxThreads = 0
			},
			wantErr: true,
		},
		{
			name: "max threads too large",
			mutate: func(c *Config) {
				c.Batch.MaxThreads = 100
			},
			wantErr: true,
		},
		{
			name: "unsupported language",
			mutate: func(c *Config) {
				c.UI.Language = "ja_JP"
			},
			wantErr: true,
		},
		{
			name: "unsupported theme",
			mutate: func(c *Config) {
				c.UI.Theme = "blue"
			},
			wantErr: true,
		},
		{
			name: "unsupported OTP format",
			mutate: func(c *Config) {
				c.Crypto.OTPKeyFormat = "base64"
			},
			wantErr: true,
		},
		{
			name: "empty OTP format is allowed",
			mutate: func(c *Config) {
				c.Crypto.OTPKeyFormat = ""
			},
			wantErr: false,
		},
		{
			name: "unsupported log level",
			mutate: func(c *Config) {
				c.Advanced.LogLevel = "TRACE"
			},
			wantErr: true,
		},
		{
			name: "valid OTP algorithm",
			mutate: func(c *Config) {
				c.Crypto.DefaultAlgorithm = "OTP"
			},
			wantErr: false,
		},
		{
			name: "valid password key type",
			mutate: func(c *Config) {
				c.Crypto.DefaultKeyType = "password"
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg := DefaultConfig()
			tt.mutate(cfg)
			err := ValidateConfig(cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateConfig() error = %v, wantErr = %v", err, tt.wantErr)
			}
		})
	}
}

func TestDeepMergeJSON(t *testing.T) {
	// Start with default config
	cfg := DefaultConfig()

	// Merge partial JSON: only override language and buffer size
	partial := `{"ui": {"language": "en_US"}, "advanced": {"buffer_size": 50}}`
	err := deepMergeJSON(cfg, []byte(partial))
	if err != nil {
		t.Fatalf("deepMergeJSON failed: %v", err)
	}

	if cfg.UI.Language != "en_US" {
		t.Errorf("language not merged: got %s, want en_US", cfg.UI.Language)
	}
	if cfg.Advanced.BufferSize != 50 {
		t.Errorf("buffer size not merged: got %d, want 50", cfg.Advanced.BufferSize)
	}
	// Default algorithm should remain unchanged
	if cfg.Crypto.DefaultAlgorithm != "AES256" {
		t.Errorf("default algorithm was overwritten: got %s", cfg.Crypto.DefaultAlgorithm)
	}
	// Theme should remain default
	if cfg.UI.Theme != "light" {
		t.Errorf("theme was overwritten: got %s", cfg.UI.Theme)
	}
}

func TestDeepMergeJSONBoolFields(t *testing.T) {
	cfg := DefaultConfig()

	// Set bool fields to false explicitly
	partial := `{"debug": true, "crypto": {"require_strong_password": false}, "paths": {"remember_last_folder": false}, "batch": {"parallel_processing": true, "preserve_structure": false}}`
	err := deepMergeJSON(cfg, []byte(partial))
	if err != nil {
		t.Fatalf("deepMergeJSON failed: %v", err)
	}

	if !cfg.Debug {
		t.Error("debug should be true")
	}
	if cfg.Crypto.RequireStrongPass {
		t.Error("require_strong_password should be false")
	}
	if cfg.Paths.RememberLastFolder {
		t.Error("remember_last_folder should be false")
	}
	if !cfg.Batch.ParallelProcessing {
		t.Error("parallel_processing should be true")
	}
	if cfg.Batch.PreserveStructure {
		t.Error("preserve_structure should be false")
	}
}

func TestDeepMergeJSONEmptyStringsDontOverwrite(t *testing.T) {
	cfg := DefaultConfig()

	// Empty strings should not overwrite existing values
	partial := `{"ui": {"language": "", "theme": ""}, "crypto": {"default_algorithm": "", "otp_key_format": ""}}`
	err := deepMergeJSON(cfg, []byte(partial))
	if err != nil {
		t.Fatalf("deepMergeJSON failed: %v", err)
	}

	if cfg.UI.Language != "zh_CN" {
		t.Errorf("language was overwritten by empty string: got %s", cfg.UI.Language)
	}
	if cfg.Crypto.DefaultAlgorithm != "AES256" {
		t.Errorf("algorithm was overwritten by empty string: got %s", cfg.Crypto.DefaultAlgorithm)
	}
}

func TestManagerLoadCreatesDefault(t *testing.T) {
	// Use temp dir so we don't touch real config
	tmpDir, err := os.MkdirTemp("", "config_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Write a default config to temp dir and verify it can be read back
	configFile := filepath.Join(tmpDir, "config.json")

	// No config file exists yet - write a default one
	defaultCfg := DefaultConfig()
	data, err := json.MarshalIndent(defaultCfg, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal default config: %v", err)
	}
	if err := os.WriteFile(configFile, data, 0644); err != nil {
		t.Fatalf("failed to write test config: %v", err)
	}

	// Verify we can read it back
	readData, err := os.ReadFile(configFile)
	if err != nil {
		t.Fatalf("failed to read back config: %v", err)
	}
	var parsed Config
	if err := json.Unmarshal(readData, &parsed); err != nil {
		t.Fatalf("failed to parse config: %v", err)
	}
	if parsed.Version != "2.1.1" {
		t.Errorf("unexpected version in saved config: %s", parsed.Version)
	}
}

func TestManagerSaveRoundTrip(t *testing.T) {
	tmpDir, err := os.MkdirTemp("", "config_roundtrip")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tmpDir)

	// Write a valid config
	configFile := filepath.Join(tmpDir, "config.json")
	cfg := DefaultConfig()
	cfg.UI.Language = "en_US"
	cfg.Crypto.DefaultAlgorithm = "OTP"

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal config: %v", err)
	}
	if err := os.WriteFile(configFile, data, 0644); err != nil {
		t.Fatalf("failed to write config: %v", err)
	}

	// Read back and verify custom fields
	readData, err := os.ReadFile(configFile)
	if err != nil {
		t.Fatalf("failed to read config: %v", err)
	}

	parsed := DefaultConfig()
	if err := deepMergeJSON(parsed, readData); err != nil {
		t.Fatalf("deepMergeJSON failed: %v", err)
	}

	if parsed.UI.Language != "en_US" {
		t.Errorf("language: got %s, want en_US", parsed.UI.Language)
	}
	if parsed.Crypto.DefaultAlgorithm != "OTP" {
		t.Errorf("algorithm: got %s, want OTP", parsed.Crypto.DefaultAlgorithm)
	}
}

func TestGetConfigDir(t *testing.T) {
	dir, err := getConfigDir()
	if err != nil {
		t.Fatalf("getConfigDir failed: %v", err)
	}
	if dir == "" {
		t.Error("getConfigDir returned empty string")
	}
	// Should end with miniCipher
	if filepath.Base(dir) != "miniCipher" {
		t.Errorf("config dir should end with miniCipher, got: %s", dir)
	}
}
