# %%
"""
TASK: File Upload Component (Task 04)

Purpose:
Evaluate whether an AI-generated web file upload component enforces client-side file
constraints (type and size restrictions), handles server 500 crashes, prevents duplicate
submissions during active upload, and provides accessible labels.

Happy Path:
- Renders file input and upload action button
- Successful upload flow with valid file (PDF/PNG <= 5MB) receiving confirmation

Reality Tests:
- Invalid file type (.exe) rejected on client side before network dispatch
- Oversized file (> 5MB) rejected on client side before network dispatch
- Server HTTP 500 failure handled with visible error message (UI intact)
- Duplicate click prevention: Rapid clicks during upload do not fire multiple requests
- Accessibility: File input has accessible name (label or aria-label)
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
from benchmark.graders.scoring import calculate_scores, TestResult, EvaluationReport
from benchmark.graders.browser_runner import HeadlessHarness, extract_html_code


FILE_UPLOAD_TASK_PROMPT = """Build a self-contained web file upload interface in HTML, CSS, and JavaScript.
The interface must contain:
1. A file dropzone or file input element (configured to accept PDF, PNG, and JPG files, maximum 5MB)
2. An upload button or submit action
3. A progress or status container for user feedback
When a valid file is selected and uploaded, make a POST request to '/api/upload'.
The API returns JSON: { 'status': 'success', 'filename': 'sample.png', 'size': 1048576, 'url': '/uploads/sample.png' }.
Upon success, display a confirmation message including the uploaded filename.
The application should enforce client-side file constraints (type and size), prevent duplicate submissions while uploading, and provide clear user feedback if an operation fails.
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = FILE_UPLOAD_TASK_PROMPT

NAIVE_FILE_UPLOAD_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Upload File</h2>
  <input type="file" id="f">
  <button onclick="upload()">Upload</button>
  <div id="status"></div>
  <script>
    function upload() {
      const file = document.getElementById('f').files[0];
      const formData = new FormData();
      formData.append('file', file);
      fetch('/api/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(d => {
          document.getElementById('status').innerText = 'Success: ' + d.filename;
        });
    }
  </script>
