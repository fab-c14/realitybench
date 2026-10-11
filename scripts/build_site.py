"""
Build site/index.html from results/leaderboard.json.

Usage:
    uv run python scripts/build_site.py
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RESULTS = ROOT / "results" / "leaderboard.json"
OUT = ROOT / "site" / "index.html"
GITHUB_URL = "https://github.com/fab-c14/realitybench"
KAGGLE_URL = "https://www.kaggle.com/benchmarks/neondev0/realitybench"
DEV_URL = "https://dev.to/fabc14/i-asked-ai-models-to-build-web-apps-most-of-them-shipped-a-fake-server-inside-the-page-5hl0"

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


def _cls(score: float) -> str:
    return "good" if score >= 90 else "bad" if score < 60 else ""


def _cell(score: float) -> str:
    return f"<td class='{_cls(score)}'>{score:.1f}</td>"


def build() -> str:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    models = data["models"]
    head = "".join(f"<th>{escape(name)}</th>" for name in models)
    overall = "".join(_cell(score) for score in data["overall"])
    task_rows = [
        f"<tr><td>{escape(task['slug'])}</td>{''.join(_cell(score) for score in task['scores'])}</tr>"
        for task in data["tasks"]
    ]

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
<div class="links"><a href="{KAGGLE_URL}">Kaggle benchmark</a><a href="{DEV_URL}">Write-up</a><a href="{GITHUB_URL}">Source on GitHub</a></div>

<h2>How it scores</h2>
<div class="scores">
<p><b>Overall</b>One number from 0 to 100. Happy path is 40% of the weight. Server errors, bad input, double clicks, keyboard-only use and a 375px screen are the other 60%.</p>
<p><b>What counts</b>Text a person can see. A page that replaces <code>fetch</code> or <code>XMLHttpRequest</code> answers itself, and the request never arrives.</p>
<p><b>One run</b>Each cell is a single run of that model on that task. The same table is on the Kaggle leaderboard.</p>
</div>

<h2>Leaderboard</h2>
<div class="wrap"><table>
<thead><tr><th>Task</th>{head}</tr></thead>
<tbody>{''.join(task_rows)}
<tr><td><b>Overall</b></td>{overall}</tr></tbody>
</table></div>
<p class="muted">Scores from the Kaggle leaderboard. Updated {escape(data["updated"])}.</p>

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
