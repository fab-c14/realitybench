"""
RealityBench Scoring Engine
Calculates Demo Score (Happy Path), Reality Score (Perturbations), and Reality Gap.
"""

from dataclasses import dataclass, field
from typing import Any

# Provisional weighting according to RealityBench specification
WEIGHTS = {
    # Demo Score categories (Total 40%)
    "functional_correctness": 0.25,
    "expected_interactions": 0.15,
    
    # Reality Score categories (Total 60%)
    "failure_recovery": 0.20,
    "state_robustness": 0.15,
    "input_robustness": 0.10,
    "accessibility": 0.07,
    "responsive_behavior": 0.05,
    "interaction_safety": 0.03,
}

DEMO_CATEGORIES = {"functional_correctness", "expected_interactions"}
REALITY_CATEGORIES = {
    "failure_recovery",
    "state_robustness",
    "input_robustness",
    "accessibility",
    "responsive_behavior",
    "interaction_safety",
}


CATEGORY_WEIGHTS = WEIGHTS


@dataclass
class TestResult:
    __test__ = False  # Prevent pytest from collecting this data class as a test suite

    test_name: str
    category: str
    regime: str  # 'demo' or 'reality'
    passed: bool
    details: str = ""
    failure_type: str = ""


@dataclass
class EvaluationReport:
    task_name: str
    demo_score: float = 0.0
    reality_score: float = 0.0
    reality_gap: float = 0.0
    overall_score: float = 0.0
    category_scores: dict[str, float] = field(default_factory=dict)
    test_results: list[TestResult] = field(default_factory=list)
    failure_taxonomy: list[str] = field(default_factory=list)
    # The page replaced fetch/XMLHttpRequest, i.e. shipped its own fake server. Reported, not scored.
    fake_backend: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_name": self.task_name,
            "demo_score": round(self.demo_score, 4),
            "reality_score": round(self.reality_score, 4),
            "reality_gap": round(self.reality_gap, 4),
            "overall_score": round(self.overall_score, 4),
            "fake_backend": self.fake_backend,
            "category_scores": {k: round(v, 4) for k, v in self.category_scores.items()},
            "failure_taxonomy": self.failure_taxonomy,
            "tests_passed": sum(1 for t in self.test_results if t.passed),
            "tests_total": len(self.test_results),
            "test_details": [
                {
                    "name": t.test_name,
                    "category": t.category,
                    "regime": t.regime,
                    "passed": t.passed,
                    "details": t.details,
                    "failure_type": t.failure_type,
                }
                for t in self.test_results
            ]
        }


def calculate_scores(task_name: str, test_results: list[TestResult]) -> EvaluationReport:
    """
    Computes category scores, Demo Score, Reality Score, and Reality Gap
    from a list of TestResult objects.
    """
    if not test_results:
        return EvaluationReport(task_name=task_name)

    category_totals: dict[str, int] = {}
    category_passed: dict[str, int] = {}

    for t in test_results:
        category_totals[t.category] = category_totals.get(t.category, 0) + 1
        if t.passed:
            category_passed[t.category] = category_passed.get(t.category, 0) + 1

    # Calculate fraction passed per category (0.0 to 1.0)
    category_fractions: dict[str, float] = {}
    for cat in WEIGHTS:
        total = category_totals.get(cat, 0)
        if total > 0:
            category_fractions[cat] = category_passed.get(cat, 0) / total
        else:
            category_fractions[cat] = 1.0  # Unused category gets full weight or neutral

    # Demo Score: normalized to 0.0 - 1.0 scale
    demo_weight_sum = sum(WEIGHTS[c] for c in DEMO_CATEGORIES)
    demo_weighted_sum = sum(category_fractions.get(c, 0.0) * WEIGHTS[c] for c in DEMO_CATEGORIES)
    demo_score = (demo_weighted_sum / demo_weight_sum) if demo_weight_sum > 0 else 0.0

    # Reality Score: normalized to 0.0 - 1.0 scale
    reality_weight_sum = sum(WEIGHTS[c] for c in REALITY_CATEGORIES)
    reality_weighted_sum = sum(category_fractions.get(c, 0.0) * WEIGHTS[c] for c in REALITY_CATEGORIES)
    reality_score = (reality_weighted_sum / reality_weight_sum) if reality_weight_sum > 0 else 0.0

    # Overall weighted score
    overall_score = sum(category_fractions.get(c, 0.0) * WEIGHTS[c] for c in WEIGHTS)

    # Signature metric: Reality Gap
    reality_gap = demo_score - reality_score

    # Failure taxonomy
    failures = [t.failure_type for t in test_results if not t.passed and t.failure_type]

    return EvaluationReport(
        task_name=task_name,
        demo_score=demo_score,
        reality_score=reality_score,
        reality_gap=reality_gap,
        overall_score=overall_score,
        category_scores=category_fractions,
        test_results=test_results,
        failure_taxonomy=failures,
    )
