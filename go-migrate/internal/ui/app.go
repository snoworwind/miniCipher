package ui

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/widget"

	"github.com/snoworwind/minicipher/internal/batch"
	"github.com/snoworwind/minicipher/internal/config"
	"github.com/snoworwind/minicipher/internal/crypto"
	"github.com/snoworwind/minicipher/internal/lang"
)

// App GUI 应用主结构
type App struct {
	win    fyne.Window
	cfgMgr *config.Manager
	cfg    *config.Config
	tr     *lang.Translator

	// 算法选择
	algoSelect     *widget.Select
	keyTypeSelect  *widget.Select
	passwordEntry  *widget.Entry

	// 加密面板
	encInputEntry  *widget.Entry
	encOutputEntry *widget.Entry
	encStatusLabel *widget.Label

	// 解密面板
	decInputEntry   *widget.Entry
	decKeyFileEntry *widget.Entry
	decPassEntry    *widget.Entry
	decOutputEntry  *widget.Entry
	decStatusLabel  *widget.Label

	// 批量面板
	batchInputEntry  *widget.Entry
	batchOutputEntry *widget.Entry
	batchStatusLabel *widget.Label
	batchProgress    *widget.ProgressBar
	batchCancelBtn   *widget.Button
	batchProcessor   *batch.BatchProcessor
}

// NewApp 创建GUI应用
func NewApp(cfgMgr *config.Manager, fApp fyne.App) *App {
	return &App{
		cfgMgr: cfgMgr,
		win:    fApp.NewWindow("miniCipher"),
	}
}

// Run 启动GUI主循环
func (a *App) Run() {
	a.win.Resize(fyne.NewSize(800, 680))

	var err error
	a.cfg, err = a.cfgMgr.Load()
	if err != nil {
		a.cfg = config.DefaultConfig()
	}
	a.tr = lang.NewTranslator(a.cfg.UI.Language)

	a.batchProcessor = batch.New(a.cfg.Batch.MaxThreads, 10)
	a.batchProcessor.SetProgressCallback(a.onBatchProgress)

	a.setupUI()
	a.win.ShowAndRun()
}

func (a *App) setupUI() {
	a.win.SetTitle(a.tr.T("app.title"))
	a.setupMenu()

	algoBox := a.buildAlgorithmPanel()

	tabs := container.NewAppTabs(
		container.NewTabItem(a.tr.T("encryption"), a.buildEncryptPanel()),
		container.NewTabItem(a.tr.T("decryption"), a.buildDecryptPanel()),
		container.NewTabItem(a.tr.T("batch.title"), a.buildBatchPanel()),
	)

	statusBar := widget.NewLabel(a.tr.T("status.ready"))

	content := container.NewBorder(
		algoBox,
		statusBar,
		nil, nil,
		tabs,
	)

	a.win.SetContent(content)
}

func (a *App) setupMenu() {
	fileMenu := fyne.NewMenu(a.tr.T("file_menu"),
		fyne.NewMenuItem(a.tr.T("settings"), a.openSettings),
		fyne.NewMenuItemSeparator(),
		fyne.NewMenuItem(a.tr.T("exit"), func() {
			a.win.Close()
		}),
	)

	langMenu := fyne.NewMenu(a.tr.T("language_menu"),
		fyne.NewMenuItem("简体中文", func() {
			a.tr.SetLanguage("zh_CN")
			a.cfg.UI.Language = "zh_CN"
			a.cfgMgr.Save()
			a.win.SetTitle(a.tr.T("app.title"))
		}),
		fyne.NewMenuItem("English", func() {
			a.tr.SetLanguage("en_US")
			a.cfg.UI.Language = "en_US"
			a.cfgMgr.Save()
			a.win.SetTitle(a.tr.T("app.title"))
		}),
	)

	helpMenu := fyne.NewMenu(a.tr.T("help_menu"),
		fyne.NewMenuItem(a.tr.T("about"), func() {
			dialog.ShowInformation(a.tr.T("about"), "MiniCipher v2.0\nGo Implementation\nMIT License\n\nFile encryption tool supporting OTP and AES256-GCM.", a.win)
		}),
	)

	a.win.SetMainMenu(fyne.NewMainMenu(fileMenu, langMenu, helpMenu))
}

func (a *App) openSettings() {
	sd := NewSettingsDialog(a)
	sd.Show()
}

