package lang

import "fmt"

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

// T 翻译指定key（不带参数格式化）
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

// Tf 翻译指定key并进行参数格式化
// 用法: t.Tf("error.encryption_failed", err.Error())
// 对应翻译模板: "加密失败: %s"
func (t *Translator) Tf(key string, args ...interface{}) string {
	format := t.T(key)
	if len(args) == 0 {
		return format
	}
	return fmt.Sprintf(format, args...)
}

// SetLanguage 切换语言
func (t *Translator) SetLanguage(lang string) {
	t.currentLang = lang
}

// GetLanguage 获取当前语言
func (t *Translator) GetLanguage() string {
	return t.currentLang
}

// defaultTranslations 默认翻译文本
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
		"batch.progress.status":              "%s: %d/%d - %s",
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
		"error.batch_failed":                 "批量处理失败: %s",
		"error.no_key":                       "需要密钥文件",
		"error.no_password":                  "密码模式需要密码",
		"error.need_both_dirs":               "请选择输入和输出目录",
		"error.input_file_missing":           "错误: 输入文件不存在: %s",
		"error.output_dir_missing":           "错误: 输出目录不存在: %s",
		"success.encryption":                 "✅ 加密成功！\n算法: %s\n输出文件: %s",
		"success.decryption":                 "✅ 解密成功！\n算法: %s\n输出文件: %s",
		"success.encryption_with_key":        "✅ 加密成功！\n密钥文件: %s (请妥善保管!)",
		"success.encryption_stat":            "✅ 加密成功!\n输出文件: %s",
		"success.decryption_stat":            "✅ 解密成功!\n输出文件: %s",
		"success.batch_result":               "✅ %d/%d 成功, %d 失败, 耗时 %s (%.1f%%)",
		"key_save_failed":                    "⚠️ 密钥保持失败: %v",
		"warn.key_save":                      "警告: 保存密钥文件失败: %v",
		"error.config_load":                  "加载配置失败: %v",
		"error.unknown_command":              "未知命令: %s",
		"error.missing_args":                 "错误: 需要输入文件路径和输出文件路径",
		"error.missing_encrypt_args":         "错误: 需要加密文件路径和输出文件路径",
		"error.algo_not_supported":           "不支持的算法: %s",
		"error.password_stdin":               "从标准输入读取密码失败: %v",
		"error.password_env_empty":           "环境变量 %s 为空或未设置",
		"warn.password_cli":                  "⚠️  警告: 使用 --password= 标志会将密码暴露在 shell 历史中。",
		"warn.password_cli_hint":             "   推荐使用 --password-stdin 或 --password-env=MINICIPHER_PASSWORD",
		"hint.password_usage":                "使用: echo <密码> | %s encrypt ... --password-stdin",
		"usage.title":                        "\n用法:\n  minicipher encrypt <input_file> <output_file> [选项]\n  minicipher decrypt <input_file> <output_file> [选项]\n  minicipher batch encrypt <input_dir> <output_dir> [选项]\n  minicipher batch decrypt <input_dir> <output_dir> [选项]\n  minicipher test\n\n加密选项:\n  --algo=AES256|OTP        加密算法 (默认: 配置文件设置)\n  --key-type=random|password  密钥类型 (默认: 配置文件设置)\n  --password-stdin          从标准输入读取密码 (推荐)\n  --password-env=VAR        从环境变量读取密码 (例如 --password-env=MINICIPHER_PASSWORD)\n\n解密选项:\n  --key-file=<path>         密钥文件路径\n  --password-stdin          从标准输入读取密码\n  --password-env=VAR        从环境变量读取密码\n\n批量选项:\n  --mode=recursive|folder|files  处理模式 (默认: recursive)\n  --preserve-structure      保持目录结构\n  --parallel                启用并行处理\n  --max-threads=<n>         最大线程数 (默认: 4)\n\n密码安全说明:\n  推荐使用 --password-stdin 或环境变量方式提供密码，\n  避免密码出现在命令行参数中（命令行参数会被记录到 shell 历史）。\n  也可以通过设置环境变量 MINICIPHER_PASSWORD 来提供密码。\n\n示例:\n  # 加密（推荐：stdin 密码）\n  echo \"MySecret123\" | minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-stdin\n\n  # 加密（环境变量密码）\n  MINICIPHER_PASSWORD=MySecret123 minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-env=MINICIPHER_PASSWORD\n\n  # 加密（随机密钥 - 无需密码）\n  minicipher encrypt doc.pdf doc.pdf.enc --algo=AES256 --key-type=random\n\n  # OTP 加密\n  minicipher encrypt data.bin data.bin.enc --algo=OTP\n\n  # 解密\n  echo \"MySecret123\" | minicipher decrypt secret.txt.enc output.txt --password-stdin\n  minicipher decrypt doc.pdf.enc output.pdf --key-file=doc.pdf.enc.key\n\n  # 批量加密\n  minicipher batch encrypt ./docs ./encrypted --mode=recursive --preserve-structure\n",

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
		"settings.otp_key_format":            "OTP密钥文件格式",
		"settings.otp_hex":                   "十六进制 (.txt)",
		"settings.otp_binary":                "二进制 (.bin)",
		"settings.otp_format_info":           "选择密钥文件保存格式，十六进制便于查看，二进制更节省空间",
		"settings.buffer_size":               "缓冲区大小 (MB)",
		"settings.enable_parallel":           "启用并行处理",
		"settings.max_threads":               "最大线程数",
		"settings.advanced_info":             "当前版本的高级设置仅包含已实现的功能：\n• 调试模式：控制控制台输出详细程度\n• 日志级别：控制日志信息详细程度\n• 缓冲区大小：控制文件分块处理的大小",
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
		"batch.progress.status":              "%s: %d/%d - %s",
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
		"error.batch_failed":                 "Batch processing failed: %s",
		"error.no_key":                       "Key file required",
		"error.no_password":                  "Password mode requires a password",
		"error.need_both_dirs":               "Please select input and output directories",
		"error.input_file_missing":           "Error: input file not found: %s",
		"error.output_dir_missing":           "Error: output directory not found: %s",
		"success.encryption":                 "✅ Encryption successful!\nAlgorithm: %s\nOutput file: %s",
		"success.decryption":                 "✅ Decryption successful!\nAlgorithm: %s\nOutput file: %s",
		"success.encryption_with_key":        "✅ Encryption successful!\nKey file: %s (keep it safe!)",
		"success.encryption_stat":            "✅ Encryption successful!\nOutput file: %s",
		"success.decryption_stat":            "✅ Decryption successful!\nOutput file: %s",
		"success.batch_result":               "✅ %d/%d succeeded, %d failed, elapsed %s (%.1f%%)",
		"key_save_failed":                    "⚠️ Key save failed: %v",
		"warn.key_save":                      "Warning: failed to save key file: %v",
		"error.config_load":                  "Failed to load config: %v",
		"error.unknown_command":              "Unknown command: %s",
		"error.missing_args":                 "Error: input and output file paths required",
		"error.missing_encrypt_args":         "Error: input and output file paths required",
		"error.algo_not_supported":           "Unsupported algorithm: %s",
		"error.password_stdin":               "Failed to read password from stdin: %v",
		"error.password_env_empty":           "Environment variable %s is empty or not set",
		"warn.password_cli":                  "⚠️  Warning: using --password= flag exposes the password in shell history.",
		"warn.password_cli_hint":             "   Use --password-stdin or --password-env=MINICIPHER_PASSWORD instead",
		"hint.password_usage":                "Usage: echo <password> | %s encrypt ... --password-stdin",
		"usage.title":                        "\nUsage:\n  minicipher encrypt <input_file> <output_file> [options]\n  minicipher decrypt <input_file> <output_file> [options]\n  minicipher batch encrypt <input_dir> <output_dir> [options]\n  minicipher batch decrypt <input_dir> <output_dir> [options]\n  minicipher test\n\nEncrypt options:\n  --algo=AES256|OTP        Encryption algorithm (default: config setting)\n  --key-type=random|password  Key type (default: config setting)\n  --password-stdin          Read password from stdin (recommended)\n  --password-env=VAR        Read password from env var (e.g. --password-env=MINICIPHER_PASSWORD)\n\nDecrypt options:\n  --key-file=<path>         Key file path\n  --password-stdin          Read password from stdin\n  --password-env=VAR        Read password from env var\n\nBatch options:\n  --mode=recursive|folder|files  Processing mode (default: recursive)\n  --preserve-structure      Preserve directory structure\n  --parallel                Enable parallel processing\n  --max-threads=<n>         Max threads (default: 4)\n\nPassword security:\n  Use --password-stdin or environment variable to provide password,\n  avoid passwords in command line arguments (they get logged in shell history).\n  You can also set the MINICIPHER_PASSWORD environment variable.\n\nExamples:\n  # Encrypt (recommended: stdin password)\n  echo \"MySecret123\" | minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-stdin\n\n  # Encrypt (env var password)\n  MINICIPHER_PASSWORD=MySecret123 minicipher encrypt secret.txt secret.txt.enc --key-type=password --password-env=MINICIPHER_PASSWORD\n\n  # Encrypt (random key - no password needed)\n  minicipher encrypt doc.pdf doc.pdf.enc --algo=AES256 --key-type=random\n\n  # OTP encrypt\n  minicipher encrypt data.bin data.bin.enc --algo=OTP\n\n  # Decrypt\n  echo \"MySecret123\" | minicipher decrypt secret.txt.enc output.txt --password-stdin\n  minicipher decrypt doc.pdf.enc output.pdf --key-file=doc.pdf.enc.key\n\n  # Batch encrypt\n  minicipher batch encrypt ./docs ./encrypted --mode=recursive --preserve-structure\n",

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
		"settings.otp_key_format":            "OTP Key File Format",
		"settings.otp_hex":                   "Hexadecimal (.txt)",
		"settings.otp_binary":                "Binary (.bin)",
		"settings.otp_format_info":           "Select key file format, hexadecimal for easy viewing, binary for space efficiency",
		"settings.buffer_size":               "Buffer Size (MB)",
		"settings.enable_parallel":           "Enable Parallel Processing",
		"settings.max_threads":               "Max Threads",
		"settings.advanced_info":             "Current version advanced settings include:\n• Debug mode: Controls console output verbosity\n• Log level: Controls log message detail\n• Buffer size: Controls file chunk processing size",
		"settings.success":                   "Settings saved!",
		"settings.success_restart":           "Settings saved! Language or theme changes will fully take effect after restart.",
		"settings.reset":                     "Settings reset to defaults",
		"settings.history_cleared":           "History cleared",
		"theme.light":                        "Light Theme",
		"theme.dark":                         "Dark Theme",
	},
}