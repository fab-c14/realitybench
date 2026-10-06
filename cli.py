"""
RealityBench CLI
Rich-powered terminal interface for RealityBench:
- Live colorful execution dashboard
- Continuous Rich Live + Layout updates
- Task catalog inspection with syntax highlighting
- Pilot study execution (Tasks 1, 2, 3)
- Task x Model Performance Matrix
- Terminal Graphs and Failure Analytics
- CI/Kaggle compatibility (--no-animation, --no-color, --quiet)
"""

import json
import os
import sys

import typer

# Ensure realitybench is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
bench_root = os.path.abspath(current_dir)
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

from benchmark.run_full_benchmark import (
    RESULTS_DIR,
    run_full_suite,
    run_pilot_suite,
)
from benchmark.tasks.registry import ALL_TASKS, TASK_MAP
from ui import (
    code_panel,
    configure_ui,
    console,
    error_panel,
    install_rich_traceback,
    matrix_table,
    print_banner,
    print_section_rule,
    score_comparison_chart,
    scoreboard_table,
    task_breakdown_table,
    task_catalog_table,
    task_result_panel,
    test_results_table,
)

install_rich_traceback()

app = typer.Typer(
    help="RealityBench: Benchmarking AI-Generated Software Beyond the Happy Path",
    rich_markup_mode="rich",
    no_args_is_help=True
)