func (a *App) buildAlgorithmPanel() *fyne.Container {
	a.keyTypeSelect = widget.NewSelect([]string{"random", "password"}, nil)
	a.keyTypeSelect.SetSelected(a.cfg.Crypto.DefaultKeyType)

	a.algoSelect = widget.NewSelect([]string{"AES256", "OTP"}, func(s string) {
		if a.keyTypeSelect == nil {
			return
		}
		if s == "OTP" {
			a.keyTypeSelect.SetSelected("random")
			a.keyTypeSelect.Disable()
			a.passwordEntry.Hide()
		} else {
			a.keyTypeSelect.Enable()
		}
	})
	a.algoSelect.SetSelected(a.cfg.Crypto.DefaultAlgorithm)
	// 初始化密码输入框可见性
	if a.cfg.Crypto.DefaultAlgorithm == "OTP" {
		a.keyTypeSelect.Disable()
	}

	a.passwordEntry = widget.NewPasswordEntry()
	a.passwordEntry.SetPlaceHolder(a.tr.T("password"))

	// 根据初始算法显示/隐藏密码输入框
	showPassword := a.cfg.Crypto.DefaultAlgorithm != "OTP" && a.keyTypeSelect.Selected == "password"

	algoInfo := widget.NewLabel(a.tr.T("otp_info"))
	if a.cfg.Crypto.DefaultAlgorithm == "AES256" {
		algoInfo.SetText(a.tr.T("aes_info"))
	}
	a.algoSelect.OnChanged = func(s string) {
		if a.keyTypeSelect == nil {
			return
		}
		if s == "OTP" {
			a.keyTypeSelect.SetSelected("random")
			a.keyTypeSelect.Disable()
			a.passwordEntry.Hide()
			algoInfo.SetText(a.tr.T("otp_info"))
		} else {
			a.keyTypeSelect.Enable()
			algoInfo.SetText(a.tr.T("aes_info"))
		}
	}
	a.keyTypeSelect.OnChanged = func(s string) {
		if s == "password" && a.algoSelect.Selected != "OTP" {
			a.passwordEntry.Show()
		} else {
			a.passwordEntry.Hide()
		}
	}

	// 初始化密码框状态
	if !showPassword {
		a.passwordEntry.Hide()
	}

	return container.NewVBox(
		widget.NewLabel(a.tr.T("algorithm.settings")),
		container.NewGridWithColumns(4,
			widget.NewLabel(a.tr.T("encryption_algorithm")),
			a.algoSelect,
			widget.NewLabel(a.tr.T("key_type")),
			a.keyTypeSelect,
		),
		container.NewGridWithColumns(2,
			widget.NewLabel(a.tr.T("password")),
			a.passwordEntry,
		),
		algoInfo,
	)
}

func (a *App) browseFile(entry *widget.Entry) {
	dialog.ShowFileOpen(func(r fyne.URIReadCloser, err error) {
		if r != nil {
			entry.SetText(r.URI().Path())
		}
	}, a.win)
}

func (a *App) browseDir(entry *widget.Entry) {
	dialog.ShowFolderOpen(func(u fyne.ListableURI, err error) {
		if u != nil {
			entry.SetText(u.Path())
		}
	}, a.win)
}

// ========== 加密面板 ==========
func (a *App) buildEncryptPanel() fyne.CanvasObject {
	a.encInputEntry = widget.NewEntry()
	a.encInputEntry.SetPlaceHolder(a.tr.T("input_file"))

	a.encOutputEntry = widget.NewEntry()
	a.encOutputEntry.SetPlaceHolder(a.tr.T("output_dir"))

	a.encStatusLabel = widget.NewLabel("")

	doEncrypt := widget.NewButton(a.tr.T("start_encryption"), a.doEncrypt)
	doEncrypt.Importance = widget.HighImportance

	return container.NewVBox(
		widget.NewLabel(a.tr.T("encryption")),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseFile(a.encInputEntry) }),
			nil,
			a.encInputEntry,
		),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseDir(a.encOutputEntry) }),
			nil,
			a.encOutputEntry,
		),
		doEncrypt,
		a.encStatusLabel,
		widget.NewLabel(a.tr.T("tips.encrypt")),
	)
}

