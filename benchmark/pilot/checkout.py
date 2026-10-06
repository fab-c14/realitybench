# %%
"""
RealityBench - Pilot Task 3: Checkout Component
Evaluates generated web checkout software on Happy Path vs. Controlled Perturbations.
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


CHECKOUT_TASK_PROMPT = """Build a self-contained web checkout interface in HTML, CSS, and JavaScript.
The checkout interface must contain:
1. Customer details inputs: Full Name, Email Address, and Shipping Address
2. Order summary displaying an item with price and a total amount ($49.00)
3. A 'Pay & Place Order' submit button
When submitted, the application should make a POST request to '/api/checkout' with a JSON payload containing 'name', 'email', 'address', and 'amount'.
Upon receiving a successful response ({ 'order_id': 'ORD-12345', 'status': 'confirmed' }), display an order confirmation with the order ID.
The application should provide appropriate input validation, prevent double charging, and handle errors with clear user feedback.
Provide all code in a single self-contained HTML document without external dependencies."""

TASK_SPEC = CHECKOUT_TASK_PROMPT

NAIVE_CHECKOUT_CODE = """
<!DOCTYPE html><html><body>
  <h2>Checkout</h2>
  <p>Total: $49.00</p>
  <input type="text" id="name" placeholder="Full Name">
  <input type="text" id="email" placeholder="Email">
  <input type="text" id="addr" placeholder="Address">
  <button onclick="pay()">Pay & Place Order</button>
  <div id="status"></div>
  <script>
    function pay() {
      const name = document.getElementById('name').value;
      const email = document.getElementById('email').value;
      const address = document.getElementById('addr').value;
      fetch('/api/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, email, address, amount: 49.00 })
      })
      .then(r => r.json())
      .then(data => {
        document.getElementById('status').innerText = 'Order confirmed: ' + data.order_id;
      });
    }
  </script>
</body></html>
"""

ROBUST_CHECKOUT_CODE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
  <h2>Checkout</h2>
  <div class="summary">Total: $49.00</div>
  <form id="checkout-form">
    <input type="text" id="name" name="name" required placeholder="Full Name">
    <input type="email" id="email" name="email" required placeholder="Email">
    <textarea id="addr" name="address" required placeholder="Shipping Address"></textarea>
    <button type="submit" id="pay-btn">Pay & Place Order</button>
  </form>
  <div id="status" role="status"></div>
  <script>
    const form = document.getElementById('checkout-form');
    const btn = document.getElementById('pay-btn');
    const status = document.getElementById('status');

    form.onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('name').value.trim();
      const email = document.getElementById('email').value.trim();
      const address = document.getElementById('addr').value.trim();
      if (!name || !email || !address) return;

      btn.disabled = true;
      btn.innerText = 'Processing Payment...';
      status.innerText = '';

      try {
        const res = await fetch('/api/checkout', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ name, email, address, amount: 49.00 })
        });
        if (!res.ok) throw new Error('Payment declined by bank');
        const data = await res.json();
        status.innerText = 'Order confirmed! Order ID: ' + data.order_id;
      } catch (err) {
        status.innerText = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
        btn.innerText = 'Pay & Place Order';
      }
    };
  </script>
</body></html>
"""