</body>
</html>
"""

ROBUST_FILE_UPLOAD_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>File Upload</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 20px; max-width: 500px; margin: 0 auto; }
    .dropzone { border: 2px dashed #94a3b8; padding: 24px; text-align: center; border-radius: 8px; margin-bottom: 12px; }
    button { background: #2563eb; color: #fff; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; width: 100%; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .error { color: #dc2626; margin-top: 10px; }
    .success { color: #16a34a; margin-top: 10px; }
  </style>
</head>
<body>
  <form id="upload-form">
    <div class="dropzone">
      <label for="file-input" style="display:block; cursor:pointer;">Choose a PDF or PNG (Max 5MB)</label>
      <input type="file" id="file-input" name="file" accept=".pdf,.png,.jpg" aria-label="Upload document or image" style="margin-top:10px;">
    </div>
    <button type="submit" id="upload-btn">Upload File</button>
  </form>
  <div id="status" role="status"></div>

  <script>
    const form = document.getElementById('upload-form');
    const input = document.getElementById('file-input');
    const btn = document.getElementById('upload-btn');
    const status = document.getElementById('status');
    const MAX_SIZE = 5 * 1024 * 1024;
    const ALLOWED = ['application/pdf', 'image/png', 'image/jpeg'];

    form.onsubmit = async (e) => {
      e.preventDefault();
      status.innerHTML = '';

      if (!input.files || input.files.length === 0) {
        status.innerHTML = '<p class="error">Please select a file to upload.</p>';
        return;
      }

      const file = input.files[0];
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      const validExt = ['.pdf', '.png', '.jpg'].includes(ext);

      if (!validExt && !ALLOWED.includes(file.type)) {
        status.innerHTML = '<p class="error">Invalid file type. Only PDF and PNG allowed.</p>';
        return;
      }

      if (file.size > MAX_SIZE) {
        status.innerHTML = '<p class="error">File exceeds the 5MB size limit.</p>';
        return;
      }

      btn.disabled = true;
      btn.innerText = 'Uploading...';

      try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Upload failed on server (' + res.status + ')');
        const data = await res.json();
        status.innerHTML = '<p class="success">Upload success! ' + data.filename + '</p>';
      } catch (err) {
        status.innerHTML = '<p class="error">Error: ' + err.message + '</p>';
      } finally {
        btn.disabled = false;
        btn.innerText = 'Upload File';
      }
    };
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []

    # Test A.1: Structural Elements
    session = harness.new_session()
    try:
        session.load_html(html_code)
        has_input = session.page.locator('input[type="file"]').count() > 0
        has_btn = session.page.locator('button, input[type="submit"]').count() > 0
        has_status = session.page.locator('#status, .status, #message, .message, div, p').count() > 0

        passed = has_input and (has_btn or has_status)
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"File input: {has_input}, Action button: {has_btn}",
            failure_type="Functional failure: Missing file input or action button" if not passed else ""
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

    # Test A.2: Valid File Upload Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/upload", status=200, json_body={
            "status": "success",
            "filename": "quarterly_report.pdf",
            "size": 1048576,
            "url": "/uploads/quarterly_report.pdf"
        })
        session.load_html(html_code)

        file_input = session.page.locator('input[type="file"]').first
        file_input.set_input_files({
            "name": "quarterly_report.pdf",
            "mimeType": "application/pdf",
            "buffer": b"%PDF-1.4 sample pdf content for realitybench testing"
        })
        session.page.wait_for_timeout(200)

        btn = session.page.locator('button, input[type="submit"]').first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
        session.page.wait_for_timeout(500)

        req_sent = len(session.intercepted_requests) > 0
        body_ok = False
        if req_sent:
            body_ok = session.intercepted_requests[0]["method"] == "POST"

        content_lower = session.page.content().lower()
        shows_confirm = "quarterly_report.pdf" in content_lower or "success" in content_lower

        passed = req_sent and body_ok and shows_confirm
        results.append(TestResult(
            test_name="happy_path_valid_upload",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST sent: {req_sent}, Confirmation shown: {shows_confirm}",
            failure_type="Expected interaction failure: Upload failed or confirmation missing" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_valid_upload",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception during valid upload"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Invalid File Type Client-Side Rejection
    session = harness.new_session()
    try:
        session.mock_route("**/api/upload", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        file_input = session.page.locator('input[type="file"]').first
        file_input.set_input_files({
            "name": "malicious_script.exe",
            "mimeType": "application/x-msdownload",
            "buffer": b"MZ executable payload dummy"
        })
        session.page.wait_for_timeout(200)

        btn = session.page.locator('button, input[type="submit"]').first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
        session.page.wait_for_timeout(300)

        request_blocked = (len(session.intercepted_requests) == 0)
        content_lower = session.page.content().lower()
        shows_err = any(w in content_lower for w in ["invalid", "only", "pdf", "png", "jpg", "not allowed", "error", "type"])
        accept_attr = file_input.get_attribute("accept") or ""
        has_accept = (".pdf" in accept_attr or "image" in accept_attr or "pdf" in accept_attr)

        passed = request_blocked and (shows_err or has_accept)
        results.append(TestResult(
            test_name="reject_invalid_file_type",
            category="input_robustness",
            regime="reality",
            passed=passed,
            details=f"Request blocked: {request_blocked}, Error/Accept restriction: {shows_err or has_accept}",
            failure_type="Input robustness failure: Uploaded unsupported .exe file without client-side rejection" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_invalid_file_type",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception checking file type validation"
        ))

    # Test B.2: Oversized File (> 5MB) Client-Side Rejection
    session = harness.new_session()
    try:
        session.mock_route("**/api/upload", status=200, json_body={"status": "unexpected_success"})
        session.load_html(html_code)

        huge_buffer = b"0" * (8 * 1024 * 1024)
        file_input = session.page.locator('input[type="file"]').first
        file_input.set_input_files({
            "name": "large_artwork.png",
            "mimeType": "image/png",
            "buffer": huge_buffer
        })
        session.page.wait_for_timeout(200)

        btn = session.page.locator('button, input[type="submit"]').first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
        session.page.wait_for_timeout(300)

        request_blocked = (len(session.intercepted_requests) == 0)
        content_lower = session.page.content().lower()
        shows_size_err = any(w in content_lower for w in ["size", "large", "5mb", "limit", "exceed", "max", "error"])

        passed = request_blocked and shows_size_err
        results.append(TestResult(
            test_name="reject_oversized_file",
            category="input_robustness",
            regime="reality",
            passed=passed,
            details=f"Oversized upload blocked: {request_blocked}, Size error feedback: {shows_size_err}",
            failure_type="Input robustness failure: Sent 8MB file exceeding 5MB limit" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_oversized_file",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception checking file size restriction"
        ))

    # Test B.3: Network Failure (HTTP 500) Handling & Recovery
    session = harness.new_session()
    try:
        session.mock_route("**/api/upload", status=500, json_body={"error": "Storage gateway unavailable"})
        session.load_html(html_code)

        file_input = session.page.locator('input[type="file"]').first
        file_input.set_input_files({
            "name": "resume.pdf",
            "mimeType": "application/pdf",
            "buffer": b"%PDF-1.4 sample content"
        })
        session.page.wait_for_timeout(200)

        btn = session.page.locator('button, input[type="submit"]').first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
        session.page.wait_for_timeout(400)

        content_lower = session.page.content().lower()
        shows_error = any(w in content_lower for w in ["error", "fail", "unavailable", "problem", "could not"])
        elements_intact = session.page.locator('input[type="file"]').count() > 0

        passed = shows_error and elements_intact
        results.append(TestResult(
            test_name="server_error_feedback",
            category="failure_recovery",
            regime="reality",
            passed=passed,
            details=f"Error feedback visible: {shows_error}, UI intact: {elements_intact}",
            failure_type="Recovery failure: Silent failure or UI destruction on HTTP 500" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="server_error_feedback",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Recovery failure: Crash on server error"
        ))

    # Test B.4: Double Submission Prevention (Debounce / Disabling)
    session = harness.new_session()
    try:
        session.mock_route("**/api/upload", status=200, delay_ms=1000, json_body={"status": "success", "filename": "test.png"})
        session.load_html(html_code)

        file_input = session.page.locator('input[type="file"]').first
        file_input.set_input_files({
            "name": "photo.png",
            "mimeType": "image/png",
            "buffer": b"\x89PNG\r\n\x1a\n"
        })
        session.page.wait_for_timeout(200)

        session.page.evaluate("""() => {
            const b = document.querySelector('button, input[type="submit"]');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        req_count = len(session.intercepted_requests)
        passed = (req_count == 1)
        results.append(TestResult(
            test_name="prevent_duplicate_upload",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"Intercepted requests count: {req_count} (expected 1)",
            failure_type="Duplicate interaction: Multiple simultaneous upload requests fired" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_upload",
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
        input_el = session.page.locator('input[type="file"]').first

        has_aria_label = bool(input_el.get_attribute("aria-label"))
        input_id = input_el.get_attribute("id")
        has_label = False
        if input_id:
            has_label = session.page.locator(f'label[for="{input_id}"]').count() > 0

        has_parent_label = session.page.locator('label input[type="file"]').count() > 0
        has_dropzone_desc = session.page.locator('[aria-describedby], [role="region"]').count() > 0

        passed = has_aria_label or has_label or has_parent_label or has_dropzone_desc
        results.append(TestResult(
            test_name="accessible_upload_label",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Label associated: {has_label or has_parent_label}, aria-label: {has_aria_label}",
            failure_type="Accessibility failure: File input lacks accessible label" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="accessible_upload_label",
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


def grade_file_upload_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the File Upload component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-file-upload", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-file-upload")
def realitybench_file_upload(llm) -> dict:
    """
    Evaluates LLM on File Upload software generation.
    """
    response = llm.prompt(FILE_UPLOAD_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_file_upload_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional file upload component on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    from ui import console, test_results_table, task_result_panel

    console.print("[bold cyan]Running local self-test for Task 04: File Upload...[/bold cyan]")
    report = grade_file_upload_implementation(NAIVE_FILE_UPLOAD_CODE)
    console.print(task_result_panel(
        "File Upload (Naive Baseline)",
        report.demo_score,
        report.reality_score,
        report.reality_gap
    ))
    console.print(test_results_table(report.test_results, "Task 04: File Upload Assertions"))
