# %%
"""
RealityBench - Pilot Task 2: Search Component
Evaluates generated web search software on Happy Path vs. Controlled Perturbations.
"""

import sys
import os
import json
from typing import Dict, Any

# Ensure realitybench package is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
bench_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

import kaggle_benchmarks as kbench
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code


SEARCH_TASK_PROMPT = """Build a self-contained web search component in HTML, CSS, and JavaScript.
The interface must contain:
1. A search text input field
2. A search button
3. A results container to display items
When a search is performed, the application should make a GET request to '/api/search?q={query}'.
The API responds with JSON: { 'results': [ { 'id': 1, 'title': '...', 'description': '...' } ] }.
When results are returned, display the list of item titles and descriptions.
The application should provide appropriate user feedback, validation, and handle states when searches cannot be completed."""

TASK_SPEC = SEARCH_TASK_PROMPT

SAMPLE_RESULTS = {
    "results": [
        {"id": 1, "title": "Design Principles", "description": "Fundamentals of robust interface engineering."},
        {"id": 2, "title": "State Machines", "description": "Managing deterministic UI state transitions."}
    ]
}

NAIVE_SEARCH_CODE = """
<!DOCTYPE html><html><body>
  <input type="text" id="q" placeholder="Search...">
  <button onclick="doSearch()">Search</button>
  <div id="results"></div>
  <script>
    function doSearch() {
      const q = document.getElementById('q').value;
      fetch('/api/search?q=' + encodeURIComponent(q))
        .then(r => r.json())
        .then(data => {
          let html = '';
          data.results.forEach(item => {
            html += '<div><h3>' + item.title + '</h3><p>' + item.description + '</p></div>';
          });
          document.getElementById('results').innerHTML = html;
        });
    }
  </script>
</body></html>
"""

