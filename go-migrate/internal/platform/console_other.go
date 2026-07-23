//go:build !windows

package platform

// AttachOrAllocConsole is a no-op on non-Windows platforms.
// On Unix systems, terminal handling is managed by the shell / .app bundle.
func AttachOrAllocConsole() (isNewConsole bool) {
	return false
}