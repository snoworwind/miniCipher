package main

import (
	"fyne.io/fyne/v2/app"

	"github.com/snoworwind/minicipher/internal/config"
	"github.com/snoworwind/minicipher/internal/ui"
)

func main() {
	app := app.NewWithID("com.snoworwind.minicipher")
	cfgMgr := config.NewManager()
	guiApp := ui.NewApp(cfgMgr, app)
	guiApp.Run()
}