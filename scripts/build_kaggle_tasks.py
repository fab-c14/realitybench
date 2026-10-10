"""
Build self-contained Kaggle Benchmark task files.

Kaggle uploads a single .py file per task, so the shared grader modules
(`benchmark/graders/scoring.py`, `benchmark/graders/browser_runner.py`) are
inlined into each task, local-only imports are stripped, and the task ends
with an unconditional `.run(kbench.llm)` cell.

Usage:
    uv run python scripts/build_kaggle_tasks.py
Output:
    kaggle_tasks/<slug>.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "benchmark" / "tasks"
GRADERS_DIR = ROOT / "benchmark" / "graders"
OUT_DIR = ROOT / "kaggle_tasks"

LOCAL_IMPORT_RE = re.compile(r"^\s*(from (benchmark|ui)[\w.]* import .*|import (benchmark|ui)\b.*)$")
SYS_PATH_BLOCK_RE = re.compile(
    r"^(# Ensure realitybench package is on path\n)?"
    r"current_dir = os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\n"
    r"bench_root = .*\n"
    r"if bench_root not in sys\.path:\n"
    r"\s+sys\.path\.insert\(0, bench_root\)\n",
    re.MULTILINE,
)
TASK_DECORATOR_RE = re.compile(r'@kbench\.task\(name="([^"]+)"\)\s*\ndef (realitybench_\w+)')

SETUP_CELL = '''# %%
# Ensure a headless Chromium is available for the Playwright grader.
import subprocess
import sys as _sys


def _ensure_chromium() -> None:
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        return
    except Exception:
        pass
    subprocess.run([_sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], check=False)
    subprocess.run([_sys.executable, "-m", "playwright", "install", "chromium"], check=True)


_ensure_chromium()
'''


def _strip_module_docstring(source: str) -> str:
    stripped = source.lstrip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            end = stripped.find(quote, 3)
            if end != -1:
                return stripped[end + 3:].lstrip("\n")
    return source


def _grader_source() -> str:
    parts = []
    for name in ("scoring.py", "browser_runner.py"):
        body = _strip_module_docstring((GRADERS_DIR / name).read_text(encoding="utf-8"))
        parts.append(f"# ---- inlined from benchmark/graders/{name} ----\n{body.rstrip()}\n")
    return "# %%\n" + "\n\n".join(parts) + "\n"


def _split_task(source: str) -> str:
    """Return the task body with local-only imports and the __main__ block removed."""
    main_idx = source.find('\nif __name__ == "__main__":')
    if main_idx != -1:
        source = source[:main_idx].rstrip() + "\n"
    source = re.sub(r"\n# %%\s*$", "\n", source.rstrip() + "\n")
    source, removed = SYS_PATH_BLOCK_RE.subn("", source)
    if removed != 1:
        raise ValueError("Expected exactly one sys.path bootstrap block")

    lines = [line for line in source.splitlines() if not LOCAL_IMPORT_RE.match(line)]
    return "\n".join(lines).rstrip() + "\n"


def build_task(path: Path) -> tuple[str, Path]:
    source = path.read_text(encoding="utf-8")
    match = TASK_DECORATOR_RE.search(source)
    if not match:
        raise ValueError(f"No @kbench.task found in {path.name}")
    slug, func_name = match.groups()

    body = _split_task(source)
    output = "\n".join([
        f"# %%\n# RealityBench Kaggle task: {slug} (generated from benchmark/tasks/{path.name})\n",
        SETUP_CELL,
        _grader_source(),
        body,
        f"# %%\n{func_name}.run(kbench.llm)\n",
    ])

    out_path = OUT_DIR / f"{slug}.py"
    out_path.write_text(output, encoding="utf-8")
    return slug, out_path


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for path in sorted(TASKS_DIR.glob("task_*.py")):
        slug, out_path = build_task(path)
        print(f"{slug} -> {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
