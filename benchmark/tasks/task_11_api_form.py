# %%
"""
TASK: Dependent Dynamic API Form (Cascading Dropdowns)
Task Index: 11
Identifier: realitybench-api-form

Purpose:
  Evaluates whether generated asynchronous form software correctly manages dependent
  cascading state, network failure resilience, submission debounce, and validation.

Happy Path (Demo Regime):
  - demo_elements_rendered: Country select, dependent region select, and submit button exist.
  - demo_cascading_flow: Selecting country fetches /api/regions and populates options; submitting dispatches POST to /api/location and displays confirmation.

Reality Tests (Perturbation Regime):
  - reality_dependent_api_error_recovery: Server returns HTTP 500 on region fetch; UI displays clear error feedback and permits retry.
  - reality_country_switch_state_reset: Changing parent country selection immediately clears stale region value.
  - reality_empty_submission_validation: Incomplete submissions without country or region selection are blocked.
  - reality_double_click_safety: Rapid double-clicking submit button dispatches exactly one POST request.
  - reality_accessibility_labels: Accessible <label> elements or ARIA descriptors associated with selectors.
  - reality_mobile_responsive: Layout maintains zero horizontal overflow on mobile viewport (375x667).

Scoring:
  - Demo Score: Rendering and successful cascading selection interaction.
  - Reality Score: Weighted adversarial resilience across 6 perturbation categories.
  - Reality Gap: Demo Score - Reality Score.
"""

import sys
import os
from typing import List

# Ensure realitybench package is on path
current_dir = os.path.dirname(os.path.abspath(__file__))
bench_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

import kaggle_benchmarks as kbench
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code
from ui import console, task_result_panel, test_results_table, print_banner


# =============================================================================
# Task Prompts & Specifications
# =============================================================================

API_FORM_TASK_PROMPT = """Build a self-contained country and region selector form component in HTML, CSS, and JavaScript.
The interface must contain:
1. Country selector dropdown (<select id="country">) with options like 'Select country...', 'US' (United States), 'CA' (Canada), 'GB' (United Kingdom)
2. Region/State selector dropdown (<select id="region">), disabled or indicating empty until a country is selected
3. Submit button ('Save Location')
When a country is selected, dynamically fetch the available regions via GET from '/api/regions?country={code}'.
The API responds with JSON: [ { 'code': 'CA', 'name': 'California' }, { 'code': 'NY', 'name': 'New York' } ].
When the user submits the form, send a POST request to '/api/location' with { 'country': '...', 'region': '...' }.
Upon successful submission (returns { 'status': 'saved' }), show a success message.
The application should:
- Display a clear loading state while fetching regions
- Handle region API failures (e.g., HTTP 500): display an error message and allow retrying
- When the country is changed, immediately clear the previously selected region and populate new ones
- Prevent form submission if either country or region is not selected
- Prevent duplicate POST submissions if the submit button is clicked multiple times rapidly
- Ensure accessible form controls with proper labels
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = API_FORM_TASK_PROMPT


# =============================================================================
# Reference Implementations
# =============================================================================

NAIVE_API_FORM_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Location Selector</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .form-group { margin-bottom: 15px; }
    select { width: 250px; padding: 6px; }
  </style>
</head>
<body>
  <h2>Location Selector</h2>
  <div class="form-group">
    Country:
    <select id="country" onchange="loadRegions()">
      <option value="">Select country...</option>
      <option value="US">United States</option>
      <option value="CA">Canada</option>
      <option value="GB">United Kingdom</option>
    </select>
  </div>
  <div class="form-group">
    Region:
    <select id="region">
      <option value="">Select region...</option>
    </select>
  </div>
  <button id="submit-btn" onclick="submitLocation()">Save Location</button>
  <div id="status"></div>

  <script>
    async function loadRegions() {
      const country = document.getElementById('country').value;
      // Naive: doesn't reset previous region if user switches, fails silently on 500
      try {
        const res = await fetch('/api/regions?country=' + country);
        const data = await res.json();
        const regionSelect = document.getElementById('region');
        data.forEach(item => {
          const opt = document.createElement('option');
          opt.value = item.code;
          opt.text = item.name;
          regionSelect.appendChild(opt);
        });
      } catch (err) {
        // Silent catch - leaves user hanging
      }
    }

    async function submitLocation() {
      const country = document.getElementById('country').value;
      const region = document.getElementById('region').value;
      // Naive: no validation check, no double click protection
      const res = await fetch('/api/location', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ country, region })
      });
      if (res.ok) {
        document.getElementById('status').innerText = 'Location saved successfully!';
      }
    }
  </script>
</body>
</html>
"""

