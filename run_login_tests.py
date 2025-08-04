#!/usr/bin/env python3
"""
Main runner script for login tests using CrewAI + Playwright.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.crews.qa_crew import QACrew


def main():
    """Main function to run login tests."""
    console = Console()
    
    # Print welcome banner
    console.print(Panel.fit(
        "[bold blue]AISquare Studio QA - Login Test Automation[/bold blue]\\n"
        "[green]CrewAI + Playwright Test Runner[/green]",
        border_style="blue"
    ))
    
    # Check environment setup
    console.print("\\n[yellow]Checking environment setup...[/yellow]")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        console.print("[red]❌ .env file not found![/red]")
        console.print("[yellow]📝 Please copy env_template to .env and update with your values[/yellow]")
        console.print("   cp env_template .env")
        return False
    
    console.print("[green]✅ Environment file found[/green]")
    
    # Create reports directory
    reports_dir = Path("reports/screenshots")
    reports_dir.mkdir(parents=True, exist_ok=True)
    console.print("[green]✅ Reports directory ready[/green]")
    
    # Initialize QA Crew
    console.print("\\n[yellow]Initializing QA Crew...[/yellow]")
    try:
        qa_crew = QACrew()
        console.print("[green]✅ QA Crew initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize QA Crew: {str(e)}[/red]")
        return False
    
    # Run tests
    console.print("\\n[yellow]Running login test scenarios...[/yellow]")
    
    try:
        results = qa_crew.run_all_login_tests()
        
        # Display results table
        table = Table(title="Test Results Summary")
        table.add_column("Scenario", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        for scenario_name, result in results.items():
            if result.get('error'):
                status = "❌ FAILED"
                details = result['error'][:50] + "..." if len(result['error']) > 50 else result['error']
            else:
                status = "✅ PASSED"
                details = "Test completed successfully"
            
            table.add_row(scenario_name, status, details)
        
        console.print(table)
        
        # Save detailed results
        results_file = Path("reports/test_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        console.print(f"\\n[green]📄 Detailed results saved to: {results_file}[/green]")
        console.print(f"[green]📸 Screenshots saved to: reports/screenshots/[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Test execution failed: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
