# %%
"""
TASK: Chat Component (Task 07)

Purpose:
Evaluate whether an AI-generated web chat interface validates against empty messages,
handles server errors without wiping conversation history, prevents double-click spam,
supports keyboard Enter submission, wraps long unbroken strings, and fits mobile screens.

Happy Path:
- Renders scrollable message history, text input, and send button
- Normal message flow: Appends user message, clears input, dispatches POST to /api/chat,
  and renders bot reply

Reality Tests:
- Blank or whitespace-only messages blocked from network dispatch
- Server error (HTTP 500) displays in-chat error feedback without wiping prior history
- Rapid duplicate clicks on Send button do not spam multiple POST requests
- Keyboard accessibility: Pressing Enter in input submits message
- Long unbroken string (150 chars) wraps properly without horizontal viewport blowout
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


CHAT_TASK_PROMPT = """Build a self-contained web chat interface in HTML, CSS, and JavaScript.
The interface must contain:
1. A scrollable message history container
2. A message text input or textarea
3. A 'Send' button
When the user sends a message, append their message to the chat history, clear the input, and make a POST request to '/api/chat' with { 'message': '...' }.
The server responds with { 'reply': '...' }. Upon receiving the response, append the bot reply to the chat history.
The application should:
- Prevent sending empty or whitespace-only messages
- Prevent duplicate sends on rapid clicks or Enter key spam
- Display an in-chat error notification if the API call fails (HTTP 500) without crashing or clearing chat history
- Automatically scroll to the latest message
- Support sending messages using the keyboard (Enter key)
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = CHAT_TASK_PROMPT

NAIVE_CHAT_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Chat</h2>
  <div id="chat" style="height: 200px; overflow-y: scroll;"></div>
  <input type="text" id="msg">
  <button onclick="send()">Send</button>
  <script>
    function send() {
      const msg = document.getElementById('msg').value;
      const chat = document.getElementById('chat');
      chat.innerHTML += '<p>User: ' + msg + '</p>';
      document.getElementById('msg').value = '';
      fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: msg })
      })
      .then(r => r.json())
      .then(d => {
        chat.innerHTML += '<p>Bot: ' + d.reply + '</p>';
      });
    }
  </script>
