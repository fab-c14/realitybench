"""
RealityBench Central UI Presentation Package
Unified presentation layer powered by Rich.
"""

from .charts import (
    failure_categories_chart,
    gap_gauge,
    horizontal_bar,
    score_comparison_chart,
    sparkline,
)
from .console import (
    configure_ui,
    console,
    install_rich_traceback,
    print_banner,
    print_section_rule,
    ui_options,
)
from .dashboard import BenchmarkDashboard
from .panels import (
    code_panel,
    error_panel,
    task_header_panel,
    task_result_panel,
)
from .progress import create_benchmark_progress
from .screens import render_final_screen, render_startup_screen
from .styles import (
    BENCHMARK_THEME,
    FAIL_ICON,
    INFO_ICON,
    MONOCHROME_THEME,
    PASS_ICON,
    THEME_STYLES,
    WARN_ICON,
)
from .tables import (
    failure_summary_table,
    matrix_table,
    scoreboard_table,
    task_breakdown_table,
    task_catalog_table,
    test_results_table,
)

__all__ = [
    "BENCHMARK_THEME",
    "FAIL_ICON",
    "INFO_ICON",
    "MONOCHROME_THEME",
    "PASS_ICON",
    "THEME_STYLES",
    "WARN_ICON",
    "BenchmarkDashboard",
    "code_panel",
    "configure_ui",
    "console",
    "create_benchmark_progress",
    "error_panel",
    "failure_categories_chart",
    "failure_summary_table",
    "gap_gauge",
    "horizontal_bar",
    "install_rich_traceback",
    "matrix_table",
    "print_banner",
    "print_section_rule",
    "render_final_screen",
    "render_startup_screen",
    "score_comparison_chart",
    "scoreboard_table",
    "sparkline",
    "task_breakdown_table",
    "task_catalog_table",
    "task_header_panel",
    "task_result_panel",
    "test_results_table",
    "ui_options",
]
