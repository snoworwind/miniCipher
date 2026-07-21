package ui

import (
	"fmt"
	"strconv"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/widget"

	"github.com/snoworwind/minicipher/internal/config"
)

// SettingsDialog 设置对话框
type SettingsDialog struct {
	app    *App
	win    fyne.Window
	cfgMgr *config.Manager
	cfg    *config.Config

	original *config.Config // 原始设置快照

	// UI 组件
	langSelect     *widget.Select
	themeSelect    *widget.Select
	algoSelect     *widget.Select
	keyTypeSelect  *widget.Select
	passMinEntry   *widget.Entry
	strongCheck    *widget.Check
	inputDirEntry  *widget.Entry
	outputDirEntry *widget.Entry
	rememberCheck  *widget.Check
	debugCheck     *widget.Check
	logLevelSelect *widget.Select
	applyBtn       *widget.Button
}

// NewSettingsDialog 创建设置对话框
func NewSettingsDialog(a *App) *SettingsDialog {
	cfg := a.cfgMgr.Get()
	if cfg == nil {
		cfg = config.DefaultConfig()
	}

	sd := &SettingsDialog{
		app:    a,
		cfgMgr: a.cfgMgr,
		cfg:    cfg,
	}
	// 深拷贝原始设置
	orig := *cfg
	sd.original = &orig

	sd.win = fyne.CurrentApp().NewWindow(a.tr.T("settings"))
	sd.setupUI()
	sd.win.Resize(fyne.NewSize(620, 520))

	return sd
}

func (sd *SettingsDialog) Show() {
	sd.win.Show()
}

func (sd *SettingsDialog) setupUI() {
	tr := sd.app.tr

	generalTab := sd.buildGeneralTab()
	cryptoTab := sd.buildCryptoTab()
	pathsTab := sd.buildPathsTab()
	advancedTab := sd.buildAdvancedTab()

	tabs := container.NewAppTabs(
		container.NewTabItem(tr.T("tab.general"), generalTab),
		container.NewTabItem(tr.T("tab.encryption"), cryptoTab),
		container.NewTabItem(tr.T("tab.paths"), pathsTab),
		container.NewTabItem(tr.T("tab.advanced"), advancedTab),
	)

	sd.applyBtn = widget.NewButton(tr.T("apply"), sd.onApply)
	sd.applyBtn.Importance = widget.HighImportance
	cancelBtn := widget.NewButton(tr.T("cancel"), sd.onCancel)
	okBtn := widget.NewButton(tr.T("ok"), sd.onOK)
	resetBtn := widget.NewButton(tr.T("reset"), sd.onReset)

	buttons := container.NewBorder(nil, nil, resetBtn, container.NewHBox(cancelBtn, okBtn, sd.applyBtn))

	content := container.NewBorder(nil, buttons, nil, nil, tabs)
	sd.win.SetContent(content)
}

func (sd *SettingsDialog) buildGeneralTab() fyne.CanvasObject {
	tr := sd.app.tr
	cfg := sd.cfg

	sd.langSelect = widget.NewSelect([]string{"简体中文", "English"}, nil)
	if cfg.UI.Language == "en_US" {
		sd.langSelect.SetSelected("English")
	} else {
		sd.langSelect.SetSelected("简体中文")
	}

	sd.themeSelect = widget.NewSelect([]string{tr.T("theme.light"), tr.T("theme.dark")}, nil)
	if cfg.UI.Theme == "dark" {
		sd.themeSelect.SetSelected(tr.T("theme.dark"))
	} else {
		sd.themeSelect.SetSelected(tr.T("theme.light"))
	}

	sd.algoSelect = widget.NewSelect([]string{"OTP", "AES256"}, nil)
	sd.algoSelect.SetSelected(cfg.Crypto.DefaultAlgorithm)

	sd.keyTypeSelect = widget.NewSelect([]string{"random", "password"}, nil)
	sd.keyTypeSelect.SetSelected(cfg.Crypto.DefaultKeyType)

	form := widget.NewForm(
		&widget.FormItem{Text: tr.T("settings.ui_language"), Widget: sd.langSelect},
		&widget.FormItem{Text: tr.T("settings.ui_theme"), Widget: sd.themeSelect},
		&widget.FormItem{Text: tr.T("settings.default_algorithm"), Widget: sd.algoSelect},
		&widget.FormItem{Text: tr.T("settings.default_key_type"), Widget: sd.keyTypeSelect},
	)

	return container.NewVBox(
		widget.NewLabelWithStyle(tr.T("tab.general"), fyne.TextAlignLeading, fyne.TextStyle{Bold: true}),
		form,
	)
}

