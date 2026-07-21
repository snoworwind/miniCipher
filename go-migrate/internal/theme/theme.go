package theme

// ThemeType 主题类型
type ThemeType string

const (
	ThemeLight ThemeType = "light"
	ThemeDark  ThemeType = "dark"
)

// ThemeColors 主题颜色
type ThemeColors struct {
	BG              string
	FG              string
	Primary         string
	Secondary       string
	Accent          string
	Success         string
	Warning         string
	Error           string
	Border          string
	Hover           string
	Active          string
	TextPrimary     string
	TextSecondary   string
	Disabled        string
	WindowBG        string
	FrameBG         string
	EntryBG         string
	EntryFG         string
	ButtonBG        string
	ButtonFG        string
	LabelBG         string
	LabelFG         string
	ComboBoxBG      string
	ComboBoxFG      string
	StatusBG        string
	StatusFG        string
	MenuBG          string
	MenuFG          string
	MenuActiveBG    string
	MenuActiveFG    string
	MenuDisabledFG  string
}

// LightColors 浅色主题颜色
var LightColors = ThemeColors{
	BG:              "#ffffff",
	FG:              "#000000",
	Primary:         "#2196F3",
	Secondary:       "#f5f5f5",
	Accent:          "#4CAF50",
	Success:         "#4CAF50",
	Warning:         "#FF9800",
	Error:           "#F44336",
	Border:          "#e0e0e0",
	Hover:           "#1976D2",
	Active:          "#0D47A1",
	TextPrimary:     "#212121",
	TextSecondary:   "#757575",
	Disabled:        "#bdbdbd",
	WindowBG:        "#ffffff",
	FrameBG:         "#fafafa",
	EntryBG:         "#ffffff",
	EntryFG:         "#000000",
	ButtonBG:        "#2196F3",
	ButtonFG:        "#ffffff",
	LabelBG:         "#ffffff",
	LabelFG:         "#212121",
	ComboBoxBG:      "#ffffff",
	ComboBoxFG:      "#000000",
	StatusBG:        "#e3f2fd",
	StatusFG:        "#1976D2",
	MenuBG:          "#ffffff",
	MenuFG:          "#212121",
	MenuActiveBG:    "#2196F3",
	MenuActiveFG:    "#ffffff",
	MenuDisabledFG:  "#bdbdbd",
}

// DarkColors 深色主题颜色
var DarkColors = ThemeColors{
	BG:              "#1e1e1e",
	FG:              "#e0e0e0",
	Primary:         "#1565C0",
	Secondary:       "#303030",
	Accent:          "#81C784",
	Success:         "#81C784",
	Warning:         "#FFB74D",
	Error:           "#E57373",
	Border:          "#555555",
	Hover:           "#0D47A1",
	Active:          "#0D47A1",
	TextPrimary:     "#ffffff",
	TextSecondary:   "#aaaaaa",
	Disabled:        "#666666",
	WindowBG:        "#1e1e1e",
	FrameBG:         "#252525",
	EntryBG:         "#2d2d2d",
	EntryFG:         "#ffffff",
	ButtonBG:        "#1565C0",
	ButtonFG:        "#ffffff",
	LabelBG:         "#1e1e1e",
	LabelFG:         "#ffffff",
	ComboBoxBG:      "#2d2d2d",
	ComboBoxFG:      "#ffffff",
	StatusBG:        "#252525",
	StatusFG:        "#90CAF9",
	MenuBG:          "#252525",
	MenuFG:          "#e0e0e0",
	MenuActiveBG:    "#1565C0",
	MenuActiveFG:    "#ffffff",
	MenuDisabledFG:  "#666666",
}

// Manager 主题管理器
type Manager struct {
	currentTheme ThemeType
}

// NewManager 创建主题管理器
func NewManager() *Manager {
	return &Manager{
		currentTheme: ThemeLight,
	}
}

// GetTheme 获取当前主题
func (m *Manager) GetTheme() ThemeType {
	return m.currentTheme
}

// SetTheme 设置主题
func (m *Manager) SetTheme(t ThemeType) {
	if t == ThemeLight || t == ThemeDark {
		m.currentTheme = t
	}
}

// GetColors 获取当前主题颜色
func (m *Manager) GetColors() *ThemeColors {
	if m.currentTheme == ThemeDark {
		return &DarkColors
	}
	return &LightColors
}

// GetThemeByName 通过名称获取主题
func GetThemeByName(name string) (ThemeType, bool) {
	switch name {
	case "light":
		return ThemeLight, true
	case "dark":
		return ThemeDark, true
	default:
		return ThemeLight, false
	}
}

// GetColorsByName 通过名称获取颜色
func GetColorsByName(name ThemeType) *ThemeColors {
	if name == ThemeDark {
		return &DarkColors
	}
	return &LightColors
}

// IsDarkTheme 判断是否为深色主题
func (m *Manager) IsDarkTheme() bool {
	return m.currentTheme == ThemeDark
}

// ToggleTheme 切换主题
func (m *Manager) ToggleTheme() ThemeType {
	if m.currentTheme == ThemeLight {
		m.currentTheme = ThemeDark
	} else {
		m.currentTheme = ThemeLight
	}
	return m.currentTheme
}

// AvailableThemes 获取可用主题列表
func (m *Manager) AvailableThemes() map[ThemeType]string {
	return map[ThemeType]string{
		ThemeLight: "浅色主题",
		ThemeDark:  "深色主题",
	}
}