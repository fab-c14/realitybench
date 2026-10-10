# %%
"""
TASK: Multi-Step Workflow Wizard
Task Index: 12
Identifier: realitybench-workflow

Purpose:
  Evaluates whether generated multi-step wizard software correctly handles inter-step
  state preservation, step validation boundaries, back navigation, network recovery,
  and debounce on final checkout/submission.

Happy Path (Demo Regime):
  - demo_elements_rendered: Account inputs, step navigation, and wizard indicators render.
  - demo_complete_workflow: Progresses through Step 1 (Account), Step 2 (Plan), Step 3 (Review), and submits to /api/workflow/complete with confirmed order UI.

Reality Tests (Perturbation Regime):
  - reality_incomplete_step_progression_blocked: Blank or invalid Step 1 values prevent progression to Step 2.
  - reality_back_navigation_state_preservation: Clicking 'Back' preserves previously entered values across step transitions.
  - reality_final_submission_failure_recovery: HTTP 500 on final submission displays error feedback and preserves all entered data on Step 3 for retrying.
  - reality_double_click_safety: Rapid double-clicking 'Submit Order' button dispatches exactly one POST request.
  - reality_accessibility_steps_and_labels: Form fields have semantic labels and wizard contains accessible step landmarks.
  - reality_mobile_responsive: Layout maintains zero horizontal overflow on mobile viewport (375x667).

Scoring:
  - Demo Score: Rendering and successful completion of full 3-step wizard workflow.
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
from benchmark.kaggle_runtime import should_run_kbench
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code


# =============================================================================
# Task Prompts & Specifications
# =============================================================================

WORKFLOW_TASK_PROMPT = """Build a self-contained 3-step onboarding workflow wizard component in HTML, CSS, and JavaScript.
The workflow must contain:
1. Step 1: Account Information
   - Full Name (text input)
   - Email Address (email input)
   - 'Next' button
2. Step 2: Subscription Plan
   - Plan selection (dropdown or radio group: 'Starter', 'Professional', 'Enterprise')
   - 'Back' button and 'Next' button
3. Step 3: Review & Confirmation
   - Summary display showing the entered name, email, and selected plan
   - Terms & Conditions checkbox ('I accept the terms and conditions')
   - 'Back' button and 'Submit Order' button
When the user submits on Step 3, send a POST request to '/api/workflow/complete' with { 'name': '...', 'email': '...', 'plan': '...', 'terms': true }.
Upon success (returns { 'status': 'completed', 'order_id': 'ORD-9876' }), display an order completion screen with the order ID.
The application should:
- Prevent advancing to Step 2 if Step 1 fields are blank or invalid
- Preserve all user-entered data when clicking 'Back' to return to previous steps
- Handle submission failures on Step 3 (e.g., HTTP 500): show a clear error message and preserve the user's data on Step 3 so they can retry without restarting from Step 1
- Prevent duplicate order submissions if 'Submit Order' is clicked multiple times rapidly
- Ensure accessible controls and step indicators
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = WORKFLOW_TASK_PROMPT


# =============================================================================
# Reference Implementations
# =============================================================================

NAIVE_WORKFLOW_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Setup Wizard</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .step-section { margin-bottom: 20px; }
    input[type="text"], input[type="email"], select { width: 280px; padding: 6px; margin-bottom: 10px; display: block; }
    button { padding: 8px 16px; margin-right: 10px; }
  </style>
