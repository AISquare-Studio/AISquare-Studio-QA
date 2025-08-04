#!/usr/bin/env python3
"""
Quick test runner to verify the framework setup without requiring API keys.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.crews.qa_crew import QACrew


def test_framework_setup():
    """Test that the framework is properly set up."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold green]🧪 Framework Setup Test[/bold green]\\n"
        "[yellow]Testing basic structure without API calls[/yellow]",
        border_style="green"
    ))
    
    try:
        # Test 1: Load test data
        console.print("\\n[yellow]1. Testing test data loading...[/yellow]")
        qa_crew = QACrew()
        test_data = qa_crew.load_test_data()
        console.print("[green]✅ Test data loaded successfully[/green]")
        
        # Test 2: Check environment config loading (without real .env values)
        console.print("\\n[yellow]2. Testing environment config loading...[/yellow]")
        env_config = qa_crew.load_environment_config()
        console.print("[green]✅ Environment config structure loaded[/green]")
        
        # Test 3: Test scenario access
        console.print("\\n[yellow]3. Testing scenario access...[/yellow]")
        scenarios = test_data['test_scenarios']['login']
        selectors = test_data['selectors']['login_page']
        console.print(f"[green]✅ Found {len(scenarios)} login scenarios[/green]")
        console.print(f"[green]✅ Found {len(selectors)} CSS selectors[/green]")
        
        # Test 4: Test code generation prompt (without API call)
        console.print("\\n[yellow]4. Testing code generation prompt creation...[/yellow]")
        scenario = scenarios['valid_login']
        prompt = qa_crew.planner_agent_wrapper.generate_test_code(scenario, selectors)
        console.print("[green]✅ Code generation prompt created successfully[/green]")
        
        # Test 5: Test code validation (with dummy code)
        console.print("\\n[yellow]5. Testing code validation...[/yellow]")
        dummy_code = '''
def run_test(page, config):
    page.goto(config['login_url'])
    page.wait_for_load_state('networkidle')
    assert page.title(), "Page should have a title"
'''
        is_safe, message = qa_crew.executor_agent_wrapper.validate_code_safety(dummy_code)
        if is_safe:
            console.print("[green]✅ Code validation working correctly[/green]")
        else:
            console.print(f"[yellow]⚠️  Validation issue: {message}[/yellow]")
        
        console.print("\\n" + "="*60)
        console.print("[bold green]🎉 Framework setup test completed successfully![/bold green]")
        console.print("\\n[yellow]Next steps:[/yellow]")
        console.print("1. Add your OpenAI API key to .env file")
        console.print("2. Add your staging environment URL to .env file")
        console.print("3. Add test credentials to .env file")
        console.print("4. Run: [bold]python run_login_tests.py[/bold]")
        
        return True
        
    except Exception as e:
        console.print(f"\\n[red]❌ Test failed: {str(e)}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False


if __name__ == "__main__":
    success = test_framework_setup()
    sys.exit(0 if success else 1)