ROBUST_SEARCH_CODE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
  <form id="search-form">
    <input type="search" id="q" name="q" required placeholder="Search...">
    <button type="submit" id="search-btn">Search</button>
  </form>
  <div id="status" role="status"></div>
  <div id="results"></div>
  <script>
    const form = document.getElementById('search-form');
    const btn = document.getElementById('search-btn');
    const status = document.getElementById('status');
    const results = document.getElementById('results');

    form.onsubmit = async (e) => {
      e.preventDefault();
      const q = document.getElementById('q').value.trim();
      if (!q) return;

      btn.disabled = true;
      status.innerText = 'Searching...';
      results.innerHTML = '';

      try {
        const res = await fetch('/api/search?q=' + encodeURIComponent(q));
        if (!res.ok) throw new Error('Search failed: ' + res.status);
        const data = await res.json();
        if (!data.results || data.results.length === 0) {
          status.innerText = 'No results found.';
        } else {
          status.innerText = 'Found ' + data.results.length + ' results.';
          results.innerHTML = data.results.map(r => '<div><h3>' + r.title + '</h3><p>' + r.description + '</p></div>').join('');
        }
      } catch (err) {
        status.innerText = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    };
  </script>
</body></html>
"""


def grade_search_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Search component across:
    Regime A (Happy Path / Demo Score) and Regime B (Controlled Perturbations / Reality Score).
    """
    results = []

    with HeadlessHarness() as harness:
        # -------------------------------------------------------------
        # REGIME A: HAPPY PATH (Demo Score)
        # -------------------------------------------------------------

        # Test A.1: Structural Elements
        session = harness.new_session()
        try:
            session.load_html(html_code)
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            btn_el = session.page.locator('button, input[type="submit"]').first
            
            has_elements = (input_el.count() > 0 and btn_el.count() > 0)
            results.append(TestResult(
                test_name="happy_path_render_elements",
                category="functional_correctness",
                regime="demo",
                passed=has_elements,
                details="Search input and search button rendered",
                failure_type="Functional failure: Missing search input or button" if not has_elements else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="happy_path_render_elements",
                category="functional_correctness",
                regime="demo",
                passed=False,
                details=str(e),
                failure_type="Functional failure: Crash on render"
            ))

        # Test A.2: Expected Interaction - Successful Search Flow
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=200, json_body=SAMPLE_RESULTS)
            session.load_html(html_code)
            
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            btn_el = session.page.locator('button, input[type="submit"]').first
            
            input_el.fill("principles")
            btn_el.click()
            session.page.wait_for_timeout(400)

            req_sent = len(session.intercepted_requests) > 0
            query_passed = False
            if req_sent:
                query_passed = "principles" in session.intercepted_requests[0]["url"]

            content_lower = session.page.content().lower()
            shows_results = "design principles" in content_lower and "robust interface" in content_lower

            passed = req_sent and query_passed and shows_results
            results.append(TestResult(
                test_name="happy_path_successful_search",
                category="expected_interactions",
                regime="demo",
                passed=passed,
                details=f"Request sent: {req_sent}, Query captured: {query_passed}, Results displayed: {shows_results}",
                failure_type="Expected interaction failure: Search results not rendered" if not passed else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="happy_path_successful_search",
                category="expected_interactions",
                regime="demo",
                passed=False,
                details=str(e),
                failure_type="Expected interaction failure: Crash during search execution"
            ))

        # -------------------------------------------------------------
        # REGIME B: REALITY PERTURBATIONS (Reality Score)
        # -------------------------------------------------------------

        # Test B.1: Input Robustness - Empty Query Handling
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=200, json_body=SAMPLE_RESULTS)
            session.load_html(html_code)
            btn_el = session.page.locator('button, input[type="submit"]').first
            btn_el.click()
            session.page.wait_for_timeout(300)

            # Robust search should not query backend with blank or whitespace query
            reqs = session.intercepted_requests
            blocked = (len(reqs) == 0 or (len(reqs) > 0 and "q=" in reqs[0]["url"] and not reqs[0]["url"].endswith("q=")))
            results.append(TestResult(
                test_name="input_empty_query_check",
                category="input_robustness",
                regime="reality",
                passed=blocked,
                details="Blank search suppressed before API dispatch",
                failure_type="Validation failure: Sent empty search query to API" if not blocked else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="input_empty_query_check",
                category="input_robustness",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Validation failure: Exception on empty query"
            ))

        # Test B.2: State Robustness - Empty Results Graceful Handling
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=200, json_body={"results": []})
            session.load_html(html_code)
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            btn_el = session.page.locator('button, input[type="submit"]').first
            
            input_el.fill("nonexistentquery")
            btn_el.click()
            session.page.wait_for_timeout(400)

            content_lower = session.page.content().lower()
            shows_empty_state = any(w in content_lower for w in ["no results", "found 0", "not found", "no items", "0 results"])
            results.append(TestResult(
                test_name="state_empty_results_feedback",
                category="state_robustness",
                regime="reality",
                passed=shows_empty_state,
                details="Empty results state rendered friendly user feedback",
                failure_type="State consistency failure: Blank container on zero search results" if not shows_empty_state else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="state_empty_results_feedback",
                category="state_robustness",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="State consistency failure: Exception on empty results"
            ))

        # Test B.3: Failure Recovery - HTTP 500 Network Failure
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=500, json_body={"error": "Search service down"})
            session.load_html(html_code)
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            btn_el = session.page.locator('button, input[type="submit"]').first
            
            input_el.fill("algorithms")
            btn_el.click()
            session.page.wait_for_timeout(500)

            content_lower = session.page.content().lower()
            shows_error = any(w in content_lower for w in ["error", "failed", "unavailable", "try again", "unable"])
            results.append(TestResult(
                test_name="network_500_search_recovery",
                category="failure_recovery",
                regime="reality",
                passed=shows_error,
                details="Error message displayed upon HTTP 500 failure",
                failure_type="Recovery failure: Silent failure on search server 500" if not shows_error else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="network_500_search_recovery",
                category="failure_recovery",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Network failure: App crashed on 500 search error"
            ))

        # Test B.4: Interaction Safety - Rapid Debounce / Double Submission
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=200, json_body=SAMPLE_RESULTS, delay_ms=400)
            session.load_html(html_code)
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            input_el.fill("react")

            # Fire rapid duplicate clicks
            session.page.evaluate("""() => {
                const b = document.querySelector('button[type="submit"], button');
                if (b) { b.click(); b.click(); }
            }""")
            session.page.wait_for_timeout(600)

            req_count = len(session.intercepted_requests)
            is_debounced = (req_count == 1)
            results.append(TestResult(
                test_name="rapid_search_duplicate_safety",
                category="interaction_safety",
                regime="reality",
                passed=is_debounced,
                details=f"Requests triggered on rapid click: {req_count} (expected: 1)",
                failure_type="Duplicate interaction: Multiple API searches spammed on double-click" if not is_debounced else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="rapid_search_duplicate_safety",
                category="interaction_safety",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Interaction safety: Exception on rapid click"
            ))

        # Test B.5: Accessibility - Keyboard Search via Enter
        session = harness.new_session()
        try:
            session.mock_route("**/api/search*", status=200, json_body=SAMPLE_RESULTS)
            session.load_html(html_code)
            input_el = session.page.locator('input[type="search"], input[type="text"], input').first
            
            input_el.focus()
            input_el.type("keyboard")
            session.page.keyboard.press("Enter")
            session.page.wait_for_timeout(400)

            key_submitted = len(session.intercepted_requests) > 0
            results.append(TestResult(
                test_name="keyboard_accessibility_search_enter",
                category="accessibility",
                regime="reality",
                passed=key_submitted,
                details="Search submittable via keyboard Enter key",
                failure_type="Accessibility failure: Search cannot be triggered by Enter key" if not key_submitted else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="keyboard_accessibility_search_enter",
                category="accessibility",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Accessibility failure: Keyboard navigation crashed"
            ))

        # Test B.6: Responsive Behavior - Mobile Viewport Integrity
        session = harness.new_session()
        try:
            session.load_html(html_code, viewport={"width": 375, "height": 667})
            has_no_overflow = session.page.evaluate(
                "() => document.documentElement.scrollWidth <= window.innerWidth + 2"
            )
            results.append(TestResult(
                test_name="mobile_viewport_overflow",
                category="responsive_behavior",
                regime="reality",
                passed=has_no_overflow,
                details="No horizontal overflow on mobile viewport",
                failure_type="Responsive failure: Horizontal scroll overflow on mobile" if not has_no_overflow else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="mobile_viewport_overflow",
                category="responsive_behavior",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Responsive failure: Exception on mobile check"
            ))

    return calculate_scores("realitybench-search", results)


