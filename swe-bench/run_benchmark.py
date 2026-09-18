#!/usr/bin/env python3
"""
SWE-bench Lite Runner for Claude Opus 5
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from anthropic import Anthropic
from datasets import load_dataset
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Load environment variables
load_dotenv()

console = Console()

class SWEBenchRunner:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        self.num_tasks = int(os.getenv("NUM_TASKS", "2"))
        self.model = os.getenv("MODEL_NAME", "claude-opus-5")
        self.results_dir = Path(os.getenv("RESULTS_DIR", "./results"))

        if not self.api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not set![/red]")
            sys.exit(1)

        # Initialize Anthropic client
        self.client = Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Create results directory
        self.results_dir.mkdir(exist_ok=True)

    def load_swe_bench_lite(self) -> List[Dict]:
        """Load SWE-bench Lite dataset"""
        console.print("[cyan]Loading SWE-bench Lite dataset...[/cyan]")
        try:
            dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
            tasks = list(dataset)[:self.num_tasks]
            console.print(f"[green]Loaded {len(tasks)} tasks[/green]")
            return tasks
        except Exception as e:
            console.print(f"[red]Error loading dataset: {e}[/red]")
            sys.exit(1)

    def create_prompt(self, task: Dict) -> str:
        """Create prompt for Claude from task"""
        problem_statement = task.get("problem_statement", "")
        repo = task.get("repo", "")
        base_commit = task.get("base_commit", "")

        prompt = f"""You are an expert software engineer tasked with fixing a bug in the {repo} repository.

**Problem Description:**
{problem_statement}

**Repository:** {repo}
**Base Commit:** {base_commit}

Please analyze the problem and provide a solution. Include:
1. Root cause analysis
2. The fix (code changes)
3. Explanation of your solution

Format your response as a structured solution.
"""
        return prompt

    def call_claude(self, prompt: str, task_id: str) -> Optional[Dict]:
        """Call Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                "task_id": task_id,
                "model": self.model,
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            console.print(f"[red]Error calling API for {task_id}: {e}[/red]")
            return None

    def run_benchmark(self):
        """Run the benchmark"""
        console.print(f"\n[bold cyan]SWE-bench Lite Test Runner[/bold cyan]")
        console.print(f"Model: [yellow]{self.model}[/yellow]")
        console.print(f"Tasks: [yellow]{self.num_tasks}[/yellow]")
        console.print(f"Base URL: [yellow]{self.base_url}[/yellow]\n")

        # Load tasks
        tasks = self.load_swe_bench_lite()

        results = []
        total_tokens = {"input": 0, "output": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                f"Processing {self.num_tasks} tasks...",
                total=self.num_tasks
            )

            for idx, task in enumerate(tasks, 1):
                task_id = task.get("instance_id", f"task_{idx}")
                progress.update(
                    task_progress,
                    description=f"Processing {task_id} ({idx}/{self.num_tasks})"
                )

                # Create prompt and call Claude
                prompt = self.create_prompt(task)
                result = self.call_claude(prompt, task_id)

                if result:
                    results.append(result)
                    total_tokens["input"] += result["usage"]["input_tokens"]
                    total_tokens["output"] += result["usage"]["output_tokens"]

                progress.advance(task_progress)
                time.sleep(1)  # Rate limiting

        # Save results
        self.save_results(results, total_tokens)
        self.display_summary(results, total_tokens)

    def save_results(self, results: List[Dict], total_tokens: Dict):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"swe_bench_results_{timestamp}.json"

        output_data = {
            "metadata": {
                "model": self.model,
                "num_tasks": self.num_tasks,
                "timestamp": datetime.now().isoformat(),
                "total_tokens": total_tokens
            },
            "results": results
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        console.print(f"\n[green]Results saved to: {output_file}[/green]")

    def display_summary(self, results: List[Dict], total_tokens: Dict):
        """Display summary table"""
        table = Table(title="SWE-bench Lite Test Summary")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Model", self.model)
        table.add_row("Total Tasks", str(len(results)))
        table.add_row("Successful", str(len([r for r in results if r])))
        table.add_row("Input Tokens", f"{total_tokens['input']:,}")
        table.add_row("Output Tokens", f"{total_tokens['output']:,}")
        table.add_row("Total Tokens", f"{sum(total_tokens.values()):,}")

        console.print("\n")
        console.print(table)

def main():
    runner = SWEBenchRunner()
    runner.run_benchmark()

if __name__ == "__main__":
    main()
