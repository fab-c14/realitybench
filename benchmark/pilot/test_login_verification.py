"""
Verification script for RealityBench Login Task.
Validates grader against both Naive (happy-path only) and Robust implementations.
"""

import sys
import os

# Add realitybench to path
bench_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if bench_root not in sys.path:
    sys.path.insert(0, bench_root)

from benchmark.pilot.login import grade_login_implementation


NAIVE_CODE = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <h2>Login</h2>
  <input type="text" id="email" placeholder="Email" />
  <input type="password" id="password" placeholder="Password" />
  <button onclick="login()">Login</button>
  <div id="msg"></div>

  <script>
    function login() {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      .then(res => res.json())
      .then(data => {
        document.getElementById('msg').innerText = 'Welcome ' + (data.user?.name || '');
      });
    }
  </script>
</body>
</html>
"""

ROBUST_CODE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login</title>
</head>
<body>
  <form id="login-form">
    <label for="email">Email</label>
    <input type="email" id="email" name="email" required placeholder="name@domain.com" />
    <label for="password">Password</label>
    <input type="password" id="password" name="password" required placeholder="Enter password" />
    <button type="submit" id="submit-btn">Login</button>
  </form>
  <div id="status" role="status"></div>

  <script>
    const form = document.getElementById('login-form');
    const btn = document.getElementById('submit-btn');
    const status = document.getElementById('status');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      if (!email || !password) return;

      btn.disabled = true;
      btn.innerText = 'Logging in...';
      status.innerText = '';

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Server error occurred during login');
        }
        status.innerText = 'Welcome ' + (data.user?.name || 'User') + '! Login successful.';
      } catch (err) {
        status.innerText = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
        btn.innerText = 'Login';
      }
    });
  </script>
</body>
</html>
"""


def main():
    print("==================================================================")
    print("REALITYBENCH PILOT 1: LOGIN GRADER VERIFICATION")
    print("==================================================================")
    
    print("\n1. Evaluating Naive Implementation (Happy-path only)...")
    r_naive = grade_login_implementation(NAIVE_CODE)
    print(f"   Demo Score:   {r_naive.demo_score:6.2%}")
    print(f"   Reality Score:{r_naive.reality_score:6.2%}")
    print(f"   Reality Gap:  {r_naive.reality_gap:6.2%}")
    print(f"   Tests Passed: {sum(1 for t in r_naive.test_results if t.passed)}/{len(r_naive.test_results)}")

    print("\n2. Evaluating Robust Implementation (Production resilient)...")
    r_robust = grade_login_implementation(ROBUST_CODE)
    print(f"   Demo Score:   {r_robust.demo_score:6.2%}")
    print(f"   Reality Score:{r_robust.reality_score:6.2%}")
    print(f"   Reality Gap:  {r_robust.reality_gap:6.2%}")
    print(f"   Tests Passed: {sum(1 for t in r_robust.test_results if t.passed)}/{len(r_robust.test_results)}")
    
    print("\nTest Detail Comparison:")
    print(f"{'Test Name':<35} | {'Naive':<6} | {'Robust':<6} | {'Category'}")
    print("-" * 75)
    for t_n, t_r in zip(r_naive.test_results, r_robust.test_results):
        n_status = "PASS" if t_n.passed else "FAIL"
        r_status = "PASS" if t_r.passed else "FAIL"
        print(f"{t_n.test_name:<35} | {n_status:<6} | {r_status:<6} | {t_n.category}")
    print("==================================================================")


if __name__ == "__main__":
    main()
