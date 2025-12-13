"""Test structured logger."""
import pytest
import json
import tempfile
import os
from cerespp.logger import StructuredLogger


class TestStructuredLogger:
    """Test StructuredLogger class."""

    def test_creation(self):
        """Test creating a logger."""
        logger = StructuredLogger('test')
        assert logger.logger.name == 'test'
        assert logger.output_file is None

    def test_creation_with_file(self):
        """Test creating a logger with output file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            log_file = f.name

        try:
            logger = StructuredLogger('test', output_file=log_file)
            assert logger.output_file == log_file
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_log_step(self):
        """Test logging a step."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            log_file = f.name

        try:
            logger = StructuredLogger('test', output_file=log_file)
            logger.log_step('Test Step', 'started', filename='test.fits')
            logger.log_step('Test Step', 'completed', duration=1.5)

            # Read log file
            with open(log_file, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 2

            # Parse first log entry
            log1 = json.loads(lines[0])
            assert log1['step'] == 'Test Step'
            assert log1['status'] == 'started'
            assert log1['filename'] == 'test.fits'
            assert 'timestamp' in log1

            # Parse second log entry
            log2 = json.loads(lines[1])
            assert log2['step'] == 'Test Step'
            assert log2['status'] == 'completed'
            assert log2['duration'] == 1.5

        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)

    def test_info_message(self):
        """Test logging info message."""
        logger = StructuredLogger('test')
        # Should not raise
        logger.info("Test message")
        logger.info("Test message", key="value")

    def test_warning_message(self):
        """Test logging warning message."""
        logger = StructuredLogger('test')
        # Should not raise
        logger.warning("Test warning")
        logger.warning("Test warning", key="value")

    def test_error_message(self):
        """Test logging error message."""
        logger = StructuredLogger('test')
        # Should not raise
        logger.error("Test error")
        logger.error("Test error", key="value")

    def test_debug_message(self):
        """Test logging debug message."""
        logger = StructuredLogger('test')
        # Should not raise
        logger.debug("Test debug")
        logger.debug("Test debug", key="value")
