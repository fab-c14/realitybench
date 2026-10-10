"""
RealityBench CLI: grade AI-generated web pages against real-user conditions.

    realitybench tasks                         list the 12 tasks
    realitybench prompt checkout               print the spec to give your AI
    realitybench grade checkout page.html      grade the page your AI wrote
    realitybench baselines                     sanity-check the graders
"""

import json
from pathlib import Path
from typing import Annotated

import typer

from benchmark.graders.browser_runner import extract_html_code
from benchmark.graders.scoring import EvaluationReport
from benchmark.tasks.registry import ALL_TASKS, TASK_MAP, TaskDefinition

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)


def _task(name: str) -> TaskDefinition:
    task = TASK_MAP.get(name) or TASK_MAP.get(f"realitybench-{name}")
    if task is None:
        raise typer.BadParameter(f"Unknown task '{name}'. Run `realitybench tasks` to see the list.")
    return task


def _print_report(report: EvaluationReport) -> None:
    typer.echo(f"\n{report.task_name}")
    typer.echo(f"  Demo score     {report.demo_score:6.0%}   (happy path)")
    typer.echo(f"  Reality score  {report.reality_score:6.0%}   (errors, bad input, double clicks, mobile)")
    typer.echo(f"  Reality gap    {report.reality_gap:+6.0%}\n")
    if report.fake_backend:
        typer.echo("  WARNING  The page replaces fetch/XMLHttpRequest: it answers its own requests")
        typer.echo("           with a built-in fake server instead of calling the real API.\n")
    for t in report.test_results:
        mark = "PASS" if t.passed else "FAIL"
        typer.echo(f"  {mark}  [{t.regime:7}] {t.test_name}")
        if not t.passed:
            typer.echo(f"        {t.details}")


@app.command("tasks")
def list_tasks() -> None:
    """List the 12 tasks."""
    for t in ALL_TASKS:
        short = t.task_id.removeprefix("realitybench-")
        typer.echo(f"{t.task_number:02}  {short:16} {t.category_focus}")


@app.command("prompt")
def show_prompt(task: str) -> None:
    """Print a task's spec, ready to paste into any AI model."""
    typer.echo(_task(task).prompt)


@app.command("grade")
def grade(
    task: str,
    file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="HTML file, or a model reply containing it")],
    as_json: Annotated[bool, typer.Option("--json", help="Print the full report as JSON")] = False,
) -> None:
    """Grade an HTML page in a headless browser."""
    code = extract_html_code(file.read_text(encoding="utf-8"))
    report = _task(task).grader(code)
    if as_json:
        typer.echo(json.dumps(report.to_dict(), indent=2))
    else:
        _print_report(report)


@app.command("baselines")
def baselines() -> None:
    """Grade the hand-written naive and robust pages for every task."""
    for t in ALL_TASKS:
        naive, robust = t.grader(t.naive_code), t.grader(t.robust_code)
        typer.echo(f"{t.task_id:28} naive gap {naive.reality_gap:+.2f}   robust gap {robust.reality_gap:+.2f}")


if __name__ == "__main__":
    app()
