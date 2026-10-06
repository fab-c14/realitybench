"""
RealityBench Terminal Graphs & Visualizations
Rich-compatible terminal charts for Demo vs. Reality comparison,
Reality Gap gauges, failure category distributions, and sparklines.
Includes automatic CP1252/ASCII fallback to guarantee zero encoding crashes on Windows.
"""

import sys

from rich import box
from rich.table import Table
from rich.text import Text


def get_bar_chars() -> tuple[str, str]:
    """
    Returns (fill_char, empty_char) based on terminal character encoding capability.
    Uses Unicode blocks if supported; falls back to ASCII for CP1252/Windows console safety.
    """
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "\u2588\u2591".encode(encoding)
        return "\u2588", "\u2591"
    except (UnicodeEncodeError, LookupError):
        return "#", "-"


def get_sparkline_chars() -> list[str]:
    """Returns sparkline tick levels with ASCII fallback."""
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "\u2581\u2583\u2585\u2587\u2588".encode(encoding)
        return [" ", "\u2581", "\u2582", "\u2583", "\u2584", "\u2585", "\u2586", "\u2587", "\u2588"]
    except (UnicodeEncodeError, LookupError):
        return ["_", ".", "-", "=", "+", "*", "#"]


def horizontal_bar(
    val: float,
    max_val: float = 1.0,
    width: int = 18,
    color: str = "green",
    show_pct: bool = True
) -> Text:
    """
    Renders a styled completeness bar:
    - Full completion (100%): pure solid bars [==================]
    - Mid completion (<100%): arrow bars [=========>        ]
    """
    ratio = max(0.0, min(1.0, val / max_val if max_val > 0 else 0.0))
    filled_count = round(ratio * width)

    bar = Text()
    bar.append("[", style="muted")
    if filled_count <= 0:
        bar.append(" " * width, style="muted")
    elif filled_count >= width or ratio >= 0.999:
        bar.append("=" * width, style=f"bold {color}")
    else:
        if filled_count == 1:
            bar.append(">", style=f"bold {color}")
        else:
            bar.append("=" * (filled_count - 1), style=color)
            bar.append(">", style=f"bold {color}")
        bar.append(" " * (width - filled_count), style="muted")
    bar.append("]", style="muted")

    if show_pct:
        bar.append(f" {val * 100:>5.1f}%", style=color)

    return bar


def gap_gauge(gap: float, width: int = 14) -> Text:
    """
    Renders a colored gauge indicating the severity of the Reality Gap:
    - Full gap: pure bars [==============]
    - Mid gap: arrow bars [=======>      ]
    """
    clamped_gap = max(0.0, min(1.0, gap))
    filled_count = round(clamped_gap * width)

    if gap <= 0.05:
        color = "green"
        status = "Resilient"
    elif gap <= 0.20:
        color = "yellow"
        status = "Moderate"
    else:
        color = "bold red"
        status = "Fragility Alert"

    gauge = Text()
    gauge.append("[", style="muted")
    if filled_count <= 0:
        gauge.append(" " * width, style="muted")
    elif filled_count >= width or clamped_gap >= 0.999:
        gauge.append("=" * width, style=f"bold {color}")
    else:
        if filled_count == 1:
            gauge.append(">", style=f"bold {color}")
        else:
            gauge.append("=" * (filled_count - 1), style=color)
            gauge.append(">", style=f"bold {color}")
        gauge.append(" " * (width - filled_count), style="muted")
    gauge.append("]", style="muted")
    gauge.append(f" {gap * 100:>+5.1f}%", style="reality_gap")
    gauge.append(f" ({status})", style=color)

    return gauge


def score_comparison_chart(
    demo_score: float,
    reality_score: float,
    reality_gap: float,
    width: int = 16
) -> Table:
    """
    Renders a comparative horizontal chart for Demo Score, Reality Score, and Reality Gap.
    """
    table = Table(
        box=box.SIMPLE,
        show_header=False,
        show_edge=False,
        pad_edge=False,
        collapse_padding=True
    )
    table.add_column("Metric", style="bold white", width=18)
    table.add_column("Visualization", width=width + 12)

    # Demo Bar
    demo_bar = horizontal_bar(demo_score, width=width, color="cyan")
    table.add_row("Demo Score (Happy)", demo_bar)

    # Reality Bar
    reality_color = "green" if reality_score >= 0.70 else ("yellow" if reality_score >= 0.40 else "red")
    reality_bar = horizontal_bar(reality_score, width=width, color=reality_color)
    table.add_row("Reality Score (Stress)", reality_bar)

    # Gap Gauge
    gap_bar = gap_gauge(reality_gap, width=width)
    table.add_row("Reality Gap (Delta)", gap_bar)

    return table


def failure_categories_chart(
    category_stats: dict[str, dict[str, int]],
    width: int = 16
) -> Table:
    """
    Renders a horizontal bar chart displaying failure rates across vulnerability categories.
    """
    table = Table(
        title="[header]Failure Distribution by Category[/header]",
        box=box.ROUNDED,
        border_style="border",
        header_style="bold red",
        show_lines=False
    )
    table.add_column("Category", style="white", width=22, overflow="fold")
    table.add_column("Failure Rate Bar", width=width + 10, overflow="fold")
    table.add_column("Failed/Total", justify="right", style="muted", width=12, overflow="fold")

    for cat_name, stats in category_stats.items():
        total = stats.get("tested", 0)
        failed = stats.get("failed", 0)
        rate = (failed / total) if total > 0 else 0.0

        bar_color = "red" if rate > 0.4 else ("yellow" if rate > 0.1 else "green")
        rate_bar = horizontal_bar(rate, width=width, color=bar_color)

        formatted_name = cat_name.replace("_", " ").title()
        table.add_row(
            formatted_name,
            rate_bar,
            f"{failed}/{total}"
        )

    return table


def sparkline(values: list[float], max_val: float = 1.0) -> str:
    """
    Generates a compact sparkline trend string from a list of numeric values.
    """
    if not values:
        return ""
    levels = get_sparkline_chars()
    num_levels = len(levels) - 1

    chars = []
    for v in values:
        ratio = max(0.0, min(1.0, v / max_val if max_val > 0 else 0.0))
        idx = round(ratio * num_levels)
        chars.append(levels[idx])

    return "".join(chars)
