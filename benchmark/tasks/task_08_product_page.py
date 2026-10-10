# %%
"""
TASK: Product Page Component (Task 08)

Purpose:
Evaluate whether an AI-generated e-commerce product detail page properly manages
variant stock availability (disabling buttons for out-of-stock items), validates quantity
inputs, handles broken product image URLs, and prevents double-clicks on cart additions.

Happy Path:
- Renders product title, price ($99.00), main product image, variant selector, and quantity
- Normal add-to-cart flow sends POST to /api/cart and displays cart feedback

Reality Tests:
- Out-of-stock variant selection disables 'Add to Cart' button and displays 'Out of Stock'
- Negative / zero / fractional quantities rejected before network dispatch
- Broken image resilience: Image has alt text or onerror fallback placeholder
- Double-click prevention: Rapid duplicate clicks on 'Add to Cart' fire only one request
- Accessibility: Product controls and image alt attribute present
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


PRODUCT_PAGE_TASK_PROMPT = """Build a self-contained e-commerce product detail page component in HTML, CSS, and JavaScript.
The interface must contain:
1. Product title, price ($99.00), and main product image
2. Variant selector (e.g., Color: 'Midnight Blue' [in stock], 'Lunar Silver' [out of stock])
3. Quantity selector (integer input, minimum 1, maximum available stock)
4. 'Add to Cart' button and cart feedback area
When the user adds to cart, send a POST request to '/api/cart' with { 'product_id': 'PROD-101', 'variant': '...', 'quantity': ... }.
Upon success (returns { 'status': 'added', 'cart_count': 1 }), display a success toast/message.
The application should:
- Handle missing or broken image URLs with a visible fallback placeholder (no broken image icon)
- Disable the 'Add to Cart' button and display 'Out of Stock' when an unavailable variant is chosen
- Reject negative, zero, or fractional quantities
- Prevent multiple cart additions on rapid button double-clicks
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = PRODUCT_PAGE_TASK_PROMPT

NAIVE_PRODUCT_PAGE_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Acoustic Noise-Cancelling Headphones</h2>
  <p>$99.00</p>
  <img src="https://example.com/headphones.jpg">
  <select id="variant">
    <option value="blue">Midnight Blue (In Stock)</option>
    <option value="silver">Lunar Silver (Out of Stock)</option>
  </select>
  <input type="number" id="qty" value="1">
  <button onclick="add()">Add to Cart</button>
  <div id="cart-msg"></div>
  <script>
    function add() {
      const variant = document.getElementById('variant').value;
      const qty = document.getElementById('qty').value;
      fetch('/api/cart', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ product_id: 'PROD-101', variant: variant, quantity: qty })
      })
      .then(r => r.json())
      .then(d => {
        document.getElementById('cart-msg').innerText = 'Added to cart!';
      });
    }
  </script>
