"""
RealityBench Reusable Rich Tables
Central table definitions for scoreboards, task results, failure summaries, and assertion tests.
"""

from typing import Any

from rich import box
from rich.table import Table

from .styles import FAIL_ICON, PASS_ICON


def scoreboard_table(target_summaries: dict[str, dict[str, float]]) -> Table:
    """
    Renders the central Model Leaderboard comparing Demo Score, Reality Score, and Reality Gap.
    """
    table = Table(
        title="[header]RealityBench: Multi-Model Empirical Scoreboard[/header]",
        box=box.HEAVY_EDGE,
        border_style="border",
        header_style="bold yellow",
        show_lines=True
    )
    table.add_column("Evaluation Target", style="model", width=20, overflow="fold")
    table.add_column("Demo Score\n(Happy Path)", justify="center", style="info", width=12, overflow="fold")
    table.add_column("Reality Score\n(Perturb)", justify="center", style="success", width=14, overflow="fold")
    table.add_column("Reality Gap\n(Gap)", justify="center", style="reality_gap", width=12, overflow="fold")
    table.add_column("Robustness Rating", justify="center", width=20, overflow="fold")

    for target, s in target_summaries.items():
        demo = s.get("avg_demo_score", 0.0) * 100
        reality = s.get("avg_reality_score", 0.0) * 100
        gap = s.get("avg_reality_gap", 0.0) * 100

        if gap <= 5.0:
            rating = "[success][*****] Production Ready[/success]"
        elif gap <= 15.0:
            rating = "[info][****] Resilient[/info]"
        elif gap <= 30.0:
            rating = "[warning][***] Moderate Fragility[/warning]"
        else:
            rating = "[failure][*] High Fragility Trap[/failure]"

        table.add_row(
            target,
            f"{demo:.2f}%",
            f"{reality:.2f}%",
            f"{gap:+.2f}%",
            rating
        )

    return table


def task_breakdown_table(arg1: Any, arg2: Any) -> Table:
    """
    Renders a per-task score breakdown for a specific evaluation target.
    Accepts (target_name, tasks_dict) or (tasks_dict, target_name).
    """
    if isinstance(arg1, str):
        target_name = arg1
        tasks_dict = arg2
    else:
        tasks_dict = arg1
        target_name = str(arg2)

    table = Table(
        title=f"[header]Task Performance Breakdown: [model]{target_name}[/model][/header]",
        box=box.ROUNDED,
        border_style="border",
        header_style="bold cyan",
        show_lines=True
    )
    table.add_column("Task ID", style="task", width=28, overflow="fold")
    table.add_column("Demo Score", justify="center", style="info", width=12, overflow="fold")
    table.add_column("Reality Score", justify="center", style="success", width=14, overflow="fold")
    table.add_column("Reality Gap", justify="center", style="reality_gap", width=14, overflow="fold")
    table.add_column("Status", justify="center", width=12, overflow="fold")

    for task_id, rep in tasks_dict.items():
        demo = rep.get("demo_score", 0.0) * 100
        reality = rep.get("reality_score", 0.0) * 100
        gap = rep.get("reality_gap", 0.0) * 100

        status = "[success]PASSED[/success]" if reality >= 70.0 else "[failure]FRAGILE[/failure]"
        table.add_row(
            task_id,
            f"{demo:.1f}%",
            f"{reality:.1f}%",
            f"{gap:+.1f}%",
            status
        )

    return table


def test_results_table(test_results: list[Any], task_name: str = "") -> Table:
    """Renders individual deterministic test assertions with pass/fail indicators."""
    table = Table(
        title=f"[header]Assertion Results: [task]{task_name}[/task][/header]" if task_name else "[header]Assertion Results[/header]",
        box=box.ROUNDED,
        border_style="border",
        header_style="bold magenta",
        show_lines=False
    )
    table.add_column("Result", justify="center", width=8, overflow="fold")
    table.add_column("Regime", justify="center", style="info", width=10, overflow="fold")
    table.add_column("Category", style="warning", width=24, overflow="fold")
    table.add_column("Test Name", style="white", min_width=32, overflow="fold")
    table.add_column("Details", style="muted", overflow="fold")

    for t in test_results:
        icon = PASS_ICON if t.passed else FAIL_ICON
        regime = getattr(t, "regime", "").upper()
        cat = getattr(t, "category", "")
        name = getattr(t, "test_name", "")
        details = getattr(t, "details", "")

        table.add_row(icon, regime, cat, name, details)

    return table


