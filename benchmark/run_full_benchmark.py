"""
RealityBench Full Suite Runner
Executes evaluation across benchmark tasks for:
- Naive Baseline
- Robust Baseline
- Active Ollama LLM Models (e.g. qwen2.5-coder:1.5b, gemma2:2b)
Saves results to results/full_benchmark_results.json.
"""

import sys
import os
import json
import time
import requests
from typing import Dict, Any, List, Optional

# Ensure realitybench package is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
bench_root = os.path.abspath(os.path.join(current_dir, ".."))
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

from benchmark.tasks.registry import ALL_TASKS, TASK_MAP, TaskDefinition
from benchmark.graders.browser_runner import extract_html_code
from benchmark.graders.scoring import EvaluationReport
from ui import (
    console,
    configure_ui,
    BenchmarkDashboard,
    render_startup_screen,
    render_final_screen,
    error_panel,
    install_rich_traceback,
)

install_rich_traceback()

OLLAMA_API_URL = "http://localhost:11434/api/generate"
RESULTS_DIR = os.path.join(bench_root, "results")
GEN_CODE_DIR = os.path.join(RESULTS_DIR, "generated_code")


def ensure_directories():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(GEN_CODE_DIR, exist_ok=True)


def get_available_ollama_models() -> List[str]:
    """Checks which models are currently available in local Ollama."""
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            data = res.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []


def generate_llm_code(model_name: str, task: TaskDefinition) -> str:
    """Prompts Ollama for the task implementation or returns cached code."""
    model_slug = model_name.replace(":", "_").replace("/", "_")
    model_dir = os.path.join(GEN_CODE_DIR, model_slug)
    os.makedirs(model_dir, exist_ok=True)
    cache_path = os.path.join(model_dir, f"{task.task_id}.html")

    # If already cached, reuse
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    system_prompt = (
        "You are an expert web software engineer. Write clean, self-contained HTML, CSS, "
        "and JavaScript implementing the requested UI component according to the prompt. "
        "Return ONLY the self-contained HTML document inside ```html ... ``` code block."
    )
    payload = {
        "model": model_name,
        "prompt": f"{system_prompt}\n\nTask:\n{task.prompt}",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
        }
    }

    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        resp.raise_for_status()
        raw_text = resp.json().get("response", "")
        code = extract_html_code(raw_text)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(code)
        return code
    except Exception as e:
        console.print(error_panel("Ollama Generation Failed", f"Model: {model_name}\nError: {e}"))
        return ""


def evaluate_task_for_target(task: TaskDefinition, target_name: str) -> EvaluationReport:
    """Evaluates a single task for a target (baseline or LLM)."""
    if target_name == "naive-baseline":
        code = task.naive_code
    elif target_name == "robust-baseline":
        code = task.robust_code
    else:
        code = generate_llm_code(target_name, task)

    if not code:
        # Return empty failure report
        return EvaluationReport(task_name=task.task_id)

    try:
        return task.grader(code)
    except Exception as e:
        console.print(error_panel(f"Grader Failed on {task.name}", str(e)))
        return EvaluationReport(task_name=task.task_id)


def run_tasks_suite(
    tasks: List[TaskDefinition],
    models_to_evaluate: Optional[List[str]] = None,
    suite_title: str = "FULL 12-TASK BENCHMARK SUITE",
    results_filename: str = "full_benchmark_results.json",
    no_animation: bool = False,
    no_color: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """Runs the benchmark across the specified subset of tasks and models."""
    ensure_directories()
    configure_ui(no_animation=no_animation, no_color=no_color, quiet=quiet)

    available_models = get_available_ollama_models()
    default_targets = ["naive-baseline", "robust-baseline"]
    for candidate in ["qwen2.5-coder:1.5b", "gemma2:2b"]:
        if any(candidate in m for m in available_models):
            default_targets.append(candidate)

    targets = models_to_evaluate or default_targets

    # Render polished startup screen
    render_startup_screen(targets=targets, task_count=len(tasks), no_animation=no_animation)

    full_results: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_count": len(tasks),
        "targets": targets,
        "evaluations": {},
        "target_summaries": {}
    }

    # Execute inside the live interactive dashboard
    with BenchmarkDashboard(
        targets=targets,
        total_tasks=len(tasks),
        no_animation=no_animation,
        quiet=quiet
    ) as dashboard:

        for target in targets:
            full_results["evaluations"][target] = {}
            total_demo = 0.0
            total_reality = 0.0
            total_gap = 0.0

            for task in tasks:
                dashboard.set_task_start(
                    target=target,
                    task_idx=task.task_number,
                    task_name=task.name,
                    category_focus=task.category_focus
                )

                report = evaluate_task_for_target(task, target)
                full_results["evaluations"][target][task.task_id] = report.to_dict()

                total_demo += report.demo_score
                total_reality += report.reality_score
                total_gap += report.reality_gap

                dashboard.set_task_complete(target, task.task_id, report)

            n = len(tasks)
            avg_demo = total_demo / n
            avg_reality = total_reality / n
            avg_gap = total_gap / n

            summary = {
                "avg_demo_score": round(avg_demo, 4),
                "avg_reality_score": round(avg_reality, 4),
                "avg_reality_gap": round(avg_gap, 4),
            }
            full_results["target_summaries"][target] = summary
            dashboard.set_target_summary(target, summary)

    # Save complete dataset
    out_path = os.path.join(RESULTS_DIR, results_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)

    # Render final celebratory presentation screen
    render_final_screen(full_results, tasks, no_animation=no_animation)

    return full_results


def run_full_suite(
    models_to_evaluate: Optional[List[str]] = None,
    no_animation: bool = False,
    no_color: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """Runs all 12 tasks across targets."""
    return run_tasks_suite(
        tasks=ALL_TASKS,
        models_to_evaluate=models_to_evaluate,
        suite_title="REALITYBENCH: FULL 12-TASK BENCHMARK SUITE",
        results_filename="full_benchmark_results.json",
        no_animation=no_animation,
        no_color=no_color,
        quiet=quiet
    )


def run_pilot_suite(
    models_to_evaluate: Optional[List[str]] = None,
    no_animation: bool = False,
    no_color: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """Runs the 3 pilot tasks (Login, Search, Checkout) across targets."""
    pilot_task_ids = ["realitybench-login", "realitybench-search", "realitybench-checkout"]
    pilot_tasks = [TASK_MAP[tid] for tid in pilot_task_ids if tid in TASK_MAP]
    return run_tasks_suite(
        tasks=pilot_tasks,
        models_to_evaluate=models_to_evaluate,
        suite_title="REALITYBENCH: 3-TASK PILOT STUDY",
        results_filename="pilot_benchmark_results.json",
        no_animation=no_animation,
        no_color=no_color,
        quiet=quiet
    )


if __name__ == "__main__":
    run_full_suite()
