# %%
"""
TASK: CRUD Dashboard Component (Task 05)

Purpose:
Evaluate whether an AI-generated web task management / CRUD dashboard handles
whitespace validation, server mutation failures (HTTP 500 rollback), empty datasets,
rapid double-click task creation, and keyboard/mobile constraints.

Happy Path:
- Initial task list loaded and rendered from GET /api/tasks
- New task creation flow sending POST to /api/tasks and updating DOM
- Task deletion flow sending DELETE to /api/tasks/{id}

Reality Tests:
- Blank or whitespace-only task title blocked before network dispatch
- Server mutation failure (HTTP 500 on DELETE) rolls back or retains item in DOM
- Empty dataset ({ 'tasks': [] }) renders friendly empty state ("No tasks yet")
- Rapid duplicate clicks on 'Add Task' trigger only a single POST request
- Accessible input labeling for task input
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


CRUD_DASHBOARD_TASK_PROMPT = """Build a self-contained web task management CRUD dashboard in HTML, CSS, and JavaScript.
The interface must contain:
1. An input field and 'Add Task' button to create new tasks
2. A task list container displaying tasks with their title and a 'Delete' action button for each task
3. An empty state indicator when no tasks exist ("No tasks yet")
When initialized, fetch initial tasks from GET '/api/tasks' (returns { 'tasks': [ { 'id': 1, 'title': 'Task One' } ] }).
When a new task is added, make a POST request to '/api/tasks' with { 'title': '...' }.
When a task is deleted, prompt for confirmation before making a DELETE request to '/api/tasks/{id}'.
The application should validate non-empty task titles, gracefully handle failed server mutations without corrupting local UI state, and provide appropriate user feedback.
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = CRUD_DASHBOARD_TASK_PROMPT

SAMPLE_TASKS = {
    "tasks": [
        {"id": 1, "title": "Write RealityBench documentation"},
        {"id": 2, "title": "Implement test harnesses"}
    ]
}

NAIVE_CRUD_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Tasks</h2>
  <input type="text" id="title" placeholder="New task">
  <button onclick="addTask()">Add Task</button>
  <ul id="list"></ul>
  <script>
    fetch('/api/tasks')
      .then(r => r.json())
      .then(d => {
        d.tasks.forEach(render);
      });

    function render(task) {
      const li = document.createElement('li');
      li.id = 'task-' + task.id;
      li.innerHTML = task.title + ' <button onclick="del(' + task.id + ')">Delete</button>';
      document.getElementById('list').appendChild(li);
    }

    function addTask() {
      const title = document.getElementById('title').value;
      fetch('/api/tasks', { method: 'POST', body: JSON.stringify({ title }) })
        .then(r => r.json())
        .then(d => render(d.task));
    }

    function del(id) {
      document.getElementById('task-' + id).remove();
      fetch('/api/tasks/' + id, { method: 'DELETE' });
    }
  </script>
