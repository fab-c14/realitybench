"""
RealityBench Central Color Language & Style Definitions
Establishes a unified visual hierarchy across terminal presentations.
"""

from rich.style import Style
from rich.theme import Theme

# -----------------------------------------------------------------------------
# Color Language Guidelines:
# GREEN:   Success, passed assertions, completed tasks, healthy results
# RED:     Failures, errors, crashed applications, failed assertions
# YELLOW:  Warnings, retries, degraded behavior, reality gap warnings
# CYAN:    Informational data, model names, task names, benchmark metadata
# MAGENTA: Key research metrics, Reality Gap, notable findings
# BLUE:    Neutral informational sections, borders, structural outlines
# MUTED:   Secondary details, timestamps, file paths
# -----------------------------------------------------------------------------

THEME_STYLES = {
    "success": Style(color="green", bold=True),
    "failure": Style(color="red", bold=True),
    "error": Style(color="red", bold=True),
    "warning": Style(color="yellow", bold=True),
    "info": Style(color="cyan"),
    "model": Style(color="cyan", bold=True),
    "task": Style(color="green", bold=True),
    "metric": Style(color="magenta", bold=True),
    "reality_gap": Style(color="magenta", bold=True),
    "muted": Style(color="white", dim=True),
    "border": Style(color="blue"),
    "header": Style(color="bright_cyan", bold=True),
    "command": Style(color="bright_cyan", bold=True),
    "demo": Style(color="cyan", bold=True),
    "reality": Style(color="green", bold=True),
    "gap_high": Style(color="red", bold=True),
    "gap_med": Style(color="yellow", bold=True),
    "gap_low": Style(color="green", bold=True),
}

BENCHMARK_THEME = Theme(THEME_STYLES)

# Monochrome theme for --no-color mode
MONOCHROME_STYLES = {
    k: Style() for k in THEME_STYLES
}
MONOCHROME_THEME = Theme(MONOCHROME_STYLES)

# Symbolic Status Indicators (CP1252 / Windows Terminal Safe)
PASS_ICON = "[green][PASS][/green]"
FAIL_ICON = "[red][FAIL][/red]"
WARN_ICON = "[yellow][WARN][/yellow]"
INFO_ICON = "[cyan][INFO][/cyan]"
