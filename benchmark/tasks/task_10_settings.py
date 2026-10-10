# %%
"""
TASK: User Settings Panel (Task 10)

Purpose:
Evaluate whether an AI-generated user settings panel validates empty names and malformed
emails, restores original state upon 'Discard Changes', preserves user input during
HTTP 500 save failures, debounces rapid duplicate saves, and conforms to accessibility/mobile standards.

Happy Path:
- Renders profile fields (name, email, notifications toggle), and actions (Save, Discard)
- Successful save flow sends POST/PUT to /api/settings and renders success feedback

Reality Tests:
- Blank name or invalid email format rejected before network dispatch
- Discard Changes restores initial form values
- HTTP 500 save error displays visible error without wiping edited user inputs
- Double-click prevention: Rapid duplicate clicks on Save dispatch only one request
- Accessible form controls with proper label association
- Responsive behavior: 375px mobile viewport has no horizontal scroll overflow

Scoring:
Demo Score: functional_correctness (25%), expected_interactions (15%)
Reality Score: failure_recovery (20%), state_robustness (15%), input_robustness (10%),
               accessibility (7%), responsive_behavior (5%), interaction_safety (3%)
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
from benchmark.kaggle_runtime import should_run_kbench
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code


SETTINGS_TASK_PROMPT = """Build a self-contained user settings panel component in HTML, CSS, and JavaScript.
The interface must contain:
1. Profile fields:
   - Full Name (text input)
   - Email address (email input)
   - Notification preference (checkbox or toggle switch: 'Email Notifications')
2. Action buttons: 'Save Changes' and 'Discard Changes' (or 'Cancel')
3. Visual indication or tracking when there are unsaved changes
When the user clicks 'Save Changes', send a POST or PUT request to '/api/settings' with { 'name': '...', 'email': '...', 'notifications': boolean }.
Upon success (returns { 'status': 'saved', 'updated_at': '2026-10-06T12:00:00Z' }), display a success notification.
The application should:
- Validate that Name is not blank and Email is a valid email address before submitting
- Handle save failures (e.g., HTTP 500): show a prominent error message without clearing the user's edits
- When 'Discard Changes' is clicked, restore the last saved settings
- Prevent duplicate requests if 'Save Changes' is clicked repeatedly while saving
- Ensure accessible form controls with proper labels
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = SETTINGS_TASK_PROMPT

NAIVE_SETTINGS_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>User Settings</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .form-group { margin-bottom: 15px; }
    input[type="text"], input[type="email"] { width: 300px; padding: 8px; }
    button { padding: 8px 16px; margin-right: 10px; }
  </style>
</head>
<body>
  <h2>User Settings</h2>
  <div class="form-group">
    Name: <input type="text" id="name" value="Initial Name">
  </div>
  <div class="form-group">
    Email: <input type="email" id="email" value="initial@example.com">
  </div>
  <div class="form-group">
    <input type="checkbox" id="notifications" checked> Receive email alerts
  </div>
  <button id="save-btn" onclick="saveSettings()">Save Changes</button>
  <button id="discard-btn" onclick="discardSettings()">Discard Changes</button>
  <div id="status"></div>

  <script>
    async function saveSettings() {
      const name = document.getElementById('name').value;
      const email = document.getElementById('email').value;
      const notifications = document.getElementById('notifications').checked;

      try {
        const res = await fetch('/api/settings', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name, email, notifications })
        });
        if (res.ok) {
          document.getElementById('status').innerText = 'Settings saved successfully!';
        } else {
          document.getElementById('name').value = '';
          document.getElementById('email').value = '';
          document.getElementById('status').innerText = 'Server error.';
        }
      } catch (e) {
        document.getElementById('status').innerText = 'Network error.';
      }
    }

    function discardSettings() {
      document.getElementById('status').innerText = 'Discarded';
    }
  </script>
