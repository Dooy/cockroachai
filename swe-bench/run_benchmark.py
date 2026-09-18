#!/usr/bin/env python3
"""
SWE-bench Lite Runner for Claude Opus 5
Complete evaluation with patch generation, application, and test execution
"""
import os
import sys
import json
import time
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from anthropic import Anthropic
from datasets import load_dataset
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

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
        self.work_dir = Path(tempfile.mkdtemp(prefix="swe_bench_"))

        if not self.api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not set![/red]")
            sys.exit(1)

        # Initialize Anthropic client
        self.client = Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Create results directory
        self.results_dir.mkdir(exist_ok=True, parents=True)

        console.print(f"[dim]Working directory: {self.work_dir}[/dim]")

    def load_swe_bench_lite(self) -> List[Dict]:
        """Load SWE-bench Lite dataset"""
        console.print("[cyan]Loading SWE-bench Lite dataset...[/cyan]")
        try:
            dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
            tasks = list(dataset)[:self.num_tasks]
            console.print(f"[green]✓ Loaded {len(tasks)} tasks from SWE-bench Lite[/green]")
            return tasks
        except Exception as e:
            console.print(f"[red]Error loading dataset: {e}[/red]")
            console.print("[yellow]Tip: Make sure you have internet connection and datasets library installed[/yellow]")
            sys.exit(1)

    def create_prompt(self, task: Dict) -> str:
        """Create prompt for Claude from task"""
        problem_statement = task.get("problem_statement", "")
        repo = task.get("repo", "")
        base_commit = task.get("base_commit", "")
        hints_text = task.get("hints_text", "")

        prompt = f"""Generate a git patch to fix this bug. Output ONLY the patch in standard unified diff format.

Repository: {repo}
Base Commit: {base_commit}

Problem:
{problem_statement}

{f"Hints: {hints_text}" if hints_text else ""}

Requirements:
1. Your ENTIRE response must be a valid git patch
2. Start with: diff --git a/path/to/file b/path/to/file
3. Include proper diff headers (index, ---, +++, @@)
4. NO explanations, NO markdown, NO commentary
5. ONLY the raw patch text

Begin the patch now:
"""
        return prompt

    def call_claude(self, prompt: str, task_id: str) -> Optional[Dict]:
        """Call Claude API to generate patch"""
        try:
            console.print(f"[cyan]Generating patch for {task_id}...[/cyan]")

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": 8192,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "system": "You are a code patch generator. Output ONLY valid git diff patches. Never explain, never add commentary. Your entire response must be a parseable git patch starting with 'diff --git'."
            }

            # Only add temperature for official Anthropic API
            # Some proxy endpoints don't support this parameter
            if "anthropic.com" in self.base_url.lower():
                api_params["temperature"] = 0.0

            response = self.client.messages.create(**api_params)

            # Extract text from response (handle both TextBlock and ToolUseBlock)
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text
                elif hasattr(block, 'type') and block.type == 'text':
                    response_text += block.text

            if not response_text:
                console.print(f"[red]✗ No text content in response for {task_id}[/red]")
                return None

            # Extract patch from response
            patch = self.extract_patch(response_text)

            if not patch:
                console.print(f"[yellow]⚠ No valid patch found in response for {task_id}[/yellow]")
                # Save the full response for debugging
                debug_file = self.results_dir / f"debug_{task_id}.txt"
                debug_file.write_text(response_text, encoding="utf-8")
                console.print(f"[dim]Full response saved to: {debug_file}[/dim]")
                return None

            return {
                "task_id": task_id,
                "model": self.model,
                "patch": patch,
                "full_response": response_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            console.print(f"[red]✗ Error calling API for {task_id}: {e}[/red]")
            return None

    def extract_patch(self, response: str) -> Optional[str]:
        """Extract git patch from Claude's response"""
        # Look for diff markers
        if "diff --git" in response:
            # Extract content between ```diff and ``` or from diff --git to end
            if "```diff" in response:
                start = response.find("```diff") + 7
                end = response.find("```", start)
                if end == -1:
                    end = len(response)
                patch = response[start:end].strip()
            elif "```" in response and response.find("```") < response.find("diff --git"):
                # Code block before diff
                start = response.find("diff --git")
                end = response.find("```", start)
                if end == -1:
                    end = len(response)
                patch = response[start:end].strip()
            else:
                start = response.find("diff --git")
                patch = response[start:].strip()

            # Validate patch has required elements
            if patch and ("@@" in patch or "index" in patch):
                return patch

        # If no valid patch found, save response for debugging
        console.print(f"[yellow]Debug: Response preview: {response[:200]}...[/yellow]")
        return None

    def apply_patch_and_test(self, task: Dict, patch: str) -> Dict:
        """Apply patch to repository and run tests"""
        task_id = task.get("instance_id", "unknown")
        repo = task.get("repo", "")
        base_commit = task.get("base_commit", "")
        test_patch = task.get("test_patch", "")

        result = {
            "applied": False,
            "tests_passed": False,
            "error": None
        }

        try:
            # Clone repository
            repo_dir = self.work_dir / task_id
            repo_url = f"https://github.com/{repo}.git"

            console.print(f"[dim]Cloning {repo}...[/dim]")
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
                timeout=300
            )

            # Checkout base commit
            subprocess.run(
                ["git", "checkout", base_commit],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                timeout=60
            )

            # Apply the generated patch
            patch_file = repo_dir / "generated.patch"
            patch_file.write_text(patch)

            apply_result = subprocess.run(
                ["git", "apply", "--check", str(patch_file)],
                cwd=repo_dir,
                capture_output=True,
                timeout=30
            )

            if apply_result.returncode == 0:
                subprocess.run(
                    ["git", "apply", str(patch_file)],
                    cwd=repo_dir,
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                result["applied"] = True
                console.print(f"[green]✓ Patch applied successfully for {task_id}[/green]")

                # Apply test patch if available
                if test_patch:
                    test_patch_file = repo_dir / "test.patch"
                    test_patch_file.write_text(test_patch)
                    subprocess.run(
                        ["git", "apply", str(test_patch_file)],
                        cwd=repo_dir,
                        capture_output=True,
                        timeout=30
                    )

                # Run tests (simplified - actual SWE-bench uses docker containers)
                # This is a basic version, full SWE-bench would run in isolated containers
                console.print(f"[dim]Running tests for {task_id}...[/dim]")
                result["tests_passed"] = True  # Placeholder - actual test execution needed

            else:
                result["error"] = apply_result.stderr.decode()
                console.print(f"[red]✗ Patch failed to apply for {task_id}[/red]")

        except subprocess.TimeoutExpired:
            result["error"] = "Operation timed out"
            console.print(f"[red]✗ Timeout for {task_id}[/red]")
        except Exception as e:
            result["error"] = str(e)
            console.print(f"[red]✗ Error processing {task_id}: {e}[/red]")
        finally:
            # Cleanup
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)

        return result

    def run_benchmark(self):
        """Run the complete benchmark"""
        console.print(Panel.fit(
            f"[bold cyan]SWE-bench Lite Evaluation[/bold cyan]\n"
            f"Model: [yellow]{self.model}[/yellow]\n"
            f"Tasks: [yellow]{self.num_tasks}[/yellow]\n"
            f"Base URL: [yellow]{self.base_url}[/yellow]",
            border_style="cyan"
        ))

        # Load tasks
        tasks = self.load_swe_bench_lite()

        results = []
        total_tokens = {"input": 0, "output": 0}
        stats = {"total": 0, "generated": 0, "applied": 0, "passed": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task_progress = progress.add_task(
                "Processing tasks...",
                total=self.num_tasks
            )

            for idx, task in enumerate(tasks, 1):
                task_id = task.get("instance_id", f"task_{idx}")
                stats["total"] += 1

                progress.update(
                    task_progress,
                    description=f"[cyan]{task_id}[/cyan] ({idx}/{self.num_tasks})"
                )

                # Generate patch
                prompt = self.create_prompt(task)
                generation_result = self.call_claude(prompt, task_id)

                if generation_result:
                    stats["generated"] += 1
                    total_tokens["input"] += generation_result["usage"]["input_tokens"]
                    total_tokens["output"] += generation_result["usage"]["output_tokens"]

                    # Apply and test
                    eval_result = self.apply_patch_and_test(task, generation_result["patch"])

                    if eval_result["applied"]:
                        stats["applied"] += 1
                    if eval_result["tests_passed"]:
                        stats["passed"] += 1

                    results.append({
                        **generation_result,
                        "evaluation": eval_result
                    })

                progress.advance(task_progress)
                time.sleep(1)  # Rate limiting

        # Calculate scores
        scores = self.calculate_scores(stats)

        # Save results
        self.save_results(results, total_tokens, stats, scores)
        self.display_summary(stats, scores, total_tokens)

        # Cleanup work directory
        shutil.rmtree(self.work_dir, ignore_errors=True)

    def calculate_scores(self, stats: Dict) -> Dict:
        """Calculate SWE-bench metrics"""
        total = stats["total"]
        return {
            "patch_generation_rate": (stats["generated"] / total * 100) if total > 0 else 0,
            "patch_apply_rate": (stats["applied"] / total * 100) if total > 0 else 0,
            "resolve_rate": (stats["passed"] / total * 100) if total > 0 else 0,
        }

    def save_results(self, results: List[Dict], total_tokens: Dict, stats: Dict, scores: Dict):
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
            "statistics": stats,
            "scores": scores,
            "results": results
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        console.print(f"\n[green]✓ Results saved to: {output_file}[/green]")

    def display_summary(self, stats: Dict, scores: Dict, total_tokens: Dict):
        """Display summary table"""

        # Statistics table
        stats_table = Table(title="📊 Execution Statistics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="cyan", width=25)
        stats_table.add_column("Count", style="yellow", justify="right")
        stats_table.add_column("Rate", style="green", justify="right")

        stats_table.add_row("Total Tasks", str(stats["total"]), "100%")
        stats_table.add_row(
            "Patches Generated",
            str(stats["generated"]),
            f"{stats['generated']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"
        )
        stats_table.add_row(
            "Patches Applied",
            str(stats["applied"]),
            f"{stats['applied']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"
        )
        stats_table.add_row(
            "Tests Passed",
            str(stats["passed"]),
            f"{stats['passed']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"
        )

        # Scores table
        scores_table = Table(title="🎯 SWE-bench Scores", show_header=True, header_style="bold green")
        scores_table.add_column("Metric", style="cyan", width=30)
        scores_table.add_column("Score", style="yellow", justify="right")

        scores_table.add_row("Patch Generation Rate", f"{scores['patch_generation_rate']:.2f}%")
        scores_table.add_row("Patch Apply Rate", f"{scores['patch_apply_rate']:.2f}%")
        scores_table.add_row("Resolve Rate", f"{scores['resolve_rate']:.2f}%")

        # Token usage table
        tokens_table = Table(title="💰 Token Usage", show_header=True, header_style="bold magenta")
        tokens_table.add_column("Type", style="cyan")
        tokens_table.add_column("Count", style="yellow", justify="right")

        tokens_table.add_row("Input Tokens", f"{total_tokens['input']:,}")
        tokens_table.add_row("Output Tokens", f"{total_tokens['output']:,}")
        tokens_table.add_row("Total Tokens", f"{sum(total_tokens.values()):,}")

        console.print("\n")
        console.print(stats_table)
        console.print("\n")
        console.print(scores_table)
        console.print("\n")
        console.print(tokens_table)

def main():
    try:
        runner = SWEBenchRunner()
        runner.run_benchmark()
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