</body>
</html>
"""

ROBUST_CHAT_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chat Assistant</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 16px; max-width: 450px; margin: 0 auto; }
    .chat-container { display: flex; flex-direction: column; height: 80vh; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; }
    .messages { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
    .msg { padding: 8px 12px; border-radius: 8px; max-width: 80%; word-break: break-word; overflow-wrap: anywhere; }
    .msg.user { background: #2563eb; color: #fff; align-self: flex-end; }
    .msg.bot { background: #f1f5f9; color: #0f172a; align-self: flex-start; }
    .msg.error { background: #fee2e2; color: #b91c1c; align-self: center; font-size: 13px; }
    form { display: flex; gap: 6px; padding: 8px; border-top: 1px solid #cbd5e1; background: #fff; }
    input { flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; }
    button { padding: 8px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="chat-container">
    <div id="messages" class="messages" role="log" aria-live="polite"></div>
    <form id="chat-form">
      <input type="text" id="chat-input" placeholder="Type a message..." aria-label="Chat message" required>
      <button type="submit" id="send-btn">Send</button>
    </form>
  </div>

  <script>
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const btn = document.getElementById('send-btn');
    const msgContainer = document.getElementById('messages');

    function appendMessage(text, type) {
      const el = document.createElement('div');
      el.className = 'msg ' + type;
      el.textContent = text;
      msgContainer.appendChild(el);
      msgContainer.scrollTop = msgContainer.scrollHeight;
    }

    form.onsubmit = async (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      appendMessage(message, 'user');
      input.value = '';
      btn.disabled = true;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });
        if (!res.ok) throw new Error('Assistant service unavailable');
        const data = await res.json();
        appendMessage(data.reply || 'No reply received', 'bot');
      } catch (err) {
        appendMessage('Error: ' + err.message, 'error');
      } finally {
        btn.disabled = false;
        input.focus();
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
        has_input = session.page.locator('input[type="text"], textarea, input').count() > 0
        has_send = session.page.locator('button, input[type="submit"]').count() > 0
        has_history = session.page.locator('#messages, #chat, .messages, .chat, ul, div').count() > 0

        passed = has_input and has_send and has_history
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Input: {has_input}, Send button: {has_send}, History: {has_history}",
            failure_type="Functional failure: Missing chat input or history container" if not passed else ""
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

    # Test A.2: Normal Message & Reply Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={
            "reply": "I am your automated AI assistant."
        })
        session.load_html(html_code)

        input_el = session.page.locator('input[type="text"], textarea, input').first
        send_btn = session.page.locator('button, input[type="submit"]').first

        input_el.fill("Hello RealityBench")
        send_btn.click()
        session.page.wait_for_timeout(400)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        post_fired = len(post_requests) > 0
        content_lower = session.page.content().lower()

        user_msg_shown = "hello realitybench" in content_lower
        bot_reply_shown = "automated ai assistant" in content_lower
        input_cleared = (input_el.input_value().strip() == "")

        passed = post_fired and user_msg_shown and bot_reply_shown and input_cleared
        results.append(TestResult(
            test_name="happy_path_send_and_reply",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST: {post_fired}, User msg shown: {user_msg_shown}, Reply shown: {bot_reply_shown}, Cleared: {input_cleared}",
            failure_type="Expected interaction failure: Chat message or bot reply not rendered" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_send_and_reply",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception sending message"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Prevent Empty/Whitespace Messages
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={"reply": "unexpected"})
        session.load_html(html_code)

        input_el = session.page.locator('input[type="text"], textarea, input').first
        send_btn = session.page.locator('button, input[type="submit"]').first

        input_el.fill("    ")
        send_btn.click()
        session.page.wait_for_timeout(300)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        blocked = (len(post_requests) == 0)

        results.append(TestResult(
            test_name="reject_whitespace_message",
            category="input_robustness",
            regime="reality",
            passed=blocked,
            details=f"Whitespace message blocked: {blocked}",
            failure_type="Input robustness failure: Sent whitespace-only chat message to server" if not blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_whitespace_message",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing empty message"
        ))

    # Test B.2: Server Error Handling & History Integrity
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={"reply": "First response ok."})
        session.load_html(html_code)

        input_el = session.page.locator('input[type="text"], textarea, input').first
        send_btn = session.page.locator('button, input[type="submit"]').first

        input_el.fill("First question")
        send_btn.click()
        session.page.wait_for_timeout(400)

        session.mock_route("**/api/chat", status=500, json_body={"error": "Chat service overloaded"})
        input_el.fill("Second question causing error")
        send_btn.click()
        session.page.wait_for_timeout(400)

        content_lower = session.page.content().lower()
        shows_error = any(w in content_lower for w in ["error", "fail", "unable", "overloaded", "problem", "could not"])
        first_msg_preserved = "first question" in content_lower and "first response ok" in content_lower

        passed = shows_error and first_msg_preserved
        results.append(TestResult(
            test_name="server_error_feedback_and_preservation",
            category="failure_recovery",
            regime="reality",
            passed=passed,
            details=f"Error feedback visible: {shows_error}, Prior history preserved: {first_msg_preserved}",
            failure_type="Recovery failure: Silent crash or history wiped out on server error" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="server_error_feedback_and_preservation",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Recovery failure: Exception during chat error test"
        ))

    # Test B.3: Double Click / Rapid Send Prevention
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={"reply": "Fast reply"}, delay_ms=800)
        session.load_html(html_code)

        input_el = session.page.locator('input[type="text"], textarea, input').first
        input_el.fill("Rapid double click test")

        session.page.evaluate("""() => {
            const b = document.querySelector('button, input[type="submit"]');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        post_count = len([r for r in session.intercepted_requests if r["method"] == "POST"])
        passed = (post_count == 1)

        results.append(TestResult(
            test_name="prevent_duplicate_message_send",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"POST requests fired: {post_count} (expected 1)",
            failure_type="Duplicate interaction: Multiple messages sent on double click" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_message_send",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction safety failure: Exception testing double click"
        ))

    # Test B.4: Keyboard Enter Key Submission
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={"reply": "Enter received"})
        session.load_html(html_code)

        input_el = session.page.locator('input[type="text"], textarea, input').first
        input_el.focus()
        input_el.type("Submitted with enter")
        session.page.keyboard.press("Enter")
        session.page.wait_for_timeout(400)

        post_count = len([r for r in session.intercepted_requests if r["method"] == "POST"])
        passed = (post_count > 0)

        results.append(TestResult(
            test_name="keyboard_enter_send",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Message submitted via Enter key: {passed}",
            failure_type="Accessibility failure: Pressing Enter does not submit message" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="keyboard_enter_send",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception testing Enter key"
        ))

    # Test B.5: Long Unbroken Word-Wrap Integrity
    session = harness.new_session()
    try:
        session.mock_route("**/api/chat", status=200, json_body={"reply": "Got long message"})
        session.load_html(html_code)

        long_word = "A" * 150
        input_el = session.page.locator('input[type="text"], textarea, input').first
        send_btn = session.page.locator('button, input[type="submit"]').first
        input_el.fill(long_word)
        send_btn.click()
        session.page.wait_for_timeout(300)

        scroll_width = session.page.evaluate("document.documentElement.scrollWidth")
        client_width = session.page.evaluate("document.documentElement.clientWidth")
        no_overflow = scroll_width <= (client_width + 5)

        results.append(TestResult(
            test_name="unbroken_string_overflow_wrap",
            category="state_robustness",
            regime="reality",
            passed=no_overflow,
            details=f"scrollWidth: {scroll_width}, clientWidth: {client_width}",
            failure_type="State robustness failure: Long unbroken string caused horizontal viewport blowout" if not no_overflow else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="unbroken_string_overflow_wrap",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception testing long word wrap"
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


def grade_chat_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Chat component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-chat", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-chat")
def realitybench_chat(llm) -> dict:
    """
    Evaluates LLM on Chat software generation.
    """
    response = llm.prompt(CHAT_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_chat_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional chat component on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    from ui import console, test_results_table, task_result_panel

    console.print("[bold cyan]Running local self-test for Task 07: Chat Component...[/bold cyan]")
    report = grade_chat_implementation(NAIVE_CHAT_CODE)
    console.print(task_result_panel(
        "Chat Component (Naive Baseline)",
        report.demo_score,
        report.reality_score,
        report.reality_gap
    ))
    console.print(test_results_table(report.test_results, "Task 07: Chat Assertions"))
