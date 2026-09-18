"""
SWE-agent wrapper for Claude Opus 5
Runs official SWE-agent with custom configuration
"""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    # Get configuration from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    model = os.getenv("MODEL", "claude-opus-5")
    num_tasks = int(os.getenv("NUM_TASKS", "2"))

    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set[/red]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold cyan]SWE-agent with {model}[/bold cyan]\n"
        f"Tasks: {num_tasks}\n"
        f"Base URL: {base_url}",
        title="Configuration"
    ))

    # Set environment variables for SWE-agent
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = api_key
    env["ANTHROPIC_BASE_URL"] = base_url

    # Build SWE-agent command
    cmd = [
        "python", "/swe-agent/run.py",
        "--model_name", model,
        "--data_path", "princeton-nlp/SWE-bench_Lite",
        "--split", "test",
        "--instance_filter", f"0:{num_tasks}",  # Run first N tasks
        "--config_file", "/app/config/default.yaml",
        "--output_dir", "/app/results"
    ]

    console.print(f"\n[yellow]Running command:[/yellow]\n{' '.join(cmd)}\n")

    # Run SWE-agent
    try:
        subprocess.run(cmd, env=env, check=True)
        console.print("\n[green]✓ SWE-agent completed successfully[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]✗ SWE-agent failed with exit code {e.returncode}[/red]")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        sys.exit(130)

if __name__ == "__main__":
    main()
