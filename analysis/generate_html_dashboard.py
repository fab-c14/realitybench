"""
RealityBench Showcase & Empirical Evaluation Interface
Generates an anti-slop, editorial, and interactive product experience (results/dashboard.html)
strictly adhering to the /taste framework, Google Stitch guidelines, and zero-slop design directives.
"""

import json
import os
import webbrowser
from html import escape as html_escape
from typing import Any

bench_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(bench_root, "results")
FULL_RESULTS = os.path.join(RESULTS_DIR, "full_benchmark_results.json")
PILOT_RESULTS = os.path.join(RESULTS_DIR, "pilot_benchmark_results.json")
# Same schema as full_benchmark_results.json ("target_summaries"); written from Kaggle runs.
KAGGLE_RESULTS = os.path.join(RESULTS_DIR, "kaggle_results.json")
OUTPUT_HTML = os.path.join(RESULTS_DIR, "dashboard.html")


def load_dataset() -> tuple[dict[str, Any], str]:
    if os.path.exists(FULL_RESULTS):
        with open(FULL_RESULTS, "r", encoding="utf-8") as f:
            data, label = json.load(f), "Full Benchmark Suite (12 Tasks)"
    elif os.path.exists(PILOT_RESULTS):
        with open(PILOT_RESULTS, "r", encoding="utf-8") as f:
            data, label = json.load(f), "Pilot Calibration Suite (3 Tasks)"
    else:
        raise FileNotFoundError("No benchmark results found. Run `realitybench pilot` or `realitybench run` first.")

    sources = {name: "local" for name in data.get("target_summaries", {})}
    if os.path.exists(KAGGLE_RESULTS):
        with open(KAGGLE_RESULTS, "r", encoding="utf-8") as f:
            kaggle = json.load(f)
        for name, summary in kaggle.get("target_summaries", {}).items():
            data.setdefault("target_summaries", {})[name] = summary
            sources[name] = "kaggle"
        data["timestamp"] = max(data.get("timestamp", ""), kaggle.get("timestamp", ""))
    data["sources"] = sources
    return data, label


def _source_label(name: str, source: str) -> str:
    if name.endswith("-baseline"):
        return "Hand-written reference"
    if source == "kaggle":
        return "Kaggle Benchmarks run"
    return "Local model run"


def _status(gap: float) -> tuple[str, str, str]:
    """(pill text, pill class, gap color var) for an average Reality Gap."""
    if gap <= 0.02:
        return "Production ready", "pill-green", "var(--accent-emerald)"
    if gap <= 0.15:
        return "Resilient", "pill-blue", "var(--text-primary)"
    return "Fragility trap", "pill-red", "var(--accent-crimson)"


def build_model_cards(target_summaries: dict[str, Any], sources: dict[str, str]) -> str:
    ordered = sorted(target_summaries.items(), key=lambda kv: kv[1].get("avg_reality_gap", 0.0))
    cards = []
    for name, s in ordered:
        demo = s.get("avg_demo_score", 0.0)
        reality = s.get("avg_reality_score", 0.0)
        gap = s.get("avg_reality_gap", demo - reality)
        pill, pill_class, gap_color = _status(gap)
        reality_color = "var(--accent-crimson)" if gap > 0.15 else "var(--accent-emerald)"
        cards.append(f"""
                <div class="model-card">
                    <div>
                        <div class="model-card-header">
                            <span class="model-name">{html_escape(name)}</span>
                            <span class="status-pill {pill_class}">{pill}</span>
                        </div>
                        <div class="model-source">{_source_label(name, sources.get(name, "local"))}</div>
                        <div class="score-pair">
                            <span class="score-lbl">Demo Score</span>
                            <span class="score-num" style="color: var(--accent-blue-hover);">{demo * 100:.1f}%</span>
                        </div>
                        <div class="score-pair">
                            <span class="score-lbl">Reality Score</span>
                            <span class="score-num" style="color: {reality_color};">{reality * 100:.1f}%</span>
                        </div>
                    </div>
                    <div class="gap-callout">
                        <span>Reality Gap</span>
                        <span style="font-weight: 700; color: {gap_color};">{"+" if gap > 0 else ""}{gap * 100:.1f}%</span>
                    </div>
                </div>""")
    return "".join(cards)