func (sd *SettingsDialog) buildCryptoTab() fyne.CanvasObject {
	tr := sd.app.tr
	cfg := sd.cfg

	sd.passMinEntry = widget.NewEntry()
	sd.passMinEntry.SetText(strconv.Itoa(cfg.Crypto.PasswordMinLength))

	sd.strongCheck = widget.NewCheck(tr.T("settings.require_strong_password"), nil)
	sd.strongCheck.SetChecked(cfg.Crypto.RequireStrongPass)

	form := widget.NewForm(
		&widget.FormItem{Text: tr.T("settings.password_min_length"), Widget: sd.passMinEntry},
		&widget.FormItem{Text: "", Widget: sd.strongCheck},
	)

	return container.NewVBox(
		widget.NewLabelWithStyle(tr.T("tab.encryption"), fyne.TextAlignLeading, fyne.TextStyle{Bold: true}),
		form,
		widget.NewLabel(tr.T("settings.password_info")),
	)
}

func (sd *SettingsDialog) buildPathsTab() fyne.CanvasObject {
	tr := sd.app.tr
	cfg := sd.cfg

	sd.inputDirEntry = widget.NewEntry()
	sd.inputDirEntry.SetText(cfg.Paths.DefaultInputDir)
	browseInputBtn := widget.NewButton(tr.T("browse"), func() {
		dialog.ShowFolderOpen(func(u fyne.ListableURI, err error) {
			if u != nil {
				sd.inputDirEntry.SetText(u.Path())
			}
		}, sd.win)
	})

	sd.outputDirEntry = widget.NewEntry()
	sd.outputDirEntry.SetText(cfg.Paths.DefaultOutputDir)
	browseOutputBtn := widget.NewButton(tr.T("browse"), func() {
		dialog.ShowFolderOpen(func(u fyne.ListableURI, err error) {
			if u != nil {
				sd.outputDirEntry.SetText(u.Path())
			}
		}, sd.win)
	})

	sd.rememberCheck = widget.NewCheck(tr.T("settings.remember_last_folder"), nil)
	sd.rememberCheck.SetChecked(cfg.Paths.RememberLastFolder)

	clearHistoryBtn := widget.NewButton(tr.T("settings.clear_history"), sd.onClearHistory)

	form := widget.NewForm(
		&widget.FormItem{Text: tr.T("settings.default_input_dir"), Widget: container.NewBorder(nil, nil, browseInputBtn, nil, sd.inputDirEntry)},
		&widget.FormItem{Text: tr.T("settings.default_output_dir"), Widget: container.NewBorder(nil, nil, browseOutputBtn, nil, sd.outputDirEntry)},
	)
	_ = clearHistoryBtn

	return container.NewVBox(
		widget.NewLabelWithStyle(tr.T("tab.paths"), fyne.TextAlignLeading, fyne.TextStyle{Bold: true}),
		form,
		sd.rememberCheck,
		clearHistoryBtn,
	)
}

func (sd *SettingsDialog) buildAdvancedTab() fyne.CanvasObject {
	tr := sd.app.tr
	cfg := sd.cfg

	sd.debugCheck = widget.NewCheck(tr.T("settings.debug_mode"), nil)
	sd.debugCheck.SetChecked(cfg.Debug)

	sd.logLevelSelect = widget.NewSelect([]string{"DEBUG", "INFO", "WARNING", "ERROR"}, nil)
	sd.logLevelSelect.SetSelected("INFO")

	form := widget.NewForm(
		&widget.FormItem{Text: "", Widget: sd.debugCheck},
		&widget.FormItem{Text: tr.T("settings.log_level"), Widget: sd.logLevelSelect},
	)

	return container.NewVBox(
		widget.NewLabelWithStyle(tr.T("tab.advanced"), fyne.TextAlignLeading, fyne.TextStyle{Bold: true}),
		form,
		widget.NewLabel(tr.T("settings.advanced_info")),
	)
}

