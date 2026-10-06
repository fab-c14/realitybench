"""
RealityBench Reusable Rich Progress Displays
Clean, unified progress bars and spinners for multi-task and multi-model benchmark runs.
"""

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .console import console


def create_benchmark_progress() -> Progress:
    """
    Creates a standard Rich Progress bar for tracking benchmark task progression.
    Displays Model, Task name, Phase (Demo/Reality), Progress bar, and Elapsed Time.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[model]{task.fields[model]:<18}[/model]"),
        TextColumn("[task]{task.fields[task]:<22}[/task]"),
        TextColumn("[info]{task.fields[phase]:<10}[/info]"),
        BarColumn(bar_width=25),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False
    )