</head>
<body>
  <h2>Setup Wizard</h2>

  <div id="step-1" class="step-section">
    <h3>Step 1: Account</h3>
    Name: <input type="text" id="name">
    Email: <input type="email" id="email">
    <button onclick="goToStep(2)">Next</button>
  </div>

  <div id="step-2" class="step-section" style="display:none;">
    <h3>Step 2: Plan</h3>
    Plan:
    <select id="plan">
      <option value="starter">Starter</option>
      <option value="pro">Professional</option>
      <option value="enterprise">Enterprise</option>
    </select>
    <!-- Naive back wipes inputs by resetting form or replacing HTML -->
    <button onclick="naiveBack()">Back</button>
    <button onclick="goToStep(3)">Next</button>
  </div>

  <div id="step-3" class="step-section" style="display:none;">
    <h3>Step 3: Review</h3>
    <div id="summary"></div>
    <label><input type="checkbox" id="terms" checked> I accept the terms</label><br><br>
    <button onclick="goToStep(2)">Back</button>
    <button id="submit-btn" onclick="submitWorkflow()">Submit Order</button>
  </div>

  <div id="status"></div>

  <script>
    let currentStep = 1;

    function goToStep(n) {
      // Naive: no validation check before proceeding
      document.getElementById('step-1').style.display = (n === 1) ? 'block' : 'none';
      document.getElementById('step-2').style.display = (n === 2) ? 'block' : 'none';
      document.getElementById('step-3').style.display = (n === 3) ? 'block' : 'none';
      currentStep = n;
      if (n === 3) {
        document.getElementById('summary').innerText = 'Account: ' + document.getElementById('name').value;
      }
    }

    function naiveBack() {
      // Naive wipes data on back navigation
      document.getElementById('name').value = '';
      document.getElementById('email').value = '';
      goToStep(1);
    }

    async function submitWorkflow() {
      const name = document.getElementById('name').value;
      const email = document.getElementById('email').value;
      const plan = document.getElementById('plan').value;
      const terms = document.getElementById('terms').checked;

      // Naive: no double click protection, wipes data on failure
      try {
        const res = await fetch('/api/workflow/complete', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name, email, plan, terms })
        });
        if (res.ok) {
          const data = await res.json();
          document.getElementById('status').innerText = 'Order completed! Order ID: ' + data.order_id;
        } else {
          // Naive: wipes data on error and resets to step 1
          document.getElementById('name').value = '';
          document.getElementById('email').value = '';
          goToStep(1);
          document.getElementById('status').innerText = 'Server error occurred.';
        }
      } catch (err) {
        document.getElementById('status').innerText = 'Network error.';
      }
    }
  </script>
