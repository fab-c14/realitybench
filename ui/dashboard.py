"""
RealityBench Live Dashboard
Rich Live + Layout continuously updating interactive benchmark dashboard.
Provides real-time visualization of model execution, sub-test streaming,
live leaderboards, score comparison charts, and failure distributions.
"""

import sys
import time
from typing import Any

from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.spinner import Spinner
from rich.text import Text

from .charts import failure_categories_chart, horizontal_bar, score_comparison_chart
from .console import console, ui_options
from .tables import scoreboard_table, test_results_table


class NpmArrowBarColumn(ProgressColumn):
    """
    Renders an npm-style animated progress bar:
    - Full completion (100%): pure solid bars [====================] in vibrant bold green
    - Mid completion (<100%): arrow bars completion [==========>         ] in bright cyan
    """

    def __init__(self, bar_width: int = 20):
        super().__init__()
        self.bar_width = bar_width

    def render(self, task: Any) -> Text:
        ratio = (task.completed / task.total) if task.total else 0.0
        ratio = max(0.0, min(1.0, ratio))
        filled = round(ratio * self.bar_width)

        bar = Text()
        bar.append("[", style="muted")
        if ratio >= 0.999 or task.finished or filled >= self.bar_width:
            bar.append("=" * self.bar_width, style="bold green")
        elif filled <= 0:
            bar.append(" " * self.bar_width, style="muted")
        else:
            if filled == 1:
                bar.append(">", style="bold bright_cyan")
            else:
                bar.append("=" * (filled - 1), style="bright_cyan")
                bar.append(">", style="bold bright_cyan")
            bar.append(" " * (self.bar_width - filled), style="muted")
        bar.append("]", style="muted")
        return bar