ROBUST_API_FORM_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Location Selector</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 24px;
      background: #f8fafc;
      color: #1e293b;
    }
    .card {
      max-width: 480px;
      margin: 0 auto;
      background: #ffffff;
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h2 { margin-top: 0; font-size: 1.35rem; }
    .form-group {
      margin-bottom: 18px;
      display: flex;
      flex-direction: column;
    }
    label {
      font-weight: 600;
      font-size: 0.88rem;
      margin-bottom: 6px;
      color: #334155;
    }
    select {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.95rem;
      background: #fff;
    }
    select:disabled {
      background: #f1f5f9;
      cursor: not-allowed;
    }
    .btn-submit {
      width: 100%;
      padding: 12px;
      background: #2563eb;
      color: #fff;
      font-size: 1rem;
      font-weight: 600;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      margin-top: 8px;
      transition: background 0.2s;
    }
    .btn-submit:hover:not(:disabled) {
      background: #1d4ed8;
    }
    .btn-submit:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .feedback {
      margin-top: 14px;
      padding: 12px;
      border-radius: 6px;
      font-size: 0.9rem;
      display: none;
    }
    .feedback.success {
      display: block;
      background: #dcfce7;
      color: #166534;
      border: 1px solid #bbf7d0;
    }
    .feedback.error {
      display: block;
      background: #fee2e2;
      color: #991b1b;
      border: 1px solid #fecaca;
    }
  </style>
</head>
<body>
  <div class="card">
    <h2>Select Location</h2>
    <form id="location-form" novalidate>
      <div class="form-group">
        <label for="country">Country</label>
        <select id="country" name="country" required>
          <option value="">Select country...</option>
          <option value="US">United States</option>
          <option value="CA">Canada</option>
          <option value="GB">United Kingdom</option>
        </select>
      </div>

      <div class="form-group">
        <label for="region">State / Province</label>
        <select id="region" name="region" required disabled>
          <option value="">Select country first...</option>
        </select>
      </div>

      <button type="submit" id="submit-btn" class="btn-submit">Save Location</button>
      <div id="feedback" class="feedback" role="alert"></div>
    </form>
  </div>

  <script>
    const countrySelect = document.getElementById('country');
    const regionSelect = document.getElementById('region');
    const submitBtn = document.getElementById('submit-btn');
    const feedback = document.getElementById('feedback');
    const form = document.getElementById('location-form');

    let isSubmitting = false;

    countrySelect.addEventListener('change', async () => {
      const country = countrySelect.value;
      feedback.style.display = 'none';

      // Always reset region dropdown completely
      regionSelect.innerHTML = '';
      if (!country) {
        regionSelect.disabled = true;
        regionSelect.innerHTML = '<option value="">Select country first...</option>';
        return;
      }

      regionSelect.disabled = true;
      regionSelect.innerHTML = '<option value="">Loading regions...</option>';

      try {
        const res = await fetch('/api/regions?country=' + encodeURIComponent(country));
        if (!res.ok) {
          throw new Error('Server returned HTTP ' + res.status);
        }
        const data = await res.json();

        regionSelect.innerHTML = '<option value="">Select region...</option>';
        data.forEach(item => {
          const opt = document.createElement('option');
          opt.value = item.code;
          opt.textContent = item.name;
          regionSelect.appendChild(opt);
        });
        regionSelect.disabled = false;
      } catch (err) {
        regionSelect.innerHTML = '<option value="">Error loading regions</option>';
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Failed to load regions. Please retry or select another country.';
      }
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (isSubmitting) return;

      const country = countrySelect.value;
      const region = regionSelect.value;

      if (!country || !region) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Validation Error: Both Country and Region must be selected.';
        return;
      }

      isSubmitting = true;
      submitBtn.disabled = true;
      submitBtn.innerText = 'Saving...';
      feedback.style.display = 'none';

      try {
        const res = await fetch('/api/location', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ country, region })
        });

        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();

        feedback.style.display = 'block';
        feedback.className = 'feedback success';
        feedback.innerText = 'Location saved successfully!';
      } catch (err) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Failed to save location: ' + err.message;
      } finally {
        isSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.innerText = 'Save Location';
      }
    });
  </script>