</body>
</html>
"""

ROBUST_CRUD_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Task Dashboard</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 20px; max-width: 500px; margin: 0 auto; }
    .form-group { display: flex; gap: 8px; margin-bottom: 16px; }
    input { flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; }
    button { padding: 8px 16px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .delete-btn { background: #ef4444; padding: 4px 10px; font-size: 13px; }
    ul { list-style: none; padding: 0; margin: 0; }
    li { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }
    .empty-state { text-align: center; color: #64748b; padding: 24px; }
    .error { color: #dc2626; margin-bottom: 10px; font-size: 14px; }
  </style>
</head>
<body>
  <h2>Task Management</h2>
  <div id="error-banner" class="error" role="alert"></div>
  <form id="task-form" class="form-group">
    <input type="text" id="task-title" name="title" placeholder="What needs to be done?" aria-label="Task title" required>
    <button type="submit" id="add-btn">Add Task</button>
  </form>
  <div id="empty-state" class="empty-state" style="display:none;">No tasks yet. Add a task above!</div>
  <ul id="task-list" role="list"></ul>

  <script>
    let tasks = [];
    const listEl = document.getElementById('task-list');
    const emptyEl = document.getElementById('empty-state');
    const errEl = document.getElementById('error-banner');
    const form = document.getElementById('task-form');
    const input = document.getElementById('task-title');
    const addBtn = document.getElementById('add-btn');

    function showError(msg) { errEl.innerText = msg; }
    function clearError() { errEl.innerText = ''; }

    function renderList() {
      listEl.innerHTML = '';
      if (tasks.length === 0) {
        emptyEl.style.display = 'block';
        return;
      }
      emptyEl.style.display = 'none';
      tasks.forEach(t => {
        const li = document.createElement('li');
        li.id = 'task-' + t.id;
        li.innerHTML = `<span>${t.title}</span><button class="delete-btn" onclick="handleDelete(${t.id})">Delete</button>`;
        listEl.appendChild(li);
      });
    }

    async function loadTasks() {
      try {
        const res = await fetch('/api/tasks');
        if (!res.ok) throw new Error('Failed to load tasks');
        const data = await res.json();
        tasks = data.tasks || [];
        renderList();
      } catch (err) {
        showError('Error loading tasks: ' + err.message);
      }
    }

    form.onsubmit = async (e) => {
      e.preventDefault();
      clearError();
      const title = input.value.trim();
      if (!title) {
        showError('Task title cannot be empty.');
        return;
      }

      addBtn.disabled = true;
      try {
        const res = await fetch('/api/tasks', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
        if (!res.ok) throw new Error('Server rejected new task');
        const data = await res.json();
        tasks.push(data.task || { id: Date.now(), title });
        input.value = '';
        renderList();
      } catch (err) {
        showError('Could not add task: ' + err.message);
      } finally {
        addBtn.disabled = false;
      }
    };

    async function handleDelete(id) {
      clearError();
      const confirmed = confirm('Are you sure you want to delete this task?');
      if (!confirmed) return;

      try {
        const res = await fetch('/api/tasks/' + id, { method: 'DELETE' });
        if (!res.ok) throw new Error('Deletion failed on server');
        tasks = tasks.filter(t => t.id !== id);
        renderList();
      } catch (err) {
        showError('Error deleting task: ' + err.message);
      }
    }

    loadTasks();
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []

    # Test A.1: Render & Initial Data Fetch
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.load_html(html_code)
        session.page.wait_for_timeout(400)

        content_lower = session.page.content().lower()
        shows_items = "write realitybench" in content_lower and "implement test" in content_lower
        has_input = session.page.locator('input[type="text"], input').count() > 0
        has_add_btn = session.page.locator('button, input[type="submit"]').count() > 0

        passed = shows_items and has_input and has_add_btn
        results.append(TestResult(
            test_name="happy_path_render_initial_data",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Initial items rendered: {shows_items}, Input/Add button: {has_input and has_add_btn}",
            failure_type="Functional failure: Initial tasks not loaded or controls missing" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_render_initial_data",
            category="functional_correctness",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Functional failure: Crash loading initial data"
        ))

    # Test A.2: Create New Task Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        session.mock_route("**/api/tasks", status=201, json_body={"task": {"id": 3, "title": "Deploy to Kaggle"}})

        input_el = session.page.locator('input[type="text"], input').first
        add_btn = session.page.locator('button:has-text("Add"), input[value*="Add" i], button').first

        input_el.fill("Deploy to Kaggle")
        add_btn.click()
        session.page.wait_for_timeout(400)

        post_requests = [r for r in session.intercepted_requests if r["method"] == "POST"]
        post_sent = len(post_requests) > 0
        shows_new_item = "deploy to kaggle" in session.page.content().lower()

        passed = post_sent and shows_new_item
        results.append(TestResult(
            test_name="happy_path_create_task",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"POST fired: {post_sent}, New task rendered: {shows_new_item}",
            failure_type="Expected interaction failure: Failed to create or render new task" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_create_task",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception creating task"
        ))

    # Test A.3: Delete Task Flow with Confirmation
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.page.on("dialog", lambda dialog: dialog.accept())
        session.mock_route("**/api/tasks/*", status=200, json_body={"status": "deleted"})
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        del_btn = session.page.locator('button:has-text("Delete"), button:has-text("Remove"), .delete-btn').first
        has_del = del_btn.count() > 0
        if has_del:
            del_btn.click()
            session.page.wait_for_timeout(400)

        delete_requests = [r for r in session.intercepted_requests if r["method"] == "DELETE"]
        delete_fired = len(delete_requests) > 0

        passed = has_del and delete_fired
        results.append(TestResult(
            test_name="happy_path_delete_task",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Delete button: {has_del}, DELETE request fired: {delete_fired}",
            failure_type="Expected interaction failure: Task deletion failed or DELETE request missing" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_delete_task",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception deleting task"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Reject Empty / Whitespace Task Title
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        initial_reqs = len(session.intercepted_requests)
        input_el = session.page.locator('input[type="text"], input').first
        add_btn = session.page.locator('button:has-text("Add"), button').first

        input_el.fill("    ")
        add_btn.click()
        session.page.wait_for_timeout(300)

        new_posts = [r for r in session.intercepted_requests[initial_reqs:] if r["method"] == "POST"]
        blocked = (len(new_posts) == 0)

        results.append(TestResult(
            test_name="reject_whitespace_title",
            category="input_robustness",
            regime="reality",
            passed=blocked,
            details=f"Whitespace task submission blocked: {blocked}",
            failure_type="Input robustness failure: Sent POST request with empty/whitespace task title" if not blocked else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="reject_whitespace_title",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception testing title validation"
        ))

    # Test B.2: Mutation Failure (HTTP 500) & State Integrity
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.page.on("dialog", lambda dialog: dialog.accept())
        session.mock_route("**/api/tasks/*", status=500, json_body={"error": "Database lock timeout"})
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        del_btn = session.page.locator('button:has-text("Delete"), button:has-text("Remove"), .delete-btn').first
        if del_btn.count() > 0:
            del_btn.click()
        session.page.wait_for_timeout(400)

        content_lower = session.page.content().lower()
        item_preserved = "write realitybench" in content_lower
        shows_error = any(w in content_lower for w in ["error", "fail", "unable", "lock", "problem"])

        passed = item_preserved and shows_error
        results.append(TestResult(
            test_name="mutation_failure_rollback",
            category="failure_recovery",
            regime="reality",
            passed=passed,
            details=f"Item preserved in DOM: {item_preserved}, Error feedback shown: {shows_error}",
            failure_type="State consistency failure: Item disappeared despite server DELETE failure" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="mutation_failure_rollback",
            category="failure_recovery",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Recovery failure: Exception during mutation failure test"
        ))

    # Test B.3: Empty Dataset State
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body={"tasks": []})
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        content_lower = session.page.content().lower()
        shows_empty_state = any(phrase in content_lower for phrase in ["no tasks", "no items", "empty", "add a task", "nothing"])

        results.append(TestResult(
            test_name="empty_state_rendering",
            category="state_robustness",
            regime="reality",
            passed=shows_empty_state,
            details=f"Helpful empty state rendered: {shows_empty_state}",
            failure_type="State robustness failure: Blank/unhelpful state when task list is empty" if not shows_empty_state else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="empty_state_rendering",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception checking empty state"
        ))

    # Test B.4: Double Click Prevention on Add Task
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        session.mock_route("**/api/tasks", status=201, json_body={"task": {"id": 99, "title": "Double Click"}}, delay_ms=800)

        input_el = session.page.locator('input[type="text"], input').first
        input_el.fill("Double Click Task")

        initial_posts = len([r for r in session.intercepted_requests if r["method"] == "POST"])

        session.page.evaluate("""() => {
            const b = document.querySelector('button, input[type="submit"]');
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        new_posts = len([r for r in session.intercepted_requests if r["method"] == "POST"]) - initial_posts
        passed = (new_posts == 1)

        results.append(TestResult(
            test_name="prevent_duplicate_task_creation",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"POST requests fired: {new_posts} (expected 1)",
            failure_type="Duplicate interaction: Multiple POST requests sent on double click" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_task_creation",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction safety failure: Exception testing double click"
        ))

    # Test B.5: Accessibility
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        input_el = session.page.locator('input[type="text"], input').first
        has_aria = bool(input_el.get_attribute("aria-label"))
        input_id = input_el.get_attribute("id")
        has_label = False
        if input_id:
            has_label = session.page.locator(f'label[for="{input_id}"]').count() > 0

        passed = has_aria or has_label or bool(input_el.get_attribute("placeholder"))
        results.append(TestResult(
            test_name="accessible_task_input",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Label: {has_label}, Aria-label: {has_aria}",
            failure_type="Accessibility failure: Input lacks label or accessible description" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="accessible_task_input",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting labels"
        ))

    # Test B.6: Mobile Responsive Viewport
    session = harness.new_session()
    try:
        session.mock_route("**/api/tasks", status=200, json_body=SAMPLE_TASKS)
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


def grade_crud_dashboard_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the CRUD Dashboard component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-crud-dashboard", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-crud-dashboard")
def realitybench_crud_dashboard(llm) -> dict:
    """
    Evaluates LLM on CRUD Dashboard software generation.
    """
    response = llm.prompt(CRUD_DASHBOARD_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_crud_dashboard_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional CRUD dashboard on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    from ui import console, test_results_table, task_result_panel

    console.print("[bold cyan]Running local self-test for Task 05: CRUD Dashboard...[/bold cyan]")
    report = grade_crud_dashboard_implementation(NAIVE_CRUD_CODE)
    console.print(task_result_panel(
        "CRUD Dashboard (Naive Baseline)",
        report.demo_score,
        report.reality_score,
        report.reality_gap
    ))
    console.print(test_results_table(report.test_results, "Task 05: CRUD Dashboard Assertions"))
