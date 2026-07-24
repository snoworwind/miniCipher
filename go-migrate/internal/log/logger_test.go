package log

import (
	"bytes"
	"encoding/json"
	"log/slog"
	"strings"
	"testing"
)

func TestNewLogger(t *testing.T) {
	t.Run("debug mode uses text handler", func(t *testing.T) {
		l := New("DEBUG", true)
		if l.Logger == nil {
			t.Fatal("logger should not be nil")
		}
		// Debug mode should handle debug-level messages
		var buf bytes.Buffer
		l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelDebug}))
		l.Debug("test debug message")
		if !strings.Contains(buf.String(), "test debug message") {
			t.Error("debug message should be logged in debug mode")
		}
	})

	t.Run("JSON handler when debug is false", func(t *testing.T) {
		l := New("INFO", false)
		var buf bytes.Buffer
		l.Logger = slog.New(slog.NewJSONHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo}))
		l.Info("json test", "key", "value")
		var m map[string]interface{}
		if err := json.Unmarshal(buf.Bytes(), &m); err != nil {
			t.Errorf("output should be valid JSON: %v", err)
		}
		if m["msg"] != "json test" {
			t.Errorf("unexpected msg: %v", m["msg"])
		}
	})

	t.Run("warning level filters debug and info", func(t *testing.T) {
		l := New("WARNING", false)
		var buf bytes.Buffer
		l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelWarn}))
		l.Debug("should not appear")
		l.Info("should not appear")
		l.Warn("should appear")
		output := buf.String()
		if strings.Contains(output, "should not appear") {
			t.Error("debug/info messages should be filtered at WARNING level")
		}
		if !strings.Contains(output, "should appear") {
			t.Error("warning message should appear at WARNING level")
		}
	})

	t.Run("error level filters all below", func(t *testing.T) {
		l := New("ERROR", false)
		var buf bytes.Buffer
		l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelError}))
		l.Warn("should not appear")
		l.Error("should appear")
		output := buf.String()
		if strings.Contains(output, "should not appear") {
			t.Error("warn messages should be filtered at ERROR level")
		}
		if !strings.Contains(output, "should appear") {
			t.Error("error message should appear at ERROR level")
		}
	})

	t.Run("default level is INFO for unknown input", func(t *testing.T) {
		l := New("TRACE", false)
		var buf bytes.Buffer
		l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo}))
		l.Debug("should not appear")
		l.Info("should appear")
		output := buf.String()
		if strings.Contains(output, "should not appear") {
			t.Error("debug messages should be filtered at INFO level")
		}
		if !strings.Contains(output, "should appear") {
			t.Error("info message should appear at INFO level")
		}
	})
}

func TestPrintf(t *testing.T) {
	l := New("INFO", true)
	var buf bytes.Buffer
	l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo}))
	l.Printf("formatted %s %d", "hello", 42)
	if !strings.Contains(buf.String(), "formatted hello 42") {
		t.Errorf("Printf output mismatch: %s", buf.String())
	}
}

func TestErrorf(t *testing.T) {
	l := New("INFO", true)
	var buf bytes.Buffer
	l.Logger = slog.New(slog.NewTextHandler(&buf, &slog.HandlerOptions{Level: slog.LevelInfo}))
	l.Errorf("error: %v", "something wrong")
	if !strings.Contains(buf.String(), "error: something wrong") {
		t.Errorf("Errorf output mismatch: %s", buf.String())
	}
}

func TestNoOpLogger(t *testing.T) {
	l := NoOpLogger()
	if l.Logger == nil {
		t.Fatal("NoOpLogger should not be nil")
	}
	// Should not panic and should produce no output
	l.Info("should be silent")
	l.Error("should be silent")
	l.Debug("should be silent")
	l.Warn("should be silent")
}

func TestDefaultLogger(t *testing.T) {
	// Save and restore
	orig := DefaultLogger
	defer func() { DefaultLogger = orig }()

	Setup("INFO", true)
	if DefaultLogger == nil {
		t.Fatal("DefaultLogger should be set after Setup")
	}
}

func TestGlobalFunctions(t *testing.T) {
	orig := DefaultLogger
	defer func() { DefaultLogger = orig }()

	Setup("DEBUG", true)
	// Should not panic
	Info("global info")
	Error("global error")
	Debug("global debug")
	Warn("global warn")
}