</body>
</html>
"""

ROBUST_WORKFLOW_CODE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Setup Wizard</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 24px;
      background: #f8fafc;
      color: #1e293b;
    }
    .wizard-card {
      max-width: 520px;
      margin: 0 auto;
      background: #ffffff;
      padding: 28px;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .step-indicator {
      display: flex;
      justify-content: space-between;
      margin-bottom: 24px;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 14px;
    }
    .step-pill {
      font-size: 0.85rem;
      font-weight: 600;
      color: #94a3b8;
    }
    .step-pill.active {
      color: #2563eb;
    }
    h2 { margin-top: 0; font-size: 1.3rem; }
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
    input[type="text"], input[type="email"], select {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.95rem;
    }
    input:focus, select:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
    .nav-buttons {
      display: flex;
      justify-content: space-between;
      margin-top: 24px;
      gap: 12px;
    }
    button {
      padding: 10px 20px;
      font-size: 0.95rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s;
    }
    .btn-primary {
      background: #2563eb;
      color: #ffffff;
      margin-left: auto;
    }
    .btn-primary:hover:not(:disabled) {
      background: #1d4ed8;
    }
    .btn-primary:disabled {
      background: #94a3b8;
      cursor: not-allowed;
    }
    .btn-secondary {
      background: #f1f5f9;
      color: #475569;
      border-color: #cbd5e1;
    }
    .btn-secondary:hover {
      background: #e2e8f0;
    }
    .review-summary {
      background: #f8fafc;
      padding: 16px;
      border-radius: 8px;
      margin-bottom: 18px;
      font-size: 0.92rem;
      line-height: 1.6;
      border: 1px solid #e2e8f0;
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
  </style>
</head>
<body>
  <div class="wizard-card">
    <div class="step-indicator" role="navigation" aria-label="Wizard Steps">
      <span id="pill-1" class="step-pill active">1. Account</span>
      <span id="pill-2" class="step-pill">2. Plan</span>
      <span id="pill-3" class="step-pill">3. Confirmation</span>
    </div>

    <!-- Step 1 -->
    <div id="step-1" class="wizard-step">
      <h2>Account Information</h2>
      <div class="form-group">
        <label for="name">Full Name</label>
        <input type="text" id="name" name="name" required>
      </div>
      <div class="form-group">
        <label for="email">Email Address</label>
        <input type="email" id="email" name="email" required>
      </div>
      <div class="nav-buttons">
        <button type="button" class="btn-primary" onclick="handleStep1Next()">Next</button>
      </div>
    </div>

    <!-- Step 2 -->
    <div id="step-2" class="wizard-step" style="display: none;">
      <h2>Choose Subscription Plan</h2>
      <div class="form-group">
        <label for="plan">Select Plan</label>
        <select id="plan" name="plan">
          <option value="starter">Starter Plan ($19/mo)</option>
          <option value="pro">Professional Plan ($49/mo)</option>
          <option value="enterprise">Enterprise Plan ($199/mo)</option>
        </select>
      </div>
      <div class="nav-buttons">
        <button type="button" class="btn-secondary" onclick="setStep(1)">Back</button>
        <button type="button" class="btn-primary" onclick="handleStep2Next()">Next</button>
      </div>
    </div>

    <!-- Step 3 -->
    <div id="step-3" class="wizard-step" style="display: none;">
      <h2>Review & Confirmation</h2>
      <div id="summary" class="review-summary"></div>
      <div class="form-group" style="flex-direction: row; align-items: center; gap: 8px;">
        <input type="checkbox" id="terms" name="terms" checked>
        <label for="terms" style="margin-bottom: 0; cursor: pointer;">I accept the terms and conditions</label>
      </div>
      <div class="nav-buttons">
        <button type="button" class="btn-secondary" onclick="setStep(2)">Back</button>
        <button type="button" id="submit-btn" class="btn-primary" onclick="submitOrder()">Submit Order</button>
      </div>
    </div>

    <div id="feedback" class="feedback" role="alert"></div>
  </div>

  <script>
    let currentStep = 1;
    let isSubmitting = false;

    // Persistent workflow state
    const state = {
      name: '',
      email: '',
      plan: 'pro',
      terms: true
    };

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const planSelect = document.getElementById('plan');
    const termsInput = document.getElementById('terms');
    const summaryBox = document.getElementById('summary');
    const feedback = document.getElementById('feedback');
    const submitBtn = document.getElementById('submit-btn');

    function setStep(step) {
      currentStep = step;
      document.getElementById('step-1').style.display = (step === 1) ? 'block' : 'none';
      document.getElementById('step-2').style.display = (step === 2) ? 'block' : 'none';
      document.getElementById('step-3').style.display = (step === 3) ? 'block' : 'none';

      document.getElementById('pill-1').className = 'step-pill' + (step === 1 ? ' active' : '');
      document.getElementById('pill-2').className = 'step-pill' + (step === 2 ? ' active' : '');
      document.getElementById('pill-3').className = 'step-pill' + (step === 3 ? ' active' : '');

      feedback.style.display = 'none';

      if (step === 3) {
        summaryBox.innerHTML = `
          <strong>Account:</strong> ${escapeHtml(state.name)} (${escapeHtml(state.email)})<br>
          <strong>Selected Plan:</strong> ${escapeHtml(state.plan.toUpperCase())}
        `;
      }
    }

    function escapeHtml(str) {
      return (str || '').replace(/[&<>"']/g, m => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[m]);
    }

    function handleStep1Next() {
      const nameVal = nameInput.value.trim();
      const emailVal = emailInput.value.trim();

      if (!nameVal || !emailVal) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Validation Error: Please fill in both Name and Email.';
        return;
      }

      state.name = nameVal;
      state.email = emailVal;
      setStep(2);
    }

    function handleStep2Next() {
      state.plan = planSelect.value;
      setStep(3);
    }

    async function submitOrder() {
      if (isSubmitting) return;

      if (!termsInput.checked) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Validation Error: You must accept the terms.';
        return;
      }

      isSubmitting = true;
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting...';
      feedback.style.display = 'none';

      try {
        const res = await fetch('/api/workflow/complete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: state.name,
            email: state.email,
            plan: state.plan,
            terms: true
          })
        });

        if (!res.ok) {
          throw new Error('Server returned HTTP ' + res.status);
        }

        const data = await res.json();
        feedback.style.display = 'block';
        feedback.className = 'feedback success';
        feedback.innerText = 'Order completed successfully! Order ID: ' + (data.order_id || 'ORD-9876');
      } catch (err) {
        feedback.style.display = 'block';
        feedback.className = 'feedback error';
        feedback.innerText = 'Order submission failed: ' + err.message + '. Please retry.';
      } finally {
        isSubmitting = false;
        submitBtn.disabled = false;
        submitBtn.innerText = 'Submit Order';
      }
    }
  </script>
</body>
</html>
"""


