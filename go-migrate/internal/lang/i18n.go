package lang

// Languages 支持的语言
const (
	LangZH = "zh_CN"
	LangEN = "en_US"
)

// TranslationMap 翻译映射
type TranslationMap map[string]map[string]string

// Translator 翻译器
type Translator struct {
	currentLang  string
	translations TranslationMap
}

// NewTranslator 创建翻译器
func NewTranslator(lang string) *Translator {
	t := &Translator{
		currentLang:  lang,
		translations: defaultTranslations,
	}
	return t
}

// T 翻译指定key
func (t *Translator) T(key string) string {
	if langMap, ok := t.translations[t.currentLang]; ok {
		if val, ok := langMap[key]; ok {
			return val
		}
	}
	// fallback to English
	if langMap, ok := t.translations["en_US"]; ok {
		if val, ok := langMap[key]; ok {
			return val
		}
	}
	return key
}

// SetLanguage 切换语言
func (t *Translator) SetLanguage(lang string) {
	t.currentLang = lang
}

// GetLanguage 获取当前语言
func (t *Translator) GetLanguage() string {
	return t.currentLang
}

// defaultTranslations 默认翻译文本 — 与 Python 版本保持一致
var defaultTranslations = TranslationMap{
	"zh_CN": {
		"app.title":                          "MiniCipher - 文件加密工具",
		"algorithm.settings":                 "加密设置",
		"encryption_algorithm":               "加密算法",
		"key_type":                           "密钥类型",
		"password":                           "密码",
		"random_key":                         "随机密钥",
		"otp_info":                           "OTP 一次性密码本 - 理论上不可破解，密钥长度等于文件大小",
		"aes_info":                           "AES256-GCM - 行业标准加密算法，256位密钥，GCM认证模式",
		"encryption":                         "加密",
		"decryption":                         "解密",
		"input_file":                         "输入文件",
		"output_dir":                         "输出目录",
		"browse":                             "浏览",
		"start_encryption":                   "开始加密",
		"start_decryption":                   "开始解密",
		"batch.title":                        "批量操作",
		"batch.mode":                         "处理模式",
		"batch.mode.files":                   "选择文件",
		"batch.mode.folder":                  "选择文件夹",
		"batch.mode.recursive":               "递归处理文件夹",
		"batch.select_files":                 "选择文件/文件夹",
		"batch.output_dir":                   "输出目录",
		"batch.preserve_structure":           "保持目录结构",
		"batch.enable_parallel":              "启用并行处理",
		"batch.max_threads":                  "最大线程数",
		"batch.encrypt":                      "批量加密",
		"batch.decrypt":                      "批量解密",
		"batch.cancel":                       "取消",
		"batch.progress":                     "进度",
		"status.ready":                       "就绪",
		"status.encrypting":                  "正在加密...",
		"status.decrypting":                  "正在解密...",
		"status.encrypt_done":                "加密完成",
		"status.decrypt_done":                "解密完成",
		"status.error":                       "错误",
		"success":                            "成功",
		"error":                              "错误",
		"ok":                                 "确定",
		"cancel":                             "取消",
		"apply":                              "应用",
		"save":                               "保存",
		"reset":                              "重置",
		"settings":                           "设置",
		"file_menu":                          "文件",
		"language_menu":                      "语言",
		"theme_menu":                         "主题",
		"help_menu":                          "帮助",
		"about":                              "关于",
		"exit":                               "退出",
		"tips.encrypt":                       "提示：选择要加密的文件，设置算法和密钥后点击加密。\nOTP算法只支持随机密钥模式。\n密码模式需要至少8位密码。",
		"tips.decrypt":                       "提示：选择要解密的.enc文件和对应的密钥文件或密码。\n确保密钥/密码与加密时一致。",
		"error.invalid_file":                 "无效的文件",
		"error.invalid_password":             "无效的密码",
		"error.password_too_short":           "密码太短，至少需要%d个字符",
		"error.password_weak":                "密码强度不足，需要包含大写字母、小写字母和数字",
		"error.encryption_failed":            "加密失败: %s",
		"error.decryption_failed":            "解密失败: %s",
		"error.no_key":                       "需要密钥文件",
		"error.no_password":                  "密码模式需要密码",
		"success.encryption":                 "✅ 加密成功！\n算法: %s\n输出文件: %s",
		"success.decryption":                 "✅ 解密成功！\n算法: %s\n输出文件: %s",
		"success.encryption_with_key":        "✅ 加密成功！\n密钥文件: %s (请妥善保管!)",
		"key_save_failed":                    "⚠️ 密钥保持失败: %v",

		// 设置对话框
		"tab.general":                        "常规",
		"tab.encryption":                     "加密",
		"tab.paths":                          "路径",
		"tab.advanced":                       "高级",
		"settings.ui_language":               "界面语言",
		"settings.ui_theme":                  "界面主题",
		"settings.default_algorithm":         "默认算法",
		"settings.default_key_type":          "默认密钥类型",
		"settings.password_min_length":       "密码最小长度",
		"settings.require_strong_password":   "要求强密码（大小写字母+数字）",
		"settings.password_info":             "密码策略适用于密码模式加密。强密码需包含大写字母、小写字母和数字。",
		"settings.default_input_dir":         "默认输入目录",
		"settings.default_output_dir":        "默认输出目录",
		"settings.remember_last_folder":      "记住上次使用的文件夹",
		"settings.clear_history":             "清空历史记录",
		"settings.debug_mode":                "启用调试模式",
		"settings.log_level":                 "日志级别",
		"settings.advanced_info":             "当前版本的高级设置仅包含已实现的功能：\n• 调试模式：控制控制台输出详细程度\n• 日志级别：控制日志信息详细程度",
		"settings.success":                   "设置已保存！",
		"settings.success_restart":           "设置已保存！语言或主题更改将在重启后完全生效。",
		"settings.reset":                     "设置已重置为默认值",
		"settings.history_cleared":           "历史记录已清空",
		"theme.light":                        "浅色主题",
		"theme.dark":                         "深色主题",
	},
	"en_US": {
		"app.title":                          "MiniCipher - File Encryption Tool",
		"algorithm.settings":                 "Encryption Settings",
		"encryption_algorithm":               "Encryption Algorithm",
		"key_type":                           "Key Type",
		"password":                           "Password",
		"random_key":                         "Random Key",
		"otp_info":                           "OTP One-Time Pad - Theoretically unbreakable, key equals file size",
		"aes_info":                           "AES256-GCM - Industry standard encryption, 256-bit key, GCM mode",
		"encryption":                         "Encryption",
		"decryption":                         "Decryption",
		"input_file":                         "Input File",
		"output_dir":                         "Output Directory",
		"browse":                             "Browse",
		"start_encryption":                   "Start Encryption",
		"start_decryption":                   "Start Decryption",
		"batch.title":                        "Batch Processing",
		"batch.mode":                         "Processing Mode",
		"batch.mode.files":                   "Select Files",
		"batch.mode.folder":                  "Select Folder",
		"batch.mode.recursive":               "Recursive Folder",
		"batch.select_files":                 "Select Files/Folders",
		"batch.output_dir":                   "Output Directory",
		"batch.preserve_structure":           "Preserve Directory Structure",
		"batch.enable_parallel":              "Enable Parallel Processing",
		"batch.max_threads":                  "Max Threads",
		"batch.encrypt":                      "Batch Encrypt",
		"batch.decrypt":                      "Batch Decrypt",
		"batch.cancel":                       "Cancel",
		"batch.progress":                     "Progress",
		"status.ready":                       "Ready",
		"status.encrypting":                  "Encrypting...",
		"status.decrypting":                  "Decrypting...",
		"status.encrypt_done":                "Encryption Complete",
		"status.decrypt_done":                "Decryption Complete",
		"status.error":                       "Error",
		"success":                            "Success",
		"error":                              "Error",
		"ok":                                 "OK",
		"cancel":                             "Cancel",
		"apply":                              "Apply",
		"save":                               "Save",
		"reset":                              "Reset",
		"settings":                           "Settings",
		"file_menu":                          "File",
		"language_menu":                      "Language",
		"theme_menu":                         "Theme",
		"help_menu":                          "Help",
		"about":                              "About",
		"exit":                               "Exit",
		"tips.encrypt":                       "Tips: Select a file to encrypt, choose algorithm and key, then click encrypt.\nOTP algorithm only supports random key mode.\nPassword mode requires at least 8 characters.",
		"tips.decrypt":                       "Tips: Select the .enc file and corresponding key file or password.\nEnsure the key/password matches the one used for encryption.",
		"error.invalid_file":                 "Invalid file",
		"error.invalid_password":             "Invalid password",
		"error.password_too_short":           "Password too short, minimum %d characters required",
		"error.password_weak":                "Password strength insufficient, need uppercase, lowercase and digits",
		"error.encryption_failed":            "Encryption failed: %s",
		"error.decryption_failed":            "Decryption failed: %s",
		"error.no_key":                       "Key file required",
		"error.no_password":                  "Password mode requires a password",
		"success.encryption":                 "✅ Encryption successful!\nAlgorithm: %s\nOutput file: %s",
		"success.decryption":                 "✅ Decryption successful!\nAlgorithm: %s\nOutput file: %s",
		"success.encryption_with_key":        "✅ Encryption successful!\nKey file: %s (keep it safe!)",
		"key_save_failed":                    "⚠️ Key save failed: %v",

		// Settings dialog
		"tab.general":                        "General",
		"tab.encryption":                     "Encryption",
		"tab.paths":                          "Paths",
		"tab.advanced":                       "Advanced",
		"settings.ui_language":               "Language",
		"settings.ui_theme":                  "Theme",
		"settings.default_algorithm":         "Default Algorithm",
		"settings.default_key_type":          "Default Key Type",
		"settings.password_min_length":       "Min Password Length",
		"settings.require_strong_password":   "Require strong password (upper+lower+digits)",
		"settings.password_info":             "Password policy applies to password mode encryption. Strong password must contain uppercase, lowercase and digits.",
		"settings.default_input_dir":         "Default Input Directory",
		"settings.default_output_dir":        "Default Output Directory",
		"settings.remember_last_folder":      "Remember last used folder",
		"settings.clear_history":             "Clear History",
		"settings.debug_mode":                "Enable debug mode",
		"settings.log_level":                 "Log Level",
		"settings.advanced_info":             "Current version advanced settings include:\n• Debug mode: Controls console output verbosity\n• Log level: Controls log message detail",
		"settings.success":                   "Settings saved!",
		"settings.success_restart":           "Settings saved! Language or theme changes will fully take effect after restart.",
		"settings.reset":                     "Settings reset to defaults",
		"settings.history_cleared":           "History cleared",
		"theme.light":                        "Light Theme",
		"theme.dark":                         "Dark Theme",
	},
}