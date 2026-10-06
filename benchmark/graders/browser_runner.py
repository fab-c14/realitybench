"""
RealityBench Browser Test Harness
Executes generated web applications in headless Chromium with deterministic network mocking.
"""

import re
import time
from typing import Any

from playwright.sync_api import Browser, Page, Playwright, sync_playwright


def extract_html_code(raw_response: str) -> str:
    """
    Extracts HTML/CSS/JS code from model response, stripping markdown fences if present.
    """
    text = raw_response.strip()
    
    # Try finding ```html ... ``` block
    html_match = re.search(r"```html\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if html_match:
        return html_match.group(1).strip()
    
    # Try generic code block ``` ... ```
    code_match = re.search(r"```[a-zA-Z]*\s*(.*?)\s*```", text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    
    return text


def ensure_full_html_document(content: str) -> str:
    """
    Wraps snippets in a valid HTML5 document if not already a full document.
    """
    if "<!DOCTYPE html>" in content or "<html" in content.lower():
        return content
    
    # If it's pure JavaScript
    if content.strip().startswith("function") or content.strip().startswith("class") or "document.createElement" in content:
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>RealityBench App</title></head>
<body>
<div id="app"></div>
<script>
{content}
</script>
</body>
</html>"""

    # Otherwise wrap as HTML body
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RealityBench App</title>
</head>
<body>
{content}
</body>
</html>"""


class BrowserSession:
    """
    Controlled single-page execution environment for a test case.
    """
    def __init__(self, page: Page):
        self.page = page
        self.intercepted_requests: list[dict[str, Any]] = []

    def load_html(self, html_code: str, viewport: dict[str, int] = None):
        """Loads HTML content into page with optional viewport."""
        if viewport:
            self.page.set_viewport_size(viewport)
        else:
            self.page.set_viewport_size({"width": 1280, "height": 800})
            
        full_doc = ensure_full_html_document(html_code)
        # Inject base tag so relative fetch calls (/api/...) resolve to http://realitybench.test/
        if "<head" in full_doc.lower():
            full_doc = re.sub(r"(<head[^>]*>)", r'\1<base href="http://realitybench.test/">', full_doc, count=1, flags=re.IGNORECASE)
        else:
            full_doc = '<base href="http://realitybench.test/">\n' + full_doc
            
        self.page.set_content(full_doc, wait_until="domcontentloaded")
        self.page.wait_for_timeout(100)

    def mock_route(self, url_pattern: str, status: int = 200, json_body: Any = None, delay_ms: int = 0):
        """
        Mocks network responses for a specified URL pattern.
        Records every incoming request payload.
        """
        def handle_route(route):
            request = route.request
            body = None
            try:
                body = request.post_data_json
            except Exception:
                try:
                    body = request.post_data
                except Exception:
                    try:
                        raw = request.post_data_buffer
                        body = f"<binary_data: {len(raw)} bytes>" if raw else None
                    except Exception:
                        body = "<binary_payload>"
            
            self.intercepted_requests.append({
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "post_data": body,
                "timestamp": time.time(),
            })

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

            import json
            body_bytes = json.dumps(json_body) if json_body is not None else ""
            route.fulfill(
                status=status,
                headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                body=body_bytes,
            )

        self.page.route(url_pattern, handle_route)


class HeadlessHarness:
    """
    Context manager for Playwright browser instance across tests.
    """
    def __init__(self):
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def new_session(self) -> BrowserSession:
        context = self.browser.new_context()
        page = context.new_page()
        return BrowserSession(page)