@app.command("tasks")
def list_tasks(
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """List all 12 registered benchmark tasks."""
    configure_ui(no_color=no_color)
    print_banner()
    console.print(task_catalog_table(ALL_TASKS))
    console.print("\n[muted]Tip: Use [command]realitybench inspect <task_id>[/command] to view prompt and details.[/muted]\n")


@app.command("pilot")
def execute_pilot(
    target: str | None = typer.Option(
        None, "--target", "-t",
        help="Specific target to evaluate: 'naive-baseline', 'robust-baseline', or local Ollama model"
    ),
    no_animation: bool = typer.Option(False, "--no-animation", help="Disable live layout animation for CI/Kaggle"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output mode"),
):
    """Run the 3-task pilot study (Login, Search, Checkout) to test calibration."""
    configure_ui(no_animation=no_animation, no_color=no_color, quiet=quiet)
    targets = [target] if target else None
    run_pilot_suite(
        targets,
        no_animation=no_animation,
        no_color=no_color,
        quiet=quiet
    )
    if not quiet:
        console.print("[pass]Pilot study completed successfully![/pass]\n")


@app.command("run")
def execute_benchmark(
    target: str | None = typer.Option(
        None, "--target", "-t",
        help="Evaluation target: 'naive-baseline', 'robust-baseline', model name, or 'all'"
    ),
    pilot: bool = typer.Option(
        False, "--pilot", "-p",
        help="Run only the 3-task pilot subset instead of all 12 tasks"
    ),
    no_animation: bool = typer.Option(False, "--no-animation", help="Disable live layout animation for CI/Kaggle"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output mode"),
):
    """Run RealityBench evaluation across tasks and display colorful results."""
    configure_ui(no_animation=no_animation, no_color=no_color, quiet=quiet)

    if target and target != "all":
        targets = [target]
    else:
        targets = None

    if pilot:
        run_pilot_suite(
            targets,
            no_animation=no_animation,
            no_color=no_color,
            quiet=quiet
        )
    else:
        run_full_suite(
            targets,
            no_animation=no_animation,
            no_color=no_color,
            quiet=quiet
        )

    if not quiet:
        console.print("[pass]Benchmark run completed successfully![/pass]\n")


@app.command("inspect")
def inspect_task(
    task_id: str = typer.Argument(..., help="Task identifier (e.g. realitybench-login)"),
    code: str | None = typer.Option(
        None, "--code", "-c",
        help="View reference implementation code: 'naive' or 'robust'"
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Inspect the specification, rubric, and reference code of a task."""
    configure_ui(no_color=no_color)
    print_banner()
    task = TASK_MAP.get(task_id)
    if not task:
        console.print(error_panel("Task Not Found", f"Task '{task_id}' not found.\nRun [command]realitybench tasks[/command] to view available tasks."))
        raise typer.Exit(1)

    print_section_rule(f"Task {task.task_number:02d}: {task.name}")
    console.print(f"[info]Identifier:[/info] [task]{task.task_id}[/task]")
    console.print(f"[info]Software Focus:[/info] {task.category_focus}\n")

    if code == "naive":
        console.print(code_panel(f"Naive Baseline Code ({task.task_id})", task.naive_code, language="html"))
    elif code == "robust":
        console.print(code_panel(f"Robust Baseline Code ({task.task_id})", task.robust_code, language="html"))
    else:
        console.print(code_panel(f"Product Specification & Model Prompt ({task.task_id})", task.prompt, language="text"))
        console.print("\n[muted]Tip: Pass [cyan]--code naive[/cyan] or [cyan]--code robust[/cyan] to inspect reference code.[/muted]\n")


@app.command("test")
def test_task(
    task_id: str = typer.Argument(..., help="Task identifier to test locally (e.g. realitybench-login)"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Run local headless browser evaluation of a task on naive and robust baselines."""
    configure_ui(no_color=no_color)
    print_banner()
    task = TASK_MAP.get(task_id)
    if not task:
        console.print(error_panel("Task Not Found", f"Task '{task_id}' not found.\nRun [command]realitybench tasks[/command] to view available tasks."))
        raise typer.Exit(1)

    print_section_rule(f"Executing Local Grader: {task.name}")

    console.print(f"[info]Grading Naive Baseline for [task]{task.name}[/task]...[/info]")
    r_naive = task.grader(task.naive_code)
    console.print(task_result_panel(f"{task.name} (Naive Baseline)", r_naive.demo_score, r_naive.reality_score, r_naive.reality_gap))
    console.print(test_results_table(r_naive.test_results))

    console.print(f"\n[info]Grading Robust Baseline for [task]{task.name}[/task]...[/info]")
    r_robust = task.grader(task.robust_code)
    console.print(task_result_panel(f"{task.name} (Robust Baseline)", r_robust.demo_score, r_robust.reality_score, r_robust.reality_gap))
    console.print(test_results_table(r_robust.test_results))
    console.print()


@app.command("report")
def show_report(
    pilot: bool = typer.Option(False, "--pilot", "-p", help="Show report for pilot study instead of full suite"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display the latest empirical evaluation scoreboard."""
    configure_ui(no_color=no_color)
    print_banner()
    filename = "pilot_benchmark_results.json" if pilot else "full_benchmark_results.json"
    res_path = os.path.join(RESULTS_DIR, filename)

    if not os.path.exists(res_path):
        console.print(error_panel("No Results Found", f"Result file [bold]{filename}[/bold] not found.\nRun [command]realitybench run[/command] first."))
        raise typer.Exit(1)

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summaries = data.get("target_summaries", {})
    if not summaries:
        console.print("[warning]No target summaries in results file.[/warning]")
        raise typer.Exit(1)

    print_section_rule("RealityBench Empirical Scoreboard")
    console.print(scoreboard_table(summaries))
    console.print(f"\n[muted]Evaluated: {data.get('timestamp')} | Tasks: {data.get('task_count')} | Target Count: {len(summaries)}[/muted]\n")


@app.command("matrix")
def show_matrix(
    pilot: bool = typer.Option(False, "--pilot", "-p", help="Show matrix for pilot study instead of full suite"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display the Task x Model Performance Matrix across all evaluations."""
    configure_ui(no_color=no_color)
    print_banner()
    filename = "pilot_benchmark_results.json" if pilot else "full_benchmark_results.json"
    res_path = os.path.join(RESULTS_DIR, filename)

    if not os.path.exists(res_path):
        console.print(error_panel("No Results Found", "No results found. Run [command]realitybench run[/command] first."))
        raise typer.Exit(1)

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    evaluations = data.get("evaluations", {})
    if not evaluations:
        console.print(error_panel("No Evaluations Found", "No task evaluations recorded in results file."))
        raise typer.Exit(1)

    print_section_rule("Task x Model Performance Matrix")
    console.print(matrix_table(evaluations, ALL_TASKS))
    console.print()


@app.command("charts")
def show_charts(
    target: str | None = typer.Option(None, "--target", "-t", help="Specific target to visualize"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display terminal graphs for Demo vs Reality scores and failure categories."""
    configure_ui(no_color=no_color)
    print_banner()
    res_path = os.path.join(RESULTS_DIR, "full_benchmark_results.json")
    if not os.path.exists(res_path):
        console.print(error_panel("No Results Found", "Run [command]realitybench run[/command] first."))
        raise typer.Exit(1)

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summaries = data.get("target_summaries", {})
    if not summaries:
        console.print("[warning]No summaries found.[/warning]")
        raise typer.Exit(1)

    print_section_rule("Terminal Visual Analytics")
    targets_to_show = [target] if target else list(summaries.keys())

    for tgt in targets_to_show:
        s = summaries.get(tgt)
        if not s:
            continue
        console.print(f"[model]{tgt}[/model]:")
        console.print(score_comparison_chart(
            s.get("avg_demo_score", 0.0),
            s.get("avg_reality_score", 0.0),
            s.get("avg_reality_gap", 0.0),
            width=24
        ))
        console.print()


@app.command("breakdown")
def show_breakdown(
    target: str = typer.Argument(..., help="Target name to inspect breakdown for (e.g. naive-baseline, robust-baseline)"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display task-by-task score breakdown for a specific evaluation target."""
    configure_ui(no_color=no_color)
    print_banner()
    res_path = os.path.join(RESULTS_DIR, "full_benchmark_results.json")
    if not os.path.exists(res_path):
        console.print(error_panel("No Results Found", "No full benchmark results found. Run [command]realitybench run[/command] first."))
        raise typer.Exit(1)

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    evals = data.get("evaluations", {}).get(target)
    if not evals:
        available_targets = list(data.get("evaluations", {}).keys())
        console.print(error_panel("Target Not Found", f"Target '{target}' not found in results.\nAvailable targets: {available_targets}"))
        raise typer.Exit(1)

    print_section_rule(f"Task Breakdown: {target}")
    console.print(task_breakdown_table(target, evals))
    console.print()


@app.command("view")
def open_graphical_dashboard(
    no_browser: bool = typer.Option(False, "--no-browser", help="Generate HTML dashboard without opening default browser"),
):
    """Generate and launch the interactive graphical HTML dashboard in your web browser."""
    from analysis.generate_html_dashboard import generate_and_open_dashboard
    print_banner()
    try:
        html_path = generate_and_open_dashboard(open_browser=not no_browser)
        console.print(f"[success]Graphical Dashboard Generated:[/success] [cyan]{html_path}[/cyan]")
        if not no_browser:
            console.print("[info]Opened dashboard in your default web browser.[/info]\n")
    except FileNotFoundError as e:
        console.print(error_panel("Results Missing", str(e)))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
