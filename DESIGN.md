# RealityBench Design System: Declassified Blueprints & High-Density Empirical UI

> Single Source of Truth for Google Stitch and Frontend Generation  
> Aligned with Anti-Slop Design Engineering & Stitch Semantic Design System Standards

---

## 1. Visual Atmosphere & Philosophy

- **Density Dial:** `5 / 10` (Technical Balance — dense data without claustrophobia)
- **Variance Dial:** `7 / 10` (Asymmetric Structure — offset layout, split-screen hero, varied metric cells)
- **Motion Dial:** `6 / 10` (Tactile Precision — swift spring transitions, active button compressions, no infinite floating fluff)

The visual tone is **"Declassified Research Laboratory"**: Swiss typographic rigor meets mission-critical aerospace instrumentation. It communicates absolute scientific authority, mathematical determinism, and zero tolerance for superficial "vibe-coding" fluff. Every pixel, border, and metric exists to expose the empirical delta between surface demonstration and production resilience.

---

## 2. Calibrated Color Palette

Strict rule: Single functional accent. Saturation capped below 80%. Banned: AI-purple gradients, blurry dark mesh glows, neon button halos.

| Token | Name | Hex | Functional Role |
| :--- | :--- | :--- | :--- |
| `color-bg-base` | Zinc Obsidian | `#09090b` | Global canvas background |
| `color-bg-surface` | Zinc Slate | `#121215` | Section layers, container panels |
| `color-bg-elevated` | Zinc Carbon | `#18181b` | Cards, popovers, table headers |
| `color-bg-subtle` | Zinc Graphite | `#27272a` | Hover states, tab pills, inactive controls |
| `color-border-subtle` | Zinc Stroke Low | `#27272a` | Baseline grid dividers, subtle separations |
| `color-border-strong` | Zinc Stroke High | `#3f3f46` | Active borders, input boundaries, focus rings |
| `color-text-primary` | Pure Crisp | `#fafafa` | Primary headlines, scores, key metrics |
| `color-text-secondary`| Muted Tech | `#a1a1aa` | Labels, categories, documentation body |
| `color-text-tertiary` | Dim Ghost | `#71717a` | Metadata, timestamps, helper annotations |
| `color-accent-blue` | Electric Cobalt | `#2563eb` | Regime A (Demo Score), primary actions |
| `color-accent-emerald`| Cyber Emerald | `#10b981` | Regime B (Reality Score), verified assertions |
| `color-accent-crimson`| Alert Crimson | `#ef4444` | Reality Gap indicators, failure telemetry |
| `color-accent-amber`  | Caution Amber | `#f59e0b` | Moderate fragility warnings |

---

## 3. Typographic Architecture

Typography is strictly sans-serif paired with precision monospace. Generic defaults (`Inter`, `Times New Roman`, `Georgia`, `Fraunces`) are strictly prohibited.

- **Primary Display & Interface:** `Geist Sans`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`
  - Headlines: `tracking-tight`, `leading-[1.1]`, font weight `600` to `800`.
  - Body: `leading-relaxed`, max line length `65ch`, font weight `400` to `500`.
- **Numerical & Code Telemetry:** `Geist Mono`, `JetBrains Mono`, `ui-monospace`, `monospace`
  - Applied to all scores, percentages, timestamps, task IDs, and code blocks.
  - Number tabular lining: `font-feature-settings: "tnum" 1, "zero" 1`.

---

## 4. Layout & Section Geometry

1. **Anti-Center Bias:** The hero section is strictly asymmetric (50/50 split or left-aligned typography with right-aligned live telemetry panel). Centered heroes with giant floating text are banned.
2. **Asymmetric Technical Bento:** Feature and metric grids use varied cell weights (e.g. 2-column wide scoreboard, 1-column gauge sidebar, asymmetrical failure distribution chart). Symmetrical 3-card repeating rows are banned.
3. **Viewport Discipline:** Maximum page width container `1440px` with responsive margin padding. Full-height hero uses `min-h-[100dvh]` (never `h-screen`).
4. **Mobile Collapse:** Fluidly collapses to single-column at `< 768px`. Zero horizontal scroll overflow across all viewports down to `375px`.

---

## 5. Component Specifications

### A. Action Buttons & Controls
- **Geometry:** Border radius `8px` (`rounded-lg`), height `40px` (desktop), padding `0 16px`.
- **States:**
  - Default: `bg-zinc-900 border border-zinc-700 text-zinc-100 hover:border-zinc-500 hover:bg-zinc-800`
  - Primary CTA: `bg-blue-600 hover:bg-blue-500 text-white font-medium border border-blue-500 shadow-sm`
  - Active Click: Tactile push via `transform: scale(0.98) translateY(1px)` with `transition: 80ms ease-out`.
  - Banned: Infinite glowing drop-shadows or multi-color gradients.

### B. Metric & KPI Panels
- **Structure:** Crisp `1px solid var(--color-border-subtle)` container. Top eyebrow label in small uppercase monospace (`11px`, tracking `0.08em`).
- **Score Readout:** Large `36px` monospace numeral with contextual status badge (Production Ready vs. High Fragility Trap).
- **Sub-Metric Sparklines & Gauges:** Visual horizontal indicator showing the split between Demo Score (Blue) and Reality Score (Emerald), highlighting the Reality Gap.

### C. Task Performance Matrix
- **Header:** Sticky table header with monospace column titles and model tags.
- **Rows:** Hover-highlighted table row with direct click-to-expand assertion inspector.
- **Badges:** Fixed-width pill badges showing exact reality percentage and signed Gap badge (`+67%` in crimson, `0%` in emerald).

### D. Assertion Inspector Drawer
- Slide-over or modal drawer displaying the actual headless Chromium test trace:
  - Happy Path test results (Functional correctness, expected interactions).
  - Controlled perturbation results (HTTP 500 error, debounce, whitespace, mobile viewport, keyboard).
  - Code preview tab with syntax highlighting showing the model's generated HTML artifact.

---

## 6. Motion & Interaction Engine

- **Transitions:** Swift micro-transitions (`120ms` to `200ms`) using spring curve `cubic-bezier(0.16, 1, 0.3, 1)`.
- **List Orchestration:** Staggered cascade reveal for rows and cards on initial render (`30ms` per item).
- **Tab Switching:** Instant content swap with smooth cross-fade (`opacity: 0 -> 1` over `150ms`).
- **Hover Micro-Interactions:** Subtle border lightening and `translateY(-1px)` elevation.

---

## 7. Explicit Anti-Patterns (Banned AI Tells)

1. **NO Emojis:** Replace all emojis with crisp, semantic, monochrome inline SVG glyphs.
2. **NO AI-Purple/Neon Glows:** No purple-to-cyan gradients, no glowing buttons.
3. **NO Generic 3-Card Rows:** No template marketing layouts.
4. **NO Vague "Vibe" Scoring:** All metrics must display exact percentages, assertion counts, and test names.
5. **NO Centered Hero Over Dark Mesh:** Strictly asymmetrical, left-aligned layout with technical telemetry.
6. **NO Wrapped CTAs:** Primary button labels must stay on one line across all desktop resolutions.
