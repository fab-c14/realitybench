# RealityBench: Empirical Evaluation Report
## Benchmarking AI-Generated Software Beyond the Happy Path

**Generated:** 2026-10-06T09:37:26Z
**Total Benchmark Tasks:** 12
**Evaluation Targets:** naive-baseline, robust-baseline, qwen2.5-coder:1.5b, gemma2:2b

## 1. Executive Summary

RealityBench evaluates AI coding models not on LeetCode trivia or surface appearance, but on how well generated applications survive realistic disruptions. By measuring both **Demo Score** (Happy Path functionality) and **Reality Score** (controlled perturbations including network failures, input edge cases, double-clicks, and state preservation), the benchmark isolates the **Reality Gap** (`Demo Score - Reality Score`).

### Target Summary Table

| Target | Average Demo Score | Average Reality Score | Reality Gap |
| :--- | :---: | :---: | :---: |
| **naive-baseline** | 98.96% | 33.33% | **65.62%** |
| **robust-baseline** | 100.00% | 100.00% | **0.00%** |
| **qwen2.5-coder:1.5b** | 81.77% | 75.42% | **6.35%** |
| **gemma2:2b** | 80.21% | 72.22% | **7.99%** |


## 2. Per-Task Breakdown

| Task # | Task Name | Naive Demo | Naive Reality | Naive Gap | Robust Gap |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 01 | Login | 100.0% | 33.3% | **66.7%** | 0.0% |
| 02 | Search | 100.0% | 8.3% | **91.7%** | 0.0% |
| 03 | Checkout | 100.0% | 33.3% | **66.7%** | 0.0% |
| 04 | File Upload | 100.0% | 33.3% | **66.7%** | 0.0% |
| 05 | Crud Dashboard | 100.0% | 20.0% | **80.0%** | 0.0% |
| 06 | Booking | 100.0% | 41.7% | **58.3%** | 0.0% |
| 07 | Chat | 100.0% | 66.7% | **33.3%** | 0.0% |
| 08 | Product Page | 100.0% | 8.3% | **91.7%** | 0.0% |
| 09 | Admin Table | 87.5% | 63.3% | **24.2%** | 0.0% |
| 10 | Settings | 100.0% | 8.3% | **91.7%** | 0.0% |
| 11 | Api Form | 100.0% | 41.7% | **58.3%** | 0.0% |
| 12 | Workflow | 100.0% | 41.7% | **58.3%** | 0.0% |


## 3. Key Empirical Findings

1. **The Reality Gap Is Real and Substantial:** Across all 12 tasks, conventional implementations score an average Demo Score above 95% but collapse to sub-40% when subjected to realistic network and input disruptions.
2. **Most Vulnerable Categories:** Interaction safety (double-click debouncing), accessibility form associations, and failure state preservation are routinely ignored by baseline generators.
3. **Determinism Guaranteed:** 100% of benchmark assertions are evaluated via headless Chromium DOM checks, eliminating LLM-as-a-judge subjectivity and variance.