</body>
</html>
"""

ROBUST_SETTINGS_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>User Settings</title>
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
      max-width: 520px;
      margin: 0 auto;
      background: #ffffff;
      padding: 28px;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    h2 { margin-top: 0; font-size: 1.4rem; }
    .form-group {
      margin-bottom: 20px;
      display: flex;
      flex-direction: column;
    }
    label {
      font-weight: 500;
      margin-bottom: 6px;
      font-size: 0.9rem;
    }
    input[type="text"], input[type="email"] {
      padding: 10px 14px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 1rem;
    }
    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 24px;
    }
    .actions {
      display: flex;
      gap: 12px;
    }
    button {
      padding: 10px 20px;
      border-radius: 6px;
      font-weight: 500;
      cursor: pointer;
      border: 1px solid transparent;
      font-size: 0.95rem;
    }
    .btn-save {
      background: #2563eb;
      color: #ffffff;
    }
    .btn-save:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .btn-discard {
      background: #f1f5f9;
      color: #475569;
      border-color: #cbd5e1;
    }
    .btn-discard:hover {
      background: #e2e8f0;
    }
    .feedback {
      margin-top: 16px;
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
    .dirty-badge {
      font-size: 0.75rem;
      background: #fef3c7;
      color: #92400e;
      padding: 2px 8px;
      border-radius: 12px;
      margin-left: 8px;
      display: none;
    }
  </style>
</head>
<body>
  <div class="card">
    <h2>
      Account Settings
      <span id="dirty-badge" class="dirty-badge">Unsaved changes</span>
    </h2>
    <form id="settings-form" novalidate>
      <div class="form-group">
        <label for="name">Full Name</label>
        <input type="text" id="name" name="name" required autocomplete="name">
      </div>
      <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" required autocomplete="email">
      </div>
      <div class="checkbox-group">
        <input type="checkbox" id="notifications" name="notifications">
        <label for="notifications">Receive email alerts</label>
      </div>
      <div class="actions">
        <button type="submit" id="save-btn" class="btn-save">Save Changes</button>
        <button type="button" id="discard-btn" class="btn-discard">Discard Changes</button>
      </div>
      <div id="feedback" class="feedback" role="alert"></div>
    </form>
  </div>

  <script>
    const initialSettings = {
      name: "Ada Lovelace",
      email: "ada@example.com",
      notifications: true
    };

    let isSubmitting = false;

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const notifInput = document.getElementById('notifications');
    const dirtyBadge = document.getElementById('dirty-badge');
    const feedback = document.getElementById('feedback');
    const saveBtn = document.getElementById('save-btn');
    const discardBtn = document.getElementById('discard-btn');
    const form = document.getElementById('settings-form');

    function populateForm(data) {
      nameInput.value = data.name;
      emailInput.value = data.email;
      notifInput.checked = data.notifications;
      checkDirty();
    }

    function checkDirty() {
      const isDirty = (
        nameInput.value !== initialSettings.name ||
        emailInput.value !== initialSettings.email ||
        notifInput.checked !== initialSettings.notifications
      );
      dirtyBadge.style.display = isDirty ? 'inline' : 'none';
    }

    nameInput.addEventListener('input', checkDirty);
    emailInput.addEventListener('input', checkDirty);
    notifInput.addEventListener('change', checkDirty);

    discardBtn.addEventListener('click', () => {
      populateForm(initialSettings);
      feedback.style.display = 'none';
    });

    function isValidEmail(val) {
      return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(val);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (isSubmitting) return;

      const nameVal = nameInput.value.trim();
      const emailVal = emailInput.value.trim();

      if (!nameVal) {
        feedback.className = 'feedback error';
        feedback.innerText = 'Validation Error: Full Name is required.';
        nameInput.focus();
        return;
      }

      if (!isValidEmail(emailVal)) {
        feedback.className = 'feedback error';
        feedback.innerText = 'Validation Error: Please enter a valid email address.';
        emailInput.focus();
        return;
      }

      isSubmitting = true;
      saveBtn.disabled = true;
      saveBtn.innerText = 'Saving...';
      feedback.style.display = 'none';

      try {
        const res = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: nameVal,
            email: emailVal,
            notifications: notifInput.checked
          })
        });

        if (!res.ok) {
          throw new Error('Server returned error code ' + res.status);
        }

        const data = await res.json();
        initialSettings.name = nameVal;
        initialSettings.email = emailVal;
        initialSettings.notifications = notifInput.checked;
        checkDirty();

        feedback.style.display = 'block';
        feedback.className = 'feedback success';
        feedback.innerText = 'Settings saved successfully!';
      } catch (err) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Failed to save settings: ' + err.message;
      } finally {
        isSubmitting = false;
        saveBtn.disabled = false;
        saveBtn.innerText = 'Save Changes';
      }
    });

    populateForm(initialSettings);
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []

    # Test A.1: Render Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_name = session.page.locator("input[type='text'], input#name, input[name='name']").count() > 0
        has_email = session.page.locator("input[type='email'], input#email, input[name='email']").count() > 0
        has_notify = session.page.locator("input[type='checkbox'], input#notifications, input[name='notifications'], input[name='emailNotifications']").count() > 0
        has_save = session.page.locator("button:has-text('Save'), input[type='submit']:has-text('Save'), button#save-btn").count() > 0
        has_discard = session.page.locator("button:has-text('Discard'), button:has-text('Cancel'), button#discard-btn").count() > 0

        passed = has_name and has_email and has_notify and has_save and has_discard
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Name: {has_name}, Email: {has_email}, Notify: {has_notify}, Save: {has_save}, Discard: {has_discard}",
            failure_type="Functional failure: Missing core form inputs or action buttons" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Functional failure: Exception rendering settings panel"
        ))

    # Test A.2: Expected Interaction - Successful Save
    session = harness.new_session()
    session.mock_route("**/api/settings*", status=200, json_body={"status": "saved", "updated_at": "2026-10-06T12:00:00Z"})

    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        email_box = session.page.locator("input[type='email'], input#email, input[name='email']").first
        save_btn = session.page.locator("button:has-text('Save'), button#save-btn, input[type='submit']").first

        name_box.fill("Ada Lovelace")
        email_box.fill("ada@analytical.engine")
        session.click(save_btn)
        session.page.wait_for_timeout(500)

        network_success = len(session.intercepted_requests) >= 1
        content_lower = session.visible_text()
        success_ui = any(w in content_lower for w in ["saved", "success", "updated"])

        passed = network_success and success_ui
        results.append(TestResult(
            test_name="demo_save_success",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Network success={network_success} (calls={len(session.intercepted_requests)}), UI feedback={success_ui}",
            failure_type="Interaction failure: Did not submit valid settings to /api/settings or display success feedback" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_save_success",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Interaction failure: Exception during save flow"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Input Robustness - Blank Name and Invalid Email Rejection
    session = harness.new_session()
    session.mock_route("**/api/settings*", status=200, json_body={"status": "saved"})

    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        email_box = session.page.locator("input[type='email'], input#email, input[name='email']").first
        save_btn = session.page.locator("button:has-text('Save'), button#save-btn, input[type='submit']").first

        # Case 1: blank name
        name_box.fill("   ")
        email_box.fill("valid@domain.com")
        session.click(save_btn)
        session.page.wait_for_timeout(300)

        blank_rejected = len(session.intercepted_requests) == 0

        # Case 2: invalid email
        name_box.fill("Alan Turing")
        email_box.fill("invalid-email-address")
        session.click(save_btn)
        session.page.wait_for_timeout(300)

        email_rejected = len(session.intercepted_requests) == 0

        is_invalid_email = session.page.evaluate("""() => {
            const el = document.querySelector("input[type='email'], input#email, input[name='email']");
            return el ? !el.checkValidity() : false;
        }""")

        val_passed = blank_rejected and (email_rejected or is_invalid_email)
        results.append(TestResult(
            test_name="reality_input_validation",
            category="input_robustness",
            regime="reality",
            passed=val_passed,
            details=f"Blank name blocked={blank_rejected}, Invalid email blocked={email_rejected or is_invalid_email}",
            failure_type="Input robustness failure: Submitted invalid or whitespace data to API" if not val_passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_input_validation",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing input validation"
        ))

    # Test B.2: State Robustness - Discard Changes Restores Initial State
    session = harness.new_session()
    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        discard_btn = session.page.locator("button:has-text('Discard'), button:has-text('Cancel'), button#discard-btn").first

        initial_val = name_box.input_value()

        name_box.fill("Modified Value 999")
        session.page.wait_for_timeout(200)

        session.page.on("dialog", lambda dialog: dialog.accept())
        session.click(discard_btn)
        session.page.wait_for_timeout(300)

        restored_val = name_box.input_value()
        state_restored = (restored_val == initial_val) and (restored_val != "Modified Value 999")

        results.append(TestResult(
            test_name="reality_discard_restoration",
            category="state_robustness",
            regime="reality",
            passed=state_restored,
            details=f"Initial='{initial_val}', Modified='Modified Value 999', Restored='{restored_val}'",
            failure_type="State robustness failure: Discard Changes did not restore initial settings values" if not state_restored else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_discard_restoration",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception testing discard restoration"
        ))

    # Test B.3: Failure Recovery - HTTP 500 Preserves User Input
    session = harness.new_session()
    session.mock_route("**/api/settings*", status=500, json_body={"error": "Database error", "message": "Failed to persist settings"})

    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        email_box = session.page.locator("input[type='email'], input#email, input[name='email']").first
        save_btn = session.page.locator("button:has-text('Save'), button#save-btn, input[type='submit']").first

        test_name = "Grace Hopper"
        test_email = "grace@compiler.org"
        name_box.fill(test_name)
        email_box.fill(test_email)
        session.click(save_btn)
        session.page.wait_for_timeout(500)

        content_lower = session.visible_text()
        has_error_ui = any(w in content_lower for w in ["error", "fail", "500", "problem"])

        curr_name = name_box.input_value()
        curr_email = email_box.input_value()
        input_preserved = (curr_name == test_name) and (curr_email == test_email)

        recovery_passed = has_error_ui and input_preserved
        results.append(TestResult(
            test_name="reality_error_recovery_500",
            category="failure_recovery",
            regime="reality",
            passed=recovery_passed,
            details=f"Error feedback={has_error_ui}, Form values preserved={input_preserved} (Name='{curr_name}')",
            failure_type="Failure recovery failure: Wiped user form inputs or failed to show error message on HTTP 500" if not recovery_passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_error_recovery_500",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Failure recovery failure: Exception testing 500 server error recovery"
        ))

    # Test B.4: Interaction Safety - Rapid Double-Click Debounce
    session = harness.new_session()
    session.mock_route("**/api/settings*", status=200, json_body={"status": "saved"}, delay_ms=300)

    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        email_box = session.page.locator("input[type='email'], input#email, input[name='email']").first
        save_btn = session.page.locator("button:has-text('Save'), button#save-btn, input[type='submit']").first

        name_box.fill("Linus Torvalds")
        email_box.fill("torvalds@kernel.org")

        save_btn.click(click_count=2, delay=20)
        session.page.wait_for_timeout(800)

        debounce_ok = len(session.intercepted_requests) == 1
        results.append(TestResult(
            test_name="reality_double_click_safety",
            category="interaction_safety",
            regime="reality",
            passed=debounce_ok,
            details=f"API requests dispatched during double click: {len(session.intercepted_requests)} (expected 1)",
            failure_type="Interaction safety failure: Dispatched duplicate save requests on rapid double-click" if not debounce_ok else ""
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

    # Test B.5: Accessibility - Form Labels
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
            failure_type="Accessibility failure: Missing proper form labels for screen readers" if not has_accessible_controls else ""
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


def grade_settings_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the User Settings Panel.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    report = calculate_scores("realitybench-settings", demo_results + reality_results)
    report.fake_backend = harness.fake_backend
    return report


# %%
@kbench.task(name="realitybench-settings")
def realitybench_settings(llm) -> dict:
    """
    Evaluates LLM on User Settings software generation.
    """
    response = llm.prompt(SETTINGS_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_settings_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional settings panel on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    if should_run_kbench():
        realitybench_settings.run(kbench.llm)
    else:
        for label, code in (("naive", NAIVE_SETTINGS_CODE), ("robust", ROBUST_SETTINGS_CODE)):
            r = grade_settings_implementation(code)
            print(f"{label:6} demo={r.demo_score:.2f} reality={r.reality_score:.2f} gap={r.reality_gap:+.2f}")
