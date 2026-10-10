# %%
"""
TASK: Admin Table Component (Task 09)

Purpose:
Evaluate whether an AI-generated administrative table component renders tabular controls,
fetches paginated records, gracefully handles null/undefined data values without throwing
runtime TypeError crashes, handles empty datasets, and prevents double-clicking pagination.

Happy Path:
- Renders table structure, search input, role filter dropdown, and pagination buttons
- Initial user records loaded and rendered from GET /api/users?page=1
- Pagination flow: Clicking 'Next' requests Page 2 and updates displayed rows

Reality Tests:
- Empty dataset ({ 'users': [] }) renders friendly empty state ("No users matching criteria")
- Null / undefined field values handled safely without crashing table rendering
- Search input dispatches query to backend
- Double-click prevention: Rapid duplicate clicks on pagination trigger only one request
- Accessible table semantics (th column headers and form labels)
- Responsive behavior: 375px mobile viewport has no horizontal page blowout (scroll container)

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


ADMIN_TABLE_TASK_PROMPT = """Build a self-contained administrative user table component in HTML, CSS, and JavaScript.
The interface must contain:
1. A table displaying users with columns: ID, Name, Role, Status
2. A search filter input to filter users by name
3. A role filter dropdown (All, Admin, Editor, Viewer)
4. Pagination controls (Previous, Next, page indicator)
When initialized, fetch user records from GET '/api/users?page=1&limit=5'.
The API returns { 'users': [ { 'id': 1, 'name': 'Sarah Connor', 'role': 'Admin', 'status': 'Active' } ], 'total': 12, 'page': 1, 'pages': 3 }.
When filtering or changing pages, request the appropriate query parameters (e.g., '/api/users?page=2', '/api/users?q=Sarah', '/api/users?role=Admin').
The application should:
- Display a clear empty state ("No users matching criteria") when results are empty
- Gracefully handle sorting or filtering when dataset values contain null/undefined fields without throwing unhandled exceptions
- Provide responsive design (horizontal scroll container or card view) for mobile screens
Provide all code in a single self-contained HTML document without external libraries."""

TASK_SPEC = ADMIN_TABLE_TASK_PROMPT

SAMPLE_USERS_PAGE_1 = {
    "users": [
        {"id": 1, "name": "Sarah Connor", "role": "Admin", "status": "Active"},
        {"id": 2, "name": "John Connor", "role": "Editor", "status": "Active"}
    ],
    "total": 12,
    "page": 1,
    "pages": 3
}

SAMPLE_USERS_PAGE_2 = {
    "users": [
        {"id": 3, "name": "Kyle Reese", "role": "Viewer", "status": "Pending"}
    ],
    "total": 12,
    "page": 2,
    "pages": 3
}

NAIVE_ADMIN_TABLE_CODE = """
<!DOCTYPE html>
<html>
<body>
  <h2>Users</h2>
  <input type="text" id="q" onkeyup="search()">
  <select id="role"><option>All</option></select>
  <table id="tbl">
    <thead><tr><td>ID</td><td>Name</td><td>Role</td><td>Status</td></tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <button onclick="prev()">Prev</button>
  <button onclick="next()">Next</button>
  <script>
    let page = 1;
    function load() {
      fetch('/api/users?page=' + page)
        .then(r => r.json())
        .then(d => {
          let h = '';
          d.users.forEach(u => {
            h += '<tr><td>' + u.id + '</td><td>' + u.name.toUpperCase() + '</td><td>' + u.role + '</td><td>' + u.status + '</td></tr>';
          });
          document.getElementById('tbody').innerHTML = h;
        });
    }
    function next() { page++; load(); }
    function prev() { page--; load(); }
    function search() {}
    load();
  </script>
