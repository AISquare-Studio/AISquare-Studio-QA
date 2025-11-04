"""
Screenshot Handler: Centralized screenshot capture and management
Consolidates screenshot logic from executor_agent, playwright_executor, and reporter
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ScreenshotHandler:
    """
    Centralized handler for screenshot capture, naming, and path management.
    Provides consistent screenshot handling across all AutoQA components.
    """
    
    # Screenshot type constants
    SUCCESS = "success"
    ERROR = "error"
    FAILURE = "failure"
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize screenshot handler.
        
        Args:
            base_path: Base directory for screenshots. If None, uses ACTION_PATH or current directory
        """
        self.base_path = self._determine_base_path(base_path)
        self.screenshot_dir = Path(self.base_path) / "reports" / "screenshots"
    
    def _determine_base_path(self, base_path: Optional[str]) -> str:
        """
        Determine the base path for screenshot storage.
        Priority: provided base_path > ACTION_PATH env var > current directory
        """
        if base_path:
            return base_path
        
        # Check for ACTION_PATH environment variable (used in GitHub Actions)
        action_path = os.getenv('ACTION_PATH')
        if action_path:
            return action_path
        
        # Default to current directory
        return '.'
    
    def ensure_screenshot_directory(self) -> None:
        """Create screenshot directory if it doesn't exist."""
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def get_screenshot_path(
        self,
        screenshot_type: str,
        scenario_name: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Generate a standardized screenshot path.
        
        Args:
            screenshot_type: Type of screenshot (success, error, failure)
            scenario_name: Optional scenario identifier
            timestamp: Optional timestamp string. If None, generates new one
            
        Returns:
            Absolute path to screenshot file
            
        Example:
            success_login_test_20251103_143022.png
            error_autoqa_20251103_143045.png
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build filename
        if scenario_name:
            filename = f"{screenshot_type}_{scenario_name}_{timestamp}.png"
        else:
            filename = f"{screenshot_type}_{timestamp}.png"
        
        return str(self.screenshot_dir / filename)
    
    def capture_screenshot(
        self,
        page,
        screenshot_type: str,
        scenario_name: Optional[str] = None,
        full_page: bool = True
    ) -> Optional[str]:
        """
        Capture a screenshot using Playwright page object.
        
        Args:
            page: Playwright page object
            screenshot_type: Type of screenshot (success, error, failure)
            scenario_name: Optional scenario identifier
            full_page: Whether to capture full page or viewport only
            
        Returns:
            Path to saved screenshot, or None if capture failed
        """
        try:
            self.ensure_screenshot_directory()
            screenshot_path = self.get_screenshot_path(screenshot_type, scenario_name)
            
            page.screenshot(path=screenshot_path, full_page=full_page)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            logger.warning(f"Failed to capture {screenshot_type} screenshot: {e}")
            return None
    
    def resolve_screenshot_path(self, screenshot_path: str) -> Optional[Path]:
        """
        Resolve a screenshot path by checking multiple possible locations.
        Useful when screenshot path might be relative or from different context.
        
        Args:
            screenshot_path: Path to resolve (can be relative or absolute)
            
        Returns:
            Resolved Path object if found, None otherwise
        """
        if not screenshot_path:
            return None
        
        path = Path(screenshot_path)
        
        # 1. If absolute path exists, use it
        if path.is_absolute() and path.exists():
            return path
        
        # 2. Try relative to current directory
        if path.exists():
            return path.resolve()
        
        # 3. Try relative to screenshot directory
        screenshot_dir_path = self.screenshot_dir / path.name
        if screenshot_dir_path.exists():
            return screenshot_dir_path
        
        # 4. Try relative to base path
        base_path_file = Path(self.base_path) / screenshot_path
        if base_path_file.exists():
            return base_path_file
        
        # 5. Try in GitHub workspace if available
        github_workspace = os.getenv('GITHUB_WORKSPACE')
        if github_workspace:
            workspace_path = Path(github_workspace) / screenshot_path
            if workspace_path.exists():
                return workspace_path
        
        logger.warning(f"Could not resolve screenshot path: {screenshot_path}")
        return None
    
    def get_screenshot_info(self, screenshot_path: str) -> dict:
        """
        Get information about a screenshot file.
        
        Args:
            screenshot_path: Path to screenshot file
            
        Returns:
            Dictionary with screenshot metadata (size, timestamp, exists, etc.)
        """
        resolved_path = self.resolve_screenshot_path(screenshot_path)
        
        if not resolved_path or not resolved_path.exists():
            return {
                'exists': False,
                'path': screenshot_path,
                'resolved_path': None
            }
        
        stat = resolved_path.stat()
        
        return {
            'exists': True,
            'path': screenshot_path,
            'resolved_path': str(resolved_path),
            'size_bytes': stat.st_size,
            'size_kb': stat.st_size / 1024,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified_timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'is_embeddable': stat.st_size < 100000,  # <100KB can be base64 embedded
        }


# Convenience functions for backward compatibility
def get_screenshot_path(screenshot_type: str, scenario_name: Optional[str] = None) -> str:
    """Convenience function to get screenshot path without instantiating handler."""
    handler = ScreenshotHandler()
    return handler.get_screenshot_path(screenshot_type, scenario_name)


def capture_screenshot(page, screenshot_type: str, scenario_name: Optional[str] = None) -> Optional[str]:
    """Convenience function to capture screenshot without instantiating handler."""
    handler = ScreenshotHandler()
    return handler.capture_screenshot(page, screenshot_type, scenario_name)
