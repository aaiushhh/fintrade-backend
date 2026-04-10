"""Phase 3 endpoint integration test script."""

import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"email": "admin@platform.com", "password": "admin123!"}

def login(creds):
    r = requests.post(f"{BASE_URL}/auth/login", json=creds)
    if r.status_code == 200:
        return r.json().get("access_token")
    print(f"Login failed for {creds['email']}: {r.status_code} {r.text}")
    return None

def test_endpoint(method, path, headers, json_data=None, label=None):
    url = f"{BASE_URL}{path}"
    label = label or f"{method.upper()} {path}"
    try:
        if method == "get":
            r = requests.get(url, headers=headers)
        else:
            r = requests.post(url, headers=headers, json=json_data)
        status = r.status_code
        try:
            body = r.json()
        except:
            body = r.text
        print(f"  {label} -> {status}")
        if status >= 400:
            print(f"    Response: {body}")
        return status, body
    except Exception as e:
        print(f"  {label} -> ERROR: {e}")
        return 0, None

def test():
    try:
        requests.get(f"{BASE_URL}/docs")
    except requests.exceptions.ConnectionError:
        print("Backend is not accessible at", BASE_URL)
        return

    token = login(ADMIN_CREDS)
    if not token:
        print("FATAL: Could not authenticate. Aborting.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    results = {}

    # ── Phase 1/2 Smoke Tests ────────────────────────────────────────
    print("\n=== Phase 1/2 Regression Checks ===")
    test_endpoint("get", "/health", {}, label="Health Check")
    test_endpoint("get", "/ai/faqs", headers, label="AI FAQs")
    test_endpoint("get", "/learning/dashboard", headers, label="Learning Dashboard")
    test_endpoint("get", "/exams/monthly", headers, label="Monthly Exams")

    # ── 1. Certificates ──────────────────────────────────────────────
    print("\n=== 1. Certificates ===")
    s, _ = test_endpoint("post", "/certificates/generate", headers,
                         {"course_id": 1}, "Generate Cert (expect 400/404 — no completion)")

    # ── 2. Skill Analysis ────────────────────────────────────────────
    print("\n=== 2. Skill-Based Result Analysis ===")
    test_endpoint("get", "/exams/results/analysis", headers, label="Skill Analysis")

    # ── 3. Trading Simulator ─────────────────────────────────────────
    print("\n=== 3. Trading Simulator ===")
    test_endpoint("get", "/simulator/profiles", headers, label="List Profiles")
    s, body = test_endpoint("post", "/simulator/start", headers,
                            {}, "Start Simulator (expect 403 — no cert)")
    test_endpoint("post", "/simulator/trade", headers,
                  {"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 150.0, "stop_loss": 145.0},
                  "Open Trade (expect 404 — no account)")
    test_endpoint("get", "/simulator/positions", headers, label="List Positions")
    test_endpoint("get", "/simulator/trades", headers, label="List Trades")
    test_endpoint("get", "/simulator/performance", headers, label="Performance Analytics")

    # ── 4. Placement ─────────────────────────────────────────────────
    print("\n=== 4. Placement Evaluation ===")
    test_endpoint("get", "/placement/status", headers, label="Placement Status")
    test_endpoint("post", "/placement/evaluate", headers, label="Evaluate Placement")

    # ── 5. Feedback ──────────────────────────────────────────────────
    print("\n=== 5. Feedback System ===")
    test_endpoint("post", "/feedback", headers,
                  {"rating": 5, "comments": "Excellent platform!"}, "Submit Feedback")
    test_endpoint("get", "/feedback", headers, label="List All Feedback (admin)")
    test_endpoint("get", "/feedback/my", headers, label="My Feedback")

    # ── 6. Admin Advanced Dashboard ──────────────────────────────────
    print("\n=== 6. Admin Advanced Dashboard ===")
    test_endpoint("get", "/admin/reports", headers, label="Admin Reports")
    test_endpoint("get", "/admin/certificates", headers, label="Admin Certificates")
    test_endpoint("get", "/admin/simulator", headers, label="Admin Simulator")

    print("\n=== All Phase 3 tests complete ===")

if __name__ == "__main__":
    test()
