import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine, SessionLocal
from app.seed import seed_database
from app.models import Transaction, PaymentIntent, PaymentPolicy

client = TestClient(app)

def setup_function():
    # Fresh seed before tests
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db, force=True)
    db.close()

# ----------------- T1: Intent Parse -> Confirm -> Simulate 2500 & 4200 -----------------
def test_t1_api_intent_flow():
    # 1. Parse
    p_resp = client.post("/api/intents/parse", json={"text": "Pay my electricity bill automatically if it is below ₹3000."})
    assert p_resp.status_code == 200
    draft = p_resp.json()["draft"]
    assert draft["category"] == "Utilities"
    assert draft["max_amount"] == 3000
    assert draft["action"] == "AUTO_PAY"

    # 2. Confirm without confirmed: true -> 422
    fail_create = client.post("/api/intents", json={**draft, "confirmed": False})
    assert fail_create.status_code == 422

    # Confirm with confirmed: true -> 201
    ok_create = client.post("/api/intents", json={**draft, "confirmed": True})
    assert ok_create.status_code == 201
    intent_id = ok_create.json()["id"]
    assert intent_id.startswith("PI-")

    # 3. Simulate 2500 -> ALLOW
    sim1 = client.post("/api/payments/simulate", json={
        "recipient": "Bescom",
        "amount": 2500,
        "category": "Utilities",
        "is_known_recipient": True
    })
    assert sim1.status_code == 200
    res1 = sim1.json()
    assert res1["decision"] == "ALLOW"
    assert res1["transaction"]["status"] == "EXECUTED_SIMULATED"

    # 4. Simulate 4200 -> VERIFY (intent FAIL)
    sim2 = client.post("/api/payments/simulate", json={
        "recipient": "Bescom",
        "amount": 4200,
        "category": "Utilities",
        "is_known_recipient": True
    })
    assert sim2.status_code == 200
    res2 = sim2.json()
    assert res2["decision"] == "VERIFY"
    assert res2["transaction"]["status"] == "PENDING_VERIFICATION"

# ----------------- T2: Send mother ₹10000 every month -> confirm -----------------
def test_t2_api_mother_intent():
    p_resp = client.post("/api/intents/parse", json={"text": "Send my mother ₹10000 every month."})
    assert p_resp.status_code == 200
    draft = p_resp.json()["draft"]
    assert draft["recipient"] == "Mother"
    assert draft["amount"] == 10000
    assert draft["frequency"] == "MONTHLY"

    c_resp = client.post("/api/intents", json={**draft, "confirmed": True})
    assert c_resp.status_code == 201
    saved_id = c_resp.json()["id"]

    # Verify persisted in GET /api/intents
    list_resp = client.get("/api/intents")
    assert any(i["id"] == saved_id for i in list_resp.json())

# ----------------- T3: ₹35,000 New Recipient -> VERIFY -----------------
def test_t3_api_new_recipient_large_amount():
    sim = client.post("/api/payments/simulate", json={
        "recipient": "ABC Electronics",
        "amount": 35000,
        "category": "Shopping"
    })
    assert sim.status_code == 200
    res = sim.json()
    assert res["decision"] == "VERIFY"
    assert res["transaction"]["status"] == "PENDING_VERIFICATION"
    reasons_text = " ".join(res["reasons"])
    assert "new recipient" in reasons_text.lower()
    assert "25,000" in reasons_text or "25000" in reasons_text

# ----------------- T4: Shopping rolling 7-day period limit -----------------
def test_t4_api_shopping_period_limit():
    # Simulate first shopping payment ₹7000
    s1 = client.post("/api/payments/simulate", json={
        "recipient": "Amazon",
        "amount": 7000,
        "category": "Shopping"
    })
    assert s1.status_code == 200

    # Simulate second shopping payment ₹4000 (total ₹11,000 > ₹10,000 limit PD-002)
    s2 = client.post("/api/payments/simulate", json={
        "recipient": "Amazon",
        "amount": 4000,
        "category": "Shopping"
    })
    assert s2.status_code == 200
    res = s2.json()
    assert res["decision"] == "VERIFY"
    assert any("PD-002" in r for r in res["reasons"])

# ----------------- T5: Policy Conflict Detection -----------------
def test_t5_api_policy_conflict():
    # Rent ₹15,000 AUTO_PAY is active in seed
    # Parse policy "Payments above ₹10000 require verification"
    p_resp = client.post("/api/policies/parse", json={"text": "Payments above ₹10000 require verification"})
    assert p_resp.status_code == 200
    conflicts = p_resp.json()["conflicts"]
    assert len(conflicts) > 0
    assert any("Rent" in c["intent"]["purpose"] for c in conflicts)

    # Check GET /api/conflicts
    c_list = client.get("/api/conflicts").json()
    # In initial seed, max tx is 25000 so 15000 does not conflict with initial seed,
    # but when checking against the 10000 policy, it does.

# ----------------- T7, T8, T9: Validation Errors -----------------
def test_t7_t8_t9_api_validation():
    # T7: negative amount -> 422 error envelope
    r1 = client.post("/api/payments/simulate", json={"recipient": "Amazon", "amount": -100, "category": "Shopping"})
    assert r1.status_code == 422
    assert "error" in r1.json()
    assert r1.json()["error"]["code"] == "VALIDATION_ERROR"

    # T7: string amount -> 422
    r2 = client.post("/api/payments/simulate", json={"recipient": "Amazon", "amount": "abc", "category": "Shopping"})
    assert r2.status_code == 422

    # T8: empty recipient -> 422
    r3 = client.post("/api/payments/simulate", json={"recipient": "   ", "amount": 500, "category": "Food"})
    assert r3.status_code == 422
    assert "error" in r3.json()

    # T9: ₹999,999,999 -> HOLD (under 1e9 valid Pydantic, but over 10L simulation ceiling)
    r4 = client.post("/api/payments/simulate", json={"recipient": "Real Estate Agent", "amount": 999_999_999, "category": "Rent"})
    assert r4.status_code == 200
    res4 = r4.json()
    assert res4["decision"] == "HOLD"
    assert res4["transaction"]["status"] == "HELD"

    # > 1e9 -> 422
    r5 = client.post("/api/payments/simulate", json={"recipient": "Real Estate Agent", "amount": 1_000_000_001, "category": "Rent"})
    assert r5.status_code == 422

