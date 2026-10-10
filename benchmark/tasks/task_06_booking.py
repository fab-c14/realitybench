# %%
"""
TASK: Booking Component (Task 06)

Purpose:
Evaluate whether an AI-generated appointment booking component validates past dates,
handles slot conflicts (HTTP 409) without wiping client state, validates contacts,
prevents double-booking submissions, and meets accessibility/mobile standards.

Happy Path:
- Renders date picker, time slot selector, contact inputs, and confirm button
- Successful booking flow submitting POST to /api/book and displaying confirmation

Reality Tests:
- Past dates rejected (via min date attribute or validation error feedback)
- Slot conflict (HTTP 409) handled gracefully with error while preserving form field inputs
- Blank / missing contact information rejected before network dispatch
- Double-click prevention: Rapid duplicate clicks send only a single POST request
- Accessible labels associated with form fields
- Responsive behavior: 375px mobile viewport has no horizontal scroll overflow

Scoring:
Demo Score: functional_correctness (25%), expected_interactions (15%)
Reality Score: failure_recovery (20%), state_robustness (15%), input_robustness (10%),
               accessibility (7%), responsive_behavior (5%), interaction_safety (3%)
"""

import sys
import os
from datetime import datetime, timedelta
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


BOOKING_TASK_PROMPT = """Build a self-contained appointment booking component in HTML, CSS, and JavaScript.
The interface must contain:
1. Date picker input (cannot book dates in the past)
2. Time slot selector (options: '09:00 AM', '11:00 AM', '02:00 PM', '04:00 PM')
3. Client contact inputs (Full Name, Phone Number)
4. A 'Confirm Booking' submit button
When submitted, the application should make a POST request to '/api/book' with { 'date': '...', 'slot': '...', 'name': '...', 'phone': '...' }.
Upon successful booking (returns { 'status': 'confirmed', 'booking_id': 'BK-789' }), display a confirmation message with the booking ID.
The application should validate all inputs, handle unavailable slots (HTTP 409 Conflict) without clearing other user form fields, and provide appropriate user feedback.
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = BOOKING_TASK_PROMPT

NAIVE_BOOKING_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Book Appointment</h2>
  <input type="date" id="date">
  <select id="slot">
    <option value="09:00 AM">09:00 AM</option>
    <option value="11:00 AM">11:00 AM</option>
  </select>
  <input type="text" id="name" placeholder="Name">
  <input type="tel" id="phone" placeholder="Phone">
  <button onclick="book()">Confirm Booking</button>
  <div id="status"></div>
  <script>
    function book() {
      const date = document.getElementById('date').value;
      const slot = document.getElementById('slot').value;
      const name = document.getElementById('name').value;
      const phone = document.getElementById('phone').value;
      fetch('/api/book', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ date, slot, name, phone })
      })
      .then(r => r.json())
      .then(d => {
        document.getElementById('status').innerText = 'Confirmed: ' + d.booking_id;
        document.getElementById('name').value = '';
        document.getElementById('phone').value = '';
      });
    }
  </script>
</body>
</html>
"""