func (a *App) doEncrypt() {
	inputFile := a.encInputEntry.Text
	if inputFile == "" {
		dialog.ShowError(fmt.Errorf(a.tr.T("error.invalid_file")), a.win)
		return
	}

	outputDir := a.encOutputEntry.Text
	if outputDir == "" {
		outputDir = filepath.Dir(inputFile)
	}
	outputFile := filepath.Join(outputDir, filepath.Base(inputFile)+".enc")

	algo := a.algoSelect.Selected
	keyTypeStr := a.keyTypeSelect.Selected
	password := a.passwordEntry.Text

	var kt crypto.KeyType
	if keyTypeStr == "password" {
		kt = crypto.KeyTypePassword
	} else {
		kt = crypto.KeyTypeRandom
	}

	if kt == crypto.KeyTypePassword && password == "" {
		dialog.ShowError(fmt.Errorf(a.tr.T("error.no_password")), a.win)
		return
	}

	a.encStatusLabel.SetText(a.tr.T("status.encrypting"))

	go func() {
		defer a.win.Canvas().Refresh(a.encStatusLabel)

		fc := crypto.NewFileCipher(10,
			a.cfg.Crypto.PasswordMinLength,
			a.cfg.Crypto.RequireStrongPass)

		var algoType crypto.AlgorithmType
		if algo == "OTP" {
			algoType = crypto.AlgorithmOTP
		} else {
			algoType = crypto.AlgorithmAES256
		}

		resp, err := fc.EncryptFile(crypto.EncryptionRequest{
			InputPath:  inputFile,
			OutputPath: outputFile,
			Algorithm:  algoType,
			KeyType:    kt,
			Password:   password,
		})

		if err != nil {
			a.encStatusLabel.SetText("❌ 加密失败，请检查输入文件")
			return
		}

		if resp.KeyFileNeeded {
			keyFile, err := fc.SaveAESKeyAll(resp.Key, resp.IV, resp.Tag, outputDir, filepath.Base(inputFile))
			if err != nil {
				a.encStatusLabel.SetText(fmt.Sprintf(a.tr.T("key_save_failed"), err))
				return
			}
			a.encStatusLabel.SetText(fmt.Sprintf(a.tr.T("success.encryption_with_key"), keyFile))
		} else {
			a.encStatusLabel.SetText(fmt.Sprintf(a.tr.T("success.encryption"), algo, outputFile))
		}
	}()
}

// ========== 解密面板 ==========
func (a *App) buildDecryptPanel() fyne.CanvasObject {
	a.decInputEntry = widget.NewEntry()
	a.decInputEntry.SetPlaceHolder(a.tr.T("input_file"))

	a.decKeyFileEntry = widget.NewEntry()
	a.decKeyFileEntry.SetPlaceHolder(a.tr.T("error.no_key"))

	a.decPassEntry = widget.NewPasswordEntry()
	a.decPassEntry.SetPlaceHolder(a.tr.T("password"))

	a.decOutputEntry = widget.NewEntry()
	a.decOutputEntry.SetPlaceHolder(a.tr.T("output_dir"))

	a.decStatusLabel = widget.NewLabel("")

	doDecrypt := widget.NewButton(a.tr.T("start_decryption"), a.doDecrypt)
	doDecrypt.Importance = widget.HighImportance

	return container.NewVBox(
		widget.NewLabel(a.tr.T("decryption")),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseFile(a.decInputEntry) }),
			nil,
			a.decInputEntry,
		),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseFile(a.decKeyFileEntry) }),
			nil,
			a.decKeyFileEntry,
		),
		a.decPassEntry,
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseDir(a.decOutputEntry) }),
			nil,
			a.decOutputEntry,
		),
		doDecrypt,
		a.decStatusLabel,
		widget.NewLabel(a.tr.T("tips.decrypt")),
	)
}

func (a *App) doDecrypt() {
	inputFile := a.decInputEntry.Text
	if inputFile == "" {
		dialog.ShowError(fmt.Errorf(a.tr.T("error.invalid_file")), a.win)
		return
	}

	outputDir := a.decOutputEntry.Text
	if outputDir == "" {
		outputDir = filepath.Dir(inputFile)
	}

	base := filepath.Base(inputFile)
	outputName := base
	if len(outputName) > 4 && outputName[len(outputName)-4:] == ".enc" {
		outputName = outputName[:len(outputName)-4]
	}
	outputFile := filepath.Join(outputDir, outputName)

	password := a.decPassEntry.Text
	keyFilePath := a.decKeyFileEntry.Text

	a.decStatusLabel.SetText(a.tr.T("status.decrypting"))

	go func() {
		defer a.win.Canvas().Refresh(a.decStatusLabel)

		fc := crypto.NewFileCipher(10,
			a.cfg.Crypto.PasswordMinLength,
			a.cfg.Crypto.RequireStrongPass)

		req := crypto.DecryptionRequest{
			InputPath:  inputFile,
			OutputPath: outputFile,
			Algorithm:  "", // 自动检测
			KeyPath:    keyFilePath,
			Password:   password,
		}

		if password != "" {
			req.KeyType = crypto.KeyTypePassword
		}

		_, err := fc.DecryptFile(req)
		if err != nil {
			a.decStatusLabel.SetText("❌ 解密失败，请检查密钥/密码是否正确")
			return
		}
		a.decStatusLabel.SetText(fmt.Sprintf(a.tr.T("success.decryption"), "", outputFile))
	}()
}