def task_catalog_table(all_tasks: list[Any]) -> Table:
    """Renders the catalog of all 12 registered RealityBench tasks."""
    table = Table(
        title="[header]Registered RealityBench Tasks (12 Total)[/header]",
        box=box.ROUNDED,
        border_style="border",
        header_style="bold yellow",
        show_lines=True
    )
    table.add_column("#", justify="center", style="info", width=4, overflow="fold")
    table.add_column("Task ID", style="task", width=28, overflow="fold")
    table.add_column("Task Name", style="bold white", width=26, overflow="fold")
    table.add_column("Software Engineering Focus", style="muted", overflow="fold")

    for t in all_tasks:
        table.add_row(
            f"{t.task_number:02d}",
            t.task_id,
            t.name,
            t.category_focus
        )

    return table


def failure_summary_table(category_counts: dict[str, dict[str, int]]) -> Table:
    """Renders a failure category distribution table."""
    table = Table(
        title="[header]Failure Vulnerability by Category[/header]",
        box=box.ROUNDED,
        border_style="border",
        header_style="bold red",
        show_lines=True
    )
    table.add_column("Software Category", style="white", width=30, overflow="fold")
    table.add_column("Tests Run", justify="center", style="info", width=12, overflow="fold")
    table.add_column("Failed", justify="center", style="failure", width=10, overflow="fold")
    table.add_column("Failure Rate", justify="center", style="warning", width=14, overflow="fold")

    for cat, data in category_counts.items():
        total = data.get("tested", 0)
        failed = data.get("failed", 0)
        rate = (failed / total * 100) if total > 0 else 0.0
        table.add_row(
            cat.replace("_", " ").title(),
            str(total),
            str(failed),
            f"{rate:.1f}%"
        )

    return table


def matrix_table(
    evaluations: dict[str, dict[str, Any]],
    all_tasks: list[Any]
) -> Table:
    """
    Renders the Task x Model Performance Matrix.
    Displays every task on rows and evaluation targets across columns.
    """
    targets = list(evaluations.keys())

    table = Table(
        title="[header]RealityBench: Task x Model Performance Matrix[/header]",
        box=box.HEAVY_EDGE,
        border_style="border",
        header_style="bold yellow",
        show_lines=True
    )
    table.add_column("#", justify="center", style="info", width=4, overflow="fold")
    table.add_column("Task Name", style="bold white", width=22, overflow="fold")

    for target in targets:
        # Format target name nicely
        short_name = target.replace("realitybench-", "")
        table.add_column(short_name, justify="center", style="model", overflow="fold")

    for t in all_tasks:
        task_num = f"{getattr(t, 'task_number', 0):02d}"
        task_name = getattr(t, "name", str(t))
        task_id = getattr(t, "task_id", str(t))

        row_cells = [task_num, task_name]

        for target in targets:
            target_data = evaluations.get(target, {}).get(task_id, {})
            if not target_data:
                row_cells.append("[muted]--[/muted]")
                continue

            reality_score = target_data.get("reality_score", 0.0) * 100
            gap = target_data.get("reality_gap", 0.0) * 100

            if reality_score >= 80.0:
                cell_text = f"[green]{reality_score:.0f}%[/green]"
            elif reality_score >= 50.0:
                cell_text = f"[yellow]{reality_score:.0f}%[/yellow]"
            else:
                cell_text = f"[red]{reality_score:.0f}%[/red]"

            # Append small gap tag if gap is significant
            if gap > 20.0:
                cell_text += f"\n[magenta]G:{gap:+.0f}%[/magenta]"

            row_cells.append(cell_text)

        table.add_row(*row_cells)

    return table
