#!/usr/bin/env python3
"""
IntentPay Smoke Test Script
Hits implemented endpoints on a running server.
Exits 0 on success, non-zero on failure.
"""

import sys
import httpx

def run_smoke_tests(base_url="http://127.0.0.1:8000"):
    print(f"[SMOKE] Running smoke tests against {base_url}...")
    endpoints = [
        {"path": "/api/health", "method": "GET", "expected_status": 200, "check": lambda d: d.get("status") == "ok"},
    ]

    # Additional endpoints are tested if available
    optional_endpoints = [
        {"path": "/api/users/me", "method": "GET", "expected_status": 200},
        {"path": "/api/intents", "method": "GET", "expected_status": 200},
        {"path": "/api/policies", "method": "GET", "expected_status": 200},
        {"path": "/api/payments", "method": "GET", "expected_status": 200},
        {"path": "/api/conflicts", "method": "GET", "expected_status": 200},
        {"path": "/api/suggestions", "method": "GET", "expected_status": 200},
        {"path": "/api/dashboard", "method": "GET", "expected_status": 200},
    ]

    failed = False
    with httpx.Client(timeout=5.0) as client:
        # Check required endpoints
        for ep in endpoints:
            try:
                resp = client.request(ep["method"], f"{base_url}{ep['path']}")
                if resp.status_code != ep["expected_status"]:
                    print(f"  [FAIL] {ep['method']} {ep['path']} returned HTTP {resp.status_code}, expected {ep['expected_status']}")
                    failed = True
                    continue
                if "check" in ep:
                    data = resp.json()
                    if not ep["check"](data):
                        print(f"  [FAIL] {ep['method']} {ep['path']} failed payload check: {data}")
                        failed = True
                        continue
                print(f"  [PASS] {ep['method']} {ep['path']} -> {resp.status_code}")
            except Exception as e:
                print(f"  [FAIL] {ep['method']} {ep['path']} exception: {e}")
                failed = True

        # Check optional endpoints if server returns 200 (or if they are already implemented)
        for ep in optional_endpoints:
            try:
                resp = client.request(ep["method"], f"{base_url}{ep['path']}")
                if resp.status_code == 200:
                    print(f"  [PASS] (Active) {ep['method']} {ep['path']} -> 200")
                elif resp.status_code == 404:
                    print(f"  [INFO] (Not yet mounted) {ep['method']} {ep['path']} -> 404")
                else:
                    print(f"  [WARN] {ep['method']} {ep['path']} returned unexpected {resp.status_code}")
            except Exception:
                pass

    if failed:
        print("[SMOKE] FAILED")
        sys.exit(1)
    print("[SMOKE] PASSED ALL REQUIRED CHECKS")
    sys.exit(0)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    run_smoke_tests(target)
