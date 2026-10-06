"""
RealityBench - Pilot Evaluation Runner
Runs the 3 pilot tasks (Login, Search, Checkout) across multiple models:
- naive-baseline
- robust-baseline
- qwen2.5-coder:1.5b
- qwen2.5-coder:7b
- gemma2:2b

Outputs structured results to results/pilot_results.json and prints comparative analysis.
"""

import os
import sys
import json
import re
import time
import urllib.request
from typing import Dict, Any, Optional

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from benchmark.pilot.login import LOGIN_TASK_PROMPT as LOGIN_SPEC, NAIVE_LOGIN_CODE, ROBUST_LOGIN_CODE, grade_login_implementation
from benchmark.pilot.search import SEARCH_TASK_PROMPT as SEARCH_SPEC, NAIVE_SEARCH_CODE, ROBUST_SEARCH_CODE, grade_search_implementation
from benchmark.pilot.checkout import CHECKOUT_TASK_PROMPT as CHECKOUT_SPEC, NAIVE_CHECKOUT_CODE, ROBUST_CHECKOUT_CODE, grade_checkout_implementation


def extract_html(raw_response: str) -> str:
    """Extract HTML code block from markdown or return raw string."""
    # Look for ```html ... ```
    m = re.search(r"```html\s*(.*?)\s*```", raw_response, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Look for generic ``` ... ```
    m = re.search(r"```\s*(.*?)\s*```", raw_response, re.DOTALL)
    if m:
        content = m.group(1).strip()
        if "<" in content and ">" in content:
            return content
    # If no fences, return raw if it contains HTML tags
    if "<form" in raw_response or "<input" in raw_response or "<html" in raw_response or "<div" in raw_response:
        return raw_response.strip()
    return raw_response.strip()


def query_ollama(model: str, task_prompt: str, timeout: int = 180) -> str:
    """Query local Ollama instance for model completion."""
    url = "http://localhost:11434/api/generate"
    full_prompt = (
        f"{task_prompt.strip()}\n\n"
        "Requirements:\n"
        "- Return ONLY self-contained HTML and JavaScript code.\n"
        "- Wrap the code in a single ```html ... ``` block.\n"
        "- Do not provide explanatory commentary outside the code block."
    )
    payload = json.dumps({
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,  # Low temperature for stable evaluation
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def run_pilot():
    print("=" * 80)
    print(" RealityBench - Pilot Evaluation Suite")
    print(" Benchmarking AI-Generated Software Beyond the Happy Path")
    print("=" * 80)
    
    results_dir = os.path.join(BASE_DIR, "results")
    code_dir = os.path.join(results_dir, "generated_code")
    os.makedirs(code_dir, exist_ok=True)
    
    tasks = [
        {"name": "login", "spec": LOGIN_SPEC, "evaluator": grade_login_implementation, "naive": NAIVE_LOGIN_CODE, "robust": ROBUST_LOGIN_CODE},
        {"name": "search", "spec": SEARCH_SPEC, "evaluator": grade_search_implementation, "naive": NAIVE_SEARCH_CODE, "robust": ROBUST_SEARCH_CODE},
        {"name": "checkout", "spec": CHECKOUT_SPEC, "evaluator": grade_checkout_implementation, "naive": NAIVE_CHECKOUT_CODE, "robust": ROBUST_CHECKOUT_CODE},
    ]
    
    models = [
        {"id": "naive-baseline", "type": "baseline"},
        {"id": "robust-baseline", "type": "baseline"},
        {"id": "qwen2.5-coder:1.5b", "type": "ollama"},
        {"id": "gemma2:2b", "type": "ollama"},
    ]
    
    full_results = {
        "benchmark": "RealityBench-Pilot",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {},
        "summary": []
    }
    
    for m in models:
        model_id = m["id"]
        model_type = m["type"]
        slug = model_id.replace(":", "_").replace("/", "_")
        m_code_dir = os.path.join(code_dir, slug)
        os.makedirs(m_code_dir, exist_ok=True)
        
        print(f"\n>>> Evaluating Model: {model_id} ({model_type})")
        full_results["models"][model_id] = {}
        
        model_demo_scores = []
        model_reality_scores = []
        model_gaps = []
        
        for t in tasks:
            task_name = t["name"]
            print(f"  -> Task: {task_name.upper()}... ", end="", flush=True)
            
            # Obtain code
            code = ""
            if model_id == "naive-baseline":
                code = t["naive"]
            elif model_id == "robust-baseline":
                code = t["robust"]
            else:
                code_path = os.path.join(m_code_dir, f"{task_name}.html")
                # Cache generated code if already generated
                if os.path.exists(code_path):
                    with open(code_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    print("(cached generation) ", end="", flush=True)
                else:
                    print("(generating) ", end="", flush=True)
                    try:
                        raw_resp = query_ollama(model_id, t["spec"])
                        code = extract_html(raw_resp)
                        with open(code_path, "w", encoding="utf-8") as f:
                            f.write(code)
                    except Exception as e:
                        print(f"FAILED to query model: {e}")
                        continue
            
            # Save baseline code too
            if model_type == "baseline":
                code_path = os.path.join(m_code_dir, f"{task_name}.html")
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(code)
            
            # Run deterministic evaluation
            try:
                report = t["evaluator"](code)
                demo = report.demo_score
                reality = report.reality_score
                gap = report.reality_gap
                
                model_demo_scores.append(demo)
                model_reality_scores.append(reality)
                model_gaps.append(gap)
                
                full_results["models"][model_id][task_name] = report.to_dict()
                print(f"Demo: {demo*100:.1f}%, Reality: {reality*100:.1f}%, Gap: {gap*100:.1f}%")
            except Exception as e:
                print(f"EVALUATION ERROR: {e}")
                import traceback
                traceback.print_exc()
        
        avg_demo = sum(model_demo_scores) / len(model_demo_scores) if model_demo_scores else 0.0
        avg_reality = sum(model_reality_scores) / len(model_reality_scores) if model_reality_scores else 0.0
        avg_gap = avg_demo - avg_reality
        
        full_results["summary"].append({
            "model": model_id,
            "avg_demo_score": round(avg_demo, 4),
            "avg_reality_score": round(avg_reality, 4),
            "avg_reality_gap": round(avg_gap, 4),
        })
        print(f"  ==> OVERALL: Demo={avg_demo*100:.1f}%, Reality={avg_reality*100:.1f}%, Reality Gap={avg_gap*100:.1f}%")
    
    # Save results JSON
    results_path = os.path.join(results_dir, "pilot_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)
    print(f"\n[OK] Results successfully written to {results_path}")
    
    # Print Markdown Summary Table
    print("\n" + "=" * 80)
    print(" REALITYBENCH PILOT RESULTS MATRIX")
    print("=" * 80)
    print(f"| {'Model':<22} | {'Demo Score':<12} | {'Reality Score':<14} | {'Reality Gap':<12} |")
    print(f"|{'-'*24}|{'-'*14}|{'-'*16}|{'-'*14}|")
    for s in full_results["summary"]:
        print(f"| {s['model']:<22} | {s['avg_demo_score']*100:>10.1f}% | {s['avg_reality_score']*100:>12.1f}% | {s['avg_reality_gap']*100:>10.1f}% |")
    print("=" * 80)


if __name__ == "__main__":
    run_pilot()