</body>
</html>
"""

ROBUST_ADMIN_TABLE_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>User Administration</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; padding: 16px; max-width: 650px; margin: 0 auto; }
    .filters { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    input, select { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; }
    .table-container { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; border: 1px solid #e2e8f0; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }
    th { background: #f8fafc; font-weight: 600; color: #475569; }
    .pagination { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
    button { padding: 6px 14px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .empty-state { text-align: center; padding: 24px; color: #64748b; }
  </style>
</head>
<body>
  <h2>User Administration</h2>
  <div class="filters">
    <input type="search" id="search-input" placeholder="Search by name..." aria-label="Search users" />
    <select id="role-filter" aria-label="Filter by role">
      <option value="">All Roles</option>
      <option value="Admin">Admin</option>
      <option value="Editor">Editor</option>
      <option value="Viewer">Viewer</option>
    </select>
  </div>

  <div class="table-container">
    <table aria-label="Users Table">
      <thead>
        <tr>
          <th scope="col">ID</th>
          <th scope="col">Name</th>
          <th scope="col">Role</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody id="users-body"></tbody>
    </table>
    <div id="empty-state" class="empty-state" style="display:none;">No users matching criteria.</div>
  </div>

  <div class="pagination">
    <button id="prev-btn" disabled>Previous</button>
    <span id="page-indicator">Page 1 of 1</span>
    <button id="next-btn">Next</button>
  </div>

  <script>
    let currentPage = 1;
    let totalPages = 1;
    let isLoading = false;

    const tbody = document.getElementById('users-body');
    const emptyState = document.getElementById('empty-state');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageIndicator = document.getElementById('page-indicator');
    const searchInput = document.getElementById('search-input');
    const roleSelect = document.getElementById('role-filter');

    async function fetchUsers() {
      if (isLoading) return;
      isLoading = true;
      prevBtn.disabled = true;
      nextBtn.disabled = true;

      const q = encodeURIComponent(searchInput.value.trim());
      const role = encodeURIComponent(roleSelect.value);
      const url = `/api/users?page=${currentPage}&limit=5${q ? '&q=' + q : ''}${role ? '&role=' + role : ''}`;

      try {
        const res = await fetch(url);
        if (!res.ok) throw new Error('API request failed');
        const data = await res.json();
        
        totalPages = data.pages || 1;
        pageIndicator.innerText = `Page ${currentPage} of ${totalPages}`;

        const users = data.users || [];
        tbody.innerHTML = '';
        if (users.length === 0) {
          emptyState.style.display = 'block';
        } else {
          emptyState.style.display = 'none';
          users.forEach(u => {
            const tr = document.createElement('tr');
            const safeName = u.name ? String(u.name) : '—';
            const safeRole = u.role ? String(u.role) : '—';
            const safeStatus = u.status ? String(u.status) : '—';
            tr.innerHTML = `<td>${u.id || ''}</td><td>${safeName}</td><td>${safeRole}</td><td>${safeStatus}</td>`;
            tbody.appendChild(tr);
          });
        }
      } catch (err) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:red;">Error loading users</td></tr>';
      } finally {
        isLoading = false;
        prevBtn.disabled = (currentPage <= 1);
        nextBtn.disabled = (currentPage >= totalPages);
      }
    }

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        currentPage = 1;
        fetchUsers();
      }
    });

    roleSelect.addEventListener('change', () => {
      currentPage = 1;
      fetchUsers();
    });

    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages && !isLoading) {
        currentPage++;
        fetchUsers();
      }
    });

    prevBtn.addEventListener('click', () => {
      if (currentPage > 1 && !isLoading) {
        currentPage--;
        fetchUsers();
      }
    });

    fetchUsers();
  </script>
</body>
</html>
"""


