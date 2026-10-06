"""
Tests for RealityBench Rich UI Presentation Layer
Validates that all tables, panels, banners, charts, dashboard layouts,
and terminal screens render cleanly without errors.
"""

import io

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from benchmark.graders.scoring import EvaluationReport, TestResult
from benchmark.tasks.registry import ALL_TASKS
from ui import (
    BenchmarkDashboard,
    code_panel,
    configure_ui,
    error_panel,
    failure_categories_chart,
    failure_summary_table,
    gap_gauge,
    horizontal_bar,
    matrix_table,
    print_banner,
    render_final_screen,
    render_startup_screen,
    score_comparison_chart,
    scoreboard_table,
    sparkline,
    task_breakdown_table,
    task_catalog_table,
    task_header_panel,
    task_result_panel,
)
from ui import (
    test_results_table as render_test_results_table,
)
from ui.styles import BENCHMARK_THEME


def test_panels_rendering():
    """Validates that all panel generators produce valid Rich Panels."""
    p1 = task_header_panel(1, "Authentication & Login", "Input Validation", "qwen2.5-coder:1.5b", "reality")
    assert isinstance(p1, Panel)

    p2 = task_result_panel("Task 1: Login", 1.0, 0.45, 0.55, "qwen2.5-coder:1.5b")
    assert isinstance(p2, Panel)

    p3_generic = error_panel("Execution Error", "Database disconnected")
    assert isinstance(p3_generic, Panel)

    p3_detailed = error_panel("Login", "Qwen", "HTTP 500 unhandled", is_infrastructure=False)
    assert isinstance(p3_detailed, Panel)

    p4 = code_panel("const x = 1;", language="javascript", title="Snippet")
    assert isinstance(p4, Panel)


def test_tables_rendering():
    """Validates that all table generators produce valid Rich Tables."""
    # Scoreboard
    summaries = {
        "naive-baseline": {"avg_demo_score": 0.98, "avg_reality_score": 0.33, "avg_reality_gap": 0.65},
        "robust-baseline": {"avg_demo_score": 1.0, "avg_reality_score": 1.0, "avg_reality_gap": 0.0},
    }
    t_score = scoreboard_table(summaries)
    assert isinstance(t_score, Table)
    assert t_score.row_count == 2

    # Task Breakdown
    breakdown_data = {
        "realitybench-login": {"demo_score": 1.0, "reality_score": 0.33, "reality_gap": 0.67},
        "realitybench-search": {"demo_score": 1.0, "reality_score": 0.08, "reality_gap": 0.92},
    }
    t_breakdown = task_breakdown_table("naive-baseline", breakdown_data)
    assert isinstance(t_breakdown, Table)
    assert t_breakdown.row_count == 2

    # Task Catalog
    t_catalog = task_catalog_table(ALL_TASKS)
    assert isinstance(t_catalog, Table)
    assert t_catalog.row_count == 12

    # Assertion Results
    results = [
        TestResult(test_name="demo_1", category="functional_correctness", regime="demo", passed=True, details="pass"),
        TestResult(test_name="reality_1", category="input_robustness", regime="reality", passed=False, details="fail"),
    ]
    t_results = render_test_results_table(results, "Login Test")
    assert isinstance(t_results, Table)
    assert t_results.row_count == 2

    # Failure Summary
    cat_counts = {
        "input_robustness": {"tested": 10, "failed": 4},
        "failure_recovery": {"tested": 10, "failed": 7},
    }
    t_failure = failure_summary_table(cat_counts)
    assert isinstance(t_failure, Table)
    assert t_failure.row_count == 2


def test_charts_rendering():
    """Validates that terminal charts and visualizations render correctly."""
    # Horizontal Bar
    bar_text = horizontal_bar(0.75, width=20, color="green")
    assert isinstance(bar_text, Text)
    assert "75.0%" in str(bar_text)

    # Reality Gap Gauge
    gauge_low = gap_gauge(0.02)
    assert isinstance(gauge_low, Text)
    assert "Resilient" in str(gauge_low)

    gauge_high = gap_gauge(0.65)
    assert "Fragility Alert" in str(gauge_high)

    # Score comparison chart
    comp_table = score_comparison_chart(0.95, 0.40, 0.55)
    assert isinstance(comp_table, Table)
    assert comp_table.row_count == 3

    # Failure categories chart
    cat_stats = {
        "failure_recovery": {"tested": 12, "failed": 9},
        "input_robustness": {"tested": 12, "failed": 3},
    }
    cat_chart = failure_categories_chart(cat_stats)
    assert isinstance(cat_chart, Table)
    assert cat_chart.row_count == 2

    # Sparkline
    spark = sparkline([0.1, 0.4, 0.8, 1.0, 0.5])
    assert len(spark) == 5