class BenchmarkDashboard:
    """
    Orchestrates the live updating terminal UI during benchmark execution.
    Features an in-place npm-style animated loader with vibrant semantic colors,
    arrow bars for mid-completions, and pure solid bars for full completion.
    Respects --no-animation and --quiet flags for CI / Kaggle environments.
    """

    def __init__(
        self,
        targets: list[str],
        total_tasks: int,
        no_animation: bool = False,
        quiet: bool = False
    ):
        self.targets = targets
        self.total_tasks = total_tasks
        self.total_evaluations = len(targets) * total_tasks
        self.completed_evaluations = 0

        self.no_animation = no_animation or ui_options.no_animation
        self.quiet = quiet or ui_options.quiet

        self.active_target: str = targets[0] if targets else "baseline"
        self.active_task_idx: int = 1
        self.active_task_name: str = "Initializing..."
        self.active_category_focus: str = ""
        self.status_message: str = "Preparing evaluation..."

        self.recent_assertions: list[Any] = []
        self.current_task_demo: float = 0.0
        self.current_task_reality: float = 0.0
        self.current_task_gap: float = 0.0

        # Accumulated metrics
        self.target_summaries: dict[str, dict[str, float]] = {
            t: {"avg_demo_score": 0.0, "avg_reality_score": 0.0, "avg_reality_gap": 0.0}
            for t in targets
        }
        self.evaluations_matrix: dict[str, dict[str, Any]] = {
            t: {} for t in targets
        }
        self.category_stats: dict[str, dict[str, int]] = {
            "functional_correctness": {"tested": 0, "failed": 0},
            "expected_interactions": {"tested": 0, "failed": 0},
            "failure_recovery": {"tested": 0, "failed": 0},
            "state_robustness": {"tested": 0, "failed": 0},
            "input_robustness": {"tested": 0, "failed": 0},
            "accessibility": {"tested": 0, "failed": 0},
            "responsive_behavior": {"tested": 0, "failed": 0},
            "interaction_safety": {"tested": 0, "failed": 0},
        }

        self.start_time: float = time.time()
        self.live: Live | None = None
        self.progress: Progress | None = None
        self.task_id: Any = None

    def start(self):
        """Initializes npm-style smooth animated loader."""
        self.start_time = time.time()
        if not self.no_animation and not self.quiet:
            encoding = sys.stdout.encoding or "utf-8"
            try:
                "\u280b".encode(encoding)
                spinner_name = "dots"
            except (UnicodeEncodeError, LookupError):
                spinner_name = "line"

            self.progress = Progress(
                SpinnerColumn(spinner_name=spinner_name, style="bold cyan"),
                TextColumn("[bold magenta]{task.fields[model]}[/bold magenta]"),
                TextColumn("[dim cyan]|[/dim cyan]"),
                TextColumn("[bold bright_white]{task.fields[task_count]}[/bold bright_white]"),
                TextColumn("[bold yellow]{task.fields[task_name]:<18}[/bold yellow]"),
                NpmArrowBarColumn(bar_width=14),
                TextColumn("[bold green]{task.percentage:>5.1f}%[/bold green]"),
                TimeElapsedColumn(),
                console=console,
                transient=False
            )
            self.progress.start()
            self.task_id = self.progress.add_task(
                "realitybench",
                total=self.total_evaluations,
                completed=0,
                model=self.active_target,
                task_count=f"[01/{self.total_tasks:02d}]",
                task_name="Initializing...",
                status_msg="Starting suite"
            )

    def stop(self):
        """Halts the progress loader."""
        if self.progress is not None:
            self.progress.stop()
            self.progress = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def elapsed_str(self) -> str:
        """Formats elapsed execution time as MM:SS."""
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        return f"{mins:02d}:{secs:02d}"

    def set_task_start(self, target: str, task_idx: int, task_name: str, category_focus: str):
        """Updates in-place animated loader for newly executing task."""
        self.active_target = target
        self.active_task_idx = task_idx
        self.active_task_name = task_name
        self.active_category_focus = category_focus
        self.status_message = f"Evaluating {task_name}..."
        self.current_task_demo = 0.0
        self.current_task_reality = 0.0
        self.current_task_gap = 0.0

        if self.progress is not None and self.task_id is not None:
            self.progress.update(
                self.task_id,
                model=target,
                task_count=f"[{task_idx:02d}/{self.total_tasks:02d}]",
                task_name=task_name,
                status_msg=f"{category_focus or 'Running assertions'}..."
            )
        elif self.no_animation and not self.quiet:
            console.print(
                f"[info][{self.elapsed_str()}][/info] [model]{target}[/model] -> "
                f"[task]Task {task_idx:02d}: {task_name}[/task]..."
            )

    def set_task_complete(self, target: str, task_id: str, report: Any):
        """Records task completion and updates in-place animated loader with scores."""
        self.completed_evaluations += 1
        self.current_task_demo = getattr(report, "demo_score", 0.0)
        self.current_task_reality = getattr(report, "reality_score", 0.0)
        self.current_task_gap = getattr(report, "reality_gap", 0.0)

        # Store in matrix
        self.evaluations_matrix.setdefault(target, {})[task_id] = report.to_dict()

        # Update test assertions feed
        test_results = getattr(report, "test_results", [])
        if test_results:
            self.recent_assertions = test_results[-6:]
            for t in test_results:
                cat = getattr(t, "category", "")
                if cat in self.category_stats:
                    self.category_stats[cat]["tested"] += 1
                    if not t.passed:
                        self.category_stats[cat]["failed"] += 1

        self.status_message = (
            f"Finished Task {self.active_task_idx:02d}: Demo={self.current_task_demo:.0%}, "
            f"Reality={self.current_task_reality:.0%}, Gap={self.current_task_gap:+.0%}"
        )

        if self.progress is not None and self.task_id is not None:
            demo_pct = f"{self.current_task_demo * 100:.0f}%"
            real_pct = f"{self.current_task_reality * 100:.0f}%"
            gap_pct = f"{self.current_task_gap * 100:+.0f}%"
            status_text = f"Demo: {demo_pct} | Reality: {real_pct} | Gap: {gap_pct}"
            self.progress.update(
                self.task_id,
                completed=self.completed_evaluations,
                model=target,
                status_msg=status_text
            )
        elif self.no_animation and not self.quiet:
            console.print(
                f"[info][{self.elapsed_str()}][/info] [success][OK][/success] {task_id}: "
                f"Demo={self.current_task_demo:.1%}, Reality={self.current_task_reality:.1%}, Gap={self.current_task_gap:+.1%}"
            )

    def set_target_summary(self, target: str, summary: dict[str, float]):
        """Updates summary scores for target."""
        self.target_summaries[target] = summary

    def refresh(self):
        """Maintained for backwards-compatibility; does not cause terminal flickering."""

    def build_layout(self) -> Layout:
        """Constructs the Rich Layout with header, left/right main split, and footer."""
        layout = Layout(name="root")
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="left", ratio=6),
            Layout(name="right", ratio=5)
        )

        layout["left"].split_column(
            Layout(name="task_active", size=8),
            Layout(name="assertions_feed", ratio=1)
        )

        layout["right"].split_column(
            Layout(name="live_scoreboard", ratio=1),
            Layout(name="live_categories", size=10)
        )

        # 1. Header View
        header_text = Text()
        header_text.append(" REALITY", style="bold red")
        header_text.append("BENCH ", style="bold white on red")
        header_text.append(" LIVE EVALUATION RUNNER\n", style="bold cyan")
        header_text.append(" Target: ", style="muted")
        header_text.append(f"{self.active_target:<18} ", style="model")
        header_text.append("| Elapsed: ", style="muted")
        header_text.append(f"{self.elapsed_str()} ", style="info")
        header_text.append("| Status: ", style="muted")
        header_text.append(f"{self.status_message}", style="warning")

        spinner = Spinner("dots", text=header_text, style="cyan")
        layout["header"].update(Panel(spinner, border_style="red", box=box.ROUNDED))

        # 2. Left: Active Task & Test Assertions
        task_info_table = score_comparison_chart(
            self.current_task_demo,
            self.current_task_reality,
            self.current_task_gap,
            width=18
        )
        task_panel_title = f"[task]Task {self.active_task_idx:02d}: {self.active_task_name}[/task]"
        layout["task_active"].update(
            Panel(
                task_info_table,
                title=task_panel_title,
                subtitle=f"[muted]{self.active_category_focus}[/muted]",
                border_style="border",
                box=box.ROUNDED
            )
        )

        # Assertions Feed
        if self.recent_assertions:
            feed_table = test_results_table(self.recent_assertions)
        else:
            feed_table = Text("\n   Executing headless browser assertions...", style="muted")
        layout["assertions_feed"].update(
            Panel(feed_table, title="[header]Live Assertions Stream[/header]", border_style="border", box=box.ROUNDED)
        )

        # 3. Right: Live Leaderboard & Failure Categories
        sb = scoreboard_table(self.target_summaries)
        layout["live_scoreboard"].update(
            Panel(sb, title="[header]Live Multi-Model Leaderboard[/header]", border_style="border", box=box.ROUNDED)
        )

        cat_chart = failure_categories_chart(self.category_stats, width=14)
        layout["live_categories"].update(
            Panel(cat_chart, title="[header]Failure Category Breakdown[/header]", border_style="border", box=box.ROUNDED)
        )

        # 4. Footer View
        progress_ratio = (
            self.completed_evaluations / self.total_evaluations
            if self.total_evaluations > 0 else 0.0
        )
        bar_text = horizontal_bar(progress_ratio, width=28, color="bright_cyan")
        footer_text = Text()
        footer_text.append(" Overall Progress: ", style="info")
        footer_text.append_text(bar_text)
        footer_text.append(f" ({self.completed_evaluations}/{self.total_evaluations} tasks) ", style="muted")
        footer_text.append("| Engine: Headless Chromium", style="muted")
        layout["footer"].update(Panel(footer_text, border_style="border", box=box.ROUNDED))

        return layout