# =============================================================================
# Sub-Test Execution Functions
# =============================================================================

def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates Multi-Step Workflow Wizard on standard expected operations."""
    results: List[TestResult] = []

    # Test A.1: Render Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_name = session.page.locator("input[type='text'], input#name, input[name='name']").count() > 0
        has_email = session.page.locator("input[type='email'], input#email, input[name='email']").count() > 0
        has_next = session.page.locator("button:has-text('Next'), input[type='button']:has-text('Next')").count() > 0
        has_steps = session.page.locator(".step, .wizard-step, [data-step], ol, ul").count() > 0

        passed = has_name and has_email and has_next
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Name: {has_name}, Email: {has_email}, Next Button: {has_next}, Steps UI: {has_steps}",
            failure_type="Functional failure: Missing initial wizard inputs or step controls" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_elements_rendered",
            category="functional_correctness",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Functional failure: Exception rendering workflow wizard"
        ))

    # Test A.2: Expected Interaction - Complete Full 3-Step Flow
    session = harness.new_session()
    session.mock_route("**/api/workflow/complete*", status=200, json_body={"status": "completed", "order_id": "ORD-9876"})

    try:
        session.load_html(html_code)
        # Step 1
        name_box = session.page.locator("input[type='text'], input#name, input[name='name']").first
        email_box = session.page.locator("input[type='email'], input#email, input[name='email']").first
        next_btn = session.page.locator("button:has-text('Next'):visible").first

        name_box.fill("Margaret Hamilton")
        email_box.fill("margaret@apollo.nasa.gov")
        next_btn.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Step 2: Plan selection
        plan_select = session.page.locator("select#plan:visible, select[name='plan']:visible, input[type='radio'][value*='pro' i]:visible, input[type='radio']:visible").first
        if plan_select.count() > 0:
            if plan_select.evaluate("el => el.tagName.toLowerCase()") == "select":
                plan_select.select_option(index=1)
            else:
                plan_select.check()

        # Click next to Step 3
        session.page.locator("button:has-text('Next'):visible").first.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Step 3: Terms & Submit
        terms_box = session.page.locator("input[type='checkbox']:visible").first
        if terms_box.count() > 0 and not terms_box.is_checked():
            terms_box.check()

        submit_btn = session.page.locator("button:has-text('Submit'):visible, button:has-text('Complete'):visible, button:has-text('Order'):visible").first
        submit_btn.click(timeout=3000)
        session.page.wait_for_timeout(500)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        posted_data = len(post_requests) >= 1
        content_lower = session.visible_text()
        shows_success = any(w in content_lower for w in ["completed", "order_id", "ord-9876", "success", "confirmed"])

        passed = posted_data and shows_success
        results.append(TestResult(
            test_name="demo_complete_workflow",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST dispatched={posted_data}, Order confirmation UI={shows_success}",
            failure_type="Interaction failure: Did not advance through wizard steps or submit order" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="demo_complete_workflow",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Interaction failure: Exception during multi-step workflow flow"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates Multi-Step Workflow Wizard under adversarial conditions and perturbations."""
    results: List[TestResult] = []

    # Test B.1: Input Robustness - Prevent Advancing Step 1 with Blank Fields
    session = harness.new_session()
    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text']:visible, input#name:visible, input[name='name']:visible").first
        email_box = session.page.locator("input[type='email']:visible, input#email:visible, input[name='email']:visible").first
        next_btn = session.page.locator("button:has-text('Next'):visible").first

        # Clear inputs and click Next
        name_box.fill("")
        email_box.fill("")
        next_btn.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Verify still on Step 1 (name_box still visible or Step 2 not reached)
        is_name_visible = name_box.is_visible()
        step1_blocked = is_name_visible

        results.append(TestResult(
            test_name="reality_incomplete_step_progression_blocked",
            category="input_robustness",
            regime="reality",
            passed=step1_blocked,
            details=f"Blocked invalid progression past Step 1: {step1_blocked}",
            failure_type="Input robustness failure: Advanced to Step 2 with empty required account fields" if not step1_blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_incomplete_step_progression_blocked",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing step 1 validation"
        ))

    # Test B.2: State Robustness - Back Navigation Preserves Entered Data
    session = harness.new_session()
    try:
        session.load_html(html_code)
        name_box = session.page.locator("input[type='text']:visible, input#name:visible, input[name='name']:visible").first
        email_box = session.page.locator("input[type='email']:visible, input#email:visible, input[name='email']:visible").first
        next_btn = session.page.locator("button:has-text('Next'):visible").first

        test_name = "Katherine Johnson"
        test_email = "kjohnson@orbital.nasa.gov"
        name_box.fill(test_name)
        email_box.fill(test_email)
        next_btn.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Now on Step 2 -> Click Back button
        back_btn = session.page.locator("button:has-text('Back'):visible").first
        back_btn.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Check that Step 1 fields still retain values
        curr_name = session.page.locator("input[type='text'], input#name, input[name='name']").first.input_value()
        curr_email = session.page.locator("input[type='email'], input#email, input[name='email']").first.input_value()
        state_preserved = (curr_name == test_name) and (curr_email == test_email)

        results.append(TestResult(
            test_name="reality_back_navigation_state_preservation",
            category="state_robustness",
            regime="reality",
            passed=state_preserved,
            details=f"Values preserved on Back navigation: {state_preserved} (Name='{curr_name}', Email='{curr_email}')",
            failure_type="State robustness failure: Back navigation wiped previously entered step data" if not state_preserved else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_back_navigation_state_preservation",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception testing back navigation"
        ))

    # Test B.3: Failure Recovery - HTTP 500 at Step 3 Preserves Workflow State & Allows Retry
    session = harness.new_session()
    session.mock_route("**/api/workflow/complete*", status=500, json_body={"error": "Payment Service Unavailable"})

    try:
        session.load_html(html_code)
        # Advance to Step 2
        session.page.locator("input[type='text']:visible, input#name:visible, input[name='name']:visible").first.fill("Dorothy Vaughan")
        session.page.locator("input[type='email']:visible, input#email:visible, input[name='email']:visible").first.fill("dorothy@nasa.gov")
        session.page.locator("button:has-text('Next'):visible").first.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Advance to Step 3
        plan_select = session.page.locator("select#plan:visible, select[name='plan']:visible, input[type='radio']:visible").first
        if plan_select.count() > 0:
            if plan_select.evaluate("el => el.tagName.toLowerCase()") == "select":
                plan_select.select_option(index=1)
            else:
                plan_select.check()
        session.page.locator("button:has-text('Next'):visible").first.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Check terms if present & submit
        terms_box = session.page.locator("input[type='checkbox']:visible").first
        if terms_box.count() > 0 and not terms_box.is_checked():
            terms_box.check()

        submit_btn = session.page.locator("button:has-text('Submit'):visible, button:has-text('Complete'):visible, button:has-text('Order'):visible").first
        submit_btn.click(timeout=3000)
        session.page.wait_for_timeout(500)

        content_lower = session.visible_text()
        has_error_ui = any(w in content_lower for w in ["error", "fail", "unavailable", "500", "retry"])
        retains_data = "dorothy" in content_lower

        recovery_passed = has_error_ui and retains_data
        results.append(TestResult(
            test_name="reality_final_submission_failure_recovery",
            category="failure_recovery",
            regime="reality",
            passed=recovery_passed,
            details=f"Error feedback shown={has_error_ui}, Workflow data preserved on Step 3={retains_data}",
            failure_type="Failure recovery failure: Wiped wizard data or failed to show error message on HTTP 500" if not recovery_passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_final_submission_failure_recovery",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Failure recovery failure: Exception testing step 3 submission failure"
        ))

    # Test B.4: Interaction Safety - Rapid Double-Click Debounce
    session = harness.new_session()
    session.mock_route("**/api/workflow/complete*", status=200, json_body={"status": "completed", "order_id": "ORD-123"}, delay_ms=300)

    try:
        session.load_html(html_code)
        # Step 1
        session.page.locator("input[type='text']:visible, input#name:visible, input[name='name']:visible").first.fill("Mary Jackson")
        session.page.locator("input[type='email']:visible, input#email:visible, input[name='email']:visible").first.fill("mary@nasa.gov")
        session.page.locator("button:has-text('Next'):visible").first.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Step 2
        plan_select = session.page.locator("select#plan:visible, select[name='plan']:visible, input[type='radio']:visible").first
        if plan_select.count() > 0:
            if plan_select.evaluate("el => el.tagName.toLowerCase()") == "select":
                plan_select.select_option(index=1)
            else:
                plan_select.check()
        session.page.locator("button:has-text('Next'):visible").first.click(timeout=3000)
        session.page.wait_for_timeout(300)

        # Step 3
        terms_box = session.page.locator("input[type='checkbox']:visible").first
        if terms_box.count() > 0 and not terms_box.is_checked():
            terms_box.check()

        submit_btn = session.page.locator("button:has-text('Submit'):visible, button:has-text('Complete'):visible, button:has-text('Order'):visible").first

        # Double click submit button
        submit_btn.click(click_count=2, delay=20, timeout=3000)
        session.page.wait_for_timeout(800)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        debounce_ok = len(post_requests) == 1

        results.append(TestResult(
            test_name="reality_double_click_safety",
            category="interaction_safety",
            regime="reality",
            passed=debounce_ok,
            details=f"POST requests dispatched on rapid double click: {len(post_requests)} (expected 1)",
            failure_type="Interaction safety failure: Dispatched duplicate workflow submissions on double click" if not debounce_ok else ""
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

    # Test B.5: Accessibility - Semantic Controls & Step Indicator
    session = harness.new_session()
    try:
        session.load_html(html_code)
        labels_count = session.page.locator("label").count()
        aria_count = session.page.locator("[aria-label], [aria-current], [role='progressbar'], [role='tablist']").count()
        has_accessible_ui = (labels_count >= 2) or (aria_count >= 1)

        results.append(TestResult(
            test_name="reality_accessibility_steps_and_labels",
            category="accessibility",
            regime="reality",
            passed=has_accessible_ui,
            details=f"Found {labels_count} <label> elements and {aria_count} accessible ARIA/step attributes",
            failure_type="Accessibility failure: Missing proper labels or accessible step landmarks" if not has_accessible_ui else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reality_accessibility_steps_and_labels",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting accessibility"
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

def grade_workflow_implementation(html_code: str) -> EvaluationReport:
    """Executes deterministic headless browser evaluation of the Multi-Step Workflow Wizard."""
    results: List[TestResult] = []

    with HeadlessHarness() as harness:
        results.extend(run_happy_path(harness, html_code))
        results.extend(run_reality_tests(harness, html_code))

    return calculate_scores("realitybench-workflow", results)


# %%
@kbench.task(name="realitybench-workflow")
def realitybench_workflow(llm) -> dict:
    """Evaluates LLM on Multi-Step Workflow software generation."""
    response = llm.prompt(WORKFLOW_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_workflow_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional multi-step workflow on happy path"
    )
    return report.to_dict()


if __name__ == "__main__":
    if should_run_kbench():
        realitybench_workflow.run(kbench.llm)
    else:
        for label, code in (("naive", NAIVE_WORKFLOW_CODE), ("robust", ROBUST_WORKFLOW_CODE)):
            r = grade_workflow_implementation(code)
            print(f"{label:6} demo={r.demo_score:.2f} reality={r.reality_score:.2f} gap={r.reality_gap:+.2f}")
