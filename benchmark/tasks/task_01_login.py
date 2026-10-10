# %%
"""
TASK: Authentication & Login (Task 01)

Purpose:
Evaluate whether an AI-generated web login component remains robust when
encountering invalid input, HTTP 500 server errors, double submissions,
and keyboard/mobile viewport constraints.

Happy Path:
- Renders email, password, and submit button
- Successful authentication flow with valid credentials and mock token response

Reality Tests:
- Empty credential submission blocked from network
- Malformed email format rejected before network call
- HTTP 500 error handled gracefully with visible error feedback
- Form input state preserved after network failure (no wipe)
- Double-click debounce / submit button disabled during in-flight request
- Keyboard accessibility: Enter key submits the credentials
- Responsive behavior: 375px mobile viewport has no horizontal scroll overflow

Scoring:
Demo Score: functional_correctness (25%), expected_interactions (15%)
Reality Score: failure_recovery (20%), state_robustness (15%), input_robustness (10%),
               accessibility (7%), responsive_behavior (5%), interaction_safety (3%)
"""

import sys
import os
import json
from typing import List

# Ensure realitybench package is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
bench_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

import kaggle_benchmarks as kbench
from benchmark.kaggle_runtime import should_run_kbench
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code


LOGIN_TASK_PROMPT = """Build a self-contained web login component in HTML, CSS, and JavaScript.
The interface must contain:
1. An email input (with appropriate labeling or placeholder)
2. A password input (masked password field)
3. A submit button
When submitted, the application should make a POST request to '/api/login' with a JSON payload containing 'email' and 'password'.
Upon receiving a successful response ({ 'token': '...', 'user': { 'name': '...' } }), display a visible success message or welcome state to the user.
The application should provide appropriate validation and user feedback when an operation cannot be completed.
Provide all code in a single self-contained HTML document. Do not include external dependencies like React or Tailwind CDN."""

TASK_SPEC = LOGIN_TASK_PROMPT

NAIVE_LOGIN_CODE = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <h2>Login</h2>
  <input type="text" id="email" placeholder="Email" />
  <input type="password" id="password" placeholder="Password" />
  <button onclick="login()">Login</button>
  <div id="msg"></div>

  <script>
    function login() {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      .then(res => res.json())
      .then(data => {
        document.getElementById('msg').innerText = 'Welcome ' + (data.user?.name || '');
      });
    }
  </script>
