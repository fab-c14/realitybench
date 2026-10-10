"""
Render results/dashboard.html in headless Chromium: desktop + mobile screenshots
and a list of elements that overflow the 375px mobile viewport.

Usage:
    uv run python scripts/check_dashboard.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "results" / "dashboard.html"
SHOTS = ROOT / "results" / "screenshots"

OVERFLOW_JS = """() => {
  const w = window.innerWidth;
  const out = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > w + 1) {
      out.push(el.tagName + '.' + el.className + ' right=' + Math.round(r.right));
    }
  });
  return out.slice(0, 15);
}"""


def main() -> None:
    url = DASHBOARD.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        desktop = browser.new_page(viewport={"width": 1280, "height": 800})
        desktop.goto(url)
        desktop.wait_for_timeout(500)
        desktop.screenshot(path=str(SHOTS / "dashboard_preview.png"), full_page=True)

        mobile = browser.new_page(viewport={"width": 375, "height": 800})
        mobile.goto(url)
        mobile.wait_for_timeout(300)
        mobile.screenshot(path=str(SHOTS / "dashboard_mobile.png"), full_page=True)
        overflow = mobile.evaluate(OVERFLOW_JS)
        browser.close()

    print("mobile overflow:", "none" if not overflow else "")
    for line in overflow:
        print("  ", line)


if __name__ == "__main__":
    main()
