"""
Logging configuration for AutoQA

Provides standardized logging with:
- Console output (for GitHub Actions stdout/stderr)
- Optional file logging
- Emoji-enhanced formatting for readability
- GitHub Actions annotation support (::error::, ::warning::, ::notice::)
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class GitHubActionsFormatter(logging.Formatter):
    """Custom formatter that adds emojis and supports GitHub Actions annotations"""
    
    # Emoji mapping for log levels
    EMOJIS = {
        logging.DEBUG: '🔍',
        logging.INFO: 'ℹ️',
        logging.WARNING: '⚠️',
        logging.ERROR: '❌',
        logging.CRITICAL: '🚨'
    }
    
    # Custom emoji mapping for specific message patterns
    CUSTOM_EMOJIS = {
        'success': '✅',
        'starting': '🚀',
        'generating': '🤖',
        'executing': '🧪',
        'committing': '💾',
        'running': '🏃',
        'comment': '📝',
        'screenshot': '📸',
        'found': '🔍',
        'uploaded': '✅',
        'push': '🚀',
        'notice': '📋',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with emojis"""
        # Get base emoji for level
        emoji = self.EMOJIS.get(record.levelno, 'ℹ️')
        
        # Check for custom emojis in message
        msg_lower = record.getMessage().lower()
        for keyword, custom_emoji in self.CUSTOM_EMOJIS.items():
            if keyword in msg_lower:
                emoji = custom_emoji
                break
        
        # Format: [EMOJI] Message
        record.emoji = emoji
        return f"{emoji}  {record.getMessage()}"


class GitHubActionsHandler(logging.StreamHandler):
    """Handler that outputs GitHub Actions annotations for warnings/errors"""
    
    def emit(self, record: logging.LogRecord):
        """Emit a record with GitHub Actions formatting if applicable"""
        try:
            msg = self.format(record)
            
            # For errors and warnings, also emit GitHub Actions annotations
            if record.levelno >= logging.ERROR:
                sys.stderr.write(f"::error::{record.getMessage()}\n")
                sys.stderr.flush()
            elif record.levelno == logging.WARNING:
                sys.stderr.write(f"::warning::{record.getMessage()}\n")
                sys.stderr.flush()
            
            # Normal output
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging(
    name: str = 'autoqa',
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for AutoQA
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        console: Whether to output to console (default: True)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with emoji formatting
    if console:
        console_handler = GitHubActionsHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(GitHubActionsFormatter())
        logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # File gets all messages
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = 'autoqa') -> logging.Logger:
    """
    Get or create a logger instance
    
    Args:
        name: Logger name (default: 'autoqa')
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        setup_logging(name=name)
    
    return logger


# GitHub Actions specific logging methods
def log_github_notice(message: str, logger: Optional[logging.Logger] = None):
    """Log a GitHub Actions notice annotation"""
    if logger is None:
        logger = get_logger()
    sys.stdout.write(f"::notice::{message}\n")
    sys.stdout.flush()
    logger.info(message)


def log_github_group(title: str):
    """Start a GitHub Actions log group"""
    sys.stdout.write(f"::group::{title}\n")
    sys.stdout.flush()


def log_github_endgroup():
    """End a GitHub Actions log group"""
    sys.stdout.write("::endgroup::\n")
    sys.stdout.flush()


# Default logger instance
logger = get_logger()
