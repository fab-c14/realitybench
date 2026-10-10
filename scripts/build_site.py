"""
Build the public results page (site/index.html) from results/kaggle_results.json.

Usage:
    uv run python scripts/build_site.py
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.tasks.registry import ALL_TASKS

RESULTS = ROOT / "results" / "kaggle_results.json"
OUT = ROOT / "site" / "index.html"
GITHUB_URL = "https://github.com/fab-c14/realitybench"
KAGGLE_URL = "https://www.kaggle.com/benchmarks/tasks/neondev0/realitybench-checkout"

MODEL_NAMES = {
    "claude-opus-5-5-default": "Claude Opus 5.5",
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gemini-3.8-flash": "Gemini 3.8 Flash",
    "gemini-3.7-flash": "Gemini 3.7 Flash",
    "gemma-4-31b-it": "Gemma 4 31B",
    "qwen3-coder-480b-a35b-instruct": "Qwen 3 Coder 480B",
}

CSS = """
:root { --bg:#fafaf9; --fg:#1c1917; --muted:#78716c; --line:#e7e5e4; --good:#15803d; --bad:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:880px; margin:0 auto; padding:72px 24px 96px; }
h1 { font-size:clamp(2rem,5vw,2.75rem); line-height:1.15; letter-spacing:-0.02em; margin:0 0 16px; }
h2 { font-size:1.125rem; margin:64px 0 16px; }
p { margin:0 0 12px; max-width:62ch; }
.lede { font-size:1.125rem; color:var(--muted); }
.muted { color:var(--muted); font-size:0.875rem; }
a { color:inherit; text-underline-offset:3px; }
.links { display:flex; gap:20px; margin-top:24px; }
.scores { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:8px; }
.scores b { display:block; }
.wrap { overflow-x:auto; border:1px solid var(--line); border-radius:8px; background:#fff; }
table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }
th, td { padding:10px 14px; text-align:right; border-bottom:1px solid var(--line); white-space:nowrap; }
th:first-child, td:first-child { text-align:left; }
th { font-weight:500; color:var(--muted); font-size:0.8125rem; }
tr:last-child td { border-bottom:0; }
.good { color:var(--good); } .bad { color:var(--bad); } .none { color:var(--line); }
pre { background:#fff; border:1px solid var(--line); border-radius:8px; padding:16px; overflow-x:auto; font-size:0.875rem; }
@media (max-width:640px) { main { padding-top:48px; } .scores { grid-template-columns:1fr; } }
"""


def _pct(x: float) -> str:
    return f"{x * 100:.0f}"


def _cls(score: float) -> str:
    return "good" if score >= 0.9 else "bad" if score < 0.6 else ""


def build() -> str:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    models = sorted(data["target_summaries"].items(), key=lambda kv: -kv[1]["avg_reality_score"])

    summary_rows = "\n".join(
        f"<tr><td>{escape(MODEL_NAMES.get(m, m))}</td><td>{s['tasks_run']} / {len(ALL_TASKS)}</td>"
        f"<td>{_pct(s['avg_demo_score'])}</td><td class='{_cls(s['avg_reality_score'])}'>"
        f"{_pct(s['avg_reality_score'])}</td><td>{s['avg_reality_gap'] * 100:+.0f}</td></tr>"
        for m, s in models
    )

    head = "".join(f"<th>{escape(MODEL_NAMES.get(m, m))}</th>" for m, _ in models)
    task_rows = []
    for t in ALL_TASKS:
        cells = []
        for _, s in models:
            r = s.get("per_task", {}).get(t.task_id)
            cells.append(f"<td class='{_cls(r['reality_score'])}'>{_pct(r['reality_score'])}</td>" if r
                         else "<td class='none'>&middot;</td>")
        task_rows.append(f"<tr><td>{escape(t.name)}</td>{''.join(cells)}</tr>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RealityBench: does AI-written code survive real users?</title>
<meta name="description" content="A Kaggle benchmark that grades AI-generated web apps in a real browser under server errors, bad input, double clicks and small screens.">
<style>{CSS}</style>
</head>
<body>
<main>
<h1>Does AI-written code survive real users?</h1>
<p class="lede">RealityBench asks a model to build a small web app, then opens it in a real browser
and does what users do: the server fails, they double-click, they type nonsense, they use a phone.</p>
<div class="links"><a href="{KAGGLE_URL}">Kaggle benchmark</a><a href="{GITHUB_URL}">Source on GitHub</a></div>

<h2>How it scores</h2>
<div class="scores">
<p><b>Demo score</b>The happy path works: the page renders and the main action reaches the server.</p>
<p><b>Reality score</b>It still works under a 500 error, invalid input, a double click, keyboard only and a 375px screen.</p>
<p><b>Reality gap</b>Demo minus reality. A big gap means it looks done in a demo and breaks for real users.</p>
</div>

<h2>Results</h2>
<div class="wrap"><table>
<thead><tr><th>Model</th><th>Tasks run</th><th>Demo</th><th>Reality</th><th>Gap</th></tr></thead>
<tbody>{summary_rows}</tbody>
</table></div>
<p class="muted">Scores out of 100, from runs on Kaggle Benchmarks. Updated {escape(data["timestamp"][:10])}.</p>

<h2>Reality score by task</h2>
<div class="wrap"><table>
<thead><tr><th>Task</th>{head}</tr></thead>
<tbody>{''.join(task_rows)}</tbody>
</table></div>

<h2>Grade your own page</h2>
<pre>uv sync &amp;&amp; uv run playwright install chromium
uv run realitybench prompt checkout &gt; spec.txt    # give this to any AI
uv run realitybench grade checkout page.html       # grade what it wrote</pre>
</main>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