def grade_checkout_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Checkout component across:
    Regime A (Happy Path / Demo Score) and Regime B (Controlled Perturbations / Reality Score).
    """
    results = []

    with HeadlessHarness() as harness:
        # -------------------------------------------------------------
        # REGIME A: HAPPY PATH (Demo Score)
        # -------------------------------------------------------------

        # Test A.1: Structural Elements & Order Summary
        session = harness.new_session()
        try:
            session.load_html(html_code)
            name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[id*="name" i]').first
            email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
            addr_el = session.page.locator('input[name*="addr" i], textarea[name*="addr" i], input[placeholder*="addr" i], textarea').first
            btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Order"), button:has-text("Pay"), button').first
            
            content_lower = session.page.content().lower()
            has_amount = ("49" in content_lower or "$49" in content_lower)
            has_inputs = (name_el.count() > 0 and email_el.count() > 0 and btn_el.count() > 0)

            passed = has_inputs and has_amount
            results.append(TestResult(
                test_name="happy_path_render_elements",
                category="functional_correctness",
                regime="demo",
                passed=passed,
                details=f"Inputs present: {has_inputs}, Total amount shown: {has_amount}",
                failure_type="Functional failure: Missing checkout inputs or total price" if not passed else ""
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

        # Test A.2: Expected Interaction - Successful Order Placement
        session = harness.new_session()
        try:
            session.mock_route("**/api/checkout", status=200, json_body={"order_id": "ORD-998877", "status": "confirmed"})
            session.load_html(html_code)

            name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[id*="name" i]').first
            email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
            addr_el = session.page.locator('input[name*="addr" i], textarea[name*="addr" i], input[placeholder*="addr" i], textarea').first
            btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Order"), button:has-text("Pay"), button').first

            name_el.fill("Jane Doe")
            email_el.fill("jane@example.com")
            if addr_el.count() > 0:
                addr_el.fill("123 Maple Street")
            btn_el.click()
            session.page.wait_for_timeout(400)

            req_sent = len(session.intercepted_requests) > 0
            body_valid = False
            if req_sent:
                post_data = session.intercepted_requests[0].get("post_data") or {}
                if isinstance(post_data, str):
                    try:
                        post_data = json.loads(post_data)
                    except Exception:
                        pass
                if isinstance(post_data, dict):
                    body_valid = ("email" in post_data and "jane@example.com" in str(post_data.get("email")))

            content_lower = session.page.content().lower()
            shows_confirmation = ("ord-998877" in content_lower or "confirmed" in content_lower or "order" in content_lower)

            passed = req_sent and body_valid and shows_confirmation
            results.append(TestResult(
                test_name="happy_path_order_confirmation",
                category="expected_interactions",
                regime="demo",
                passed=passed,
                details=f"Request sent: {req_sent}, Payload valid: {body_valid}, Confirmation shown: {shows_confirmation}",
                failure_type="Expected interaction failure: Order flow did not confirm" if not passed else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="happy_path_order_confirmation",
                category="expected_interactions",
                regime="demo",
                passed=False,
                details=str(e),
                failure_type="Expected interaction failure: Crash during checkout"
            ))

        # -------------------------------------------------------------
        # REGIME B: REALITY PERTURBATIONS (Reality Score)
        # -------------------------------------------------------------

        # Test B.1: Input Robustness - Blank Checkout Prevention
        session = harness.new_session()
        try:
            session.mock_route("**/api/checkout", status=200, json_body={"order_id": "ORD-BAD"})
            session.load_html(html_code)
            btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Order"), button:has-text("Pay"), button').first
            btn_el.click()
            session.page.wait_for_timeout(300)

            blocked = len(session.intercepted_requests) == 0
            results.append(TestResult(
                test_name="input_empty_checkout_validation",
                category="input_robustness",
                regime="reality",
                passed=blocked,
                details="Empty checkout blocked before charging/API call",
                failure_type="Validation failure: Placed order with empty customer data" if not blocked else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="input_empty_checkout_validation",
                category="input_robustness",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Validation failure: Exception on empty checkout"
            ))

        # Test B.2: Failure Recovery - Payment Gateway 500 Error Feedback
        session = harness.new_session()
        try:
            session.mock_route("**/api/checkout", status=500, json_body={"error": "Payment gateway timeout"})
            session.load_html(html_code)
            name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[id*="name" i]').first
            email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
            addr_el = session.page.locator('input[name*="addr" i], textarea[name*="addr" i], input[placeholder*="addr" i], textarea').first
            btn_el = session.page.locator('button[type="submit"], input[type="submit"], button:has-text("Order"), button:has-text("Pay"), button').first

            name_el.fill("Jane Doe")
            email_el.fill("jane@example.com")
            if addr_el.count() > 0:
                addr_el.fill("123 Maple Street")
            btn_el.click()
            session.page.wait_for_timeout(500)

            content_lower = session.page.content().lower()
            shows_error = any(w in content_lower for w in ["error", "failed", "declined", "unable", "try again"])
            results.append(TestResult(
                test_name="network_500_payment_error",
                category="failure_recovery",
                regime="reality",
                passed=shows_error,
                details="Payment error message displayed upon 500 response",
                failure_type="Recovery failure: Silent failure on payment 500 without user feedback" if not shows_error else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="network_500_payment_error",
                category="failure_recovery",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Network failure: App crashed on payment failure"
            ))

        # Test B.3: State Robustness - Preservation of Form Fields After Failed Payment
        try:
            # Continuing after payment 500 failure
            curr_name = name_el.input_value()
            curr_email = email_el.input_value()
            preserved = (curr_name == "Jane Doe" and curr_email == "jane@example.com")
            results.append(TestResult(
                test_name="state_preservation_on_payment_failure",
                category="state_robustness",
                regime="reality",
                passed=preserved,
                details=f"Customer details preserved: name='{curr_name}', email='{curr_email}'",
                failure_type="State consistency failure: Customer info wiped after payment error" if not preserved else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="state_preservation_on_payment_failure",
                category="state_robustness",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="State consistency failure: Exception reading preserved inputs"
            ))

        # Test B.4: Interaction Safety - Double-Charge Protection (Double Click)
        session = harness.new_session()
        try:
            session.mock_route("**/api/checkout", status=200, json_body={"order_id": "ORD-1"}, delay_ms=400)
            session.load_html(html_code)
            name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[id*="name" i]').first
            email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
            addr_el = session.page.locator('input[name*="addr" i], textarea[name*="addr" i], input[placeholder*="addr" i], textarea').first

            name_el.fill("Jane Doe")
            email_el.fill("jane@example.com")
            if addr_el.count() > 0:
                addr_el.fill("123 Maple Street")

            # Fire synchronous double-click on checkout button
            session.page.evaluate("""() => {
                const b = document.querySelector('button[type="submit"], input[type="submit"], button');
                if (b) { b.click(); b.click(); }
            }""")
            session.page.wait_for_timeout(600)

            charge_count = len(session.intercepted_requests)
            is_single_charge = (charge_count == 1)
            results.append(TestResult(
                test_name="double_charge_protection",
                category="interaction_safety",
                regime="reality",
                passed=is_single_charge,
                details=f"Orders placed on rapid double click: {charge_count} (expected: 1)",
                failure_type="Duplicate interaction: Customer double-charged on rapid button click" if not is_single_charge else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="double_charge_protection",
                category="interaction_safety",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Interaction safety: Exception on double-charge test"
            ))

        # Test B.5: Accessibility - Keyboard Submission via Enter
        session = harness.new_session()
        try:
            session.mock_route("**/api/checkout", status=200, json_body={"order_id": "ORD-KBD", "status": "confirmed"})
            session.load_html(html_code)
            
            name_el = session.page.locator('input[name*="name" i], input[placeholder*="name" i], input[id*="name" i]').first
            email_el = session.page.locator('input[type="email"], input[name*="email" i], input[placeholder*="email" i]').first
            addr_el = session.page.locator('input[name*="addr" i], textarea[name*="addr" i], input[placeholder*="addr" i], textarea').first

            name_el.fill("Jane Doe")
            email_el.fill("jane@example.com")
            if addr_el.count() > 0:
                addr_el.fill("123 Maple Street")
                
            # Focus email input and press Enter to trigger form submission
            email_el.focus()
            session.page.keyboard.press("Enter")
            session.page.wait_for_timeout(400)

            key_submitted = len(session.intercepted_requests) > 0
            results.append(TestResult(
                test_name="keyboard_accessibility_checkout_enter",
                category="accessibility",
                regime="reality",
                passed=key_submitted,
                details="Checkout form submittable via keyboard Enter navigation",
                failure_type="Accessibility failure: Cannot checkout with keyboard Enter key" if not key_submitted else ""
            ))
        except Exception as e:
            results.append(TestResult(
                test_name="keyboard_accessibility_checkout_enter",
                category="accessibility",
                regime="reality",
                passed=False,
                details=str(e),
                failure_type="Accessibility failure: Keyboard navigation crashed"
            ))

        # Test B.6: Responsive Behavior - Mobile Viewport Integrity (375x667)
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
                details="No horizontal overflow on 375px mobile checkout viewport",
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

    return calculate_scores("realitybench-checkout", results)


# %%
@kbench.task(name="realitybench-checkout")
def realitybench_checkout(llm) -> dict:
    """
    Evaluates LLM on Checkout software generation across Demo Score, Reality Score, and Reality Gap.
    """
    response = llm.prompt(CHECKOUT_TASK_PROMPT)
    code = extract_html_code(response)
    
    report = grade_checkout_implementation(code)
    
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional checkout component on happy path"
    )
    
    return report.to_dict()


# %%
if __name__ == "__main__":
    naive_code = """
    <!DOCTYPE html><html><body>
      <h2>Checkout</h2>
      <p>Total: $49.00</p>
      <input type="text" id="name" placeholder="Full Name">
      <input type="text" id="email" placeholder="Email">
      <input type="text" id="addr" placeholder="Address">
      <button onclick="pay()">Pay & Place Order</button>
      <div id="status"></div>
      <script>
        function pay() {
          const name = document.getElementById('name').value;
          const email = document.getElementById('email').value;
          const address = document.getElementById('addr').value;
          fetch('/api/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, email, address, amount: 49.00 })
          })
          .then(r => r.json())
          .then(data => {
            document.getElementById('status').innerText = 'Order confirmed: ' + data.order_id;
          });
        }
      </script>
    </body></html>
    """

    robust_code = """
    <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body>
      <h2>Checkout</h2>
      <div class="summary">Total: $49.00</div>
      <form id="checkout-form">
        <input type="text" id="name" name="name" required placeholder="Full Name">
        <input type="email" id="email" name="email" required placeholder="Email">
        <textarea id="addr" name="address" required placeholder="Shipping Address"></textarea>
        <button type="submit" id="pay-btn">Pay & Place Order</button>
      </form>
      <div id="status" role="status"></div>
      <script>
        const form = document.getElementById('checkout-form');
        const btn = document.getElementById('pay-btn');
        const status = document.getElementById('status');

        form.onsubmit = async (e) => {
          e.preventDefault();
          const name = document.getElementById('name').value.trim();
          const email = document.getElementById('email').value.trim();
          const address = document.getElementById('addr').value.trim();
          if (!name || !email || !address) return;

          btn.disabled = true;
          btn.innerText = 'Processing Payment...';
          status.innerText = '';

          try {
            const res = await fetch('/api/checkout', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ name, email, address, amount: 49.00 })
            });
            if (!res.ok) throw new Error('Payment declined by bank');
            const data = await res.json();
            status.innerText = 'Order confirmed! Order ID: ' + data.order_id;
          } catch (err) {
            status.innerText = 'Error: ' + err.message;
          } finally {
            btn.disabled = false;
            btn.innerText = 'Pay & Place Order';
          }
        };
      </script>
    </body></html>
    """

    print("Evaluating Naive Checkout...")
    r1 = grade_checkout_implementation(naive_code)
    print(f"Demo: {r1.demo_score:.2%}, Reality: {r1.reality_score:.2%}, Gap: {r1.reality_gap:.2%}")
    for t in r1.test_results:
        print(f"  [{'PASS' if t.passed else 'FAIL'}] {t.test_name}: {t.details}")

    print("\nEvaluating Robust Checkout...")
    r2 = grade_checkout_implementation(robust_code)
    print(f"Demo: {r2.demo_score:.2%}, Reality: {r2.reality_score:.2%}, Gap: {r2.reality_gap:.2%}")
    for t in r2.test_results:
        print(f"  [{'PASS' if t.passed else 'FAIL'}] {t.test_name}: {t.details}")
