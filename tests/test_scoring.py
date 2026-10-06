"""
Tests for RealityBench Scoring Engine
Validates deterministic scoring math, category weighting, and Reality Gap calculation.
"""

import pytest

from benchmark.graders.scoring import (
    TestResult,
    calculate_scores,
)


def test_perfect_run_scoring():
    """Validates that passing all tests yields 100% demo, 100% reality, and 0% gap."""
    results = [
        # Demo Regime
        TestResult(test_name="demo_render", category="functional_correctness", regime="demo", passed=True),
        TestResult(test_name="demo_flow", category="expected_interactions", regime="demo", passed=True),
        # Reality Regime across all standard categories
        TestResult(test_name="real_input", category="input_robustness", regime="reality", passed=True),
        TestResult(test_name="real_recovery", category="failure_recovery", regime="reality", passed=True),
        TestResult(test_name="real_state", category="state_robustness", regime="reality", passed=True),
        TestResult(test_name="real_safety", category="interaction_safety", regime="reality", passed=True),
        TestResult(test_name="real_a11y", category="accessibility", regime="reality", passed=True),
        TestResult(test_name="real_responsive", category="responsive_behavior", regime="reality", passed=True),
    ]

    report = calculate_scores("test-task", results)
    assert report.task_name == "test-task"
    assert report.demo_score == pytest.approx(1.0)
    assert report.reality_score == pytest.approx(1.0)
    assert report.reality_gap == pytest.approx(0.0)


def test_fragile_naive_model_scoring():
    """Validates high Reality Gap when demo passes 100% but all reality perturbations fail."""
    results = [
        # Demo Regime passes completely
        TestResult(test_name="demo_render", category="functional_correctness", regime="demo", passed=True),
        TestResult(test_name="demo_flow", category="expected_interactions", regime="demo", passed=True),
        # Reality Regime fails completely
        TestResult(test_name="real_input", category="input_robustness", regime="reality", passed=False),
        TestResult(test_name="real_recovery", category="failure_recovery", regime="reality", passed=False),
        TestResult(test_name="real_state", category="state_robustness", regime="reality", passed=False),
        TestResult(test_name="real_safety", category="interaction_safety", regime="reality", passed=False),
        TestResult(test_name="real_a11y", category="accessibility", regime="reality", passed=False),
        TestResult(test_name="real_responsive", category="responsive_behavior", regime="reality", passed=False),
    ]

    report = calculate_scores("test-task", results)
    assert report.demo_score == pytest.approx(1.0)
    assert report.reality_score == pytest.approx(0.0)
    assert report.reality_gap == pytest.approx(1.0)


def test_partial_failure_weighted_scoring():
    """Validates accurate category weight normalization with partial passes across all categories."""
    results = [
        # Demo: 1 pass, 1 fail -> (0.25*1.0 + 0.15*0.0) / 0.40 = 0.25 / 0.40 = 0.625
        TestResult(test_name="demo_render", category="functional_correctness", regime="demo", passed=True),
        TestResult(test_name="demo_flow", category="expected_interactions", regime="demo", passed=False),
        # Reality: input_robustness passes, failure_recovery fails, others pass
        TestResult(test_name="real_input", category="input_robustness", regime="reality", passed=True),
        TestResult(test_name="real_recovery", category="failure_recovery", regime="reality", passed=False),
        TestResult(test_name="real_state", category="state_robustness", regime="reality", passed=True),
        TestResult(test_name="real_safety", category="interaction_safety", regime="reality", passed=True),
        TestResult(test_name="real_a11y", category="accessibility", regime="reality", passed=True),
        TestResult(test_name="real_responsive", category="responsive_behavior", regime="reality", passed=True),
    ]

    report = calculate_scores("test-task", results)
    assert report.demo_score == pytest.approx(0.25 / 0.40)
    # failure_recovery (0.20 weight) failed out of 0.60 reality weight -> reality_score = (0.60 - 0.20) / 0.60 = 2/3
    assert report.reality_score == pytest.approx(0.40 / 0.60)
    assert report.reality_gap == pytest.approx((0.25 / 0.40) - (0.40 / 0.60))


def test_empty_results_resilience():
    """Validates that an empty test result list defaults safely to 0 scores."""
    report = calculate_scores("empty-task", [])
    assert report.task_name == "empty-task"
    assert report.demo_score == 0.0
    assert report.reality_score == 0.0
    assert report.reality_gap == 0.0


def test_evaluation_report_serialization():
    """Validates that EvaluationReport converts cleanly to dict matching JSON schema."""
    results = [
        TestResult(test_name="t1", category="cat1", regime="demo", passed=True, details="ok"),
        TestResult(test_name="t2", category="cat2", regime="reality", passed=False, failure_type="Error"),
    ]
    report = calculate_scores("serialize-task", results)
    data = report.to_dict()

    assert data["task_name"] == "serialize-task"
    assert "demo_score" in data
    assert "reality_score" in data
    assert "reality_gap" in data
    assert "category_scores" in data
    assert "tests_passed" in data
    assert "tests_total" in data
    assert len(data["test_details"]) == 2
    assert data["test_details"][0]["name"] == "t1"
    assert data["test_details"][0]["passed"] is True
