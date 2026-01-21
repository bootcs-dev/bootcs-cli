"""
Tests for streaming log functionality (Action Log support).

Tests the real-time log streaming feature that outputs to stderr
when BOOTCS_STREAM_LOGS=1 is set.
"""

import io
import os
import sys
import unittest
from unittest.mock import patch


class TestStreamingLogBasics(unittest.TestCase):
    """Test basic streaming log functionality."""

    def setUp(self):
        """Reset module state before each test."""
        # Clear any cached imports to ensure fresh state
        if "bootcs.check._api" in sys.modules:
            del sys.modules["bootcs.check._api"]

    def test_stream_disabled_by_default(self):
        """Streaming should be disabled when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the var if it exists
            os.environ.pop("BOOTCS_STREAM_LOGS", None)
            
            # Re-import to pick up env var
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            from bootcs.check._api import _stream_enabled
            
            self.assertFalse(_stream_enabled)

    def test_stream_enabled_with_env_var(self):
        """Streaming should be enabled when BOOTCS_STREAM_LOGS=1."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_LOGS": "1"}):
            # Re-import to pick up env var
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            from bootcs.check._api import _stream_enabled
            
            self.assertTrue(_stream_enabled)


class TestLogFunction(unittest.TestCase):
    """Test the log() function with streaming."""

    def test_log_appends_to_internal_log(self):
        """log() should append to _log list regardless of streaming."""
        from bootcs.check._api import _log, log
        
        _log.clear()
        log("test message")
        
        self.assertIn("test message", _log)

    def test_log_escapes_newlines(self):
        """log() should escape newlines in messages."""
        from bootcs.check._api import _log, log
        
        _log.clear()
        log("line1\nline2")
        
        self.assertIn("line1\\nline2", _log)

    def test_log_with_level_parameter(self):
        """log() should accept level parameter without error."""
        from bootcs.check._api import _log, log
        
        _log.clear()
        log("info message", level="info")
        log("warning message", level="warn")
        log("error message", level="error")
        
        self.assertEqual(len(_log), 3)

    def test_log_streams_to_stderr_when_enabled(self):
        """log() should write to stderr when streaming is enabled."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_LOGS": "1"}):
            # Re-import with streaming enabled
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _log, log
            
            # Capture stderr
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _log.clear()
                log("streamed message")
            
            output = captured.getvalue()
            self.assertIn("streamed message", output)
            self.assertIn("[INFO ]", output.upper())


class TestFormatStreamLine(unittest.TestCase):
    """Test stream line formatting."""

    def test_format_includes_level(self):
        """Formatted line should include log level."""
        from bootcs.check._api import _format_stream_line
        
        line = _format_stream_line("test", level="info")
        self.assertIn("INFO", line.upper())
        
        line = _format_stream_line("test", level="error")
        self.assertIn("ERROR", line.upper())

    def test_format_includes_timestamp_by_default(self):
        """Formatted line should include timestamp by default."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_TIMESTAMPS": "1"}):
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            from bootcs.check._api import _format_stream_line
            
            line = _format_stream_line("test", level="info")
            # Should have time format like [HH:MM:SS]
            import re
            self.assertTrue(re.search(r"\[\d{2}:\d{2}:\d{2}\]", line))


class TestStreamEvent(unittest.TestCase):
    """Test event streaming functionality."""

    def test_stream_event_format(self):
        """Event should be formatted correctly."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_LOGS": "1"}):
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _stream_event
            
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _stream_event("check_started", name="exists", description="file exists")
            
            output = captured.getvalue()
            self.assertIn("[EVENT]", output)
            self.assertIn("check_started", output)
            self.assertIn('name="exists"', output)

    def test_stream_event_escapes_special_chars(self):
        """Event values should escape quotes and newlines."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_LOGS": "1"}):
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _stream_event
            
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _stream_event("test", value='hello "world"\ntest')
            
            output = captured.getvalue()
            self.assertIn('\\"', output)  # Escaped quote
            self.assertIn("\\n", output)  # Escaped newline

    def test_stream_event_handles_numeric_values(self):
        """Event should handle numeric values without quotes."""
        with patch.dict(os.environ, {"BOOTCS_STREAM_LOGS": "1"}):
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _stream_event
            
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _stream_event("check_completed", name="test", duration_ms=123)
            
            output = captured.getvalue()
            self.assertIn("duration_ms=123", output)


class TestStreamingDisabled(unittest.TestCase):
    """Test that streaming doesn't affect normal operation when disabled."""

    def test_log_works_without_streaming(self):
        """log() should work normally when streaming is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOOTCS_STREAM_LOGS", None)
            
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _log, log
            
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _log.clear()
                log("normal message")
            
            # Should not write to stderr
            self.assertEqual(captured.getvalue(), "")
            # But should still append to log
            self.assertIn("normal message", _log)

    def test_event_silent_when_disabled(self):
        """Events should not output when streaming is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("BOOTCS_STREAM_LOGS", None)
            
            if "bootcs.check._api" in sys.modules:
                del sys.modules["bootcs.check._api"]
            
            from bootcs.check._api import _stream_event
            
            captured = io.StringIO()
            with patch("sys.stderr", captured):
                _stream_event("check_started", name="test")
            
            self.assertEqual(captured.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
