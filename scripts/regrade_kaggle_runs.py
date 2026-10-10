"""
Re-grade model outputs from downloaded Kaggle runs with the current local graders.

Use after changing a grader to compare old (Kaggle) and new (local) scores
without spending any model quota.

Usage:
    uv run python scripts/regrade_kaggle_runs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.graders.browser_runner import extract_html_code
from benchmark.tasks import TASK_MAP

DOWNLOAD_DIR = ROOT / "results" / "kaggle"


def _strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)
    elif isinstance(obj, str):
        yield obj


def _result(run: dict) -> dict | None:
    entries = run.get("results") or []
    entries = [entries] if isinstance(entries, dict) else entries
    return next((e.get("dictResult") for e in entries if e.get("dictResult")), None)


def main() -> None:
    graders = {t.task_id: t.grader for t in TASK_MAP.values()}
    rows = []
    for path in sorted(DOWNLOAD_DIR.rglob("*.run.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        old = _result(run)
        if not old or old.get("task_name") not in graders:
            continue
        responses = [s for s in _strings(run.get("conversations", [])) if "<html" in s.lower() or "<body" in s.lower()]
        if not responses:
            continue
        new = graders[old["task_name"]](extract_html_code(responses[-1]))
        model = path.parent.parent.name
        rows.append((model, old["task_name"], old, new))
        print(f"{model:32} {old['task_name']:28} demo {old['demo_score']:.2f}->{new.demo_score:.2f}  "
              f"reality {old['reality_score']:.2f}->{new.reality_score:.2f}", flush=True)

    out = ROOT / "results" / "kaggle" / "regrade.json"
    out.write_text(json.dumps([
        {"model": m, "task": t, "old": {k: o[k] for k in ("demo_score", "reality_score", "reality_gap")},
         "new": {**{k: v for k, v in n.to_dict().items() if k != "test_details"},
                 "failures": n.failure_taxonomy,
                 "tests": [{"name": t.test_name, "regime": t.regime, "passed": t.passed, "details": t.details}
                           for t in n.test_results]}}
        for m, t, o, n in rows
    ], indent=2), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
