---
title: I asked AI models to build web apps. Most of them shipped a fake server inside the page.
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23).*

**Kaggle benchmark:** [realitybench](https://www.kaggle.com/benchmarks/neondev0/realitybench)

## What I Benchmarked

AI coding demos show the happy path. The form renders, you click the button, and a green success message appears. I wanted the score to change when a real user shows up.

**RealityBench** gives a model a spec for one of twelve small web apps, then opens the page in a headless browser and uses it the way a person would:

- the server answers with a 500, or a 409 when a slot is already taken
- they double-click Pay
- they submit an empty form, a negative quantity, or a `.exe` instead of a PDF
- they only use the keyboard, or a 375px phone screen

The number on the Kaggle leaderboard is one overall score from 0 to 100. It is weighted 40% toward the happy path and 60% toward those real-user checks. The grader only counts text a person can see, and it records whether `window.fetch` and `XMLHttpRequest` are still the browser's own functions. A page that replaces them answers its own requests and never contacts the server it was told to call.

## Models Tested

The leaderboard is the four models that finished a run on every task:

- **Claude Opus 5.5**, the strongest coding model in the lineup
- **GPT-6 Sol**
- **Gemini 3.8 Flash**
- **Gemini 3.7 Flash**, the fast model people use to generate UI in bulk

Same twelve prompts. One run per task. The cell is that run's overall score.

## Findings

These are the scores on the [realitybench leaderboard](https://www.kaggle.com/benchmarks/neondev0/realitybench). Each cell matches the benchmark page.

| Task | Claude Opus 5.5 | GPT-6 Sol | Gemini 3.8 Flash | Gemini 3.7 Flash |
|---|---|---|---|---|
| realitybench-auth-login | 100.0 | 100.0 | 100.0 | 100.0 |
| realitybench-search | 43.0 | 100.0 | 100.0 | 38.0 |
| realitybench-checkout | 100.0 | 55.0 | 100.0 | 55.0 |
| realitybench-file-upload | 100.0 | 100.0 | 93.0 | 93.0 |
| realitybench-crud-dashboard | 100.0 | 72.5 | 22.0 | 95.0 |
| realitybench-booking | 100.0 | 100.0 | 82.0 | 82.0 |
| realitybench-chat | 100.0 | 100.0 | 100.0 | 100.0 |
| realitybench-product-page | 90.0 | 100.0 | 82.0 | 67.0 |
| realitybench-admin-table | 100.0 | 100.0 | 70.0 | 70.0 |
| realitybench-settings | 82.0 | 80.0 | 82.0 | 82.0 |
| realitybench-api-form | 100.0 | 100.0 | 67.0 | 67.0 |
| realitybench-workflow | 100.0 | 80.0 | 82.0 | 82.0 |
| **Overall** | **92.9** | **90.6** | **81.7** | **77.6** |

Opus leads, at 92.9, and it scores 100 on nine of the twelve tasks. Its miss is search, at 43. GPT-6 Sol is close behind at 90.6, then drops on checkout (55) and the task dashboard (72.5). Gemini 3.8 Flash is at 81.7 and falls to 22 on the task dashboard, the lowest cell in the table. Gemini 3.7 Flash is at 77.6, with search at 38 and checkout at 55.

Login and chat are 100 for every model. Settings sits in a band from 80 to 82 for every model. The tasks that separate them are search, checkout, and the task dashboard.

### Models build a fake backend into the page

The prompt says to POST to an API. Several generated pages replace `fetch` and answer locally. This is Gemini 3.7 Flash's booking page, shortened only by cutting a 409 branch:

```js
/* MOCK SERVER INTERCEPTOR (For self-contained standalone execution)
   Ensures fetch('/api/book') behaves accurately in standalone browsers. */
const originalFetch = window.fetch;
window.fetch = async function (resource, init) {
  if (typeof resource === "string" && resource.endsWith("/api/book")) {
    await new Promise((r) => setTimeout(r, 450));
    return new Response(JSON.stringify({
      status: "confirmed",
      booking_id: "BK-" + Math.floor(100 + Math.random() * 900),
    }), { status: 200, headers: { "Content-Type": "application/json" } });
  }
  return originalFetch.apply(this, arguments);
};
```

The page can show a booking id. Nothing was booked. The comment in the page says the mock is there so the file runs on its own.

Opus often writes the same kind of mock, then leaves it off unless the URL has `?demo` or `?mock`. Its settings page is the one that starts with the mock switched on.

The leaderboard score is not that flag. A page can still lose points for a double submit, a bad empty state, or a control the grader cannot press. Search is the clearest case: Opus at 43, Gemini 3.7 Flash at 38, and the other two models at 100.

### What I'd measure next

- More than one run per task, so the table can show a range.
- The same prompts with one added line: a real backend is already running at this URL. I want to know whether the fake server disappears.

## My Benchmark

- **Kaggle:** [realitybench](https://www.kaggle.com/benchmarks/neondev0/realitybench). Twelve tasks, four models, and the scores in the table above.
- **Code:** [github.com/fab-c14/realitybench](https://github.com/fab-c14/realitybench)

You can grade a page yourself:

```bash
uv sync && uv run playwright install chromium
uv run realitybench prompt checkout > spec.txt
uv run realitybench grade checkout page.html
```

`grade` accepts a plain HTML file or a model reply with the HTML in a code block. If the page replaced `fetch` or `XMLHttpRequest`, it prints a warning.