</body>
</html>
"""

ROBUST_LOGIN_CODE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login</title>
</head>
<body>
  <form id="login-form">
    <label for="email">Email</label>
    <input type="email" id="email" name="email" required placeholder="name@domain.com" />
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required placeholder="Enter password" />
    <button type="submit" id="submit-btn">Login</button>
  </form>
  <div id="status" role="status"></div>

  <script>
    const form = document.getElementById('login-form');
    const btn = document.getElementById('submit-btn');
    const status = document.getElementById('status');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      if (!email || !password) return;

      btn.disabled = true;
      btn.innerText = 'Logging in...';
      status.innerText = '';

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Server error occurred during login');
        }
        status.innerText = 'Welcome ' + (data.user?.name || 'User') + '! Login successful.';
      } catch (err) {
        status.innerText = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
        btn.innerText = 'Login';
      }
    });
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []

    # Test A.1: Functional Correctness - Structural Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first
        btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button').first

        has_elements = (email_el.count() > 0 and pass_el.count() > 0 and btn_el.count() > 0)
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=has_elements,
            details="Email input, password input, and submit button rendered",
            failure_type="Functional failure: Missing core form inputs" if not has_elements else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=False,
            details=f"Render exception: {str(e)}",
            failure_type="Functional failure: Uncaught render error"
        ))

    # Test A.2: Expected Interactions - Successful Authentication Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=200, json_body={"token": "tok_xyz987", "user": {"name": "Alice"}})
        session.load_html(html_code)

        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first
        btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button').first

        email_el.fill("alice@example.com")
        pass_el.fill("Secret123!")
        btn_el.click()
        session.page.wait_for_timeout(400)

        req_sent = len(session.intercepted_requests) > 0
        body_correct = False
        if req_sent:
            post_data = session.intercepted_requests[0].get("post_data") or {}
            if isinstance(post_data, str):
                try:
                    post_data = json.loads(post_data)
                except Exception:
                    pass
            if isinstance(post_data, dict):
                body_correct = ("email" in post_data and "alice@example.com" in str(post_data.get("email")))

        content_lower = session.page.content().lower()
        shows_success = any(w in content_lower for w in ["success", "welcome", "alice", "logged in"])

        passed = req_sent and body_correct and shows_success
        results.append(TestResult(
            test_name="happy_path_successful_auth",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Request sent: {req_sent}, Payload valid: {body_correct}, Success UI: {shows_success}",
            failure_type="Expected interaction failure: Login flow did not complete" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_successful_auth",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=f"Interaction error: {str(e)}",
            failure_type="Expected interaction failure: Crash during submission"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Input Robustness - Empty Input Validation
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=200, json_body={"token": "tok_123"})
        session.load_html(html_code)
        btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button').first
        btn_el.click()
        session.page.wait_for_timeout(300)

        blocked_request = len(session.intercepted_requests) == 0
        results.append(TestResult(
            test_name="input_empty_validation",
            category="input_robustness",
            regime="reality",
            passed=blocked_request,
            details="Empty submission prevented from hitting backend",
            failure_type="Validation failure: Sent empty credentials to API" if not blocked_request else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="input_empty_validation",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Validation failure: Exception on empty submit"
        ))

    # Test B.2: Input Robustness - Malformed Email Format
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=200, json_body={"token": "tok_123"})
        session.load_html(html_code)
        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first
        btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button').first

        email_el.fill("not-a-valid-email")
        pass_el.fill("ValidPass123!")
        btn_el.click()
        session.page.wait_for_timeout(300)

        blocked_invalid = len(session.intercepted_requests) == 0
        results.append(TestResult(
            test_name="input_malformed_email",
            category="input_robustness",
            regime="reality",
            passed=blocked_invalid,
            details="Malformed email blocked before network call",
            failure_type="Validation failure: Invalid email format allowed through" if not blocked_invalid else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="input_malformed_email",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Validation failure: Exception checking email format"
        ))

    # Test B.3: Failure Recovery - HTTP 500 Network Error Handling
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=500, json_body={"error": "Database connection failed"})
        session.load_html(html_code)
        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first
        btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button').first

        email_el.fill("bob@example.com")
        pass_el.fill("Secret123!")
        btn_el.click()
        session.page.wait_for_timeout(500)

        content_lower = session.page.content().lower()
        shows_error_message = any(w in content_lower for w in ["error", "failed", "invalid", "try again", "connection", "server"])

        results.append(TestResult(
            test_name="network_500_error_feedback",
            category="failure_recovery",
            regime="reality",
            passed=shows_error_message,
            details="Error state displayed upon HTTP 500",
            failure_type="Recovery failure: Silent failure on HTTP 500 without error feedback" if not shows_error_message else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="network_500_error_feedback",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Network failure: App crashed on 500 response"
        ))

    # Test B.4: State Robustness - Credential Preservation on Failure
    try:
        current_email_val = email_el.input_value()
        preserved = (current_email_val == "bob@example.com")
        results.append(TestResult(
            test_name="state_preservation_on_error",
            category="state_robustness",
            regime="reality",
            passed=preserved,
            details=f"Entered email preserved: '{current_email_val}'",
            failure_type="Navigation/state-loss failure: Form wiped user input after server error" if not preserved else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="state_preservation_on_error",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State consistency failure: Unable to read input value"
        ))

    # Test B.5: Interaction Safety - Rapid Double-Click Protection
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=200, json_body={"token": "tok_123"}, delay_ms=400)
        session.load_html(html_code)
        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first

        email_el.fill("fastclick@example.com")
        pass_el.fill("Pass123!")

        session.page.evaluate("""() => {
            const b = document.querySelector('button[type="submit"], input[type="submit"], button');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(600)

        req_count = len(session.intercepted_requests)
        is_safe = (req_count == 1)
        results.append(TestResult(
            test_name="double_click_protection",
            category="interaction_safety",
            regime="reality",
            passed=is_safe,
            details=f"Intercepted {req_count} request(s) on double click (expected 1)",
            failure_type="Interaction failure: Unhandled duplicate submission" if not is_safe else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="double_click_protection",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction failure: Exception on rapid clicks"
        ))

    # Test B.6: Accessibility - Keyboard Navigation (Enter key submit)
    session = harness.new_session()
    try:
        session.mock_route("**/api/login", status=200, json_body={"token": "tok_123"})
        session.load_html(html_code)
        email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
        pass_el = session.page.locator('input[type="password"]').first

        email_el.fill("keyboard@example.com")
        pass_el.fill("Secret123!")
        pass_el.press("Enter")
        session.page.wait_for_timeout(400)

        enter_submitted = len(session.intercepted_requests) > 0
        results.append(TestResult(
            test_name="keyboard_accessibility_enter_submit",
            category="accessibility",
            regime="reality",
            passed=enter_submitted,
            details="Enter key in password field submits form",
            failure_type="Accessibility failure: Enter key did not submit credentials" if not enter_submitted else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="keyboard_accessibility_enter_submit",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Keyboard navigation crashed"
        ))

    # Test B.7: Responsive Behavior - Mobile Viewport Integrity (375x667)
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
            details="No horizontal overflow on 375px mobile viewport",
            failure_type="Responsive failure: Horizontal layout overflow on mobile" if not has_no_overflow else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="mobile_viewport_overflow",
            category="responsive_behavior",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Responsive failure: Exception checking mobile layout"
        ))

    return results


def grade_login_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation across:
    Regime A (Happy Path / Demo Score) and Regime B (Controlled Perturbations / Reality Score).
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-login", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-login")
def realitybench_login(llm) -> dict:
    """
    Evaluates LLM on Login software generation across Demo Score, Reality Score, and Reality Gap.
    """
    response = llm.prompt(LOGIN_TASK_PROMPT)
    code = extract_html_code(response)

    report = grade_login_implementation(code)

    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional login component on happy path"
    )

    return report.to_dict()


# %%
if __name__ == "__main__":
    if should_run_kbench():
        realitybench_login.run(kbench.llm)
    else:

        from ui import console, test_results_table, task_result_panel

        console.print("[bold cyan]Running local self-test for Task 01: Authentication & Login...[/bold cyan]")
        report = grade_login_implementation(NAIVE_LOGIN_CODE)
        console.print(task_result_panel(
            "Authentication & Login (Naive Baseline)",
            report.demo_score,
            report.reality_score,
            report.reality_gap
        ))
        console.print(test_results_table(report.test_results, "Task 01: Login Assertions"))
