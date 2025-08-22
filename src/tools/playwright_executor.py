"""
Playwright Executor Tool: Custom CrewAI tool for Playwright test execution.
"""

from typing import Dict, Any
from playwright.sync_api import sync_playwright
import json
from pathlib import Path


def create_playwright_executor_tool():
    """Create a Playwright executor function for CrewAI."""
    
    def execute_playwright_code(code: str, config: Dict[str, Any]) -> str:
        """
        Execute Playwright test code.
        
        Args:
            code: Python code containing run_test function
            config: Configuration dictionary with URLs, credentials, etc.
            
        Returns:
            JSON string with execution results
        """
        try:
            result = {
                'success': False,
                'message': '',
                'error': '',
                'screenshot_path': None
            }
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=config.get('headless', False)
                )
                page = browser.new_page()
                
                # Set viewport
                page.set_viewport_size({"width": 1280, "height": 720})
                
                # Create safe execution environment
                exec_globals = {
                    'page': page,
                    'config': config,
                    'assert': safe_assert
                }
                
                # Execute the code (define the function)
                exec(code, exec_globals)
                
                # Call the run_test function
                exec_globals['run_test'](page, config)
                
                # Take success screenshot
                screenshot_path = f"reports/screenshots/success_{config.get('scenario_name', 'test')}.png"
                Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=screenshot_path)
                
                result.update({
                    'success': True,
                    'message': 'Test executed successfully',
                    'screenshot_path': screenshot_path
                })
                
                browser.close()
                
        except AssertionError as e:
            result.update({
                'success': False,
                'error': f'Assertion failed: {str(e)}',
                'message': 'Test assertion failed'
            })
            
            # Take failure screenshot
            try:
                if 'page' in locals():
                    error_screenshot = f"reports/screenshots/failure_{config.get('scenario_name', 'test')}.png"
                    Path(error_screenshot).parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=error_screenshot)
                    result['screenshot_path'] = error_screenshot
            except:
                pass
                
        except Exception as e:
            # Include config info in error for debugging
            config_info = f"Config keys: {list(config.keys()) if config else 'None'}, login_url: {config.get('login_url', 'NOT_FOUND') if config else 'No config'}"
            
            result.update({
                'success': False,
                'error': f"{str(e)} | Debug: {config_info}",
                'message': 'Test execution failed'
            })
            
            # Take error screenshot
            try:
                if 'page' in locals():
                    error_screenshot = f"reports/screenshots/error_{config.get('scenario_name', 'test')}.png"
                    Path(error_screenshot).parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=error_screenshot)
                    result['screenshot_path'] = error_screenshot
            except:
                pass
        
        return json.dumps(result, indent=2)
    
    return execute_playwright_code


def safe_assert(condition, message="Assertion failed"):
    """Safe assertion function with detailed error messages."""
    if not condition:
        raise AssertionError(message)
