package log

import (
	"fmt"
	"io"
	"log/slog"
	"os"
)

// Logger wraps slog.Logger for application-level logging
type Logger struct {
	*slog.Logger
}

// New creates a new application logger
// level: DEBUG, INFO, WARNING, ERROR
// debug: if true, uses text handler with debug level; otherwise uses JSON with the given level
func New(level string, debug bool) *Logger {
	var logLevel slog.Level
	switch level {
	case "DEBUG":
		logLevel = slog.LevelDebug
	case "WARNING":
		logLevel = slog.LevelWarn
	case "ERROR":
		logLevel = slog.LevelError
	default:
		logLevel = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level: logLevel,
	}

	var handler slog.Handler
	if debug {
		handler = slog.NewTextHandler(os.Stderr, opts)
	} else {
		handler = slog.NewJSONHandler(os.Stderr, opts)
	}

	return &Logger{
		Logger: slog.New(handler),
	}
}

// Printf formats and prints a message at INFO level (for compatibility with existing code)
func (l *Logger) Printf(format string, args ...interface{}) {
	l.Info(fmt.Sprintf(format, args...))
}

// Errorf formats and prints an error message
func (l *Logger) Errorf(format string, args ...interface{}) {
	l.Error(fmt.Sprintf(format, args...))
}

// NoOpLogger returns a logger that discards all output
func NoOpLogger() *Logger {
	return &Logger{
		Logger: slog.New(slog.NewTextHandler(io.Discard, nil)),
	}
}

// DefaultLogger is the global application logger
var DefaultLogger = NoOpLogger()

// Setup configures the global logger
func Setup(level string, debug bool) {
	DefaultLogger = New(level, debug)
}

// Info logs at info level
func Info(msg string, args ...any) {
	DefaultLogger.Info(msg, args...)
}

// Error logs at error level
func Error(msg string, args ...any) {
	DefaultLogger.Error(msg, args...)
}

// Debug logs at debug level
func Debug(msg string, args ...any) {
	DefaultLogger.Debug(msg, args...)
}

// Warn logs at warn level
func Warn(msg string, args ...any) {
	DefaultLogger.Warn(msg, args...)
}