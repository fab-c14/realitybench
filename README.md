# RealityBench 🛡️
### Benchmarking AI-Generated Software Beyond the Happy Path

[![CI & Deployment](https://github.com/fab-c14/realitybench/actions/workflows/ci.yml/badge.svg)](https://github.com/fab-c14/realitybench/actions/workflows/ci.yml)
[![Live Dashboard](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-2563eb.svg)](https://fab-c14.github.io/realitybench/)
[![Pylint](https://img.shields.io/badge/pylint-10.00%2F10-brightgreen.svg)](https://github.com/fab-c14/realitybench)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tested with Playwright](https://img.shields.io/badge/DOM%20Harness-Playwright%20Chromium-green.svg)](https://playwright.dev/)
[![Rich Terminal UI](https://img.shields.io/badge/CLI%20Presentation-Rich-purple.svg)](https://github.com/Textualize/rich)
[![Kaggle Benchmarks](https://img.shields.io/badge/Kaggle-Benchmarks%20SDK-20BEFF.svg)](https://github.com/Kaggle/kaggle-benchmarks)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Core Research Question:** When AI coding models generate software that works in a normal demonstration, how well does that software survive realistic failures, unexpected inputs, and non-ideal user behavior?

---

## 🔬 Core Hypothesis: The Reality Gap

Modern AI coding models have become remarkably proficient at producing code for textbook "happy paths"—scenarios where user inputs are ideal, networks never fail, and edge conditions do not occur. However, production software engineering is defined by how applications degrade under real-world stress.

RealityBench objectively measures this disparity through two distinct evaluation regimes:

1. **Regime A: Demo Score (40% Weight)**  
   Evaluates whether the software functions correctly under ideal, expected conditions:
   - **Functional Correctness (25%)**: Crucial DOM elements render, controls exist, default state initializes.
   - **Expected Interactions (15%)**: Standard user flows succeed (submitting valid data, receiving responses).

2. **Regime B: Reality Score (60% Weight)**  
   Evaluates resilience under controlled perturbations:
   - **Failure Recovery (20%)**: Handling HTTP 500 errors, connection timeouts, and preserving unsaved user state.
   - **State Robustness (15%)**: Preserving state across back navigation, cancellations, and parent selector resets.
   - **Input Robustness (10%)**: Rejecting invalid inputs, whitespace payloads, and negative numbers.
   - **Accessibility (7%)**: Semantic `<label>` associations, ARIA descriptors, and keyboard navigation.
   - **Responsive Behavior (5%)**: Preventing horizontal scroll overflow on mobile viewports (375x667).
   - **Interaction Safety (3%)**: Debouncing rapid double-clicks to block duplicate network mutations.

$$\mathbf{Reality\ Gap} = \mathbf{Demo\ Score} - \mathbf{Reality\ Score}$$

A wide **Reality Gap** identifies the **"Demo-Ready Fragility Trap"**: software that succeeds in simple demos but breaks immediately when exposed to real users and volatile networks.

---

## 🏗️ Architecture & Design Principles

- **100% Deterministic Assertions**: Every evaluation runs in a headless Chromium browser using Playwright. Zero non-deterministic LLM-as-judge scoring.
- **Fair Specification Contracts**: Prompts establish reasonable product expectations without arbitrary hidden trick requirements.
- **Unified Rich Presentation Layer (`realitybench/ui/`)**: Centralized terminal formatting with semantic color hierarchy, CP1252-safe ASCII badges, progress bars, and Syntax highlighting.
- **Modular Task Structure**: All 12 tasks follow a uniform pattern: docstring contract, constants, decomposed sub-test runners (`run_happy_path`, `run_reality_tests`), core grader, Kaggle SDK `@kbench.task` wrapper, and Rich self-test block.
- **Kaggle Benchmarks Native**: Full compatibility with the official `kaggle-benchmarks` SDK.

---

## 🎯 The 12-Task Suite

| # | Task ID | Name | Software Engineering Focus |
| :-: | :--- | :--- | :--- |
| **01** | `realitybench-login` | Authentication & Login | Input validation, lockout countdown, 401 error recovery |
| **02** | `realitybench-search` | Search & Autocomplete | Keystroke debouncing, empty results, 500 retry, keyboard navigation |
| **03** | `realitybench-checkout` | Order Checkout | Cart preservation on 500, double-submit debounce, coupon bounds |
| **04** | `realitybench-file-upload` | File Upload | File type rejection (.exe), 5MB size limits, failure retry |
| **05** | `realitybench-crud-dashboard` | Task CRUD Dashboard | Mutation rollback on 500, whitespace rejection, deletion confirmation |
| **06** | `realitybench-booking` | Appointment Booking | Past-date rejection, slot conflict 409 recovery, form preservation |
| **07** | `realitybench-chat` | Live Chat Component | Empty message rejection, in-thread 500 feedback, Enter key submit |
| **08** | `realitybench-product-page` | Product Detail Page | Out-of-stock disabling, broken image fallback, negative qty bounds |
| **09** | `realitybench-admin-table` | Admin Data Table | Null field resilience, pagination bounds, table headers markup |
| **10** | `realitybench-settings` | User Settings Panel | Dirty state tracking, discard restoration, HTTP 500 edit preservation |
| **11** | `realitybench-api-form` | Dependent API Form | Cascading dropdowns, parent switch state reset, 500 recovery |
| **12** | `realitybench-workflow` | Multi-Step Workflow Wizard | Step progression validation, Back navigation data retention, Step 3 500 retry |

---

## 📊 Empirical Multi-Model Scoreboard

Results from evaluating full baselines and local models:

```
+--------------------------------------------------------------------------------------------------+
| Evaluation Target       | Demo Score   | Reality Score | Reality Gap   | Robustness Rating       |
|-------------------------+--------------+---------------+---------------+-------------------------|
| naive-baseline          | 98.96%       | 33.33%        | +65.62%       | [*] High Fragility Trap |
| robust-baseline         | 100.00%      | 100.00%       | +0.00%        | [*****] Production Ready|
| qwen2.5-coder:1.5b      | 81.77%       | 75.42%        | +6.35%        | [****] Resilient        |
| gemma2:2b               | 80.21%       | 72.22%        | +7.99%        | [****] Resilient        |
+--------------------------------------------------------------------------------------------------+
```

---

## ⚡ Quickstart with `uv`

RealityBench uses [`uv`](https://github.com/astral-sh/uv) for fast, reproducible dependency management and execution.

```bash
# 1. Clone the repository
git clone https://github.com/fab-c14/realitybench.git
cd realitybench

# 2. Install all dependencies (including dev tools)
uv sync --all-extras

# 3. Install Playwright browser engine
uv run playwright install chromium

# 4. View available commands
uv run realitybench --help

# 5. Run the fast 3-task pilot benchmark
uv run realitybench pilot

# 6. Launch the interactive graphical browser dashboard
uv run realitybench view
```

---

## 💻 CLI Commands & Usage

RealityBench includes a colorful, developer-first CLI powered by `rich` and `typer`. You can run commands directly using `uv run realitybench <command>` or `python cli.py <command>`.

### 1. Catalog & Task Inspection

```bash
# List all 12 registered benchmark tasks
uv run realitybench tasks
# or: python cli.py tasks

# Inspect a task prompt specification with Syntax highlighting
python cli.py inspect realitybench-login

# Inspect naive or robust reference baseline implementations
python cli.py inspect realitybench-login --code naive
python cli.py inspect realitybench-login --code robust
```

### 2. Fast Pilot Execution (Tasks 1, 2, 3)

Run the fast 3-task pilot (Login, Search, Checkout) to test calibration in under 60 seconds:

```bash
python cli.py pilot
```

### 3. Full Benchmark Suite Execution

```bash
# Run full suite with animated Rich Live + Layout dashboard
python cli.py run

# Run only a specific model or baseline
python cli.py run --target naive-baseline
python cli.py run --target qwen2.5-coder:1.5b

# CI / Kaggle headless execution modes
python cli.py run --no-animation     # Disables spinners and live refreshes for clean log recording
python cli.py run --no-color         # Uses clean monochrome text without ANSI escapes
python cli.py run --quiet            # Suppresses non-essential banners
```

### 4. Visual Matrix & Terminal Charts

```bash
# Display Task x Model Performance Matrix with Reality Gap badges
python cli.py matrix

# Display terminal horizontal bar charts, Gap gauges, and score comparisons
python cli.py charts
python cli.py charts --target naive-baseline
```

### 5. Interactive Grader Self-Tests

```bash
# Test a single task locally against naive and robust baselines
python cli.py test realitybench-login
```

### 6. Empirical Scoreboards & Breakdowns

```bash
# Render multi-model leaderboard table
python cli.py report

# Render task-by-task breakdown for a target
python cli.py breakdown naive-baseline
python cli.py breakdown qwen2.5-coder:1.5b
```

### 7. Interactive Graphical Browser Dashboard

```bash
# Generate and launch the interactive graphical HTML dashboard in your default browser
uv run realitybench view

# Generate dashboard without opening browser automatically
uv run realitybench view --no-browser
```

Renders `results/dashboard.html` with interactive KPI cards, Chart.js multi-model comparisons, Reality Gap charts, and a filterable Task x Model matrix.

> 🌐 **Live Web Deployment**: The interactive dashboard is continuously deployed to GitHub Pages at **[https://fab-c14.github.io/realitybench/](https://fab-c14.github.io/realitybench/)**.

---

## 🚀 Deployment & CI/CD Architecture

RealityBench is designed for automated validation and zero-friction deployment:

1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - **Static Analysis**: Runs `ruff` and `pylint` (enforcing 10.00 / 10 quality score).
   - **Playwright Test Matrix**: Executes all 17 deterministic tests and pilot browser evaluation in headless mode.
2. **Interactive Web Dashboard on GitHub Pages**:
   - On every push to `main`, GitHub Actions automatically compiles the standalone analytics dashboard and deploys to GitHub Pages via `actions/deploy-pages@v4`.
   - Raw benchmark datasets are also published under `/data/full_benchmark_results.json` for researcher access.
3. **Distribution & Packaging (`.github/workflows/release.yml`)**:
   - Automated `uv build` wheels (`.whl`) and source distributions (`.tar.gz`) generated on release tags.

---

## 🧪 Automated Testing & CI

RealityBench maintains an automated test suite verifying scoring mathematics, task registry invariants, and Rich UI rendering safety, alongside static analysis and linting:

```bash
# Run unit test suite (17 passed)
uv run pytest -v

# Run Pylint across all benchmark, UI, and test modules (10.00 / 10)
uv run pylint benchmark/ ui/ cli.py analysis/ tests/

# Run Ruff fast linter
uv run ruff check ui/ cli.py analysis/ tests/
```

All 17 tests run deterministically without external network requests:
- `tests/test_registry.py`: Asserts all 12 tasks load with complete metadata and valid HTML baselines.
- `tests/test_scoring.py`: Asserts category weight normalization, edge cases, and JSON schema compatibility.
- `tests/test_ui.py`: Asserts table, panel, chart, matrix, dashboard layout, screens, and flag toggles across CP1252 and UTF-8 console streams.

Continuous Integration is automatically run via GitHub Actions on every push and pull request against `main` (`.github/workflows/ci.yml`).

---

## 📁 Repository Structure

```
realitybench/
├── cli.py                        # Rich CLI entry point (tasks, pilot, run, matrix, charts, inspect, report)
├── benchmark/
│   ├── run_full_benchmark.py     # Suite runner with animated Rich Live + Layout dashboard
│   ├── graders/
│   │   ├── browser_runner.py     # Playwright Chromium headless harness & route mock engine
│   │   └── scoring.py            # Deterministic scoring engine & Reality Gap calculator
│   └── tasks/
│       ├── registry.py           # Central catalog of all 12 tasks
│       ├── task_01_login.py      # Authentication & Login
│       ├── task_02_search.py     # Search & Autocomplete
│       ├── task_03_checkout.py   # Order Checkout
│       ├── task_04_file_upload.py
│       ├── task_05_crud_dashboard.py
│       ├── task_06_booking.py
│       ├── task_07_chat.py
│       ├── task_08_product_page.py
│       ├── task_09_admin_table.py
│       ├── task_10_settings.py
│       ├── task_11_api_form.py
│       └── task_12_workflow.py   # Multi-Step Workflow Wizard
├── ui/                           # Centralized Rich presentation layer
│   ├── __init__.py               # Exports all components
│   ├── console.py                # Shared console singleton, theme, and configure_ui()
│   ├── charts.py                 # Terminal bar charts, gap gauges, sparklines, categories
│   ├── dashboard.py              # Continuously updating Rich Live + Layout dashboard
│   ├── panels.py                 # Task header, score summaries, and error panels
│   ├── progress.py               # Live animated progress bars & spinners
│   ├── screens.py                # Startup pre-flight checks and celebratory final results
│   ├── styles.py                 # Semantic color palette & CP1252-safe ASCII badges
│   └── tables.py                 # Scoreboards, task breakdowns, matrix, assertion results
├── results/                      # Evaluation JSON datasets
│   └── full_benchmark_results.json
├── tests/                        # Automated unit tests (17 passing)
│   ├── test_registry.py
│   ├── test_scoring.py
│   └── test_ui.py
└── README.md
```

---

## 🛠️ Official Kaggle Benchmarks SDK Usage

Every task in RealityBench is decorated with `@kbench.task`:

```python
import kaggle_benchmarks as kbench
from benchmark.tasks.registry import ALL_TASKS

# Run tasks directly with the Kaggle Benchmarks SDK
for task in ALL_TASKS:
    task.kbench_task.run(kbench.llm)
```

---

## 📄 License

MIT License. Built for the **Kaggle Benchmarking Challenge**.