def run_happy_path(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates expected happy-path behavior (Demo Score / Regime A)."""
    results: List[TestResult] = []

    # Test A.1: Render Controls & Structure
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        has_table = session.page.locator('table, .table, [role="table"]').count() > 0
        has_search = session.page.locator('input[type="search"], input[type="text"], input').count() > 0
        has_filter = session.page.locator('select').count() > 0
        has_nav = session.page.locator('button:has-text("Next"), button:has-text(">"), button').count() >= 2

        passed = has_table and has_search and has_nav
        results.append(TestResult(
            test_name="happy_path_render_elements",
            category="functional_correctness",
            regime="demo",
            passed=passed,
            details=f"Table: {has_table}, Search: {has_search}, Filter: {has_filter}, Pagination: {has_nav}",
            failure_type="Functional failure: Missing table, search filter, or pagination buttons" if not passed else ""
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

    # Test A.2: Initial Data Fetch & Rows Render
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.load_html(html_code)
        session.page.wait_for_timeout(400)

        content_lower = session.visible_text()
        shows_sarah = "sarah connor" in content_lower
        shows_john = "john connor" in content_lower

        passed = shows_sarah and shows_john
        results.append(TestResult(
            test_name="happy_path_render_initial_rows",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Rendered users: Sarah={shows_sarah}, John={shows_john}",
            failure_type="Expected interaction failure: Initial user records not displayed in table" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_render_initial_rows",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception displaying rows"
        ))

    # Test A.3: Pagination Flow
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*page=1*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.mock_route("**/api/users*page=2*", status=200, json_body=SAMPLE_USERS_PAGE_2)
        session.mock_route("**/api/users", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        next_btn = session.page.locator('button:has-text("Next"), button:has-text(">")').first
        has_next = next_btn.count() > 0
        if has_next:
            next_btn.click()
        session.page.wait_for_timeout(400)

        page2_reqs = [r for r in session.intercepted_requests if "page=2" in r["url"]]
        page2_fired = len(page2_reqs) > 0
        content_lower = session.visible_text()
        shows_kyle = "kyle reese" in content_lower

        passed = page2_fired or shows_kyle
        results.append(TestResult(
            test_name="happy_path_pagination",
            category="expected_interactions",
            regime="demo",
            passed=passed,
            details=f"Page 2 requested: {page2_fired}, Kyle Reese displayed: {shows_kyle}",
            failure_type="Expected interaction failure: Clicking Next did not request or render Page 2" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="happy_path_pagination",
            category="expected_interactions",
            regime="demo",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception during pagination"
        ))

    return results


def run_reality_tests(harness: HeadlessHarness, html_code: str) -> List[TestResult]:
    """Evaluates resilience under controlled perturbations (Reality Score / Regime B)."""
    results: List[TestResult] = []

    # Test B.1: Empty Results State
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body={"users": [], "total": 0, "page": 1, "pages": 0})
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        content_lower = session.visible_text()
        shows_empty = any(phrase in content_lower for phrase in ["no users", "no results", "empty", "no matching", "not found"])

        results.append(TestResult(
            test_name="empty_dataset_state",
            category="state_robustness",
            regime="reality",
            passed=shows_empty,
            details=f"Empty state feedback visible: {shows_empty}",
            failure_type="State robustness failure: Blank or uninformative table when dataset is empty" if not shows_empty else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="empty_dataset_state",
            category="state_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="State robustness failure: Exception checking empty state"
        ))

    # Test B.2: Null / Undefined Field Resilience (No Crash)
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body={
            "users": [
                {"id": 99, "name": None, "role": None, "status": None}
            ],
            "total": 1,
            "page": 1,
            "pages": 1
        })
        session.load_html(html_code)
        session.page.wait_for_timeout(300)

        no_crash = session.page.locator('table, .table').count() > 0

        results.append(TestResult(
            test_name="null_field_resilience",
            category="input_robustness",
            regime="reality",
            passed=no_crash,
            details=f"Table survived null fields without crash: {no_crash}",
            failure_type="Input robustness failure: Table crashed on null/undefined record fields" if not no_crash else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="null_field_resilience",
            category="input_robustness",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Input robustness failure: Exception rendering null fields"
        ))

    # Test B.3: Search Query Dispatch
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.load_html(html_code)
        session.page.wait_for_timeout(200)

        search_input = session.page.locator('input[type="search"], input[type="text"], input').first
        search_input.fill("Sarah")
        session.page.keyboard.press("Enter")
        session.page.wait_for_timeout(400)

        search_requests = [r for r in session.intercepted_requests if ("sarah" in r["url"].lower() or "q=" in r["url"].lower())]
        query_dispatched = len(search_requests) > 0

        results.append(TestResult(
            test_name="search_query_dispatch",
            category="expected_interactions",
            regime="reality",
            passed=query_dispatched,
            details=f"Search request dispatched: {query_dispatched}",
            failure_type="Expected interaction failure: Search query not sent to API" if not query_dispatched else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="search_query_dispatch",
            category="expected_interactions",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Expected interaction failure: Exception testing search filter"
        ))

    # Test B.4: Double Click Prevention on Pagination
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*page=1*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.mock_route("**/api/users*page=2*", status=200, json_body=SAMPLE_USERS_PAGE_2, delay_ms=800)
        session.load_html(html_code)
        session.page.wait_for_timeout(200)

        initial_reqs = len(session.intercepted_requests)

        session.page.evaluate("""() => {
            const b = Array.from(document.querySelectorAll('button')).find(el => el.innerText.includes('Next') || el.innerText.includes('>'));
            if (b) { b.click(); b.click(); }
        }""")
        session.page.wait_for_timeout(400)

        new_reqs = len(session.intercepted_requests) - initial_reqs
        passed = (new_reqs <= 1)

        results.append(TestResult(
            test_name="prevent_duplicate_pagination_click",
            category="interaction_safety",
            regime="reality",
            passed=passed,
            details=f"Pagination requests fired on double click: {new_reqs}",
            failure_type="Duplicate interaction: Multiple requests fired on pagination double-click" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="prevent_duplicate_pagination_click",
            category="interaction_safety",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Interaction safety failure: Exception testing pagination double-click"
        ))

    # Test B.5: Accessibility
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body=SAMPLE_USERS_PAGE_1)
        session.load_html(html_code)
        session.page.wait_for_timeout(200)

        has_th = session.page.locator('th').count() >= 3
        has_labels = session.page.locator('label, [aria-label]').count() >= 1

        passed = has_th and has_labels
        results.append(TestResult(
            test_name="accessible_table_structure",
            category="accessibility",
            regime="reality",
            passed=passed,
            details=f"Table headers (th): {has_th}, Form labels: {has_labels}",
            failure_type="Accessibility failure: Missing <th> column headers or form labels" if not passed else ""
        ))
    except Exception as e:
        results.append(TestResult(
            test_name="accessible_table_structure",
            category="accessibility",
            regime="reality",
            passed=False,
            details=str(e),
            failure_type="Accessibility failure: Exception inspecting table accessibility"
        ))

    # Test B.6: Mobile Responsive Viewport
    session = harness.new_session()
    try:
        session.mock_route("**/api/users*", status=200, json_body=SAMPLE_USERS_PAGE_1)
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
            failure_type="Responsive failure: Table caused horizontal page blowout on mobile" if not no_horizontal_overflow else ""
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


def grade_admin_table_implementation(html_code: str) -> EvaluationReport:
    """
    Executes deterministic headless browser evaluation of the Admin Table component.
    """
    with HeadlessHarness() as harness:
        demo_results = run_happy_path(harness, html_code)
        reality_results = run_reality_tests(harness, html_code)

    return calculate_scores("realitybench-admin-table", demo_results + reality_results)


# %%
@kbench.task(name="realitybench-admin-table")
def realitybench_admin_table(llm) -> dict:
    """
    Evaluates LLM on Admin Table software generation.
    """
    response = llm.prompt(ADMIN_TABLE_TASK_PROMPT)
    code = extract_html_code(response)
    report = grade_admin_table_implementation(code)
    kbench.assertions.assert_true(
        report.demo_score > 0.0,
        expectation="Model should produce a functional admin table on happy path"
    )
    return report.to_dict()


# %%
if __name__ == "__main__":
    if should_run_kbench():
        realitybench_admin_table.run(kbench.llm)
    else:
        for label, code in (("naive", NAIVE_ADMIN_TABLE_CODE), ("robust", ROBUST_ADMIN_TABLE_CODE)):
            r = grade_admin_table_implementation(code)
            print(f"{label:6} demo={r.demo_score:.2f} reality={r.reality_score:.2f} gap={r.reality_gap:+.2f}")
