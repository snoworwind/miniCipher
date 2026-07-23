package platform

import (
	"os"
	"syscall"
)

var (
	kernel32          = syscall.MustLoadDLL("kernel32.dll")
	procAttachConsole = kernel32.MustFindProc("AttachConsole")
	procAllocConsole  = kernel32.MustFindProc("AllocConsole")
	procGetStdHandle  = kernel32.MustFindProc("GetStdHandle")
)

const (
	attachParentProcess = ^uint32(0) // ATTACH_PARENT_PROCESS = -1 = 0xFFFFFFFF
	stdOutputHandle     = ^uint32(0) - 11 + 1 // STD_OUTPUT_HANDLE = -11 = 0xFFFFFFF5
	stdErrorHandle      = ^uint32(0) - 12 + 1 // STD_ERROR_HANDLE  = -12 = 0xFFFFFFF4
)

// AttachOrAllocConsole attempts to attach to the parent process console.
// If that fails (e.g. double-click launch with no parent console), it allocates a new console.
// Stdout and stderr are redirected to the console.
// Returns true if a console was newly allocated (not just attached).
func AttachOrAllocConsole() (isNewConsole bool) {
	// First try attaching to parent console (for CLI usage from an existing terminal)
	attached, _, _ := procAttachConsole.Call(uintptr(attachParentProcess))
	if attached != 0 {
		// Successfully attached — redirect stdout/stderr handles
		redirectStdHandles()
		return false
	}

	// Parent not available — allocate a new console (for debug mode from GUI)
	allocated, _, _ := procAllocConsole.Call()
	if allocated != 0 {
		redirectStdHandles()
		return true
	}

	return false
}

// redirectStdHandles redirects os.Stdout and os.Stderr to the newly attached/allocated console.
// After AttachConsole or AllocConsole succeeds, the Windows std handles point to the console,
// but Go's os.Stdout/os.Stderr still hold the original (possibly invalid) file descriptors.
// We reopen them using the Windows API handles.
func redirectStdHandles() {
	hOut, _, _ := procGetStdHandle.Call(uintptr(stdOutputHandle))
	hErr, _, _ := procGetStdHandle.Call(uintptr(stdErrorHandle))

	if hOut != 0 && hOut != uintptr(syscall.InvalidHandle) {
		os.Stdout = os.NewFile(uintptr(hOut), "CONOUT$")
	}
	if hErr != 0 && hErr != uintptr(syscall.InvalidHandle) {
		os.Stderr = os.NewFile(uintptr(hErr), "CONERR$")
	}
}
