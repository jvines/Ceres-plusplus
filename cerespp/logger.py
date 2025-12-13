"""Structured logging for Ceres++.

Provides JSON-structured logging with step tracking for granular observability.

Author: Jose Vines
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional


class StructuredLogger:
    """Logger that outputs JSON-structured log entries.

    This logger writes structured log entries that can be easily parsed
    by log aggregation systems and monitoring tools. Each log entry includes
    a timestamp, status, and optional metadata.

    Parameters
    ----------
    name : str
        Logger name (typically __name__ of the calling module)
    output_file : Optional[str]
        Path to file for JSON log output. If None, logs only to console.
    level : int
        Logging level (e.g., logging.INFO, logging.DEBUG)

    Attributes
    ----------
    logger : logging.Logger
        Underlying Python logger instance
    output_file : Optional[str]
        Path to JSON log output file

    Examples
    --------
    >>> logger = StructuredLogger('cerespp.processor')
    >>> logger.log_step('Loading FITS', 'started', filename='test.fits')
    >>> logger.log_step('Loading FITS', 'completed', duration=0.5)
    """

    def __init__(self, name: str, output_file: Optional[str] = None,
                 level: int = logging.INFO):
        """Initialize structured logger.

        Parameters
        ----------
        name : str
            Logger name
        output_file : Optional[str]
            Path to JSON log file
        level : int
            Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.output_file = output_file

        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_step(self, step_name: str, status: str, **kwargs):
        """Log a processing step with structured metadata.

        Parameters
        ----------
        step_name : str
            Name of the processing step
        status : str
            Status of the step ('started', 'completed', 'failed')
        **kwargs
            Additional metadata to include in log entry

        Examples
        --------
        >>> logger.log_step('Converting to rest frame', 'started',
        ...                 filename='spectrum.fits')
        >>> logger.log_step('Converting to rest frame', 'completed',
        ...                 duration=5.2, rv=12.3)
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'step': step_name,
            'status': status,
            **kwargs
        }

        # Write to JSON file if configured
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except IOError as e:
                self.logger.warning(f"Failed to write to log file: {e}")

        # Log to console
        message = json.dumps(log_entry)
        if status == 'failed':
            self.logger.error(message)
        elif status == 'started':
            self.logger.info(message)
        else:
            self.logger.info(message)

    def info(self, message: str, **kwargs):
        """Log info message.

        Parameters
        ----------
        message : str
            Log message
        **kwargs
            Additional structured data
        """
        if kwargs:
            log_entry = {'message': message, **kwargs}
            self.logger.info(json.dumps(log_entry))
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """Log warning message.

        Parameters
        ----------
        message : str
            Warning message
        **kwargs
            Additional structured data
        """
        if kwargs:
            log_entry = {'message': message, **kwargs}
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.warning(message)

    def error(self, message: str, **kwargs):
        """Log error message.

        Parameters
        ----------
        message : str
            Error message
        **kwargs
            Additional structured data
        """
        if kwargs:
            log_entry = {'message': message, **kwargs}
            self.logger.error(json.dumps(log_entry))
        else:
            self.logger.error(message)

    def debug(self, message: str, **kwargs):
        """Log debug message.

        Parameters
        ----------
        message : str
            Debug message
        **kwargs
            Additional structured data
        """
        if kwargs:
            log_entry = {'message': message, **kwargs}
            self.logger.debug(json.dumps(log_entry))
        else:
            self.logger.debug(message)


# Default logger instance for convenience
default_logger = StructuredLogger('cerespp')