# ----------------- T12: Create Policy Changes Decision -----------------
def test_t12_policy_changes_decision():
    # Analyze Food ₹3000 -> currently ALLOW
    a1 = client.post("/api/payments/analyze", json={"recipient": "Big Bazaar", "amount": 3000, "category": "Food"})
    assert a1.status_code == 200
    assert a1.json()["decision"] == "ALLOW"

    # Create policy: Food payments above ₹2000 require verification
    p_create = client.post("/api/policies", json={
        "policy_type": "PERIOD_LIMIT",
        "scope": "CATEGORY",
        "scope_value": "Food",
        "period": "WEEK",
        "limit": 2000,
        "action": "VERIFY",
        "description": "Weekly Food spend limit ₹2,000",
        "confirmed": True
    })
    assert p_create.status_code == 201

    # Analyze again -> now VERIFY!
    a2 = client.post("/api/payments/analyze", json={"recipient": "Big Bazaar", "amount": 3000, "category": "Food"})
    assert a2.status_code == 200
    assert a2.json()["decision"] == "VERIFY"

# ----------------- T13 & T14: Simulate -> History -> Trace with all 9 sections -----------------
def test_t13_t14_simulate_history_trace():
    sim = client.post("/api/payments/simulate", json={
        "recipient": "Uber",
        "amount": 450,
        "category": "Travel",
        "purpose": "Morning Commute"
    })
    assert sim.status_code == 200
    tx_id = sim.json()["transaction"]["id"]

    # T13: Appears in GET /api/payments
    history = client.get("/api/payments").json()
    assert any(t["id"] == tx_id for t in history)

    # T14: GET /api/payments/{id}/trace has all sections
    trace_resp = client.get(f"/api/payments/{tx_id}/trace")
    assert trace_resp.status_code == 200
    trace = trace_resp.json()
    assert "transaction" in trace
    assert "decision" in trace
    assert "reasons" in trace
    assert "rules_evaluated" in trace
    assert "intent_evaluation" in trace
    assert "policy_evaluation" in trace
    assert "behavior_signals" in trace
    assert "cash_flow_impact" in trace
    assert "raw_input" in trace

# ----------------- T15: Idempotency with client_request_id -----------------
def test_t15_idempotent_simulation():
    req_id = "req_test_12345"
    sim1 = client.post("/api/payments/simulate", json={
        "recipient": "Uber",
        "amount": 350,
        "category": "Travel",
        "client_request_id": req_id
    })
    assert sim1.status_code == 200
    tx1_id = sim1.json()["transaction"]["id"]

    # Send exact same client_request_id again
    sim2 = client.post("/api/payments/simulate", json={
        "recipient": "Uber",
        "amount": 350,
        "category": "Travel",
        "client_request_id": req_id
    })
    assert sim2.status_code == 200
    tx2_id = sim2.json()["transaction"]["id"]

    # Must return the SAME transaction
    assert tx1_id == tx2_id

# ----------------- T16: Duplicate Policy -> 409 -----------------
def test_t16_duplicate_policy_409():
    # PD-001 in seed: NEW_RECIPIENT_LIMIT threshold 5000
    dup_resp = client.post("/api/policies", json={
        "policy_type": "NEW_RECIPIENT_LIMIT",
        "threshold": 5000,
        "action": "VERIFY",
        "description": "Any new recipient above ₹5000 requires confirmation.",
        "confirmed": True
    })
    assert dup_resp.status_code == 409
    data = dup_resp.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"
    assert "PD-001" in data["error"]["message"]

# ----------------- T17: Mock Server/DB failure -> clean JSON error envelope -----------------
def test_t10_t11_persistence():
    # Insert new intent
    i_resp = client.post("/api/intents", json={
        "purpose": "Gym Membership",
        "category": "Health",
        "amount": 2500,
        "frequency": "MONTHLY",
        "action": "AUTO_PAY",
        "confirmed": True
    })
    assert i_resp.status_code == 201
    intent_id = i_resp.json()["id"]

    # Simulate payment
    s_resp = client.post("/api/payments/simulate", json={
        "recipient": "Gold Gym",
        "amount": 2500,
        "category": "Health"
    })
    assert s_resp.status_code == 200
    tx_id = s_resp.json()["transaction"]["id"]

    # Create completely new TestClient instance (simulating restart / new session)
    new_client = TestClient(app)
    persisted_intent = new_client.get(f"/api/intents/{intent_id}")
    assert persisted_intent.status_code == 200
    assert persisted_intent.json()["purpose"] == "Gym Membership"

    persisted_trace = new_client.get(f"/api/payments/{tx_id}/trace")
    assert persisted_trace.status_code == 200
    assert persisted_trace.json()["transaction"]["recipient"] == "Gold Gym"

# ----------------- T17: Mock Server/DB failure -> clean JSON error envelope -----------------
def test_t17_mock_server_failure_envelope():
    error_client = TestClient(app, raise_server_exceptions=False)
    with patch("sqlalchemy.orm.Session.query", side_effect=Exception("Simulated DB connection crash")):
        resp = error_client.get("/api/dashboard")
        assert resp.status_code == 500
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "Traceback" not in data["error"]["message"]