# %%
@kbench.task(name="realitybench-search")
def realitybench_search(llm) -> dict:
    """
    Evaluates LLM on Search software generation across Demo Score, Reality Score, and Reality Gap.
    """
    response = llm.prompt(SEARCH_TASK_PROMPT)
    code = extract_html_code(response)
    
    report = grade_search_implementation(code)
    
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional search component on happy path"
    )
    
    return report.to_dict()


# %%
if __name__ == "__main__":
    # Local verification with naive vs robust reference implementations
    naive_code = """
    <!DOCTYPE html><html><body>
      <input type="text" id="q" placeholder="Search...">
      <button onclick="doSearch()">Search</button>
      <div id="results"></div>
      <script>
        function doSearch() {
          const q = document.getElementById('q').value;
          fetch('/api/search?q=' + encodeURIComponent(q))
            .then(r => r.json())
            .then(data => {
              let html = '';
              data.results.forEach(item => {
                html += '<div><h3>' + item.title + '</h3><p>' + item.description + '</p></div>';
              });
              document.getElementById('results').innerHTML = html;
            });
        }
      </script>
    </body></html>
    """

    robust_code = """
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
      <form id="search-form">
        <input type="search" id="q" name="q" required placeholder="Search...">
        <button type="submit" id="search-btn">Search</button>
      </form>
      <div id="status" role="status"></div>
      <div id="results"></div>
      <script>
        const form = document.getElementById('search-form');
        const btn = document.getElementById('search-btn');
        const status = document.getElementById('status');
        const results = document.getElementById('results');

        form.onsubmit = async (e) => {
          e.preventDefault();
          const q = document.getElementById('q').value.trim();
          if (!q) return;

          btn.disabled = true;
          status.innerText = 'Searching...';
          results.innerHTML = '';

          try {
            const res = await fetch('/api/search?q=' + encodeURIComponent(q));
            if (!res.ok) throw new Error('Search failed: ' + res.status);
            const data = await res.json();
            if (!data.results || data.results.length === 0) {
              status.innerText = 'No results found.';
            } else {
              status.innerText = 'Found ' + data.results.length + ' results.';
              results.innerHTML = data.results.map(r => '<div><h3>' + r.title + '</h3><p>' + r.description + '</p></div>').join('');
            }
          } catch (err) {
            status.innerText = 'Error: ' + err.message;
          } finally {
            btn.disabled = false;
          }
        };
      </script>
    </body></html>
    """

    print("Evaluating Naive Search...")
    r1 = grade_search_implementation(naive_code)
    print(f"Demo: {r1.demo_score:.2%}, Reality: {r1.reality_score:.2%}, Gap: {r1.reality_gap:.2%}")
    print(f"Passed: {sum(1 for t in r1.test_results if t.passed)}/{len(r1.test_results)}")

    print("\nEvaluating Robust Search...")
    r2 = grade_search_implementation(robust_code)
    print(f"Demo: {r2.demo_score:.2%}, Reality: {r2.reality_score:.2%}, Gap: {r2.reality_gap:.2%}")
    print(f"Passed: {sum(1 for t in r2.test_results if t.passed)}/{len(r2.test_results)}")