// ========== 批量面板 ==========
func (a *App) buildBatchPanel() fyne.CanvasObject {
	a.batchInputEntry = widget.NewEntry()
	a.batchInputEntry.SetPlaceHolder(a.tr.T("batch.select_files"))

	a.batchOutputEntry = widget.NewEntry()
	a.batchOutputEntry.SetPlaceHolder(a.tr.T("batch.output_dir"))

	a.batchProgress = widget.NewProgressBar()
	a.batchStatusLabel = widget.NewLabel("")

	doBatchEncrypt := widget.NewButton(a.tr.T("batch.encrypt"), func() {
		a.doBatch(true)
	})
	doBatchDecrypt := widget.NewButton(a.tr.T("batch.decrypt"), func() {
		a.doBatch(false)
	})

	a.batchCancelBtn = widget.NewButton(a.tr.T("batch.cancel"), func() {
		if a.batchProcessor != nil {
			a.batchProcessor.Cancel()
		}
	})
	a.batchCancelBtn.Disable()

	return container.NewVBox(
		widget.NewLabel(a.tr.T("batch.title")),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseDir(a.batchInputEntry) }),
			nil,
			a.batchInputEntry,
		),
		container.NewBorder(nil, nil,
			widget.NewButton(a.tr.T("browse"), func() { a.browseDir(a.batchOutputEntry) }),
			nil,
			a.batchOutputEntry,
		),
		container.NewHBox(doBatchEncrypt, doBatchDecrypt, a.batchCancelBtn),
		a.batchProgress,
		a.batchStatusLabel,
	)
}

func (a *App) doBatch(isEncrypt bool) {
	inputDir := a.batchInputEntry.Text
	outputDir := a.batchOutputEntry.Text

	if inputDir == "" || outputDir == "" {
		dialog.ShowError(fmt.Errorf("请选择输入和输出目录"), a.win)
		return
	}

	keyTypeStr := a.keyTypeSelect.Selected
	password := a.passwordEntry.Text
	algo := a.algoSelect.Selected

	var kt crypto.KeyType
	if keyTypeStr == "password" {
		kt = crypto.KeyTypePassword
	} else {
		kt = crypto.KeyTypeRandom
	}

	if kt == crypto.KeyTypePassword && password == "" {
		dialog.ShowError(fmt.Errorf(a.tr.T("error.no_password")), a.win)
		return
	}

	a.batchProgress.SetValue(0)
	a.batchCancelBtn.Enable()

	op := batch.OpEncrypt
	if !isEncrypt {
		op = batch.OpDecrypt
	}

	paths := []string{inputDir}

	go func() {
		defer a.batchCancelBtn.Disable()

		bp := batch.New(a.cfg.Batch.MaxThreads, 10)
		bp.SetProgressCallback(a.onBatchProgress)

		result, err := bp.Process(op, paths, outputDir, a.cfg.Batch.PreserveStructure,
			algo, kt, nil, []byte(password), nil, nil, nil)
		if err != nil {
			a.batchStatusLabel.SetText("❌ 批量处理失败，请检查输入和输出路径")
			return
		}

		elapsed := result.Duration().Round(time.Second)
		a.batchStatusLabel.SetText(fmt.Sprintf("✅ %d/%d 成功, %d 失败, 耗时 %s (%.1f%%)",
			result.SuccessFiles, result.TotalFiles, result.FailedFiles, elapsed, result.SuccessRate()))
		a.batchProgress.SetValue(1)
	}()
}

func (a *App) onBatchProgress(p batch.Progress) {
	if p.Done {
		a.batchProgress.SetValue(1)
		return
	}
	if p.TotalFiles > 0 {
		a.batchProgress.SetValue(float64(p.CurrentFile) / float64(p.TotalFiles))
		a.batchStatusLabel.SetText(fmt.Sprintf("%s: %d/%d - %s",
			a.tr.T("batch.progress"), p.CurrentFile, p.TotalFiles, p.CurrentName))
	}
}

// 保留导入引用
var _ = app.New
var _ = os.Stdout