func (sd *SettingsDialog) collectValues() *config.Config {
	newCfg := &config.Config{
		Version: sd.cfg.Version,
	}
	// UI
	lang := sd.langSelect.Selected
	if lang == "English" {
		newCfg.UI.Language = "en_US"
	} else {
		newCfg.UI.Language = "zh_CN"
	}
	themeSel := sd.themeSelect.Selected
	if themeSel == sd.app.tr.T("theme.dark") {
		newCfg.UI.Theme = "dark"
	} else {
		newCfg.UI.Theme = "light"
	}
	// Crypto
	newCfg.Crypto.DefaultAlgorithm = sd.algoSelect.Selected
	newCfg.Crypto.DefaultKeyType = sd.keyTypeSelect.Selected
	if v, err := strconv.Atoi(sd.passMinEntry.Text); err == nil && v > 0 {
		newCfg.Crypto.PasswordMinLength = v
	} else {
		newCfg.Crypto.PasswordMinLength = sd.original.Crypto.PasswordMinLength
	}
	newCfg.Crypto.RequireStrongPass = sd.strongCheck.Checked
	// Paths
	newCfg.Paths.DefaultInputDir = sd.inputDirEntry.Text
	newCfg.Paths.DefaultOutputDir = sd.outputDirEntry.Text
	newCfg.Paths.RememberLastFolder = sd.rememberCheck.Checked
	newCfg.Paths.LastInputFolder = sd.cfg.Paths.LastInputFolder
	newCfg.Paths.LastOutputFolder = sd.cfg.Paths.LastOutputFolder
	// Batch
	newCfg.Batch = sd.cfg.Batch
	// Debug
	newCfg.Debug = sd.debugCheck.Checked

	return newCfg
}

func (sd *SettingsDialog) onApply() {
	newCfg := sd.collectValues()

	langChanged := sd.cfg.UI.Language != newCfg.UI.Language
	themeChanged := sd.cfg.UI.Theme != newCfg.UI.Theme

	sd.cfg = newCfg
	sd.cfgMgr.Get().UI = newCfg.UI
	sd.cfgMgr.Get().Crypto = newCfg.Crypto
	sd.cfgMgr.Get().Paths = newCfg.Paths
	sd.cfgMgr.Get().Debug = newCfg.Debug

	if err := sd.cfgMgr.Save(); err != nil {
		dialog.ShowError(fmt.Errorf("保存设置失败: %v", err), sd.win)
		return
	}

	if langChanged || themeChanged {
		// 更新应用的主题和语言
		if langChanged {
			sd.app.tr.SetLanguage(newCfg.UI.Language)
		}
		dialog.ShowInformation(sd.app.tr.T("success"),
			sd.app.tr.T("settings.success_restart"), sd.win)
	} else {
		dialog.ShowInformation(sd.app.tr.T("success"),
			sd.app.tr.T("settings.success"), sd.win)
	}
}

func (sd *SettingsDialog) onOK() {
	sd.onApply()
	sd.win.Close()
}

func (sd *SettingsDialog) onCancel() {
	// 恢复原始设置
	sd.cfg = sd.original
	sd.win.Close()
}

func (sd *SettingsDialog) onReset() {
	defaultCfg := config.DefaultConfig()
	sd.cfg = defaultCfg
	sd.cfgMgr.Get().UI = defaultCfg.UI
	sd.cfgMgr.Get().Crypto = defaultCfg.Crypto
	sd.cfgMgr.Get().Paths = defaultCfg.Paths
	sd.cfgMgr.Get().Debug = defaultCfg.Debug

	// 更新 UI
	sd.langSelect.SetSelected("简体中文")
	sd.themeSelect.SetSelected(sd.app.tr.T("theme.light"))
	sd.algoSelect.SetSelected("AES256")
	sd.keyTypeSelect.SetSelected("random")
	sd.passMinEntry.SetText("8")
	sd.strongCheck.SetChecked(true)
	sd.inputDirEntry.SetText("")
	sd.outputDirEntry.SetText("")
	sd.rememberCheck.SetChecked(true)
	sd.debugCheck.SetChecked(false)
	sd.logLevelSelect.SetSelected("INFO")

	if err := sd.cfgMgr.Save(); err != nil {
		dialog.ShowError(fmt.Errorf("重置失败: %v", err), sd.win)
	} else {
		dialog.ShowInformation(sd.app.tr.T("success"), sd.app.tr.T("settings.reset"), sd.win)
	}
}

func (sd *SettingsDialog) onClearHistory() {
	sd.cfg.Paths.LastInputFolder = ""
	sd.cfg.Paths.LastOutputFolder = ""
	sd.cfgMgr.Get().Paths.LastInputFolder = ""
	sd.cfgMgr.Get().Paths.LastOutputFolder = ""
	if err := sd.cfgMgr.Save(); err != nil {
		dialog.ShowError(fmt.Errorf("清除失败: %v", err), sd.win)
	} else {
		dialog.ShowInformation(sd.app.tr.T("success"), sd.app.tr.T("settings.history_cleared"), sd.win)
	}
}