ROBUST_BOOKING_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Appointment Booking</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 20px; max-width: 450px; margin: 0 auto; }
    .form-group { margin-bottom: 14px; }
    label { display: block; margin-bottom: 4px; font-weight: 500; }
    input, select { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; }
    button { width: 100%; padding: 10px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .error { color: #dc2626; margin-top: 10px; }
    .success { color: #16a34a; margin-top: 10px; }
  </style>
</head>
<body>
  <h2>Book an Appointment</h2>
  <form id="booking-form">
    <div class="form-group">
      <label for="book-date">Select Date</label>
      <input type="date" id="book-date" name="date" required>
    </div>
    <div class="form-group">
      <label for="book-slot">Available Time Slot</label>
      <select id="book-slot" name="slot" required>
        <option value="">Choose a slot</option>
        <option value="09:00 AM">09:00 AM</option>
        <option value="11:00 AM">11:00 AM</option>
        <option value="02:00 PM">02:00 PM</option>
        <option value="04:00 PM">04:00 PM</option>
      </select>
    </div>
    <div class="form-group">
      <label for="client-name">Full Name</label>
      <input type="text" id="client-name" name="name" placeholder="John Doe" required>
    </div>
    <div class="form-group">
      <label for="client-phone">Phone Number</label>
      <input type="tel" id="client-phone" name="phone" placeholder="555-0199" required>
    </div>
    <button type="submit" id="submit-btn">Confirm Booking</button>
  </form>
  <div id="status" role="status"></div>

  <script>
    const form = document.getElementById('booking-form');
    const dateInput = document.getElementById('book-date');
    const slotInput = document.getElementById('book-slot');
    const nameInput = document.getElementById('client-name');
    const phoneInput = document.getElementById('client-phone');
    const btn = document.getElementById('submit-btn');
    const status = document.getElementById('status');

    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;

    form.onsubmit = async (e) => {
      e.preventDefault();
      status.innerHTML = '';

      const date = dateInput.value;
      const slot = slotInput.value;
      const name = nameInput.value.trim();
      const phone = phoneInput.value.trim();

      if (!date || !slot || !name || !phone) {
        status.innerHTML = '<p class="error">Please complete all fields.</p>';
        return;
      }

      if (date < today) {
        status.innerHTML = '<p class="error">Cannot book appointments in the past.</p>';
        return;
      }

      btn.disabled = true;
      btn.innerText = 'Reserving Slot...';

      try {
        const res = await fetch('/api/book', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ date, slot, name, phone })
        });
        const data = await res.json();
        if (res.status === 409) {
          status.innerHTML = '<p class="error">Slot conflict: ' + (data.error || 'Slot already booked') + '</p>';
          return;
        }
        if (!res.ok) throw new Error(data.error || 'Server booking failure');
        status.innerHTML = '<p class="success">Booking Confirmed! ID: ' + data.booking_id + '</p>';
      } catch (err) {
        status.innerHTML = '<p class="error">Error: ' + err.message + '</p>';
      } finally {
        btn.disabled = false;
        btn.innerText = 'Confirm Booking';
      }
    };
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Test A.1: Render Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_date = session.page.locator('input[type="date"], input[name*="date" i]').count() > 0
        has_slot = session.page.locator('select, input[type="radio"], .slot').count() > 0
        has_name = session.page.locator('input[name*="name" i], input[placeholder*="name" i]').count() > 0
        has_phone = session.page.locator('input[type="tel"], input[name*="phone" i], input[placeholder*="phone" i]').count() > 0
        has_btn = session.page.locator('button, input[type="submit"]').count() > 0

        passed = has_date and has_slot and (has_name or has_phone) and has_btn
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Date: {has_date}, Slot: {has_slot}, Contacts: {has_name or has_phone}, Button: {has_btn}",
            failure_type="Functional failure: Missing booking form controls" if not passed else ""
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

    # Test A.2: Valid Booking Submission Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/book", status=200, json_body={
            "status": "confirmed",
            "booking_id": "BK-789"
        })
        session.load_html(html_code)

        date_el = session.page.locator('input[type="date"], input[name*="date" i]').first
        if date_el.count() > 0:
            date_el.fill(tomorrow_str)

        select_el = session.page.locator('select').first
        if select_el.count() > 0:
            opts = select_el.locator('option')
            if opts.count() > 1:
                select_el.select_option(index=1)

        name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[type="text"]').first
        if name_el.count() > 0:
            name_el.fill("Alice Wonderland")

        phone_el = session.page.locator('input[type="tel"], input[name*="phone" i], input[placeholder*="phone" i]').first
        if phone_el.count() > 0:
            phone_el.fill("555-0199")

        btn = session.page.locator('button, input[type="submit"]').first
        btn.click()
        session.page.wait_for_timeout(400)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        req_sent = len(post_requests) > 0
        content_lower = session.page.content().lower()
        shows_confirm = "bk-789" in content_lower or "confirmed" in content_lower

        passed = req_sent and shows_confirm
        results.append(TestResult(
            test_name="happy_path_valid_booking",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST fired: {req_sent}, Confirmation shown: {shows_confirm}",
            failure_type="Expected interaction failure: Booking submission failed or confirmation missing" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_valid_booking",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception during booking submission"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Test B.1: Past Date Validation
    session = harness.new_session()
    try:
        session.mock_route("**/api/book", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        date_el = session.page.locator('input[type="date"], input[name*="date" i]').first
        min_attr = date_el.get_attribute("min") or ""
        today_str = datetime.now().strftime("%Y-%m-%d")
        has_min = bool(min_attr and min_attr >= today_str)

        date_el.fill(yesterday_str)
        name_el = session.page.locator('input[name*="name" i], input[type="text"]').first
        if name_el.count() > 0:
            name_el.fill("Past Person")
        btn = session.page.locator('button, input[type="submit"]').first
        btn.click()
        session.page.wait_for_timeout(300)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        blocked = (len(post_requests) == 0)
        content_lower = session.page.content().lower()
        shows_err = any(w in content_lower for w in ["past", "future", "invalid date", "cannot", "error"])

        passed = has_min or blocked or shows_err
        results.append(TestResult(
            test_name="reject_past_dates",
            category="input_robustness",
            regime="reality",
            passed=passed,
            details=f"Has min date: {has_min}, Post blocked: {blocked}, Error shown: {shows_err}",
            failure_type="Input robustness failure: Permitted booking for past dates without restriction" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_past_dates",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception checking date validation"
        ))

    # Test B.2: Slot Conflict (HTTP 409) & State Preservation
    session = harness.new_session()
    try:
        session.mock_route("**/api/book", status=409, json_body={"error": "Slot already taken by another client"})
        session.load_html(html_code)

        date_el = session.page.locator('input[type="date"], input[name*="date" i]').first
        date_el.fill(tomorrow_str)

        name_el = session.page.locator('input[name*="name" i], input[type="text"]').first
        test_name = "Preserved Client Name"
        name_el.fill(test_name)

        phone_el = session.page.locator('input[type="tel"], input[name*="phone" i]').first
        test_phone = "555-9988"
        if phone_el.count() > 0:
            phone_el.fill(test_phone)

        btn = session.page.locator('button, input[type="submit"]').first
        btn.click()
        session.page.wait_for_timeout(400)

        content_lower = session.page.content().lower()
        shows_error = any(w in content_lower for w in ["taken", "unavailable", "conflict", "already", "error"])

        current_name = name_el.input_value()
        preserved = (current_name == test_name)

        passed = shows_error and preserved
        results.append(TestResult(
            test_name="slot_conflict_state_preservation",
            category="state_robustness",
            regime="reality",
            passed=passed,
            details=f"Conflict error displayed: {shows_error}, Form fields preserved: {preserved}",
            failure_type="State robustness failure: Conflict feedback missing or user input cleared on 409" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="slot_conflict_state_preservation",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception testing conflict handling"
        ))

    # Test B.3: Missing Contact Validation
    session = harness.new_session()
    try:
        session.mock_route("**/api/book", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        date_el = session.page.locator('input[type="date"], input[name*="date" i]').first
        date_el.fill(tomorrow_str)

        btn = session.page.locator('button, input[type="submit"]').first
        btn.click()
        session.page.wait_for_timeout(300)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        blocked = (len(post_requests) == 0)

        results.append(TestResult(
            test_name="reject_empty_contacts",
            category="input_robustness",
            regime="reality",
            passed=blocked,
            details=f"Empty contact submission blocked: {blocked}",
            failure_type="Input robustness failure: Submitted booking with empty contact information" if not blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_empty_contacts",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing contact validation"
        ))

    # Test B.4: Double Click Prevention on Confirm Booking
    session = harness.new_session()
    try:
        session.mock_route("**/api/book", status=200, json_body={"status": "confirmed", "booking_id": "BK-999"}, delay_ms=800)
        session.load_html(html_code)

        date_el = session.page.locator('input[type="date"], input[name*="date" i]').first
        date_el.fill(tomorrow_str)
        select_el = session.page.locator('select').first
        if select_el.count() > 0:
            opts = select_el.locator('option')
            if opts.count() > 1:
                select_el.select_option(index=1)
        name_el = session.page.locator('input[name*="name" i], input[type="text"]').first
        name_el.fill("Speedy Clicks")
        phone_el = session.page.locator('input[type="tel"], input[name*="phone" i]').first
        if phone_el.count() > 0:
            phone_el.fill("555-1234")

        session.page.evaluate("""() => {
            const b = document.querySelector('button, input[type="submit"]');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        post_count = len([r for r in session.intercepted_requests if r["method"] == "POST"])
        passed = (post_count == 1)

        results.append(TestResult(
            test_name="prevent_duplicate_booking",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"POST requests fired: {post_count} (expected 1)",
            failure_type="Duplicate interaction: Multiple booking requests sent on double click" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_booking",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction safety failure: Exception testing double click"
        ))

    # Test B.5: Accessibility
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_labels = session.page.locator('label').count() >= 2
        has_aria = session.page.locator('[aria-label]').count() >= 2
        passed = has_labels or has_aria

        results.append(TestResult(
            test_name="accessible_booking_form",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Labels count: {session.page.locator('label').count()}, Aria: {session.page.locator('[aria-label]').count()}",
            failure_type="Accessibility failure: Form fields lack proper label association" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="accessible_booking_form",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting labels"
        ))

    # Test B.6: Mobile Responsive Viewport
    session = harness.new_session()
    try:
        session.load_html(html_code, viewport={"width": 375, "height": 667})
        session.page.wait_for_timeout(300)

        scroll_width = session.page.evaluate("document.documentElement.scrollWidth")
        client_width = session.page.evaluate("document.documentElement.clientWidth")
        no_horizontal_overflow = scroll_width <= (client_width + 5)

        results.append(TestResult(
            test_name="mobile_viewport_overflow",
            category="responsive_behavior",
            regime="reality",
            passed=no_horizontal_overflow,
            details=f"scrollWidth: {scroll_width}, clientWidth: {client_width}",
            failure_type="Responsive failure: Horizontal scroll overflow on mobile viewport" if not no_horizontal_overflow else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="mobile_viewport_overflow",
            category="responsive_behavior",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Responsive failure: Exception inspecting mobile layout"
        ))

    return results


def grade_booking_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Booking component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-booking", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-booking")
def realitybench_booking(llm) -> dict:
    """
    Evaluates LLM on Booking software generation.
    """
    response = llm.prompt(BOOKING_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_booking_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional booking component on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    if should_run_kbench():
        realitybench_booking.run(kbench.llm)
    else:

        from ui import console, test_results_table, task_result_panel

        console.print("[bold cyan]Running local self-test for Task 06: Booking Component...[/bold cyan]")
        report = grade_booking_implementation(NAIVE_BOOKING_CODE)
        console.print(task_result_panel(
            "Booking Component (Naive Baseline)",
            report.demo_score,
            report.reality_score,
            report.reality_gap
        ))
        console.print(test_results_table(report.test_results, "Task 06: Booking Assertions"))