def build_dashboard_html(data: dict[str, Any], dataset_label: str) -> str:
    target_summaries = data.get("target_summaries", {})
    timestamp = data.get("timestamp", "2026-10-09T18:00:00Z")

    # Curated task suite data with engineering focus
    tasks = [
        {
            "id": "realitybench-login",
            "number": "01",
            "name": "Authentication and Login",
            "category": "Security and Forms",
            "vulnerability": "Empty payloads allowed, password inputs missing form wrapper, double submit",
            "happy_path": "Valid email and password return mock auth token with welcome banner",
            "stress_test": "Network 500 error preserves entered email, double-click debounces, mobile 375px fits"
        },
        {
            "id": "realitybench-search",
            "number": "02",
            "name": "Search and Autocomplete",
            "category": "Async and Telemetry",
            "vulnerability": "Zero keystroke debouncing, empty result crash, unhandled 500 query errors",
            "happy_path": "Typing queries displays matching dropdown items smoothly",
            "stress_test": "300ms input debounce, empty state display, server 500 retry button"
        },
        {
            "id": "realitybench-checkout",
            "number": "03",
            "name": "Order Checkout and Cart",
            "category": "E-Commerce",
            "vulnerability": "Duplicate charges on rapid double-click, cart wiped on network failure",
            "happy_path": "Submitting valid order displays purchase confirmation and order ID",
            "stress_test": "Cart items preserved after 500 error, rapid double submit debounced, negative coupons blocked"
        },
        {
            "id": "realitybench-file-upload",
            "number": "04",
            "name": "File Upload Dropzone",
            "category": "Storage and IO",
            "vulnerability": "Executable files accepted, 5MB limits bypassed, unhandled upload crash",
            "happy_path": "Dropping a valid PDF or image shows progress bar and complete state",
            "stress_test": "Rejects .exe and script files, blocks files over 5MB client-side, retry button on fault"
        },
        {
            "id": "realitybench-crud-dashboard",
            "number": "05",
            "name": "Task CRUD Dashboard",
            "category": "State Management",
            "vulnerability": "Whitespace-only tasks created, mutation rollback missing on failed delete",
            "happy_path": "Adding, editing, and checking off tasks updates list instantaneously",
            "stress_test": "Optimistic rollback on server 500, whitespace rejected, delete confirmation modal"
        },
        {
            "id": "realitybench-booking",
            "number": "06",
            "name": "Appointment Booking",
            "category": "Calendar and Forms",
            "vulnerability": "Past dates permitted, slot conflict 409 crashes application state",
            "happy_path": "Selecting available future slot books appointment with confirmation summary",
            "stress_test": "Past dates blocked, 409 conflict recovers without wiping customer name, keyboard Enter works"
        },
        {
            "id": "realitybench-chat",
            "number": "07",
            "name": "Live Messaging Thread",
            "category": "Real-time Comms",
            "vulnerability": "Blank messages sent, in-thread network errors invisible to user",
            "happy_path": "Typing and pressing Enter sends message and scrolls into view",
            "stress_test": "Whitespace blocked, inline retry badge on 500 error, Enter key triggers send without click"
        },
        {
            "id": "realitybench-product-page",
            "number": "08",
            "name": "Product Detail Showcase",
            "category": "E-Commerce",
            "vulnerability": "Sold out items still purchasable, broken images show blank icons",
            "happy_path": "Selecting sizes and clicking Add to Cart updates counter badge",
            "stress_test": "Out-of-stock disabling, broken image fallback, negative quantities locked"
        },
        {
            "id": "realitybench-admin-table",
            "number": "09",
            "name": "Admin Data Table",
            "category": "Data and Tables",
            "vulnerability": "Null fields trigger unhandled JavaScript TypeError, pagination underflow",
            "happy_path": "Renders user records with sorting and pagination controls",
            "stress_test": "Missing fields render gracefully, page bounds enforced, semantic table header markup"
        },
        {
            "id": "realitybench-settings",
            "number": "10",
            "name": "User Settings Panel",
            "category": "State and Preferences",
            "vulnerability": "Discard button fails to restore state, save failure silently reverts edits",
            "happy_path": "Modifying profile and saving persists values successfully",
            "stress_test": "Dirty state tracking, discard restores original data, server 500 preserves unsaved edits"
        },
        {
            "id": "realitybench-api-form",
            "number": "11",
            "name": "Cascading Dependent Form",
            "category": "Forms and Async",
            "vulnerability": "Parent change leaves stale child data, dynamic fetch 500 locks form",
            "happy_path": "Selecting Country fetches and populates corresponding City list",
            "stress_test": "Switching country immediately clears stale city, dynamic 500 recovery, empty lock"
        },
        {
            "id": "realitybench-workflow",
            "number": "12",
            "name": "Multi-Step Workflow Wizard",
            "category": "Workflows",
            "vulnerability": "Back button wipes previous steps, step validation bypassed via URL",
            "happy_path": "Progressing through Steps 1 to 3 completes setup and shows receipt",
            "stress_test": "Step data retained on Back navigation, Step 3 500 allows retry without restart"
        }
    ]

    tasks_json = json.dumps(tasks)
    model_cards_html = build_model_cards(target_summaries, data.get("sources", {}))
    updated_label = timestamp[:10]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RealityBench | Benchmarking AI Software Beyond the Happy Path</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #09090b;
            --bg-surface: #111114;
            --bg-elevated: #18181c;
            --border-subtle: #222227;
            --border-strong: #33333c;
            --border-active: #4a4a58;
            --text-primary: #f4f4f7;
            --text-secondary: #92929e;
            --text-muted: #5e5e6c;
            --accent-blue: #2563eb;
            --accent-blue-hover: #3b82f6;
            --accent-emerald: #10b981;
            --accent-crimson: #ef4444;
            --accent-amber: #f59e0b;
            --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: var(--font-sans);
            -webkit-font-smoothing: antialiased;
        }}

        body {{
            background-color: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 0;
            min-height: 100vh;
        }}

        .page-wrap {{
            max-width: 1320px;
            margin: 0 auto;
            padding: 40px 24px 80px 24px;
        }}

        /* Subtle technical grid background */
        body::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background-image: 
                linear-gradient(to right, rgba(255, 255, 255, 0.015) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
            background-size: 56px 56px;
            z-index: 0;
        }}

        .content-layer {{
            position: relative;
            z-index: 1;
        }}

        /* Navigation Bar */
        .site-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 64px;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 48px;
        }}

        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text-primary);
        }}

        .nav-logo {{
            width: 28px;
            height: 28px;
            background: var(--bg-elevated);
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            color: var(--accent-blue-hover);
        }}

        .nav-title {{
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .nav-links {{
            display: flex;
            align-items: center;
            gap: 24px;
            font-size: 13px;
        }}

        .nav-links a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 120ms ease;
        }}

        .nav-links a:hover {{
            color: var(--text-primary);
        }}

        .nav-cta {{
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            background: var(--accent-blue);
            color: #ffffff !important;
            border: 1px solid var(--accent-blue-hover);
            transition: all 120ms ease;
            display: inline-block;
            white-space: nowrap;
        }}

        .nav-cta:hover {{
            background: var(--accent-blue-hover);
            transform: translateY(-1px);
        }}

        .nav-cta:active {{
            transform: scale(0.98);
        }}

        /* Asymmetric Split Hero */
        .hero-section {{
            display: grid;
            grid-template-columns: 1.15fr 1fr;
            gap: 40px;
            align-items: center;
            margin-bottom: 72px;
        }}

        @media (max-width: 990px) {{
            .hero-section {{
                grid-template-columns: 1fr;
                gap: 32px;
            }}
        }}

        .hero-content {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .hero-eyebrow {{
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            color: var(--accent-blue-hover);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .model-source {{
            font-size: 12px;
            color: var(--text-muted);
            margin: -4px 0 12px;
        }}

        .scoreboard-meta {{
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 8px;
        }}

        .hero-h1 {{
            font-size: clamp(34px, 4.2vw, 48px);
            font-weight: 800;
            line-height: 1.12;
            letter-spacing: -0.035em;
        }}

        .hero-subtext {{
            font-size: 16px;
            color: var(--text-secondary);
            line-height: 1.6;
            max-width: 50ch;
        }}

        .hero-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 8px;
            flex-wrap: wrap;
        }}

        .btn-primary {{
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 6px;
            background: var(--accent-blue);
            color: #ffffff;
            border: 1px solid var(--accent-blue-hover);
            cursor: pointer;
            transition: all 120ms ease;
            white-space: nowrap;
        }}

        .btn-primary:hover {{
            background: var(--accent-blue-hover);
            transform: translateY(-1px);
        }}

        .btn-primary:active {{
            transform: scale(0.98);
        }}

        .btn-ghost {{
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 500;
            padding: 10px 18px;
            border-radius: 6px;
            background: var(--bg-surface);
            color: var(--text-secondary);
            border: 1px solid var(--border-strong);
            cursor: pointer;
            transition: all 120ms ease;
            white-space: nowrap;
        }}

        .btn-ghost:hover {{
            color: var(--text-primary);
            border-color: var(--border-active);
            background: var(--bg-elevated);
        }}

        .btn-ghost:active {{
            transform: scale(0.98);
        }}

        /* Interactive Reality Sandbox */
        .sandbox-panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }}

        .sandbox-top {{
            background: var(--bg-elevated);
            border-bottom: 1px solid var(--border-subtle);
            padding: 12px 16px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: space-between;
            align-items: center;
        }}

        .sandbox-title {{
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
        }}

        .sandbox-controls {{
            display: flex;
            gap: 8px;
        }}

        .sim-btn {{
            font-family: var(--font-mono);
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid var(--border-subtle);
            background: var(--bg-base);
            color: var(--text-secondary);
            cursor: pointer;
            white-space: nowrap;
            transition: all 100ms ease;
        }}

        .sim-btn:hover {{
            color: var(--text-primary);
            border-color: var(--border-strong);
        }}

        .sim-btn.active {{
            background: var(--accent-blue);
            color: #ffffff;
            border-color: var(--accent-blue-hover);
        }}

        .sandbox-body {{
            padding: 24px;
        }}

        .sim-component-box {{
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            transition: all 200ms ease;
        }}

        .sim-input-row {{
            margin-bottom: 12px;
        }}

        .sim-input-row label {{
            display: block;
            font-size: 11px;
            font-family: var(--font-mono);
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
        }}

        .sim-input {{
            width: 100%;
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-family: var(--font-sans);
            outline: none;
            transition: border-color 120ms ease;
        }}

        .sim-input:focus {{
            border-color: var(--accent-blue-hover);
        }}

        .sim-submit-btn {{
            width: 100%;
            padding: 10px;
            background: var(--accent-blue);
            border: 1px solid var(--accent-blue-hover);
            color: #ffffff;
            font-weight: 600;
            font-size: 13px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 100ms ease;
        }}

        .sim-submit-btn:hover {{
            background: var(--accent-blue-hover);
        }}

        .sim-submit-btn:active {{
            transform: scale(0.98);
        }}

        .sim-status-banner {{
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-family: var(--font-mono);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 42px;
        }}

        .status-idle {{
            background: var(--bg-elevated);
            color: var(--text-secondary);
            border: 1px dashed var(--border-strong);
        }}

        .status-ok {{
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .status-fail {{
            background: rgba(239, 68, 68, 0.12);
            color: var(--accent-crimson);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        /* Section Layout Discipline */
        .section-wrap {{
            margin-bottom: 72px;
        }}

        .section-header-block {{
            margin-bottom: 28px;
        }}

        .section-title {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }}

        .section-desc {{
            color: var(--text-secondary);
            font-size: 14px;
            max-width: 65ch;
            line-height: 1.5;
        }}

        /* The Reality Gap Comparison Matrix */
        .model-cards-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}

        @media (max-width: 1024px) {{
            .model-cards-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 640px) {{
            .model-cards-grid {{
                grid-template-columns: 1fr;
            }}

            .nav-links a:not(.nav-cta) {{
                display: none;
            }}

            .catalog-table th:nth-child(1),
            .catalog-table td:nth-child(1),
            .catalog-table th:nth-child(3),
            .catalog-table td:nth-child(3) {{
                display: none;
            }}

            .catalog-table th,
            .catalog-table td {{
                width: auto !important;
            }}
        }}

        .model-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 150ms ease;
        }}

        .model-card:hover {{
            border-color: var(--border-strong);
            transform: translateY(-2px);
        }}

        .model-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}

        .model-name {{
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        .status-pill {{
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
        }}

        .pill-green {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .pill-red {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-crimson);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .pill-blue {{
            background: rgba(37, 99, 235, 0.15);
            color: var(--accent-blue-hover);
            border: 1px solid rgba(37, 99, 235, 0.3);
        }}

        .score-pair {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px dashed var(--border-subtle);
            font-size: 13px;
        }}

        .score-pair:last-child {{
            border-bottom: none;
        }}

        .score-lbl {{
            color: var(--text-secondary);
        }}

        .score-num {{
            font-family: var(--font-mono);
            font-weight: 700;
        }}

        .gap-callout {{
            margin-top: 14px;
            padding: 8px 12px;
            background: var(--bg-base);
            border-radius: 6px;
            border: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: var(--font-mono);
            font-size: 12px;
        }}

        /* 12 Tasks Interactive Catalog */
        .task-catalog-wrap {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            overflow: hidden;
        }}

        .catalog-filter-bar {{
            padding: 16px 20px;
            background: var(--bg-elevated);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .catalog-search {{
            background: var(--bg-base);
            border: 1px solid var(--border-strong);
            color: var(--text-primary);
            font-size: 12px;
            font-family: var(--font-mono);
            padding: 6px 12px;
            border-radius: 6px;
            width: 260px;
            outline: none;
        }}

        .catalog-search:focus {{
            border-color: var(--accent-blue-hover);
        }}

        .catalog-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .catalog-table th, .catalog-table td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }}

        .catalog-table th {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            background: var(--bg-base);
        }}

        .catalog-row {{
            cursor: pointer;
            transition: background 120ms ease;
        }}

        .catalog-row:hover td {{
            background: var(--bg-elevated);
        }}

        /* Modal Inspector */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            z-index: 200;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }}

        .modal-overlay.active {{
            display: flex;
        }}

        .modal-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            border-radius: 12px;
            width: min(720px, 94vw);
            max-height: 88vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7);
            display: flex;
            flex-direction: column;
        }}

        .modal-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .modal-close {{
            background: var(--bg-base);
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 12px;
            padding: 4px 10px;
            cursor: pointer;
        }}

        .modal-close:hover {{
            color: var(--text-primary);
        }}

        .modal-body {{
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .modal-detail-box {{
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 16px;
        }}

        .modal-detail-title {{
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }}

        /* Footer */
        .site-footer {{
            padding-top: 40px;
            border-top: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-muted);
            font-size: 13px;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .footer-left {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .footer-links {{
            display: flex;
            gap: 20px;
        }}

        .footer-links a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 120ms ease;
        }}

        .footer-links a:hover {{
            color: var(--text-primary);
        }}
    </style>
</head>
<body>
    <div class="page-wrap content-layer">

        <!-- Top Header Navigation -->
        <nav class="site-nav">
            <a href="#" class="nav-brand">
                <div class="nav-logo">RB</div>
                <div class="nav-title">RealityBench</div>
            </a>
            <div class="nav-links">
                <a href="#models">Results</a>
                <a href="#tasks">Tasks</a>
                <a href="#cli">Run it</a>
                <a href="https://github.com/fab-c14/realitybench" target="_blank" class="nav-cta">GitHub</a>
            </div>
        </nav>

        <!-- Asymmetric Split Hero -->
        <section class="hero-section">
            <div class="hero-content">
                <div class="hero-eyebrow">
                    <span>Kaggle Benchmarking Challenge</span>
                </div>
                <h1 class="hero-h1">
                    Does AI-written code survive real users?
                </h1>
                <p class="hero-subtext">
                    RealityBench breaks AI-generated web apps on purpose: server errors, double clicks, bad input, small screens.
                </p>
                <div class="hero-actions">
                    <button class="btn-primary" onclick="scrollToResults()">See results</button>
                    <button class="btn-ghost" id="copyCliBtn" onclick="copyCliCmd()">Copy CLI command</button>
                </div>
            </div>

            <!-- Live Interactive Reality Sandbox -->
            <div class="sandbox-panel">
                <div class="sandbox-top">
                    <span class="sandbox-title">Interactive Failure Sandbox</span>
                    <div class="sandbox-controls">
                        <button class="sim-btn active" id="btnHappy" onclick="runSim('happy')">Happy Path</button>
                        <button class="sim-btn" id="btnHttp500" onclick="runSim('500')">Inject HTTP 500</button>
                        <button class="sim-btn" id="btnSpam" onclick="runSim('spam')">Double Click</button>
                    </div>
                </div>
                <div class="sandbox-body">
                    <div class="sim-component-box">
                        <div class="sim-input-row">
                            <label>Email Address</label>
                            <input type="text" id="simEmail" class="sim-input" value="engineer@company.com">
                        </div>
                        <div class="sim-input-row">
                            <label>Password</label>
                            <input type="password" id="simPassword" class="sim-input" value="supersecretpassword">
                        </div>
                        <button class="sim-submit-btn" id="simSubmitBtn" onclick="handleSimSubmit()">Sign In to Dashboard</button>
                    </div>

                    <div id="simStatus" class="sim-status-banner status-idle">
                        <span>Select a scenario above to test runtime behavior.</span>
                        <span style="font-size: 11px; opacity: 0.7;">Playwright Chromium Verified</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- Section 2: Results -->
        <section class="section-wrap" id="models">
            <div class="section-header-block">
                <h2 class="section-title">Results</h2>
                <p class="section-desc">
                    Demo Score checks the normal flow. Reality Score checks failures and bad input. A big gap means it only works in demos.
                </p>
                <div class="scoreboard-meta">Updated {updated_label}</div>
            </div>

            <div class="model-cards-grid">{model_cards_html}
            </div>
        </section>

        <!-- Section 3: The 12 Tasks Suite -->
        <section class="section-wrap" id="tasks">
            <div class="section-header-block">
                <h2 class="section-title">The 12-Task Benchmark Suite</h2>
                <p class="section-desc">
                    Deterministic Playwright Chromium evaluation across core web engineering components. Click any task to inspect happy path specifications and reality failure vectors.
                </p>
            </div>

            <div class="task-catalog-wrap">
                <div class="catalog-filter-bar">
                    <label for="taskSearch" style="font-size: 13px; color: var(--text-secondary);">Filter tasks</label>
                    <input type="text" id="taskSearch" class="catalog-search" placeholder="Name or category">
                </div>

                <table class="catalog-table">
                    <thead>
                        <tr>
                            <th style="width: 48px;">#</th>
                            <th style="width: 240px;">Component</th>
                            <th style="width: 160px;">Category</th>
                            <th>Software Engineering Focus</th>
                        </tr>
                    </thead>
                    <tbody id="catalogBody">
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Section 4: Quickstart CLI -->
        <section class="section-wrap" id="cli">
            <div class="section-header-block">
                <h2 class="section-title">Run it yourself</h2>
                <p class="section-desc">
                    Python 3.11 and Playwright. Every score comes from a real browser check, never from another AI's opinion.
                </p>
            </div>

            <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 24px; font-family: var(--font-mono); font-size: 13px;">
                <div style="color: var(--text-muted); margin-bottom: 8px;"># Run the fast 3-task pilot benchmark locally</div>
                <div style="color: var(--text-primary); margin-bottom: 18px;">uv run realitybench pilot</div>

                <div style="color: var(--text-muted); margin-bottom: 8px;"># Run the full 12-task benchmark suite with colorful terminal layout</div>
                <div style="color: var(--text-primary); margin-bottom: 18px;">uv run realitybench run</div>

                <div style="color: var(--text-muted); margin-bottom: 8px;"># Inspect task matrix across models</div>
                <div style="color: var(--text-primary);">uv run realitybench matrix</div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="site-footer">
            <div class="footer-left">
                <span>RealityBench</span>
                <span>&bull;</span>
                <span>Kaggle Benchmarking Challenge Submission</span>
            </div>
            <div class="footer-links">
                <a href="https://github.com/fab-c14/realitybench" target="_blank">GitHub</a>
                <a href="https://dev.to/challenges/kaggle-2026-09-23" target="_blank">DEV Challenge</a>
                <a href="https://github.com/Kaggle/kaggle-benchmarks" target="_blank">Kaggle Benchmarks SDK</a>
            </div>
        </footer>

    </div>

    <!-- Task Detail Modal -->
    <div class="modal-overlay" id="taskModal" onclick="closeModal(event)">
        <div class="modal-card" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <span style="font-family: var(--font-mono); font-size: 11px; color: var(--accent-blue-hover); text-transform: uppercase;">Task Specification</span>
                    <h3 id="modalTitle" style="font-size: 18px; font-weight: 700; margin-top: 2px;">Task Details</h3>
                </div>
                <button class="modal-close" onclick="closeModalDirect()">ESC</button>
            </div>
            <div class="modal-body">
                <div class="modal-detail-box">
                    <div class="modal-detail-title">Happy Path Expectation (Demo Score 40%)</div>
                    <div id="modalHappyPath" style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"></div>
                </div>

                <div class="modal-detail-box">
                    <div class="modal-detail-title">Controlled Perturbations (Reality Score 60%)</div>
                    <div id="modalStressTest" style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"></div>
                </div>

                <div class="modal-detail-box">
                    <div class="modal-detail-title">Primary Vulnerabilities Caught</div>
                    <div id="modalVulnerability" style="font-size: 13px; color: var(--accent-crimson); line-height: 1.5;"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const tasks = {tasks_json};

        // Render Task Table
        function renderTasks() {{
            const tbody = document.getElementById("catalogBody");
            tbody.innerHTML = "";
            const query = (document.getElementById("taskSearch").value || "").toLowerCase();

            tasks.forEach(t => {{
                if (query && !t.name.toLowerCase().includes(query) && !t.category.toLowerCase().includes(query)) {{
                    return;
                }}
                const tr = document.createElement("tr");
                tr.className = "catalog-row";
                tr.onclick = () => openModal(t);

                tr.innerHTML = `
                    <td style="font-family: var(--font-mono); color: var(--text-muted);">${{t.number}}</td>
                    <td style="font-weight: 600; color: var(--text-primary);">${{t.name}}</td>
                    <td><span class="status-pill pill-blue">${{t.category}}</span></td>
                    <td style="color: var(--text-secondary);">${{t.vulnerability}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        document.getElementById("taskSearch").addEventListener("input", renderTasks);
        renderTasks();

        // Modal Logic
        function openModal(task) {{
            document.getElementById("modalTitle").textContent = task.name;
            document.getElementById("modalHappyPath").textContent = task.happy_path;
            document.getElementById("modalStressTest").textContent = task.stress_test;
            document.getElementById("modalVulnerability").textContent = task.vulnerability;
            document.getElementById("taskModal").classList.add("active");
        }}

        function closeModalDirect() {{
            document.getElementById("taskModal").classList.remove("active");
        }}

        function closeModal(e) {{
            if (e.target.id === "taskModal") {{
                closeModalDirect();
            }}
        }}

        document.addEventListener("keydown", (e) => {{
            if (e.key === "Escape") closeModalDirect();
        }});

        // Interactive Simulation
        let activeSimMode = 'happy';
        let spamCount = 0;

        function runSim(mode) {{
            activeSimMode = mode;
            spamCount = 0;
            document.querySelectorAll(".sim-btn").forEach(b => b.classList.remove("active"));
            if (mode === 'happy') document.getElementById("btnHappy").classList.add("active");
            if (mode === '500') document.getElementById("btnHttp500").classList.add("active");
            if (mode === 'spam') document.getElementById("btnSpam").classList.add("active");

            const banner = document.getElementById("simStatus");
            const btn = document.getElementById("simSubmitBtn");
            btn.disabled = false;
            btn.textContent = "Sign In to Dashboard";

            if (mode === 'happy') {{
                banner.className = "sim-status-banner status-idle";
                banner.innerHTML = "<span>Mode: Normal Happy Path. Click button to submit.</span>";
            }} else if (mode === '500') {{
                banner.className = "sim-status-banner status-fail";
                banner.innerHTML = "<span>Mode: Server will respond HTTP 500. Click to test state retention.</span>";
            }} else if (mode === 'spam') {{
                banner.className = "sim-status-banner status-idle";
                banner.innerHTML = "<span>Mode: Click button rapidly to test debounce protection.</span>";
            }}
        }}

        function handleSimSubmit() {{
            const banner = document.getElementById("simStatus");
            const email = document.getElementById("simEmail").value;
            const btn = document.getElementById("simSubmitBtn");

            if (activeSimMode === 'happy') {{
                btn.disabled = true;
                btn.textContent = "Authenticating...";
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "Signed In";
                    banner.className = "sim-status-banner status-ok";
                    banner.innerHTML = "<span>HTTP 200 OK: Authentication successful. Token issued.</span>";
                }}, 400);
            }} else if (activeSimMode === '500') {{
                btn.disabled = true;
                btn.textContent = "Connecting...";
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "Sign In to Dashboard";
                    banner.className = "sim-status-banner status-fail";
                    banner.innerHTML = "<span>HTTP 500: Server crashed. Notice: email '" + email + "' was preserved.</span>";
                }}, 400);
            }} else if (activeSimMode === 'spam') {{
                spamCount++;
                if (spamCount === 1) {{
                    banner.className = "sim-status-banner status-ok";
                    banner.innerHTML = "<span>Request 1 dispatched. Debounce lock engaged for 400ms.</span>";
                    setTimeout(() => {{
                        spamCount = 0;
                    }}, 400);
                }} else {{
                    banner.className = "sim-status-banner status-ok";
                    banner.innerHTML = "<span>Duplicate click blocked. Total prevented mutations: " + (spamCount - 1) + ".</span>";
                }}
            }}
        }}

        function scrollToResults() {{
            const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            document.getElementById("models").scrollIntoView({{ behavior: smooth ? "smooth" : "auto" }});
        }}

        function copyCliCmd() {{
            const btn = document.getElementById("copyCliBtn");
            navigator.clipboard.writeText("uv run realitybench pilot").then(() => {{
                btn.textContent = "Copied";
                setTimeout(() => {{ btn.textContent = "Copy CLI command"; }}, 1500);
            }});
        }}
    </script>
</body>
</html>"""
    return html


def generate_and_open_dashboard(open_browser: bool = True) -> str:
    data, dataset_label = load_dataset()
    html = build_dashboard_html(data, dataset_label)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[Dashboard] Generated: {OUTPUT_HTML}")
    if open_browser:
        webbrowser.open(f"file://{OUTPUT_HTML}")
    return OUTPUT_HTML


if __name__ == "__main__":
    generate_and_open_dashboard(open_browser=False)
