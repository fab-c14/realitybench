"""
RealityBench Central Console Instance & Presentation Helpers
Provides a single shared Console instance, banner utilities, and runtime UI configuration.
"""

from dataclasses import dataclass

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.traceback import install as rich_traceback_install

from .styles import BENCHMARK_THEME, MONOCHROME_THEME


@dataclass
class UIOptions:
    no_animation: bool = False
    no_color: bool = False
    quiet: bool = False


# Global UI configuration
ui_options = UIOptions()

# Global singleton console configured with the central RealityBench theme
console = Console(theme=BENCHMARK_THEME, highlight=False)


def configure_ui(no_animation: bool = False, no_color: bool = False, quiet: bool = False):
    """
    Configures the global UI options and console according to CLI/CI flags.
    """
    global console
    ui_options.no_animation = no_animation
    ui_options.no_color = no_color
    ui_options.quiet = quiet

    if no_color:
        console = Console(theme=MONOCHROME_THEME, no_color=True, highlight=False)
    else:
        console = Console(theme=BENCHMARK_THEME, highlight=False)


def install_rich_traceback():
    """
    Installs Rich traceback handler for uncaught infrastructure exceptions.
    Keeps tracebacks clean without showing noisy local variables.
    """
    rich_traceback_install(console=console, show_locals=False, width=100)


def print_banner():
    """Renders the standard RealityBench header banner unless in quiet mode."""
    if ui_options.quiet:
        return
    banner_text = Text()
    banner_text.append("  REALITY", style="bold red")
    banner_text.append("BENCH  ", style="bold white on red")
    banner_text.append("- Benchmarking AI-Generated Software Beyond the Happy Path\n", style="bold cyan")
    banner_text.append("  [100% Deterministic Assertions | Headless Chromium Harness | Kaggle Benchmarks SDK]", style="muted")
    console.print(Panel(banner_text, border_style="red", box=box.ROUNDED))


def print_section_rule(title: str):
    """Prints a styled horizontal rule across the terminal unless in quiet mode."""
    if ui_options.quiet:
        return
    console.rule(f"[header]{title}[/header]", style="border")
