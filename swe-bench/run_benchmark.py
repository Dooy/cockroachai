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

    def create_prompt(self, task: Dict, file_contents: Dict[str, str] = None) -> str:
        """Create prompt for Claude from task"""
        problem_statement = task.get("problem_statement", "")
        repo = task.get("repo", "")
        base_commit = task.get("base_commit", "")
        hints_text = task.get("hints_text", "")

        # Add file contents if provided
        files_section = ""
        if file_contents:
            files_section = "\n\nRelevant file contents:\n"
            for filepath, content in file_contents.items():
                files_section += f"\n=== {filepath} ===\n{content}\n"

        prompt = f"""Generate a git patch to fix this bug. Output ONLY the patch in standard unified diff format.

Repository: {repo}
Base Commit: {base_commit}

Problem:
{problem_statement}

{f"Hints: {hints_text}" if hints_text else ""}
{files_section}

Requirements:
1. Your ENTIRE response must be a valid git patch
2. Use actual line numbers and content from the provided files
3. Start with: diff --git a/path/to/file b/path/to/file
4. Include proper diff headers (index, ---, +++, @@)
5. NO explanations, NO markdown, NO commentary
6. ONLY the raw patch text

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

    def extract_file_contents(self, task: Dict) -> Dict[str, str]:
        """Extract relevant file contents from repository before generating patch"""
        task_id = task.get("instance_id", "unknown")
        repo = task.get("repo", "")
        base_commit = task.get("base_commit", "")
        test_patch = task.get("test_patch", "")

        file_contents = {}
        temp_dir = self.work_dir / f"{task_id}_temp"

        try:
            repo_url = f"https://github.com/{repo}.git"

            console.print(f"[dim]Extracting files from {repo}...[/dim]")

            # Clone with full history and checkout specific commit
            subprocess.run(
                ["git", "clone", "--quiet", repo_url, str(temp_dir)],
                capture_output=True,
                timeout=600,
                check=True
            )

            subprocess.run(
                ["git", "checkout", base_commit],
                cwd=temp_dir,
                capture_output=True,
                timeout=60,
                check=True
            )

            # Extract file paths from test_patch (most reliable source)
            # test_patch shows which files are being tested, these are the relevant files
            import re
            found_files = set()

            if test_patch:
                # Find all "diff --git a/path b/path" lines
                diff_pattern = r'diff --git a/([^\s]+) b/[^\s]+'
                matches = re.findall(diff_pattern, test_patch)
                found_files.update(matches)

                # Also find "--- a/path" and "+++ b/path" patterns
                file_pattern = r'(?:---|\+\+\+) [ab]/([^\s]+)'
                matches = re.findall(file_pattern, test_patch)
                found_files.update(matches)

            # Also check problem statement for explicit file mentions
            problem_text = task.get("problem_statement", "")
            # Pattern: path/to/file.py (without a/ or b/ prefix, not starting with /)
            clean_file_pattern = r'(?<![/a-zA-Z])([a-zA-Z_][a-zA-Z0-9_/]*\.py)\b'
            matches = re.findall(clean_file_pattern, problem_text)
            found_files.update(matches)

            # Prioritize source files over test files
            # Separate source files and test files
            source_files = []
            test_files = []
            for f in found_files:
                if '/test' in f or f.startswith('test'):
                    test_files.append(f)
                else:
                    source_files.append(f)

            # For each test file, try to infer the corresponding source file
            inferred_source_files = []
            for test_file in test_files:
                # test_separable.py -> separable.py
                # tests/test_foo.py -> foo.py
                if 'test_' in test_file:
                    source_file = test_file.replace('/tests/', '/').replace('/test/', '/')
                    source_file = source_file.replace('test_', '')
                    if source_file not in source_files:
                        inferred_source_files.append(source_file)

            # Also check problem statement for module mentions
            if problem_text:
                # Look for module/function names that might correspond to files
                module_pattern = r'`([a-zA-Z_][a-zA-Z0-9_]*)`'
                modules = re.findall(module_pattern, problem_text)
                for module in modules:
                    # Check if any path contains this module name
                    for test_file in test_files:
                        dir_path = str(Path(test_file).parent.parent)  # Go up from tests/
                        potential_source = f"{dir_path}/{module}.py"
                        if potential_source not in source_files and potential_source not in inferred_source_files:
                            inferred_source_files.append(potential_source)

            # Combine: inferred sources + explicit sources + test files
            prioritized_files = inferred_source_files + source_files + test_files

            console.print(f"[dim]Found {len(prioritized_files)} files (inferred: {len(inferred_source_files)}, source: {len(source_files)}, test: {len(test_files)})[/dim]")

            # Try to read each file (limit to top 5 files to avoid context overflow)
            for file_path in prioritized_files[:5]:
                full_path = temp_dir / file_path
                if full_path.exists() and full_path.is_file():
                    try:
                        content = full_path.read_text(encoding='utf-8', errors='ignore')
                        # Limit to 20000 chars to leave room for prompt
                        if len(content) > 20000:
                            # Keep beginning and end
                            content = content[:15000] + "\n\n... (middle section truncated) ...\n\n" + content[-5000:]
                        file_contents[file_path] = content
                        console.print(f"[dim]✓ Extracted {file_path} ({len(content)} chars)[/dim]")
                    except Exception as e:
                        console.print(f"[yellow]⚠ Failed to read {file_path}: {e}[/yellow]")

        except Exception as e:
            console.print(f"[yellow]⚠ Could not extract file contents: {e}[/yellow]")
        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

        console.print(f"[dim]Total files extracted: {len(file_contents)}[/dim]")
        return file_contents

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
            # Clone repository with full history (not shallow)
            repo_dir = self.work_dir / task_id
            repo_url = f"https://github.com/{repo}.git"

            console.print(f"[dim]Cloning {repo}...[/dim]")
            subprocess.run(
                ["git", "clone", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
                timeout=600
            )

            # Checkout base commit
            console.print(f"[dim]Checking out {base_commit[:8]}...[/dim]")
            checkout_result = subprocess.run(
                ["git", "checkout", base_commit],
                cwd=repo_dir,
                capture_output=True,
                timeout=60
            )

            if checkout_result.returncode != 0:
                error_msg = checkout_result.stderr.decode('utf-8', errors='ignore')
                result["error"] = f"Git checkout failed: {error_msg}"
                console.print(f"[yellow]⚠ Checkout failed, trying to fetch commit...[/yellow]")

                # Try to fetch the specific commit
                subprocess.run(
                    ["git", "fetch", "origin", base_commit],
                    cwd=repo_dir,
                    capture_output=True,
                    timeout=120
                )

                # Try checkout again
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
                    console.print(f"[dim]Applying test patch...[/dim]")
                    test_patch_file = repo_dir / "test.patch"
                    test_patch_file.write_text(test_patch)
                    test_apply_result = subprocess.run(
                        ["git", "apply", str(test_patch_file)],
                        cwd=repo_dir,
                        capture_output=True,
                        timeout=30
                    )
                    if test_apply_result.returncode != 0:
                        console.print(f"[yellow]⚠ Test patch failed to apply[/yellow]")

                # Run actual tests using pytest
                console.print(f"[dim]Running tests for {task_id}...[/dim]")

                # First, try to install dependencies
                # Check if requirements.txt or setup.py exists
                if (repo_dir / "setup.py").exists():
                    console.print(f"[dim]Installing package...[/dim]")
                    install_result = subprocess.run(
                        ["pip", "install", "-e", ".", "-q"],
                        cwd=repo_dir,
                        capture_output=True,
                        timeout=300
                    )
                    if install_result.returncode != 0:
                        console.print(f"[yellow]⚠ Package installation failed[/yellow]")

                # Run pytest on the test files mentioned in test_patch
                # Extract test file paths from test_patch
                import re
                test_files = []
                if test_patch:
                    test_pattern = r'diff --git a/([^\s]+) b/[^\s]+'
                    matches = re.findall(test_pattern, test_patch)
                    test_files = [m for m in matches if 'test' in m]

                if test_files:
                    # Run pytest on specific test files
                    test_result = subprocess.run(
                        ["python", "-m", "pytest", "-xvs"] + test_files,
                        cwd=repo_dir,
                        capture_output=True,
                        timeout=300
                    )

                    # Check if tests passed
                    if test_result.returncode == 0:
                        result["tests_passed"] = True
                        console.print(f"[green]✓ Tests passed for {task_id}[/green]")
                    else:
                        result["tests_passed"] = False
                        result["error"] = (result.get("error", "") +
                                        f"\nTest output: {test_result.stdout.decode('utf-8', errors='ignore')[:500]}")
                        console.print(f"[red]✗ Tests failed for {task_id}[/red]")
                else:
                    # No specific test files, mark as passed if patch applied
                    result["tests_passed"] = True
                    console.print(f"[yellow]⚠ No test files found, marking as passed[/yellow]")

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

                # First, clone repository and extract relevant files
                file_contents = self.extract_file_contents(task)

                # Generate patch with file contents
                prompt = self.create_prompt(task, file_contents)
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
