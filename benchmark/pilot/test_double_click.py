import sys
import os

bench_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, bench_root)

from benchmark.pilot.test_login_verification import NAIVE_CODE, ROBUST_CODE
from benchmark.graders.browser_runner import HeadlessHarness

with HeadlessHarness() as h:
    # 1. Test Naive
    s_naive = h.new_session()
    s_naive.mock_route("**/api/login", status=200, json_body={"token": "123"}, delay_ms=400)
    s_naive.load_html(NAIVE_CODE)
    s_naive.page.locator('input[type="text"]').fill("test@example.com")
    s_naive.page.locator('input[type="password"]').fill("pass")
    
    # Rapid double click via dispatch
    s_naive.page.evaluate("() => { const b = document.querySelector('button'); b.click(); b.click(); }")
    s_naive.page.wait_for_timeout(600)
    print("Naive requests count:", len(s_naive.intercepted_requests))

    # 2. Test Robust
    s_rob = h.new_session()
    s_rob.mock_route("**/api/login", status=200, json_body={"token": "123"}, delay_ms=400)
    s_rob.load_html(ROBUST_CODE)
    s_rob.page.locator("#email").fill("test@example.com")
    s_rob.page.locator("#password").fill("pass")
    
    # Rapid double click via dispatch
    s_rob.page.evaluate("() => { const b = document.querySelector('button'); b.click(); b.click(); }")
    s_rob.page.wait_for_timeout(600)
    print("Robust requests count:", len(s_rob.intercepted_requests))