def test_matrix_table_rendering():
    """Validates the Task x Model performance matrix."""
    evals = {
        "naive-baseline": {
            "realitybench-login": {"reality_score": 0.33, "reality_gap": 0.67},
            "realitybench-search": {"reality_score": 0.08, "reality_gap": 0.92},
        },
        "robust-baseline": {
            "realitybench-login": {"reality_score": 1.0, "reality_gap": 0.0},
            "realitybench-search": {"reality_score": 1.0, "reality_gap": 0.0},
        }
    }
    matrix = matrix_table(evals, ALL_TASKS[:2])
    assert isinstance(matrix, Table)
    assert matrix.row_count == 2
    assert len(matrix.columns) == 4  # #, Task Name, naive-baseline, robust-baseline


def test_dashboard_build_layout():
    """Validates the Rich Live Layout constructed by BenchmarkDashboard."""
    dash = BenchmarkDashboard(
        targets=["naive-baseline", "robust-baseline"],
        total_tasks=12,
        no_animation=True,
        quiet=False
    )
    layout = dash.build_layout()
    assert isinstance(layout, Layout)
    assert layout.get("header") is not None
    assert layout.get("main") is not None
    assert layout.get("footer") is not None

    # Test state updates
    dash.set_task_start("naive-baseline", 1, "Authentication & Login", "Input Validation")
    assert dash.active_task_name == "Authentication & Login"

    report = EvaluationReport(
        task_name="realitybench-login",
        demo_score=1.0,
        reality_score=0.33,
        reality_gap=0.67,
        test_results=[
            TestResult(test_name="t1", category="functional_correctness", regime="demo", passed=True),
            TestResult(test_name="t2", category="failure_recovery", regime="reality", passed=False),
        ]
    )
    dash.set_task_complete("naive-baseline", "realitybench-login", report)
    assert dash.completed_evaluations == 1
    assert dash.current_task_demo == 1.0
    assert dash.current_task_reality == 0.33


def test_screens_rendering():
    """Validates that startup and final screens render without throwing exceptions."""
    render_startup_screen(["naive-baseline"], task_count=3, no_animation=True)

    results = {
        "timestamp": "2026-10-06T12:00:00Z",
        "task_count": 2,
        "targets": ["naive-baseline"],
        "target_summaries": {
            "naive-baseline": {"avg_demo_score": 1.0, "avg_reality_score": 0.33, "avg_reality_gap": 0.67}
        },
        "evaluations": {
            "naive-baseline": {
                "realitybench-login": {"reality_score": 0.33, "reality_gap": 0.67}
            }
        }
    }
    render_final_screen(results, ALL_TASKS[:2], no_animation=True)


def test_ui_configuration_flags():
    """Validates that configure_ui sets global flags properly."""
    configure_ui(no_animation=True, no_color=True, quiet=True)
    from ui.console import ui_options
    assert ui_options.no_animation is True
    assert ui_options.no_color is True
    assert ui_options.quiet is True

    # Reset
    configure_ui(no_animation=False, no_color=False, quiet=False)
    assert ui_options.no_animation is False


def test_clean_terminal_encoding_output():
    """
    Renders UI elements to a mock string stream to verify that tables
    and panels produce valid text output without crashing.
    """
    buf = io.StringIO()
    test_console = Console(file=buf, width=80, theme=BENCHMARK_THEME)

    # Print banner
    print_banner()

    # Print tables to test_console
    summaries = {
        "target_1": {"avg_demo_score": 0.85, "avg_reality_score": 0.70, "avg_reality_gap": 0.15}
    }
    test_console.print(scoreboard_table(summaries))
    test_console.print(task_catalog_table(ALL_TASKS[:3]))

    output = buf.getvalue()
    assert len(output) > 0
    # Must encode cleanly to utf-8
    encoded_utf8 = output.encode("utf-8", errors="strict")
    assert len(encoded_utf8) > 0
