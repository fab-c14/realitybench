# RealityBench

**Does AI-written code survive real users?**

RealityBench asks a model to build a small web app (login, checkout, booking, chat, and 8 more), then opens it in a real headless browser and does what users do: the server returns a 500, they double-click Pay, they submit an empty form, they use a 375px phone screen.

Every page gets two scores:

| Score | What it checks |
|---|---|
| **Demo** | The happy path works: the page renders and the main action actually reaches the server. |
| **Reality** | It still works under server errors, bad input, double clicks, keyboard-only use and small screens. |
| **Reality gap** | Demo minus Reality. A big gap means it looks finished in a demo and breaks in production. |

Graders only count what a user can see. Text inside a `<script>` or a hidden element doesn't pass a check, so a page can't score by containing the word "error" or a `display:none` success banner.

## Results

Runs on [Kaggle Benchmarks](https://www.kaggle.com/benchmarks/tasks/neondev0/realitybench-checkout) with Claude Opus 5.5, GPT-5.6 Sol, Gemini 3.8 Flash, Gemma 4 31B and Qwen 3 Coder. The latest numbers are in [`results/kaggle_results.json`](results/kaggle_results.json) and on the results page (`site/index.html`).

## Grade your own page

```bash
uv sync
uv run playwright install chromium

uv run realitybench tasks                         # the 12 tasks
uv run realitybench prompt checkout > spec.txt    # give this spec to any AI
uv run realitybench grade checkout page.html      # grade what it wrote (add --json for the full report)
uv run realitybench baselines                     # check the graders on hand-written pages
```

`grade` accepts a plain HTML file or a whole model reply with the HTML in a code block.

## Run it on Kaggle

Kaggle uploads one file per task, so `build_kaggle_tasks.py` bundles each task with its graders into `kaggle_tasks/`. The account must be phone-verified.

```powershell
uv run kaggle auth login; uv run kaggle b init -y
uv run python scripts/check_kaggle_tasks.py       # bundles grade like the source, no model calls
./scripts/push_all_tasks.ps1                      # build and push all 12 tasks
./scripts/run_all_tasks.ps1                       # run them on the model lineup
uv run python scripts/collect_kaggle_results.py   # download runs into results/kaggle_results.json
uv run python scripts/build_site.py               # rebuild site/index.html
```

After changing a grader, `scripts/regrade_kaggle_runs.py` re-scores the model outputs you already downloaded, with no model quota spent. On Kaggle the login task is `realitybench-auth-login`.

## Layout

```
benchmark/graders/   browser harness and scoring (Demo 40%, Reality 60%)
benchmark/tasks/     12 tasks: prompt, graders, naive and robust reference pages
cli.py               realitybench command
scripts/             Kaggle bundling, runs, results, site
tests/               unit tests and grader calibration
```

The calibration tests check that every grader gives the robust reference page at least 95% on both scores, and opens a gap of at least 20 points on the naive page.

## License

MIT
