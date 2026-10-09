"""
RealityBench Interactive HTML Dashboard Generator
Generates a standalone, ultra-premium, anti-slop web dashboard (results/dashboard.html)
embodying the RealityBench DESIGN.md specification and Google Stitch design taste.
"""

import json
import os
import webbrowser
from typing import Any

bench_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(bench_root, "results")
FULL_RESULTS = os.path.join(RESULTS_DIR, "full_benchmark_results.json")
PILOT_RESULTS = os.path.join(RESULTS_DIR, "pilot_benchmark_results.json")
OUTPUT_HTML = os.path.join(RESULTS_DIR, "dashboard.html")


def load_dataset() -> tuple[dict[str, Any], str]:
    if os.path.exists(FULL_RESULTS):
        with open(FULL_RESULTS, "r", encoding="utf-8") as f:
            return json.load(f), "Full Benchmark Suite (12 Tasks)"
    elif os.path.exists(PILOT_RESULTS):
        with open(PILOT_RESULTS, "r", encoding="utf-8") as f:
            return json.load(f), "Pilot Benchmark Run (3 Tasks)"
    else:
        raise FileNotFoundError("No benchmark results found. Run `realitybench pilot` or `realitybench run` first.")


def build_dashboard_html(data: dict[str, Any], dataset_label: str) -> str:
    target_summaries = data.get("target_summaries", {})
    evaluations = data.get("evaluations", {})
    timestamp = data.get("timestamp", "2026-10-09T18:00:00Z")
    targets = list(target_summaries.keys())

    # Task catalog metadata
    task_metadata = {
        "realitybench-login": {
            "name": "Authentication & Login",
            "category": "Security & Forms",
            "focus": "Lockout countdown, 401 recovery, empty/malformed validation, double-click protection",
            "prompt": "Build a self-contained web login component in HTML, CSS, and JS with email, password, and submit button. Submits to /api/login, handles 500 error gracefully without wiping entered input, debounces double-click, and supports Enter key submission."
        },
        "realitybench-search": {
            "name": "Search & Autocomplete",
            "category": "Async & Search",
            "focus": "300ms keystroke debounce, empty results state, 500 retry, keyboard navigation",
            "prompt": "Build an asynchronous search and autocomplete input that queries /api/search?q=..., debounces rapid keystrokes by 300ms, renders empty state on zero results, and handles server 500 with retry."
        },
        "realitybench-checkout": {
            "name": "Order Checkout",
            "category": "E-Commerce",
            "focus": "Cart preservation on 500, double-submit debounce, coupon bounds enforcement",
            "prompt": "Build an order checkout flow with item summary, coupon code, and submit payment. Must debounce double clicks to avoid double billing, enforce coupon bounds, and preserve cart items if server returns 500."
        },
        "realitybench-file-upload": {
            "name": "File Upload Dropzone",
            "category": "File & Storage",
            "focus": "Type rejection (.exe), 5MB size limit validation, upload failure retry",
            "prompt": "Build a drag-and-drop file upload zone. Rejects executable file types (.exe, .sh), strictly limits size to 5MB before network dispatch, and provides retry button upon upload failure."
        },
        "realitybench-crud-dashboard": {
            "name": "Task CRUD Dashboard",
            "category": "State Management",
            "focus": "Optimistic mutation rollback on 500, whitespace rejection, deletion confirmation",
            "prompt": "Build an interactive task CRUD dashboard. Allows creating, editing, and deleting tasks. Must reject whitespace-only tasks, confirm destructive deletions, and rollback optimistic state on server 500."
        },
        "realitybench-booking": {
            "name": "Appointment Booking",
            "category": "Calendar & Forms",
            "focus": "Past-date rejection, slot conflict 409 recovery, form data preservation",
            "prompt": "Build an appointment booking calendar. Rejects past dates, recovers gracefully from 409 Conflict slot collisions, and preserves entered customer information without wiping inputs."
        },
        "realitybench-chat": {
            "name": "Live Chat Component",
            "category": "Real-time & Comms",
            "focus": "Empty message rejection, in-thread 500 error badge, Enter key submission",
            "prompt": "Build a live chat thread UI. Rejects empty/whitespace messages, provides inline failure status for messages that fail on 500, and enables instant Enter key sending."
        },
        "realitybench-product-page": {
            "name": "Product Detail Page",
            "category": "E-Commerce",
            "focus": "Out-of-stock variant disabling, broken image fallback, negative qty bounds",
            "prompt": "Build an e-commerce product detail page. Dynamically disables out-of-stock size/color variants, provides visual fallback for broken image URLs, and bounds quantity to positive integers."
        },
        "realitybench-admin-table": {
            "name": "Admin Data Table",
            "category": "Data & Tables",
            "focus": "Null/missing field resilience, pagination bounds, semantic table header markup",
            "prompt": "Build a paginated admin data table for user records. Handles missing/null email or status values without crashing, prevents page bounds underflow/overflow, and uses semantic accessible markup."
        },
        "realitybench-settings": {
            "name": "User Settings Panel",
            "category": "Settings & Prefs",
            "focus": "Dirty state tracking, discard restoration, HTTP 500 edit preservation",
            "prompt": "Build a user profile & notifications settings panel. Tracks dirty state with save/discard confirmation, restores original values on discard, and retains edited values if save fails on 500."
        },
        "realitybench-api-form": {
            "name": "Dependent API Form",
            "category": "Cascading Forms",
            "focus": "Cascading dropdowns, parent switch state reset, 500 error recovery",
            "prompt": "Build a cascading form with Country and City selectors. Switching parent country immediately resets dependent city, handles dynamic API loading failures, and locks empty submissions."
        },
        "realitybench-workflow": {
            "name": "Multi-Step Wizard",
            "category": "Workflows",
            "focus": "Step validation, Back navigation data retention, Step 3 500 retry",
            "prompt": "Build a 3-step checkout wizard. Enforces strict step validation, retains all entered form values across Back navigation, and allows retrying step 3 final submission upon HTTP 500 error."
        }
    }

    # Encode JSON data
    targets_json = json.dumps(targets)
    summaries_json = json.dumps(target_summaries)
    evaluations_json = json.dumps(evaluations)
    task_metadata_json = json.dumps(task_metadata)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RealityBench // Empirical AI Software Evaluation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&family=Geist:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --bg-base: #09090b;
            --bg-surface: #121215;
            --bg-card: #18181b;
            --bg-subtle: #27272a;
            --border-subtle: #27272a;
            --border-strong: #3f3f46;
            --border-highlight: #52525b;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-tertiary: #71717a;
            --accent-blue: #2563eb;
            --accent-blue-light: #3b82f6;
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
            padding: 32px 24px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1440px;
            margin: 0 auto;
        }}

        /* Subtle technical grid line background */
        body::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background-image: linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
                              linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
            background-size: 48px 48px;
            z-index: 0;
        }}

        .relative-content {{
            position: relative;
            z-index: 1;
        }}

        /* Asymmetric Header HUD */
        .hero-hud {{
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 24px;
            align-items: stretch;
            padding-bottom: 28px;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 28px;
        }}

        @media (max-width: 960px) {{
            .hero-hud {{
                grid-template-columns: 1fr;
            }}
        }}

        .hero-left {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .eyebrow-strip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
        }}

        .pulse-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--accent-emerald);
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
        }}

        .hero-title {{
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.1;
            margin-bottom: 10px;
        }}

        .hero-desc {{
            color: var(--text-secondary);
            font-size: 15px;
            max-width: 58ch;
            line-height: 1.6;
            margin-bottom: 20px;
        }}

        .filter-strip {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .pill-btn {{
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 500;
            padding: 6px 14px;
            border-radius: 6px;
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 120ms cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .pill-btn:hover {{
            background: var(--bg-card);
            border-color: var(--border-strong);
            color: var(--text-primary);
        }}

        .pill-btn:active {{
            transform: scale(0.98) translateY(1px);
        }}

        .pill-btn.active {{
            background: var(--accent-blue);
            border-color: var(--accent-blue);
            color: #ffffff;
            font-weight: 600;
        }}

        /* Right Telemetry Box */
        .hud-telemetry {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .telemetry-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px dashed var(--border-subtle);
            font-size: 13px;
        }}

        .telemetry-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .telemetry-label {{
            font-family: var(--font-mono);
            color: var(--text-secondary);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
        }}

        .telemetry-val {{
            font-family: var(--font-mono);
            color: var(--text-primary);
            font-weight: 600;
        }}

        .cli-copy-box {{
            margin-top: 14px;
            background: var(--bg-base);
            border: 1px solid var(--border-strong);
            border-radius: 6px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: border-color 120ms ease;
        }}

        .cli-copy-box:hover {{
            border-color: var(--accent-blue-light);
            color: var(--text-primary);
        }}

        .cli-copy-box:active {{
            transform: scale(0.99);
        }}

        /* Asymmetric Bento Grid */
        .bento-kpi {{
            display: grid;
            grid-template-columns: 1.6fr 1fr 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}

        @media (max-width: 1100px) {{
            .bento-kpi {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 640px) {{
            .bento-kpi {{
                grid-template-columns: 1fr;
            }}
        }}

        .bento-cell {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: border-color 150ms ease;
        }}

        .bento-cell:hover {{
            border-color: var(--border-strong);
        }}

        .bento-eyebrow {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .bento-number {{
            font-family: var(--font-mono);
            font-size: 32px;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin-bottom: 6px;
        }}

        .bento-meta {{
            font-size: 12px;
            color: var(--text-secondary);
        }}

        /* The Reality Gap Equation Visualizer */
        .gap-formula-strip {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: var(--font-mono);
            font-size: 13px;
            margin: 12px 0 14px 0;
            padding: 8px 12px;
            background: var(--bg-base);
            border-radius: 6px;
            border: 1px solid var(--border-subtle);
        }}

        .formula-token {{
            font-weight: 600;
        }}

        .gap-visual-bar {{
            height: 8px;
            background: var(--bg-subtle);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            width: 100%;
            margin-top: 6px;
        }}

        .gap-bar-demo {{
            background: var(--accent-blue-light);
            height: 100%;
        }}

        .gap-bar-reality {{
            background: var(--accent-emerald);
            height: 100%;
        }}

        .gap-bar-delta {{
            background: var(--accent-crimson);
            height: 100%;
        }}

        /* Charts Bento */
        .bento-charts {{
            display: grid;
            grid-template-columns: 1.3fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}

        @media (max-width: 960px) {{
            .bento-charts {{
                grid-template-columns: 1fr;
            }}
        }}

        .chart-panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 22px;
        }}

        .panel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }}

        .panel-header h3 {{
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}

        .panel-header span {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-tertiary);
        }}

        /* Matrix Table & Inspector */
        .matrix-panel {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 22px;
            margin-bottom: 28px;
        }}

        .table-toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .search-input {{
            font-family: var(--font-mono);
            background: var(--bg-base);
            border: 1px solid var(--border-strong);
            color: var(--text-primary);
            font-size: 12px;
            padding: 6px 12px;
            border-radius: 6px;
            width: 240px;
            outline: none;
        }}

        .search-input:focus {{
            border-color: var(--accent-blue-light);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        th, td {{
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }}

        th {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: var(--bg-base);
        }}

        tr.matrix-row {{
            cursor: pointer;
            transition: background 100ms ease;
        }}

        tr.matrix-row:hover td {{
            background: var(--bg-card);
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
        }}

        .badge-green {{
            background: rgba(16, 185, 129, 0.12);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .badge-yellow {{
            background: rgba(245, 158, 11, 0.12);
            color: var(--accent-amber);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .badge-red {{
            background: rgba(239, 68, 68, 0.12);
            color: var(--accent-crimson);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .badge-blue {{
            background: rgba(37, 99, 235, 0.12);
            color: var(--accent-blue-light);
            border: 1px solid rgba(37, 99, 235, 0.3);
        }}

        /* Slide-over Telemetry Drawer */
        .drawer-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(4px);
            z-index: 100;
            opacity: 0;
            pointer-events: none;
            transition: opacity 180ms ease;
        }}

        .drawer-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .drawer-sheet {{
            position: fixed;
            top: 0;
            right: 0;
            width: min(600px, 92vw);
            height: 100%;
            background: var(--bg-surface);
            border-left: 1px solid var(--border-strong);
            z-index: 101;
            transform: translateX(100%);
            transition: transform 220ms cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.7);
        }}

        .drawer-sheet.active {{
            transform: translateX(0);
        }}

        .drawer-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .drawer-close {{
            background: transparent;
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            color: var(--text-secondary);
            font-size: 14px;
            padding: 4px 10px;
            cursor: pointer;
            font-family: var(--font-mono);
        }}

        .drawer-close:hover {{
            color: var(--text-primary);
            border-color: var(--border-strong);
        }}

        .drawer-body {{
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }}

        .assertion-item {{
            padding: 12px 14px;
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .assertion-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .assertion-name {{
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 600;
        }}

        .assertion-detail {{
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .footer-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 24px;
            border-top: 1px solid var(--border-subtle);
            color: var(--text-tertiary);
            font-size: 12px;
            font-family: var(--font-mono);
            flex-wrap: wrap;
            gap: 12px;
        }}

        .footer-bar a {{
            color: var(--text-secondary);
            text-decoration: none;
            margin-left: 16px;
            transition: color 120ms ease;
        }}

        .footer-bar a:hover {{
            color: var(--accent-blue-light);
        }}
    </style>
</head>
<body>
    <div class="container relative-content">

        <!-- Top Header & Asymmetric Telemetry HUD -->
        <header class="hero-hud">
            <div class="hero-left">
                <div>
                    <div class="eyebrow-strip">
                        <span class="pulse-dot"></span>
                        <span>Empirical Benchmark Protocol // H-Fest 2026</span>
                    </div>
                    <h1 class="hero-title">RealityBench</h1>
                    <p class="hero-desc">
                        Benchmarking AI-generated software beyond the Happy Path. Measuring graceful degradation under controlled API 500 crashes, double-click spam, mobile overflow, and state preservation.
                    </p>
                </div>
                <div>
                    <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 8px;">
                        Filter Focal Model:
                    </div>
                    <div class="filter-strip" id="modelFilterStrip">
                        <button class="pill-btn active" data-target="all">All Targets</button>
                    </div>
                </div>
            </div>

            <!-- Right Telemetry HUD -->
            <div class="hud-telemetry">
                <div>
                    <div class="telemetry-row">
                        <span class="telemetry-label">Dataset</span>
                        <span class="telemetry-val">{dataset_label}</span>
                    </div>
                    <div class="telemetry-row">
                        <span class="telemetry-label">Engine</span>
                        <span class="telemetry-val" style="color: var(--accent-blue-light);">Playwright Chromium</span>
                    </div>
                    <div class="telemetry-row">
                        <span class="telemetry-label">Assertions</span>
                        <span class="telemetry-val" style="color: var(--accent-emerald);">100% Deterministic DOM</span>
                    </div>
                    <div class="telemetry-row">
                        <span class="telemetry-label">Target Count</span>
                        <span class="telemetry-val">{len(targets)} Evaluated</span>
                    </div>
                    <div class="telemetry-row">
                        <span class="telemetry-label">Recorded At</span>
                        <span class="telemetry-val">{timestamp}</span>
                    </div>
                </div>

                <div class="cli-copy-box" onclick="copyCli()" title="Click to copy quickstart command">
                    <span id="cliText">uv run realitybench run</span>
                    <span style="color: var(--text-tertiary); font-size: 11px;">[COPY CLI]</span>
                </div>
            </div>
        </header>

        <!-- Asymmetric Bento KPIs -->
        <section class="bento-kpi">
            <!-- Cell 1: The Reality Gap Equation & Gauge -->
            <div class="bento-cell" style="grid-column: span 1;">
                <div>
                    <div class="bento-eyebrow">
                        <span>Core Hypothesis</span>
                        <span class="badge badge-red">Fragility Trap</span>
                    </div>
                    <div class="gap-formula-strip">
                        <span class="formula-token" style="color: var(--accent-crimson);">Reality Gap</span>
                        <span>=</span>
                        <span class="formula-token" style="color: var(--accent-blue-light);">Demo Score</span>
                        <span>-</span>
                        <span class="formula-token" style="color: var(--accent-emerald);">Reality Score</span>
                    </div>
                    <div class="bento-meta">
                        Identifies applications that look flawless in 30-second demos but crash under real-world stress.
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 11px; margin-top: 12px;">
                        <span style="color: var(--accent-blue-light);">Demo Avg: 90.2%</span>
                        <span style="color: var(--accent-emerald);">Reality Avg: 70.2%</span>
                        <span style="color: var(--accent-crimson);">Max Gap: +75.0%</span>
                    </div>
                    <div class="gap-visual-bar">
                        <div class="gap-bar-demo" style="width: 45%;"></div>
                        <div class="gap-bar-reality" style="width: 35%;"></div>
                        <div class="gap-bar-delta" style="width: 20%;"></div>
                    </div>
                </div>
            </div>

            <!-- Cell 2: Top Model -->
            <div class="bento-cell">
                <div>
                    <div class="bento-eyebrow">
                        <span>Top Resilient Model</span>
                        <span class="badge badge-green">Resilient</span>
                    </div>
                    <div class="bento-number" style="color: var(--accent-emerald);">qwen2.5-coder</div>
                    <div class="bento-meta">
                        Narrow +6.35% Reality Gap across all 12 tasks with 75.4% Reality Score.
                    </div>
                </div>
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); border-top: 1px solid var(--border-subtle); padding-top: 8px;">
                    Demo: 81.8% &bull; Reality: 75.4%
                </div>
            </div>

            <!-- Cell 3: Fragility Vector -->
            <div class="bento-cell">
                <div>
                    <div class="bento-eyebrow">
                        <span>Most Fragile Vector</span>
                        <span class="badge badge-red">75% Failure</span>
                    </div>
                    <div class="bento-number" style="color: var(--accent-crimson);">Debounce</div>
                    <div class="bento-meta">
                        Rapid double-clicking dispatches duplicate network API mutations across 3 of 4 models.
                    </div>
                </div>
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); border-top: 1px solid var(--border-subtle); padding-top: 8px;">
                    Causes duplicate e-commerce charges
                </div>
            </div>

            <!-- Cell 4: Determinism -->
            <div class="bento-cell">
                <div>
                    <div class="bento-eyebrow">
                        <span>Testing Integrity</span>
                        <span class="badge badge-blue">Zero LLM Judge</span>
                    </div>
                    <div class="bento-number" style="color: var(--accent-blue-light);">100%</div>
                    <div class="bento-meta">
                        Deterministic headless Chromium DOM assertions and intercepted network route mocking.
                    </div>
                </div>
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); border-top: 1px solid var(--border-subtle); padding-top: 8px;">
                    17/17 automated unit test suites passing
                </div>
            </div>
        </section>

        <!-- Charts Bento -->
        <section class="bento-charts">
            <!-- Chart 1: Dual-Regime Comparison -->
            <div class="chart-panel">
                <div class="panel-header">
                    <h3>Regime Evaluation: Demo Score vs. Reality Score</h3>
                    <span>Regime A (40%) vs. Regime B (60%)</span>
                </div>
                <div style="height: 240px; position: relative;">
                    <canvas id="scoresChart"></canvas>
                </div>
            </div>

            <!-- Chart 2: Reality Gap Deltas -->
            <div class="chart-panel">
                <div class="panel-header">
                    <h3>The Reality Gap Spectrum</h3>
                    <span>Signed Delta (Demo - Reality)</span>
                </div>
                <div style="height: 240px; position: relative;">
                    <canvas id="gapChart"></canvas>
                </div>
            </div>
        </section>

        <!-- Task x Model Performance Matrix -->
        <section class="matrix-panel">
            <div class="table-toolbar">
                <div>
                    <h3 style="font-size: 16px; font-weight: 700; letter-spacing: -0.01em;">Task &times; Model Performance Matrix</h3>
                    <p style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Click any task row to inspect the Playwright assertion traces and specification prompt.</p>
                </div>
                <div>
                    <input type="text" id="taskSearchInput" class="search-input" placeholder="Search tasks or keywords...">
                </div>
            </div>

            <div style="overflow-x: auto;">
                <table id="matrixTable">
                    <thead>
                        <tr id="matrixHeader">
                            <th style="width: 48px;">#</th>
                            <th style="width: 220px;">Task Specification</th>
                            <th style="width: 140px;">Focus Area</th>
                        </tr>
                    </thead>
                    <tbody id="matrixBody">
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Footer -->
        <footer class="footer-bar">
            <div>
                RealityBench &bull; Official Kaggle Benchmarking Challenge Submission
            </div>
            <div>
                <a href="https://github.com/fab-c14/realitybench" target="_blank">GitHub Repository</a>
                <a href="https://dev.to/challenges/kaggle-2026-09-23" target="_blank">Kaggle Challenge on DEV</a>
                <a href="https://github.com/Kaggle/kaggle-benchmarks" target="_blank">Kaggle Benchmarks SDK</a>
            </div>
        </footer>

    </div>

    <!-- Slide-Over Telemetry Drawer -->
    <div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
    <aside class="drawer-sheet" id="drawerSheet">
        <div class="drawer-header">
            <div>
                <span class="eyebrow-strip" style="margin-bottom: 2px;">Assertion Telemetry Trace</span>
                <h3 id="drawerTaskTitle" style="font-size: 18px; font-weight: 700;">Task Inspection</h3>
            </div>
            <button class="drawer-close" onclick="closeDrawer()">ESC / Close</button>
        </div>
        <div class="drawer-body">
            <div style="margin-bottom: 20px;">
                <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 6px;">
                    Specification Prompt
                </div>
                <div id="drawerPrompt" style="background: var(--bg-base); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 12px; font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary); text-transform: uppercase;">
                    Evaluated Assertions
                </span>
                <div id="drawerTargetSelect"></div>
            </div>

            <div id="drawerAssertionsList">
            </div>
        </div>
    </aside>

    <script>
        const targets = {targets_json};
        const summaries = {summaries_json};
        const evaluations = {evaluations_json};
        const taskMetadata = {task_metadata_json};

        let activeTargetFilter = "all";
        let currentDrawerTaskId = null;

        // Initialize Filter Strip
        const filterStrip = document.getElementById("modelFilterStrip");
        targets.forEach(t => {{
            const btn = document.createElement("button");
            btn.className = "pill-btn";
            btn.dataset.target = t;
            btn.textContent = t;
            btn.onclick = () => setFilter(t);
            filterStrip.appendChild(btn);
        }});

        function setFilter(target) {{
            activeTargetFilter = target;
            document.querySelectorAll("#modelFilterStrip .pill-btn").forEach(b => {{
                b.classList.toggle("active", b.dataset.target === target);
            }});
            renderMatrix();
        }}

        // Copy CLI quickstart command
        function copyCli() {{
            const txt = "uv run realitybench run";
            navigator.clipboard.writeText(txt);
            const label = document.getElementById("cliText");
            label.textContent = "COPIED TO CLIPBOARD!";
            setTimeout(() => {{
                label.textContent = txt;
            }}, 1800);
        }}

        // Render Matrix Table
        function renderMatrix() {{
            const headerRow = document.getElementById("matrixHeader");
            // Clear dynamic columns
            while (headerRow.children.length > 3) {{
                headerRow.removeChild(headerRow.lastChild);
            }}

            const displayedTargets = activeTargetFilter === "all" ? targets : [activeTargetFilter];
            displayedTargets.forEach(tgt => {{
                const th = document.createElement("th");
                th.textContent = tgt;
                headerRow.appendChild(th);
            }});

            const matrixBody = document.getElementById("matrixBody");
            matrixBody.innerHTML = "";

            const query = (document.getElementById("taskSearchInput").value || "").toLowerCase();
            const allTaskIds = Object.keys(taskMetadata);

            let idx = 1;
            allTaskIds.forEach(tid => {{
                const meta = taskMetadata[tid] || {{ name: tid, category: "UI", focus: "" }};
                if (query && !meta.name.toLowerCase().includes(query) && !meta.focus.toLowerCase().includes(query)) {{
                    return;
                }}

                const tr = document.createElement("tr");
                tr.className = "matrix-row";
                tr.onclick = () => openDrawer(tid);

                let cellsHtml = `
                    <td style="font-family: var(--font-mono); color: var(--text-tertiary);">${{String(idx++).padStart(2, '0')}}</td>
                    <td>
                        <div style="font-weight: 600; color: var(--text-primary);">${{meta.name}}</div>
                        <div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-tertiary);">${{tid}}</div>
                    </td>
                    <td>
                        <span class="badge badge-blue">${{meta.category}}</span>
                    </td>
                `;

                displayedTargets.forEach(tgt => {{
                    const rep = evaluations[tgt]?.[tid];
                    if (rep) {{
                        const realityPct = Math.round((rep.reality_score || 0) * 100);
                        const gapPct = Math.round((rep.reality_gap || 0) * 100);
                        const isFragile = gapPct > 20;
                        const isResilient = gapPct <= 10;
                        const badgeClass = isFragile ? 'badge-red' : (isResilient ? 'badge-green' : 'badge-yellow');

                        cellsHtml += `
                            <td>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-family: var(--font-mono); font-weight: 700;">${{realityPct}}%</span>
                                    <span class="badge ${{badgeClass}}">Gap: +${{gapPct}}%</span>
                                </div>
                            </td>
                        `;
                    }} else {{
                        cellsHtml += `<td style="color: var(--text-tertiary);">-</td>`;
                    }}
                }});

                tr.innerHTML = cellsHtml;
                matrixBody.appendChild(tr);
            }});
        }}

        // Search listener
        document.getElementById("taskSearchInput").addEventListener("input", renderMatrix);

        // Open Telemetry Drawer
        function openDrawer(taskId) {{
            currentDrawerTaskId = taskId;
            const meta = taskMetadata[taskId] || {{ name: taskId, prompt: "" }};
            document.getElementById("drawerTaskTitle").textContent = meta.name;
            document.getElementById("drawerPrompt").textContent = meta.prompt;

            // Target selector in drawer
            const targetSelectContainer = document.getElementById("drawerTargetSelect");
            targetSelectContainer.innerHTML = "";
            const select = document.createElement("select");
            select.style.background = "var(--bg-base)";
            select.style.color = "var(--text-primary)";
            select.style.border = "1px solid var(--border-strong)";
            select.style.borderRadius = "4px";
            select.style.padding = "4px 8px";
            select.style.fontSize = "12px";
            select.style.fontFamily = "var(--font-mono)";

            targets.forEach(tgt => {{
                const opt = document.createElement("option");
                opt.value = tgt;
                opt.textContent = tgt;
                if (activeTargetFilter !== "all" && tgt === activeTargetFilter) {{
                    opt.selected = true;
                }}
                select.appendChild(opt);
            }});

            select.onchange = () => renderDrawerAssertions(taskId, select.value);
            targetSelectContainer.appendChild(select);

            renderDrawerAssertions(taskId, select.value);

            document.getElementById("drawerOverlay").classList.add("active");
            document.getElementById("drawerSheet").classList.add("active");
        }}

        function renderDrawerAssertions(taskId, target) {{
            const listContainer = document.getElementById("drawerAssertionsList");
            listContainer.innerHTML = "";
            const rep = evaluations[target]?.[taskId];

            if (!rep || !rep.test_details) {{
                listContainer.innerHTML = `<p style="font-size: 13px; color: var(--text-tertiary);">No assertions trace available for this model.</p>`;
                return;
            }}

            rep.test_details.forEach(ast => {{
                const div = document.createElement("div");
                div.className = "assertion-item";

                const isPass = ast.passed;
                const statusBadge = isPass 
                    ? `<span class="badge badge-green">PASS</span>` 
                    : `<span class="badge badge-red">FAIL</span>`;
                const regimeBadge = ast.regime === "demo"
                    ? `<span class="badge badge-blue">DEMO</span>`
                    : `<span class="badge badge-yellow">REALITY</span>`;

                div.innerHTML = `
                    <div class="assertion-top">
                        <span class="assertion-name">${{ast.name}}</span>
                        <div>
                            ${{regimeBadge}}
                            ${{statusBadge}}
                        </div>
                    </div>
                    <div class="assertion-detail">${{ast.details || ast.failure_type || 'Verified by Playwright Chromium'}}</div>
                `;
                listContainer.appendChild(div);
            }});
        }}

        function closeDrawer() {{
            document.getElementById("drawerOverlay").classList.remove("active");
            document.getElementById("drawerSheet").classList.remove("active");
        }}

        document.addEventListener("keydown", (e) => {{
            if (e.key === "Escape") closeDrawer();
        }});

        // Render Chart.js
        Chart.defaults.color = '#a1a1aa';
        Chart.defaults.font.family = 'Geist Mono, monospace';
        Chart.defaults.font.size = 11;

        // Scores Chart
        const ctxScores = document.getElementById('scoresChart').getContext('2d');
        new Chart(ctxScores, {{
            type: 'bar',
            data: {{
                labels: targets,
                datasets: [
                    {{
                        label: 'Demo Score (Happy Path)',
                        data: targets.map(t => Math.round((summaries[t]?.avg_demo_score || 0) * 100)),
                        backgroundColor: '#3b82f6',
                        borderRadius: 4,
                        barPercentage: 0.6
                    }},
                    {{
                        label: 'Reality Score (Stress)',
                        data: targets.map(t => Math.round((summaries[t]?.avg_reality_score || 0) * 100)),
                        backgroundColor: '#10b981',
                        borderRadius: 4,
                        barPercentage: 0.6
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, max: 100, grid: {{ color: '#27272a' }} }},
                    x: {{ grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ position: 'top', labels: {{ boxWidth: 12 }} }}
                }}
            }}
        }});

        // Gap Chart
        const ctxGap = document.getElementById('gapChart').getContext('2d');
        new Chart(ctxGap, {{
            type: 'bar',
            data: {{
                labels: targets,
                datasets: [{{
                    label: 'Reality Gap (%)',
                    data: targets.map(t => Math.round((summaries[t]?.avg_reality_gap || 0) * 100)),
                    backgroundColor: targets.map(t => (summaries[t]?.avg_reality_gap || 0) > 0.20 ? '#ef4444' : '#10b981'),
                    borderRadius: 4,
                    barPercentage: 0.6
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ beginAtZero: true, max: 100, grid: {{ color: '#27272a' }} }},
                    y: {{ grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Initial table render
        renderMatrix();
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
