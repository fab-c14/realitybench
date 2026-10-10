"""
Download Kaggle Benchmark runs and summarize them into results/kaggle_results.json.

The output uses the same "target_summaries" schema as full_benchmark_results.json,
so analysis/generate_html_dashboard.py merges it automatically.

Usage:
    uv run python scripts/collect_kaggle_results.py [--no-download]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = ROOT / "results" / "kaggle"
OUTPUT = ROOT / "results" / "kaggle_results.json"


def task_slugs() -> list[str]:
    return sorted(p.stem for p in (ROOT / "kaggle_tasks").glob("*.py"))


def download(slug: str) -> None:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    subprocess.run(
        ["uv", "run", "kaggle", "b", "t", "download", slug],
        cwd=DOWNLOAD_DIR, env=env, check=False, capture_output=True,
    )


def latest_runs() -> dict[tuple[str, str], dict]:
    """
    Newest completed run per (model, task), counting only each task's latest version
    so every published score comes from the same graders.
    Download layout: results/kaggle/<slug>/<version>/<model>/<run id>/*.run.json
    """
    found = []
    for path in DOWNLOAD_DIR.rglob("*.run.json"):
        run = json.loads(path.read_text(encoding="utf-8"))
        entries = run.get("results") or []
        if isinstance(entries, dict):
            entries = [entries]
        result = next((e.get("dictResult") for e in entries if e.get("dictResult")), None)
        if result and "demo_score" in result:
            slug, version, model = path.parts[-5], int(path.parts[-4]), path.parts[-3]
            found.append((slug, version, model, run.get("endTime", ""), result))

    newest_version: dict[str, int] = {}
    for slug, version, *_ in found:
        newest_version[slug] = max(version, newest_version.get(slug, 0))

    runs: dict[tuple[str, str], dict] = {}
    for slug, version, model, end, result in found:
        if version != newest_version[slug]:
            continue
        key = (model, result.get("task_name", slug))
        if key not in runs or end > runs[key]["endTime"]:
            runs[key] = {"endTime": end, "result": result}
    return runs


def summarize(runs: dict[tuple[str, str], dict]) -> dict:
    per_model: dict[str, list[dict]] = defaultdict(list)
    for (model, _task), run in runs.items():
        per_model[model].append(run["result"])

    summaries = {}
    for model, results in sorted(per_model.items()):
        n = len(results)
        summaries[model] = {
            "avg_demo_score": round(sum(r["demo_score"] for r in results) / n, 4),
            "avg_reality_score": round(sum(r["reality_score"] for r in results) / n, 4),
            "avg_reality_gap": round(sum(r["reality_gap"] for r in results) / n, 4),
            "tasks_run": n,
            "fake_backend_pages": sum(1 for r in results if r.get("fake_backend")),
            "per_task": {
                r["task_name"]: {
                    "demo_score": r["demo_score"],
                    "reality_score": r["reality_score"],
                    "reality_gap": r["reality_gap"],
                    "fake_backend": bool(r.get("fake_backend")),
                    "failures": r.get("failure_taxonomy", []),
                }
                for r in sorted(results, key=lambda r: r["task_name"])
            },
        }
    return summaries


def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if "--no-download" not in sys.argv:
        for slug in task_slugs():
            print(f"Downloading {slug}")
            download(slug)

    summaries = summarize(latest_runs())
    payload = {
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "kaggle-benchmarks",
        "target_summaries": summaries,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for model, s in summaries.items():
        print(f"{model}: demo={s['avg_demo_score']:.3f} reality={s['avg_reality_score']:.3f} "
              f"gap={s['avg_reality_gap']:.3f} fake_backend={s['fake_backend_pages']} ({s['tasks_run']} tasks)")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
