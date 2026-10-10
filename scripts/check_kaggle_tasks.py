"""
Smoke-check generated Kaggle task bundles without calling a model.

Each bundle is executed as a notebook would run it (no `__file__`, no local
packages on the path), minus its final `.run(kbench.llm)` cell, then its grader
is run on the robust and naive baselines.

Usage:
    uv run python scripts/check_kaggle_tasks.py [slug ...]
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / "kaggle_tasks"


def check(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    source = source[: source.rfind("# %%")]
    module = types.ModuleType("__kaggle_bundle_check__")
    sys.modules[module.__name__] = module
    namespace = module.__dict__
    exec(compile(source, str(path), "exec", dont_inherit=True), namespace)  # noqa: S102

    grader = next(v for k, v in namespace.items() if k.startswith("grade_") and k.endswith("_implementation"))
    robust = next(v for k, v in namespace.items() if k.startswith("ROBUST_") and k.endswith("_CODE"))
    naive = next(v for k, v in namespace.items() if k.startswith("NAIVE_") and k.endswith("_CODE"))

    r = grader(robust)
    n = grader(naive)
    ok = r.reality_gap <= 0.05 and r.reality_score >= 0.95 and n.reality_gap >= 0.20
    status = "OK  " if ok else "FAIL"
    print(f"{status} {path.stem}: robust D={r.demo_score:.2f} R={r.reality_score:.2f} | naive gap={n.reality_gap:.2f}")
    return ok


def main() -> int:
    os.environ.pop("KAGGLE_KERNEL_RUN_TYPE", None)
    # Ensure local packages cannot be imported by accident.
    sys.path = [p for p in sys.path if Path(p or ".").resolve() != ROOT]
    slugs = sys.argv[1:]
    paths = [BUNDLE_DIR / f"{s}.py" for s in slugs] if slugs else sorted(BUNDLE_DIR.glob("*.py"))
    results = [check(p) for p in paths]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
