package config

import (
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

// ValidationType 验证类型
type ValidationType string

const (
	ValidationString  ValidationType = "string"
	ValidationInteger ValidationType = "integer"
	ValidationFloat   ValidationType = "float"
	ValidationBoolean ValidationType = "boolean"
	ValidationEnum    ValidationType = "enum"
	ValidationPath    ValidationType = "path"
	ValidationEmail   ValidationType = "email"
	ValidationURL     ValidationType = "url"
	ValidationRegex   ValidationType = "regex"
)

// ValidationRule 验证规则
type ValidationRule struct {
	Type         ValidationType `json:"type"`
	Required     bool           `json:"required"`
	MinLen       *int           `json:"min_len,omitempty"`
	MaxLen       *int           `json:"max_len,omitempty"`
	MinVal       *float64       `json:"min_val,omitempty"`
	MaxVal       *float64       `json:"max_val,omitempty"`
	Pattern      string         `json:"pattern,omitempty"`
	AllowedValues []string      `json:"allowed_values,omitempty"`
	MustExist    bool           `json:"must_exist,omitempty"`
	MustBeDir    bool           `json:"must_be_dir,omitempty"`
	MustBeFile   bool           `json:"must_be_file,omitempty"`
	AllowEmpty   bool           `json:"allow_empty,omitempty"`
	Default      interface{}    `json:"default,omitempty"`
}

// ValidationError 验证错误
type ValidationError struct {
	ConfigKey string
	Value     interface{}
	Message   string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("配置项 '%s' 验证失败: %s (值: %v)", e.ConfigKey, e.Message, e.Value)
}

// ConfigValidator 配置验证器
type ConfigValidator struct {
	rules map[string]*ValidationRule
}

// NewConfigValidator 创建配置验证器
func NewConfigValidator() *ConfigValidator {
	return &ConfigValidator{
		rules: getDefaultRules(),
	}
}

// getDefaultRules 获取默认验证规则
func getDefaultRules() map[string]*ValidationRule {
	return map[string]*ValidationRule{
		// 版本
		"version": {
			Type:     ValidationString,
			MinLen:   intPtr(1),
			MaxLen:   intPtr(20),
			Required: true,
		},
		// 语言设置
		"ui.language": {
			Type:          ValidationEnum,
			AllowedValues: []string{"zh_CN", "en_US"},
			Required:      true,
			Default:       "zh_CN",
		},
		// 主题设置
		"ui.theme": {
			Type:          ValidationEnum,
			AllowedValues: []string{"light", "dark"},
			Required:      true,
			Default:       "light",
		},
		// 加密配置
		"crypto.default_algorithm": {
			Type:          ValidationEnum,
			AllowedValues: []string{"OTP", "AES256"},
			Required:      true,
			Default:       "AES256",
		},
		"crypto.default_key_type": {
			Type:          ValidationEnum,
			AllowedValues: []string{"random", "password"},
			Required:      true,
			Default:       "random",
		},
		"crypto.password_min_length": {
			Type:     ValidationInteger,
			Required: true,
			MinVal:   floatPtr(4),
			MaxVal:   floatPtr(32),
			Default:  8,
		},
		"crypto.require_strong_password": {
			Type:     ValidationBoolean,
			Required: true,
			Default:  true,
		},
		// 路径配置
		"paths.default_input_dir": {
			Type:       ValidationPath,
			MustBeDir:  true,
			AllowEmpty: true,
			Required:   false,
			Default:    "",
		},
		"paths.default_output_dir": {
			Type:       ValidationPath,
			MustBeDir:  true,
			AllowEmpty: true,
			Required:   false,
			Default:    "",
		},
		"paths.remember_last_folder": {
			Type:     ValidationBoolean,
			Required: true,
			Default:  true,
		},
		"paths.last_input_folder": {
			Type:       ValidationPath,
			MustBeDir:  true,
			AllowEmpty: true,
			Required:   false,
			Default:    "",
		},
		"paths.last_output_folder": {
			Type:       ValidationPath,
			MustBeDir:  true,
			AllowEmpty: true,
			Required:   false,
			Default:    "",
		},
		// 高级配置
		"advanced.debug_mode": {
			Type:     ValidationBoolean,
			Required: true,
			Default:  false,
		},
		"advanced.log_level": {
			Type:          ValidationEnum,
			AllowedValues: []string{"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"},
			Required:      true,
			Default:       "INFO",
		},
		// 批量配置
		"batch.parallel_processing": {
			Type:     ValidationBoolean,
			Required: true,
			Default:  false,
		},
		"batch.max_threads": {
			Type:     ValidationInteger,
			Required: true,
			MinVal:   floatPtr(1),
			MaxVal:   floatPtr(16),
			Default:  4,
		},
		"batch.preserve_structure": {
			Type:     ValidationBoolean,
			Required: true,
			Default:  true,
		},
	}
}

// intPtr 返回 int 指针
func intPtr(i int) *int {
	return &i
}

// floatPtr 返回 float64 指针
func floatPtr(f float64) *float64 {
	return &f
}

// ValidateKey 验证单个配置键的值
func (cv *ConfigValidator) ValidateKey(configKey string, value interface{}) (bool, string) {
	rule, ok := cv.rules[configKey]
	if !ok {
		return true, "" // 没有验证规则，直接通过
	}

	// 检查必需性
	if value == nil && rule.Required {
		return false, "配置项是必需的"
	}
	if value == nil {
		return true, ""
	}

	switch rule.Type {
	case ValidationString:
		return cv.validateString(value, rule)
	case ValidationInteger:
		return cv.validateInteger(value, rule)
	case ValidationFloat:
		return cv.validateFloat(value, rule)
	case ValidationBoolean:
		return cv.validateBoolean(value)
	case ValidationEnum:
		return cv.validateEnum(value, rule)
	case ValidationPath:
		return cv.validatePath(value, rule)
	default:
		return false, fmt.Sprintf("未知的验证类型: %s", rule.Type)
	}
}

// ValidateConfig 验证整个配置字典
func (cv *ConfigValidator) ValidateConfig(config map[string]interface{}) (bool, map[string]string) {
	errors := make(map[string]string)
	for key, rule := range cv.rules {
		value := getNestedValue(config, key)
		isValid, msg := cv.validateValue(value, rule)
		if !isValid {
			errors[key] = msg
		}
	}
	return len(errors) == 0, errors
}

func (cv *ConfigValidator) validateValue(value interface{}, rule *ValidationRule) (bool, string) {
	if value == nil && rule.Required {
		return false, "配置项是必需的"
	}
	if value == nil {
		return true, ""
	}

	switch rule.Type {
	case ValidationString:
		return cv.validateString(value, rule)
	case ValidationInteger:
		return cv.validateInteger(value, rule)
	case ValidationFloat:
		return cv.validateFloat(value, rule)
	case ValidationBoolean:
		return cv.validateBoolean(value)
	case ValidationEnum:
		return cv.validateEnum(value, rule)
	case ValidationPath:
		return cv.validatePath(value, rule)
	default:
		return false, fmt.Sprintf("未知的验证类型: %s", rule.Type)
	}
}

func (cv *ConfigValidator) validateString(value interface{}, rule *ValidationRule) (bool, string) {
	str, ok := value.(string)
	if !ok {
		return false, "值不是字符串类型"
	}

	if str == "" && !rule.AllowEmpty {
		return false, "字符串不能为空"
	}
	if str == "" {
		return true, ""
	}

	if rule.MinLen != nil && len(str) < *rule.MinLen {
		return false, fmt.Sprintf("字符串长度不能小于 %d", *rule.MinLen)
	}
	if rule.MaxLen != nil && len(str) > *rule.MaxLen {
		return false, fmt.Sprintf("字符串长度不能大于 %d", *rule.MaxLen)
	}
	if rule.Pattern != "" {
		matched, _ := regexp.MatchString(rule.Pattern, str)
		if !matched {
			return false, "值不符合正则表达式模式"
		}
	}

	return true, ""
}

func (cv *ConfigValidator) validateInteger(value interface{}, rule *ValidationRule) (bool, string) {
	var intVal int
	switch v := value.(type) {
	case int:
		intVal = v
	case float64:
		intVal = int(v)
	case string:
		var err error
		intVal, err = strconv.Atoi(v)
		if err != nil {
			return false, "无效的整数值"
		}
	default:
		return false, "无效的整数值"
	}

	if rule.MinVal != nil && float64(intVal) < *rule.MinVal {
		return false, fmt.Sprintf("整数值不能小于 %.0f", *rule.MinVal)
	}
	if rule.MaxVal != nil && float64(intVal) > *rule.MaxVal {
		return false, fmt.Sprintf("整数值不能大于 %.0f", *rule.MaxVal)
	}

	return true, ""
}

func (cv *ConfigValidator) validateFloat(value interface{}, rule *ValidationRule) (bool, string) {
	f, err := toFloat64(value)
	if err != nil {
		return false, "无效的浮点数值"
	}

	if rule.MinVal != nil && f < *rule.MinVal {
		return false, fmt.Sprintf("浮点数值不能小于 %f", *rule.MinVal)
	}
	if rule.MaxVal != nil && f > *rule.MaxVal {
		return false, fmt.Sprintf("浮点数值不能大于 %f", *rule.MaxVal)
	}

	return true, ""
}

func (cv *ConfigValidator) validateBoolean(value interface{}) (bool, string) {
	switch v := value.(type) {
	case bool:
		return true, ""
	case string:
		lower := strings.ToLower(v)
		if lower == "true" || lower == "false" || lower == "yes" || lower == "no" || lower == "1" || lower == "0" {
			return true, ""
		}
	case float64:
		if v == 0 || v == 1 {
			return true, ""
		}
	}
	return false, "无效的布尔值"
}

func (cv *ConfigValidator) validateEnum(value interface{}, rule *ValidationRule) (bool, string) {
	str, ok := value.(string)
	if !ok {
		return false, "枚举值必须是字符串"
	}

	for _, allowed := range rule.AllowedValues {
		if str == allowed {
			return true, ""
		}
	}

	return false, fmt.Sprintf("值必须在允许的列表中: %v", rule.AllowedValues)
}

func (cv *ConfigValidator) validatePath(value interface{}, rule *ValidationRule) (bool, string) {
	str, ok := value.(string)
	if !ok {
		return false, "路径必须是字符串"
	}

	if str == "" {
		if rule.AllowEmpty {
			return true, ""
		}
		return false, "路径不能为空"
	}

	if rule.MustExist {
		if _, err := os.Stat(str); os.IsNotExist(err) {
			return false, "路径必须存在"
		}
	}

	if rule.MustBeDir {
		info, err := os.Stat(str)
		if err == nil && !info.IsDir() {
			return false, "路径必须是目录"
		}
	}

	if rule.MustBeFile {
		info, err := os.Stat(str)
		if err == nil && info.IsDir() {
			return false, "路径必须是文件"
		}
	}

	return true, ""
}

// Sanitize 使用默认值修复无效配置
func (cv *ConfigValidator) Sanitize(config map[string]interface{}) (map[string]interface{}, map[string]string) {
	result := make(map[string]interface{})
	for k, v := range config {
		result[k] = v
	}

	errors := make(map[string]string)
	for key, rule := range cv.rules {
		value := getNestedValue(result, key)
		isValid, _ := cv.validateValue(value, rule)
		if !isValid && rule.Default != nil {
			setNestedValue(result, key, rule.Default)
		} else if !isValid {
			errors[key] = "验证失败且无默认值"
		}
	}

	return result, errors
}

// GetDefault 获取配置键的默认值
func (cv *ConfigValidator) GetDefault(configKey string) interface{} {
	if rule, ok := cv.rules[configKey]; ok {
		return rule.Default
	}
	return nil
}

// GetAllDefaults 获取所有配置键的默认值
func (cv *ConfigValidator) GetAllDefaults() map[string]interface{} {
	defaults := make(map[string]interface{})
	for key, rule := range cv.rules {
		if rule.Default != nil {
			defaults[key] = rule.Default
		}
	}
	return defaults
}

// getNestedValue 使用点分隔符从嵌套map中获取值
func getNestedValue(config map[string]interface{}, key string) interface{} {
	keys := strings.Split(key, ".")
	current := config
	for i, k := range keys {
		if i == len(keys)-1 {
			return current[k]
		}
		if v, ok := current[k]; ok {
			if m, ok := v.(map[string]interface{}); ok {
				current = m
			} else {
				return nil
			}
		} else {
			return nil
		}
	}
	return nil
}

// setNestedValue 使用点分隔符在嵌套map中设置值
func setNestedValue(config map[string]interface{}, key string, value interface{}) {
	keys := strings.Split(key, ".")
	current := config
	for i, k := range keys {
		if i == len(keys)-1 {
			current[k] = value
			return
		}
		if _, ok := current[k]; !ok {
			current[k] = make(map[string]interface{})
		}
		if m, ok := current[k].(map[string]interface{}); ok {
			current = m
		} else {
			return
		}
	}
}

// toFloat64 将任意值转换为 float64
func toFloat64(value interface{}) (float64, error) {
	switch v := value.(type) {
	case float64:
		return v, nil
	case float32:
		return float64(v), nil
	case int:
		return float64(v), nil
	case int64:
		return float64(v), nil
	case string:
		return strconv.ParseFloat(v, 64)
	default:
		return 0, fmt.Errorf("cannot convert %T to float64", value)
	}
}