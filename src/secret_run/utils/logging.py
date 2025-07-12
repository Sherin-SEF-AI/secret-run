"""Logging configuration and utilities."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import rich.console
import rich.logging
from rich.console import Console
from rich.theme import Theme

# Global console instance
_console: Optional[Console] = None


def get_console() -> Console:
    """Get the global console instance."""
    global _console
    if _console is None:
        theme = Theme({
            "info": "cyan",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        })
        _console = Console(theme=theme)
    return _console


def setup_logging(
    level: str = "INFO",
    format_type: str = "structured",
    log_file: Optional[Path] = None,
    max_size: str = "10MB",
    max_files: int = 5,
) -> None:
    """Setup logging configuration."""
    
    # Parse log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    if format_type == "structured":
        formatter = logging.Formatter(
            fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"module": "%(name)s", "message": "%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with Rich
    console_handler = rich.logging.RichHandler(
        console=get_console(),
        show_time=True,
        show_path=False,
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max size
        max_size_bytes = _parse_size(max_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size_bytes,
            backupCount=max_files,
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def _parse_size(size_str: str) -> int:
    """Parse size string to bytes."""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


def mask_secrets(text: str, secrets: dict) -> str:
    """Mask secrets in text output."""
    masked_text = text
    for key, value in secrets.items():
        if value in masked_text:
            masked_text = masked_text.replace(value, f"***{key}***")
    return masked_text


class SecretFilter(logging.Filter):
    """Filter to mask secrets in log messages."""
    
    def __init__(self, secrets: dict):
        super().__init__()
        self.secrets = secrets
    
    def filter(self, record):
        if hasattr(record, 'msg'):
            record.msg = mask_secrets(str(record.msg), self.secrets)
        if hasattr(record, 'args') and record.args is not None:
            record.args = tuple(
                mask_secrets(str(arg), self.secrets) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True 