</body>
</html>
"""

ROBUST_PRODUCT_PAGE_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Acoustic Headphones - Store</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 20px; max-width: 480px; margin: 0 auto; }
    .product-img { width: 100%; height: 240px; background: #f1f5f9; object-fit: cover; border-radius: 8px; }
    .price { font-size: 24px; font-weight: bold; color: #0f172a; margin: 8px 0; }
    .form-group { margin-bottom: 12px; }
    label { display: block; margin-bottom: 4px; font-weight: 500; }
    select, input { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; }
    button { width: 100%; padding: 12px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .out-of-stock-badge { color: #dc2626; font-weight: bold; margin-top: 4px; font-size: 14px; }
    .feedback { margin-top: 12px; font-weight: 500; }
    .feedback.success { color: #16a34a; }
    .feedback.error { color: #dc2626; }
  </style>
</head>
<body>
  <h2>Acoustic Noise-Cancelling Headphones</h2>
  <div class="price">$99.00</div>
  <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
       alt="Over-ear wireless headphones in midnight blue"
       class="product-img"
       onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22240%22><rect width=%22100%%22 height=%22100%%22 fill=%22%23eee%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23aaa%22>Product Image Unavailable</text></svg>'">

  <form id="product-form" style="margin-top: 16px;">
    <div class="form-group">
      <label for="color-variant">Color Variant</label>
      <select id="color-variant" name="variant" aria-label="Product color variant">
        <option value="midnight_blue" data-stock="10">Midnight Blue (In Stock)</option>
        <option value="lunar_silver" data-stock="0">Lunar Silver (Out of Stock)</option>
      </select>
      <div id="stock-status" class="out-of-stock-badge" style="display: none;">Out of Stock</div>
    </div>

    <div class="form-group">
      <label for="quantity">Quantity</label>
      <input type="number" id="quantity" name="quantity" min="1" max="10" value="1" aria-label="Item quantity" required>
    </div>

    <button type="submit" id="add-btn">Add to Cart</button>
  </form>
  <div id="feedback" class="feedback" role="status"></div>

  <script>
    const form = document.getElementById('product-form');
    const variantSelect = document.getElementById('color-variant');
    const stockStatus = document.getElementById('stock-status');
    const qtyInput = document.getElementById('quantity');
    const btn = document.getElementById('add-btn');
    const feedback = document.getElementById('feedback');

    function updateStockState() {
      const selected = variantSelect.options[variantSelect.selectedIndex];
      const stock = parseInt(selected.getAttribute('data-stock') || '0', 10);
      if (stock <= 0) {
        btn.disabled = true;
        btn.innerText = 'Out of Stock';
        stockStatus.style.display = 'block';
      } else {
        btn.disabled = false;
        btn.innerText = 'Add to Cart';
        stockStatus.style.display = 'none';
      }
    }

    variantSelect.addEventListener('change', updateStockState);
    updateStockState();

    form.onsubmit = async (e) => {
      e.preventDefault();
      feedback.className = 'feedback';
      feedback.innerText = '';

      const selected = variantSelect.options[variantSelect.selectedIndex];
      const stock = parseInt(selected.getAttribute('data-stock') || '0', 10);
      if (stock <= 0) {
        feedback.className = 'feedback error';
        feedback.innerText = 'This variant is currently out of stock.';
        return;
      }

      const qty = parseInt(qtyInput.value, 10);
      if (isNaN(qty) || qty <= 0) {
        feedback.className = 'feedback error';
        feedback.innerText = 'Please select a valid quantity (minimum 1).';
        return;
      }

      btn.disabled = true;
      btn.innerText = 'Adding...';

      try {
        const res = await fetch('/api/cart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product_id: 'PROD-101', variant: variantSelect.value, quantity: qty })
        });
        if (!res.ok) throw new Error('Could not add item to cart');
        const data = await res.json();
        feedback.className = 'feedback success';
        feedback.innerText = 'Added to cart! (' + data.cart_count + ' items)';
      } catch (err) {
        feedback.className = 'feedback error';
        feedback.innerText = 'Error: ' + err.message;
      } finally {
        updateStockState();
      }
    };
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
        has_title = session.page.locator('h1, h2, h3, .title').count() > 0
        has_img = session.page.locator('img, svg, .product-image').count() > 0
        has_variant = session.page.locator('select, input[type="radio"], .variant').count() > 0
        has_qty = session.page.locator('input[type="number"], select[name*="qty" i], input[name*="qty" i]').count() > 0
        has_btn = session.page.locator('button, input[type="submit"]').count() > 0

        passed = has_title and has_img and has_btn
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Title: {has_title}, Img: {has_img}, Variant: {has_variant}, Qty: {has_qty}, Button: {has_btn}",
            failure_type="Functional failure: Missing product details, image, or action button" if not passed else ""
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

    # Test A.2: Valid Add to Cart Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/cart", status=200, json_body={
            "status": "added",
            "cart_count": 1
        })
        session.load_html(html_code)

        variant_el = session.page.locator('select, input[type="radio"]').first
        if variant_el.count() > 0:
            if variant_el.evaluate("el => el.tagName.toLowerCase()") == "select":
                opts = variant_el.locator('option')
                if opts.count() > 0:
                    variant_el.select_option(index=0)
            else:
                variant_el.check()

        qty_el = session.page.locator('input[type="number"], input[name*="qty" i]').first
        if qty_el.count() > 0:
            qty_el.fill("1")

        btn = session.page.locator('button:has-text("Add"), button').first
        btn.click()
        session.page.wait_for_timeout(400)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        post_sent = len(post_requests) > 0
        content_lower = session.visible_text()
        shows_feedback = any(w in content_lower for w in ["added", "cart", "success", "1 item"])

        passed = post_sent and shows_feedback
        results.append(TestResult(
            test_name="happy_path_add_to_cart",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST fired: {post_sent}, Cart feedback shown: {shows_feedback}",
            failure_type="Expected interaction failure: Add to cart submission failed" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_add_to_cart",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception adding to cart"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Out-of-Stock Variant Handling
    session = harness.new_session()
    try:
        session.mock_route("**/api/cart", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        session.page.evaluate("""() => {
            const select = document.querySelector('select');
            if (select) {
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].text.toLowerCase().includes('out of stock') || select.options[i].text.toLowerCase().includes('lunar')) {
                        select.selectedIndex = i;
                        select.dispatchEvent(new Event('change'));
                        break;
                    }
                }
            }
            const radios = document.querySelectorAll('input[type="radio"]');
            radios.forEach(r => {
                const label = r.closest('label')?.innerText || '';
                if (label.toLowerCase().includes('out of stock') || label.toLowerCase().includes('lunar')) {
                    r.checked = true;
                    r.dispatchEvent(new Event('change'));
                }
            });
        }""")
        session.page.wait_for_timeout(300)

        btn = session.page.locator('button:has-text("Add"), button:has-text("Out"), button').first
        is_disabled = btn.is_disabled() or ("out of stock" in btn.text_content().lower())

        if btn.count() > 0 and not is_disabled:
            btn.click()
        session.page.wait_for_timeout(300)

        no_post_sent = len([r for r in session.intercepted_requests if r["method"] == "POST"]) == 0
        content_lower = session.visible_text()
        shows_out_of_stock = "out of stock" in content_lower

        passed = (is_disabled or no_post_sent) and shows_out_of_stock
        results.append(TestResult(
            test_name="handle_out_of_stock_variant",
            category="state_robustness",
            regime="reality",
            passed=passed,
            details=f"Button disabled: {is_disabled}, Post blocked: {no_post_sent}, 'Out of Stock' text: {shows_out_of_stock}",
            failure_type="State robustness failure: Out-of-stock variant can still be added to cart" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="handle_out_of_stock_variant",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception checking stock state"
        ))

    # Test B.2: Reject Negative / Zero Quantity
    session = harness.new_session()
    try:
        session.mock_route("**/api/cart", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        qty_el = session.page.locator('input[type="number"], input[name*="qty" i]').first
        if qty_el.count() > 0:
            qty_el.fill("-5")

        btn = session.page.locator('button:has-text("Add"), button').first
        btn.click()
        session.page.wait_for_timeout(300)

        post_count = len([r for r in session.intercepted_requests if r["method"] == "POST"])
        blocked = (post_count == 0)

        results.append(TestResult(
            test_name="reject_invalid_quantity",
            category="input_robustness",
            regime="reality",
            passed=blocked,
            details=f"Negative quantity blocked: {blocked}",
            failure_type="Input robustness failure: Submitted cart order with negative quantity (-5)" if not blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_invalid_quantity",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing invalid quantity"
        ))

    # Test B.3: Broken Image Fallback Handling
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_fallback = session.page.evaluate("""() => {
            const img = document.querySelector('img');
            if (!img) return true;
            if (img.getAttribute('onerror')) return true;
            return !!img.alt;
        }""")

        results.append(TestResult(
            test_name="broken_image_resilience",
            category="failure_recovery",
            regime="reality",
            passed=has_fallback,
            details=f"Image alt or fallback attribute present: {has_fallback}",
            failure_type="Recovery failure: Product image has no alt text or error fallback" if not has_fallback else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="broken_image_resilience",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Recovery failure: Exception checking image fallback"
        ))

    # Test B.4: Double Click Prevention on Add to Cart
    session = harness.new_session()
    try:
        session.mock_route("**/api/cart", status=200, json_body={"status": "added", "cart_count": 1}, delay_ms=800)
        session.load_html(html_code)

        session.page.evaluate("""() => {
            const b = document.querySelector('button, input[type="submit"]');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        post_count = len([r for r in session.intercepted_requests if r["method"] == "POST"])
        passed = (post_count == 1)

        results.append(TestResult(
            test_name="prevent_duplicate_cart_add",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"POST requests fired: {post_count} (expected 1)",
            failure_type="Duplicate interaction: Multiple cart POST requests fired on double click" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_cart_add",
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
        has_labels = session.page.locator('label').count() >= 1
        has_aria = session.page.locator('[aria-label]').count() >= 1
        img_alt = bool(session.page.locator('img').first.get_attribute('alt') if session.page.locator('img').count() > 0 else True)

        passed = (has_labels or has_aria) and img_alt
        results.append(TestResult(
            test_name="accessible_product_controls",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Labels: {has_labels}, Aria: {has_aria}, Image alt: {img_alt}",
            failure_type="Accessibility failure: Missing form labels or image alt text" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="accessible_product_controls",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting accessibility"
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


def grade_product_page_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Product Page component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-product-page", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-product-page")
def realitybench_product_page(llm) -> dict:
    """
    Evaluates LLM on Product Page software generation.
    """
    response = llm.prompt(PRODUCT_PAGE_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_product_page_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional product page on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    if should_run_kbench():
        realitybench_product_page.run(kbench.llm)
    else:
        for label, code in (("naive", NAIVE_PRODUCT_PAGE_CODE), ("robust", ROBUST_PRODUCT_PAGE_CODE)):
            r = grade_product_page_implementation(code)
            print(f"{label:6} demo={r.demo_score:.2f} reality={r.reality_score:.2f} gap={r.reality_gap:+.2f}")
