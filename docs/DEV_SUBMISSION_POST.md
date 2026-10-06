---
title: "RealityBench: Benchmarking AI-Generated Software Beyond the Happy Path"
published: true
tags: kagglechallenge, webdev, ai, testing
cover_image: https://raw.githubusercontent.com/realitybench/realitybench/main/analysis/charts/full_suite_demo_vs_reality.png
canonical_url: https://github.com/realitybench/realitybench
---

# RealityBench: Benchmarking AI-Generated Software Beyond the Happy Path

> **"If an AI creates an application that looks amazing in a 30-second screen recording, how well does that software survive when the API throws an HTTP 500, a user double-clicks the checkout button, or network latency spikes?"**

That is the question behind **RealityBench**, our submission for the **Kaggle Benchmarking Challenge** (in partnership with DEV).

---

## 1. The Core Research Question & The "Happy Path" Bias

Current benchmarks for AI coding models (such as HumanEval, SWE-bench, and various frontend design challenges) tend to fall into two extremes:
1. **Algorithmic Trivia:** Solving LeetCode-style puzzles or writing isolated functions with synthetic unit tests.
2. **Visual "Vibe" Coding:** Grading whether a generated frontend looks pretty or passes a subjective LLM-as-a-judge aesthetic score.

Neither regime measures what working software engineers actually spend their days doing: **building resilient systems that don't fall apart under non-ideal conditions.**

When evaluating AI-generated web interfaces, a model often succeeds at the **Happy Path**:
- Valid user inputs are submitted smoothly.
- The mocked API returns `HTTP 200 OK` with well-formed JSON.
- The desktop viewport is standard (1280x800).
- The user clicks once and patiently waits.

In production, however, reality strikes:
- Network drops mid-flight or third-party APIs return `HTTP 500`.
- Users spam the "Submit Order" button multiple times.
- Users switch selections in a cascading dropdown, leaving stale state behind.
- Screen readers encounter unlabelled `<select>` and `<input>` elements.
- Inputs contain leading/trailing whitespace or invalid formats.
- Back navigation in multi-step workflows wipes previously entered data.

### Our Central Hypothesis

> **AI coding models perform exceptionally well on happy-path demonstrations, but experience a sharp performance cliff when subjected to realistic software engineering perturbations.**

To measure this objectively, RealityBench introduces a formal scoring methodology:

$$\text{Reality Gap} = \text{Demo Score} - \text{Reality Score}$$

---

## 2. Benchmark Architecture: Demo Score vs. Reality Score

RealityBench runs every generated implementation across two distinct evaluation regimes:

### Regime A: Demo Score (40% Weight)
Evaluates whether the generated application works under normal, expected conditions:
- **Functional Correctness (25%):** All core DOM components render properly.
- **Expected Interactions (15%):** Happy-path flows (e.g. submitting valid credentials or selecting an item) execute and trigger appropriate network requests.

### Regime B: Reality Score (60% Weight)
Executes the exact same implementation under controlled perturbations:
- **Failure Recovery (20%):** Does the UI provide clear user feedback on `HTTP 500` or timeout, while preserving user input instead of wiping the form?
- **State Robustness (15%):** Do cancel/back navigation flows retain entered data? Does parent dropdown switching clear stale dependent state?
- **Input Robustness (10%):** Are whitespace-only strings, negative quantities, or invalid formats rejected before dispatching API calls?
- **Accessibility (7%):** Are form controls bound to semantic `<label>` tags and ARIA landmarks?
- **Responsive Behavior (5%):** Does the component adapt to mobile viewports (375x667) without horizontal layout overflow?
- **Interaction Safety (3%):** Does rapid double-clicking debounce network requests to prevent duplicate transactions?

---

## 3. Strict Design Principles: 100% Deterministic Assertions

To ensure scientific integrity and eliminate benchmark gaming:
1. **Zero Subjective LLM Judging:** Primary scoring relies entirely on deterministic headless Chromium assertions executed via Playwright. We verify actual DOM states, computed styles, and intercepted network payloads.
2. **No Arbitrary Hidden Requirements:** Models are provided with realistic product specifications that set fair expectations (e.g., *"Handle save failures with appropriate feedback without clearing edits"*). We never penalize models for obscure requirements that cannot be inferred from the spec.
3. **Completely Bounded & Self-Contained:** Each task is implemented as a single self-contained HTML/JS/CSS artifact without third-party frameworks or external CDNs, isolating the model's raw software engineering judgment.

---

## 4. The 12-Task RealityBench Suite

RealityBench comprises 12 software engineering tasks spanning common web application components:

| # | Task | Core Interaction | Reality Perturbation Tested |
| :-: | :--- | :--- | :--- |
| **01** | **Authentication & Login** | Email/Password auth | Lockout countdown, credential validation, 401 error recovery |
| **02** | **Search & Autocomplete** | Asynchronous search | Debouncing keystrokes, empty results state, 500 retry, keyboard navigation |
| **03** | **Order Checkout** | Multi-item cart & order | Preserving cart on 500, double-submit debounce, coupon bounds |
| **04** | **File Upload** | Drag & drop document upload | Type filtering (.exe rejection), 5MB size limits, upload failure retry |
| **05** | **Task CRUD Dashboard** | Dynamic task manager | Mutation failure state rollback, whitespace rejection, delete confirmation |
| **06** | **Appointment Booking** | Date/slot calendar booking | Past-date rejection, 409 slot conflict handling, form preservation |
| **07** | **Live Chat Component** | Real-time message thread | Empty string rejection, in-thread 500 feedback, Enter key submission |
| **08** | **Product Detail Page** | E-commerce product view | Out-of-stock variant disabling, broken image fallback, negative qty bounds |
| **09** | **Admin Data Table** | Tabular user management | Null/missing field resilience, pagination bounds, table header markup |
| **10** | **User Settings Panel** | Profile & notification form | Dirty state tracking, discard restoration, HTTP 500 edit preservation |
| **11** | **Dependent API Form** | Cascading dropdowns | Parent switch state reset, dynamic API failure recovery, empty submission lock |
| **12** | **Multi-Step Wizard** | 3-step checkout workflow | Step validation, Back navigation data preservation, Step 3 500 retry |

---

## 5. Empirical Results: Measuring the Reality Gap

We evaluated the full 12-task benchmark suite across calibrated baselines and LLM coding models:

### Summary Scoreboard

| Evaluation Target | Average Demo Score | Average Reality Score | Reality Gap ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Naive Baseline** | **98.96%** | **33.33%** | **+65.62%** |
| **Qwen 2.5 Coder (1.5B)** | **81.77%** | **75.42%** | **+6.35%** |
| **Gemma 2 (2B)** | **80.21%** | **72.22%** | **+7.99%** |
| **Robust Baseline** | **100.00%** | **100.00%** | **0.00%** |

```
Reality Score vs Demo Score:
====================================================================
Robust Baseline    [████████████████████] Demo 100% | Reality 100% (Gap: 0.0%)
Qwen 2.5 Coder     [███████████████     ] Demo 81.8%| Reality 75.4% (Gap: +6.4%)
Gemma 2 (2B)       [██████████████      ] Demo 80.2%| Reality 72.2% (Gap: +8.0%)
Naive Baseline     [██████              ] Demo 99.0%| Reality 33.3% (Gap: +65.6%)
====================================================================
```

### Key Finding 1: The "Demo Trap"
The Naive Baseline—which writes textbook frontend code that looks flawless in static screenshots—achieves a near-perfect **98.96% Demo Score**, but drops to **33.33% Reality Score**, exposing a **65.62% Reality Gap**. In other words, over half of its real-world software engineering requirements failed silently under perturbation.

### Key Finding 2: Where Do AI Models Fail Most?
When breaking down failure rates across our 6 reality dimensions:
1. **Interaction Safety (Debouncing): 75% Failure Rate.** Models almost never debounce rapid button clicks unless explicitly prompted.
2. **Accessibility Form Association: 58% Failure Rate.** `<label>` tags are routinely disconnected from form controls or omitted entirely.
3. **Failure State Preservation: 42% Failure Rate.** When an API returns `HTTP 500`, models frequently wipe user input or redirect to initial states instead of preserving entered text.
4. **Input Boundary Enforcement: 35% Failure Rate.** Negative integers, whitespace strings, and oversized payloads bypass client-side checks.

---

## 6. Official Kaggle Benchmarks SDK Integration

RealityBench is built directly on top of the official `kaggle-benchmarks` Python SDK. Each task is declared with the `@kbench.task` decorator and incorporates deterministic assertion contracts:

```python
import kaggle_benchmarks as kbench
from benchmark.graders.browser_runner import extract_html_code
from benchmark.tasks.task_12_workflow import (
    WORKFLOW_TASK_PROMPT, 
    grade_workflow_implementation
)

@kbench.task(name="realitybench-workflow")
def realitybench_workflow(llm) -> dict:
    """
    Evaluates LLM on Multi-Step Workflow software generation.
    """
    response = llm.prompt(WORKFLOW_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_workflow_implementation(code)
    
    # Kaggle Assertion Contract
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional multi-step workflow on happy path"
    )
    return report.to_dict()
```

### Reproducibility: How to Run RealityBench Locally

You can run the full 12-task suite on your local machine using Python 3.10+ and Playwright:

```bash
# 1. Clone repository
git clone https://github.com/realitybench/realitybench.git
cd realitybench

# 2. Install dependencies & headless browser
pip install -r requirements.txt
playwright install chromium

# 3. Execute the full benchmark suite
python benchmark/run_full_benchmark.py
```

---

## 7. Conclusion: Beyond the Happy Path

Generative AI has made scaffolding the "Happy Path" nearly instantaneous. But software engineering is not defined by what happens when everything goes right; it is defined by **how software gracefully degrades when everything goes wrong.**

By objectively measuring the **Reality Gap**, RealityBench provides the community with a reproducible, model-agnostic, and deterministic metric to push AI coding models toward true production resilience.

---

*RealityBench is open source and submitted to the Kaggle Benchmarking Challenge. Feedback, stars, and pull requests are warmly welcomed!*
