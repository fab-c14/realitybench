"""
Lock naive-vs-robust Reality Gap calibration for all 12 tasks.

Naive baselines must show a meaningful Reality Gap (demo-ready fragility).
Robust baselines must score ~perfect Demo and Reality (gap ≈ 0).
"""

import pytest

from benchmark.tasks.registry import ALL_TASKS

# admin-table naive is the weakest gap in the suite (~0.24); keep a small floor.
MIN_NAIVE_GAP = 0.20
MAX_ROBUST_GAP = 0.05
MIN_ROBUST_DEMO = 0.95
MIN_ROBUST_REALITY = 0.95


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.task_id)
def test_robust_baseline_is_production_ready(task):
    report = task.grader(task.robust_code)
    assert report.demo_score >= MIN_ROBUST_DEMO, (
        f"{task.task_id} robust demo={report.demo_score:.4f}"
    )
    assert report.reality_score >= MIN_ROBUST_REALITY, (
        f"{task.task_id} robust reality={report.reality_score:.4f}"
    )
    assert report.reality_gap <= MAX_ROBUST_GAP, (
        f"{task.task_id} robust gap={report.reality_gap:.4f}"
    )


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.task_id)
def test_naive_baseline_exhibits_reality_gap(task):
    report = task.grader(task.naive_code)
    assert report.demo_score >= 0.75, (
        f"{task.task_id} naive demo too low ({report.demo_score:.4f}); "
        "naive should still pass happy path"
    )
    assert report.reality_gap >= MIN_NAIVE_GAP, (
        f"{task.task_id} naive gap={report.reality_gap:.4f} "
        f"(demo={report.demo_score:.4f}, reality={report.reality_score:.4f})"
    )
