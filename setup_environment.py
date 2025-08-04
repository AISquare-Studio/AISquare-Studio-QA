#!/usr/bin/env python3
"""
Setup script for the QA automation environment.
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e.stderr}")
        return False


def main():
    """Main setup function."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]AISquare Studio QA - Environment Setup[/bold blue]\\n"
        "[green]Setting up CrewAI + Playwright automation environment[/green]",
        border_style="blue"
    ))
    
    with Progress() as progress:
        setup_task = progress.add_task("[cyan]Setting up environment...", total=5)
        
        # Step 1: Install Python dependencies
        console.print("\\n[yellow]Installing Python dependencies...[/yellow]")
        if run_command("pip install -r requirements.txt", "pip install"):
            console.print("[green]✅ Python dependencies installed[/green]")
        else:
            console.print("[red]❌ Failed to install Python dependencies[/red]")
            return False
        progress.update(setup_task, advance=1)
        
        # Step 2: Install Playwright browsers
        console.print("\\n[yellow]Installing Playwright browsers...[/yellow]")
        if run_command("playwright install chromium firefox webkit", "playwright install"):
            console.print("[green]✅ Playwright browsers installed[/green]")
        else:
            console.print("[red]❌ Failed to install Playwright browsers[/red]")
            return False
        progress.update(setup_task, advance=1)
        
        # Step 3: Create .env file if it doesn't exist
        console.print("\\n[yellow]Setting up environment configuration...[/yellow]")
        env_file = Path(".env")
        env_template = Path("env_template")
        
        if not env_file.exists() and env_template.exists():
            env_file.write_text(env_template.read_text())
            console.print("[green]✅ Created .env file from template[/green]")
            console.print("[yellow]📝 Please update .env file with your actual values[/yellow]")
        elif env_file.exists():
            console.print("[green]✅ .env file already exists[/green]")
        else:
            console.print("[red]❌ No env_template found[/red]")
        progress.update(setup_task, advance=1)
        
        # Step 4: Create necessary directories
        console.print("\\n[yellow]Creating project directories...[/yellow]")
        directories = [
            "reports/screenshots",
            "tests/generated"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        console.print("[green]✅ Project directories created[/green]")
        progress.update(setup_task, advance=1)
        
        # Step 5: Test basic imports
        console.print("\\n[yellow]Testing basic imports...[/yellow]")
        try:
            import crewai
            import playwright
            import pytest
            import yaml
            console.print("[green]✅ All required packages imported successfully[/green]")
        except ImportError as e:
            console.print(f"[red]❌ Import error: {str(e)}[/red]")
            return False
        progress.update(setup_task, advance=1)
    
    # Final instructions
    console.print("\\n" + "="*60)
    console.print("[bold green]🎉 Setup completed successfully![/bold green]")
    console.print("\\n[yellow]Next steps:[/yellow]")
    console.print("1. Update your .env file with actual staging URL and credentials")
    console.print("2. Run the tests: [bold]python run_login_tests.py[/bold]")
    console.print("3. Or use pytest: [bold]pytest tests/test_login.py -v[/bold]")
    console.print("\\n[cyan]Happy testing! 🚀[/cyan]")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