</body>
</html>
"""


# =============================================================================
# Sub-Test Execution Functions
# =============================================================================

def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates Dependent API Form on standard expected operations."""
    results: List[TestResult] = []

    # Test A.1: Render Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_country = session.page.locator("select#country, select[name='country']").count() > 0
        has_region = session.page.locator("select#region, select[name='region']").count() > 0
        has_btn = session.page.locator("button:has-text('Save'), button:has-text('Submit'), input[type='submit']").count() > 0

        passed = has_country and has_region and has_btn
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Country: {has_country}, Region: {has_region}, Submit Button: {has_btn}",
            failure_type="Functional failure: Missing country select, region select, or submit button" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Functional failure: Exception rendering cascading form"
        ))

    # Test A.2: Expected Interaction - Successful Cascading Selection & Submit
    session = harness.new_session()
    session.mock_route("**/api/regions*country=US*", status=200, json_body=[
        {"code": "CA", "name": "California"},
        {"code": "NY", "name": "New York"}
    ])
    session.mock_route("**/api/location*", status=200, json_body={"status": "saved"})

    try:
        session.load_html(html_code)
        country_select = session.page.locator("select#country, select[name='country']").first
        region_select = session.page.locator("select#region, select[name='region']").first
        submit_btn = session.page.locator("button:has-text('Save'), button:has-text('Submit'), input[type='submit']").first

        # Select country US
        country_select.select_option(value="US")
        session.page.wait_for_timeout(400)

        # Check region dropdown populated
        region_options_count = region_select.locator("option").count()
        has_options = region_options_count >= 2

        # Select region CA
        region_select.select_option(index=1)
        session.page.wait_for_timeout(200)

        # Submit location
        submit_btn.click()
        session.page.wait_for_timeout(500)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        posted_data = len(post_requests) >= 1
        content_lower = session.page.content().lower()
        shows_success = any(w in content_lower for w in ["saved", "success", "confirmed"])

        passed = has_options and posted_data and shows_success
        results.append(TestResult(
            test_name="demo_cascading_flow",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Regions populated={has_options} (count={region_options_count}), POST dispatched={posted_data}, UI success={shows_success}",
            failure_type="Interaction failure: Did not fetch regions or submit selected location" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_cascading_flow",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Interaction failure: Exception during cascading selection flow"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates Dependent API Form under adversarial conditions and perturbations."""
    results: List[TestResult] = []

    # Test B.1: Failure Recovery - HTTP 500 on Region Fetch
    session = harness.new_session()
    session.mock_route("**/api/regions*country=CA*", status=500, json_body={"error": "Database error", "message": "Failed to load regions"})

    try:
        session.load_html(html_code)
        country_select = session.page.locator("select#country, select[name='country']").first
        country_select.select_option(value="CA")
        session.page.wait_for_timeout(500)

        content_lower = session.page.content().lower()
        shows_error = any(w in content_lower for w in ["error", "fail", "unable", "500", "retry"])

        results.append(TestResult(
            test_name="reality_dependent_api_error_recovery",
            category="failure_recovery",
            regime="reality",
            passed=shows_error,
            details=f"Error feedback displayed on 500: {shows_error}",
            failure_type="Failure recovery failure: Page failed silently or did not show error feedback on 500" if not shows_error else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_dependent_api_error_recovery",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Failure recovery failure: Exception testing 500 region failure"
        ))

    # Test B.2: State Robustness - Switching Country Resets Prior Region Selection
    session = harness.new_session()
    session.mock_route("**/api/regions*country=US*", status=200, json_body=[
        {"code": "CA", "name": "California"}
    ])
    session.mock_route("**/api/regions*country=GB*", status=200, json_body=[
        {"code": "ENG", "name": "England"}
    ])
    session.mock_route("**/api/location*", status=200, json_body={"status": "saved"})

    try:
        session.load_html(html_code)
        country_select = session.page.locator("select#country, select[name='country']").first
        region_select = session.page.locator("select#region, select[name='region']").first
        submit_btn = session.page.locator("button:has-text('Save'), button:has-text('Submit'), input[type='submit']").first

        # 1. Select US and California
        country_select.select_option(value="US")
        session.page.wait_for_timeout(300)
        region_select.select_option(index=1)
        session.page.wait_for_timeout(200)

        # 2. Switch Country to GB
        country_select.select_option(value="GB")
        session.page.wait_for_timeout(400)

        # 3. Check that region value is NOT still "CA" (California)
        curr_region_val = region_select.input_value()
        state_reset_ok = (curr_region_val != "CA")

        results.append(TestResult(
            test_name="reality_country_switch_state_reset",
            category="state_robustness",
            regime="reality",
            passed=state_reset_ok,
            details=f"Prior region 'CA' cleared upon country change: {state_reset_ok} (current: '{curr_region_val}')",
            failure_type="State robustness failure: Stale region selection persisted across country change" if not state_reset_ok else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_country_switch_state_reset",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception testing country switch state reset"
        ))

    # Test B.3: Input Robustness - Incomplete Form Submission Blocked
    session = harness.new_session()
    session.mock_route("**/api/location*", status=200, json_body={"status": "saved"})

    try:
        session.load_html(html_code)
        submit_btn = session.page.locator("button:has-text('Save'), button:has-text('Submit'), input[type='submit']").first

        # Submit without selecting country or region
        submit_btn.click()
        session.page.wait_for_timeout(300)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        empty_submission_blocked = len(post_requests) == 0

        results.append(TestResult(
            test_name="reality_empty_submission_validation",
            category="input_robustness",
            regime="reality",
            passed=empty_submission_blocked,
            details=f"Empty form POST blocked: {empty_submission_blocked} (calls={len(post_requests)})",
            failure_type="Input robustness failure: Submitted unselected form to /api/location" if not empty_submission_blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_empty_submission_validation",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing incomplete submission"
        ))

    # Test B.4: Interaction Safety - Rapid Double-Click Debounce
    session = harness.new_session()
    session.mock_route("**/api/regions*country=US*", status=200, json_body=[
        {"code": "CA", "name": "California"}
    ])
    session.mock_route("**/api/location*", status=200, json_body={"status": "saved"}, delay_ms=300)

    try:
        session.load_html(html_code)
        country_select = session.page.locator("select#country, select[name='country']").first
        region_select = session.page.locator("select#region, select[name='region']").first
        submit_btn = session.page.locator("button:has-text('Save'), button:has-text('Submit'), input[type='submit']").first

        country_select.select_option(value="US")
        session.page.wait_for_timeout(300)
        region_select.select_option(index=1)
        session.page.wait_for_timeout(200)

        # Rapid double-click submit
        submit_btn.click(click_count=2, delay=20)
        session.page.wait_for_timeout(800)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        debounce_ok = len(post_requests) == 1

        results.append(TestResult(
            test_name="reality_double_click_safety",
            category="interaction_safety",
            regime="reality",
            passed=debounce_ok,
            details=f"POST requests dispatched during double click: {len(post_requests)} (expected 1)",
            failure_type="Interaction safety failure: Dispatched duplicate location submissions" if not debounce_ok else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_double_click_safety",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction safety failure: Exception testing double click"
        ))

    # Test B.5: Accessibility - Semantic Labels
    session = harness.new_session()
    try:
        session.load_html(html_code)
        labels_count = session.page.locator("label").count()
        aria_labels_count = session.page.locator("[aria-label], [aria-labelledby]").count()
        has_accessible_controls = (labels_count >= 2) or (aria_labels_count >= 2)

        results.append(TestResult(
            test_name="reality_accessibility_labels",
            category="accessibility",
            regime="reality",
            passed=has_accessible_controls,
            details=f"Found {labels_count} <label> elements and {aria_labels_count} ARIA labelled controls",
            failure_type="Accessibility failure: Missing proper labels for dropdowns" if not has_accessible_controls else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_accessibility_labels",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting form accessibility"
        ))

    # Test B.6: Mobile Responsiveness
    session = harness.new_session()
    try:
        session.load_html(html_code, viewport={"width": 375, "height": 667})
        session.page.wait_for_timeout(300)

        scroll_width = session.page.evaluate("document.documentElement.scrollWidth")
        client_width = session.page.evaluate("document.documentElement.clientWidth")
        overflow_ok = scroll_width <= client_width + 10

        results.append(TestResult(
            test_name="reality_mobile_responsive",
            category="responsive_behavior",
            regime="reality",
            passed=overflow_ok,
            details=f"Scroll width: {scroll_width}px vs Client width: {client_width}px",
            failure_type="Responsive failure: Horizontal scroll overflow on mobile viewport" if not overflow_ok else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_mobile_responsive",
            category="responsive_behavior",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Responsive failure: Exception inspecting mobile layout"
        ))

    return results


# =============================================================================
# Primary Grader Orchestration
# =============================================================================

def grade_api_form_implementation(html_code: str) -> EvaluationReport:
    """Executes deterministic headless browser evaluation of the Dependent API Form."""
    results: List[TestResult] = []

    with HeadlessHarness() as harness:
        results.extend(run_happy_path(harness, html_code))
        results.extend(run_reality_tests(harness, html_code))

    return calculate_scores("realitybench-api-form", results)


# %%
@kbench.task(name="realitybench-api-form")
def realitybench_api_form(llm) -> dict:
    """Evaluates LLM on Dependent API Form software generation."""
    response = llm.prompt(API_FORM_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_api_form_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional dependent API form on happy path"
    )
    return report.to_dict()


if __name__ == "__main__":
    print_banner()
    console.print("[task]Evaluating Task 11: Dependent Dynamic API Form[/task]\n")

    r1 = grade_api_form_implementation(NAIVE_API_FORM_CODE)
    console.print(task_result_panel("Task 11: API Form (Naive Baseline)", r1.demo_score, r1.reality_score, r1.reality_gap))
    console.print(test_results_table(r1.test_results))

    r2 = grade_api_form_implementation(ROBUST_API_FORM_CODE)
    console.print(task_result_panel("Task 11: API Form (Robust Baseline)", r2.demo_score, r2.reality_score, r2.reality_gap))
    console.print(test_results_table(r2.test_results))
