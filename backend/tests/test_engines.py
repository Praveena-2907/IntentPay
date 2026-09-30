import pytest
from datetime import datetime, timezone, timedelta

from app.engines.intent_engine import evaluate_intent, match_intent
from app.engines.policy_engine import evaluate_policies
from app.engines.behavior_engine import evaluate_behavior_signals
from app.engines.decision_engine import evaluate_decision, SIMULATION_CEILING
from app.engines.explain import generate_explanation
from app.engines.conflict import find_conflicts
from app.engines.impact import calculate_payment_impact, calculate_what_if_scenario
from app.engines.recurring import detect_recurring_suggestions

# Sample known recipients
KNOWN_RECIPIENTS = ["Landlord", "TNEB Electricity", "Water Board", "Netflix", "ACT Fibernet", "Mother", "Big Bazaar", "Uber", "Amazon", "Airtel"]

# Sample Active Intents
SAMPLE_INTENTS = [
    {
        "id": "PI-001",
        "purpose": "Monthly Apartment Rent",
        "recipient": "Landlord",
        "category": "Rent",
        "amount": 15000,
        "max_amount": None,
        "frequency": "MONTHLY",
        "action": "AUTO_PAY",
        "status": "ACTIVE"
    },
    {
        "id": "PI-002",
        "purpose": "Electricity Utility Bill",
        "recipient": "TNEB Electricity",
        "category": "Utilities",
        "amount": None,
        "max_amount": 3000,
        "frequency": "MONTHLY",
        "action": "AUTO_PAY",
        "conditions": [{"field": "amount", "operator": "<=", "value": 3000}],
        "status": "ACTIVE"
    }
]

# Sample Policies
SAMPLE_POLICIES = [
    {
        "id": "PD-001",
        "policy_type": "NEW_RECIPIENT_LIMIT",
        "threshold": 5000,
        "action": "VERIFY",
        "status": "ACTIVE",
        "description": "New recipient limit ₹5,000"
    },
    {
        "id": "PD-002",
        "policy_type": "PERIOD_LIMIT",
        "scope": "CATEGORY",
        "scope_value": "Shopping",
        "period": "WEEK",
        "limit": 10000,
        "action": "VERIFY",
        "status": "ACTIVE",
        "description": "Weekly Shopping limit ₹10,000"
    },
    {
        "id": "PD-003",
        "policy_type": "MAX_TRANSACTION_AMOUNT",
        "threshold": 25000,
        "action": "VERIFY",
        "status": "ACTIVE",
        "description": "Max transaction limit ₹25,000"
    }
]

# Baseline historical transactions (adequate history with Utilities baseline ~ 2200 and weekly avg ~ 1400)
NOW = datetime.now(timezone.utc)
SAMPLE_HISTORY = [
    {"status": "EXECUTED_SIMULATED", "amount": 2150, "category": "Utilities", "recipient": "TNEB Electricity", "timestamp": (NOW - timedelta(days=62)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 2240, "category": "Utilities", "recipient": "TNEB Electricity", "timestamp": (NOW - timedelta(days=32)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 1500, "category": "Utilities", "recipient": "Airtel", "timestamp": (NOW - timedelta(days=45)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 1500, "category": "Utilities", "recipient": "Airtel", "timestamp": (NOW - timedelta(days=15)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 600, "category": "Utilities", "recipient": "Water Board", "timestamp": (NOW - timedelta(days=20)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 15000, "category": "Rent", "recipient": "Landlord", "timestamp": (NOW - timedelta(days=65)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 15000, "category": "Rent", "recipient": "Landlord", "timestamp": (NOW - timedelta(days=35)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 1800, "category": "Food", "recipient": "Big Bazaar", "timestamp": (NOW - timedelta(days=10)).isoformat()},
    {"status": "EXECUTED_SIMULATED", "amount": 2100, "category": "Food", "recipient": "Big Bazaar", "timestamp": (NOW - timedelta(days=20)).isoformat()}
]

# ----------------- Test T1: Electricity bill ₹2500 (ALLOW) vs ₹4200 (VERIFY) -----------------
def test_t1_electricity_allow_and_verify():
    # 2500 electricity (known recipient, under max 3000)
    payment_allow = {
        "recipient": "TNEB Electricity",
        "amount": 2500,
        "category": "Utilities",
        "timestamp": NOW.isoformat()
    }
    intent_res = evaluate_intent(payment_allow, SAMPLE_INTENTS)
    assert intent_res["result"] == "PASS"

    policy_res = evaluate_policies(payment_allow, SAMPLE_POLICIES, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    assert len(policy_res["violated_policies"]) == 0

    behavior_res = evaluate_behavior_signals(payment_allow, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    assert len(behavior_res["signals"]) == 0 # 2500 is not 2.5x of 2193

    decision = evaluate_decision(payment_allow, intent_res, policy_res, behavior_res)
    assert decision["decision"] == "ALLOW"

    # 4200 electricity (exceeds max 3000 intent ceiling)
    payment_verify = {
        "recipient": "TNEB Electricity",
        "amount": 4200,
        "category": "Utilities",
        "timestamp": NOW.isoformat()
    }
    intent_verify = evaluate_intent(payment_verify, SAMPLE_INTENTS)
    assert intent_verify["result"] == "FAIL"

    policy_v = evaluate_policies(payment_verify, SAMPLE_POLICIES, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    behavior_v = evaluate_behavior_signals(payment_verify, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    dec_v = evaluate_decision(payment_verify, intent_verify, policy_v, behavior_v)
    assert dec_v["decision"] == "VERIFY"
    assert any("exceeds" in r.lower() or "limit" in r.lower() for r in dec_v["reasons"])

# ----------------- Test T3: ₹35,000 New Recipient -----------------
def test_t3_new_recipient_large_amount():
    payment = {
        "recipient": "ABC Electronics",
        "amount": 35000,
        "category": "Shopping",
        "timestamp": NOW.isoformat()
    }
    intent_res = evaluate_intent(payment, SAMPLE_INTENTS) # NO_MATCH
    assert intent_res["result"] == "NO_MATCH"

    policy_res = evaluate_policies(payment, SAMPLE_POLICIES, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    # Violates PD-001 (new recipient > 5000) and PD-003 (amount > 25000)
    assert len(policy_res["violated_policies"]) >= 2
    violated_ids = [p["policy_id"] for p in policy_res["violated_policies"]]
    assert "PD-001" in violated_ids
    assert "PD-003" in violated_ids

    behavior_res = evaluate_behavior_signals(payment, SAMPLE_HISTORY, KNOWN_RECIPIENTS)
    assert any(s["signal"] == "NEW_RECIPIENT" for s in behavior_res["signals"])
    assert any(s["signal"] == "HIGH_AMOUNT" for s in behavior_res["signals"])

    decision = evaluate_decision(payment, intent_res, policy_res, behavior_res)
    assert decision["decision"] == "VERIFY"

# ----------------- Test T4: Shopping rolling 7-day period limit -----------------
def test_t4_shopping_period_limit():
    history_with_shopping = list(SAMPLE_HISTORY)
    # Add prior ₹7000 shopping 2 days ago
    history_with_shopping.append({
        "status": "EXECUTED_SIMULATED",
        "amount": 7000,
        "category": "Shopping",
        "recipient": "Amazon",
        "timestamp": (NOW - timedelta(days=2)).isoformat()
    })

    payment = {
        "recipient": "Amazon",
        "amount": 4000,
        "category": "Shopping",
        "timestamp": NOW.isoformat()
    }
    intent_res = evaluate_intent(payment, SAMPLE_INTENTS)
    policy_res = evaluate_policies(payment, SAMPLE_POLICIES, history_with_shopping, KNOWN_RECIPIENTS)

    # Prior 7000 + 4000 = 11000 > limit 10000 -> violates PD-002
    assert any(p["policy_id"] == "PD-002" for p in policy_res["violated_policies"])

    behavior_res = evaluate_behavior_signals(payment, history_with_shopping, KNOWN_RECIPIENTS)
    decision = evaluate_decision(payment, intent_res, policy_res, behavior_res)
    assert decision["decision"] == "VERIFY"

# ----------------- Test T5: Conflict Detection -----------------
def test_t5_conflict_detection():
    # Active intent: Rent ₹15,000 AUTO_PAY
    # New policy: Max transaction amount ₹10,000 (VERIFY)
    conflicting_policy = {
        "id": "PD-NEW",
        "policy_type": "MAX_TRANSACTION_AMOUNT",
        "threshold": 10000,
        "action": "VERIFY",
        "status": "ACTIVE",
        "description": "Max transaction limit ₹10,000"
    }

    conflicts = find_conflicts(SAMPLE_INTENTS, [conflicting_policy], KNOWN_RECIPIENTS)
    assert len(conflicts) > 0
    c = conflicts[0]
    assert c["intent"]["id"] == "PI-001"
    assert c["policy"]["id"] == "PD-NEW"
    assert "KEEP_POLICY" in c["resolutions"]
    assert "UPDATE_INTENT" in c["resolutions"]

# ----------------- Test T7, T8, T9: Invalid Data & Simulation Ceiling -----------------
def test_t7_t8_t9_invalid_and_ceiling():
    # T8: Empty recipient -> HOLD
    bad_payment_empty = {"recipient": "", "amount": 1000, "category": "Food"}
    dec = evaluate_decision(bad_payment_empty, {"result": "NO_MATCH"}, {"violated_policies": []}, {"signals": []})
    assert dec["decision"] == "HOLD"

    # T7: Zero / negative amount -> HOLD
    bad_payment_zero = {"recipient": "Amazon", "amount": 0, "category": "Shopping"}
    dec2 = evaluate_decision(bad_payment_zero, {"result": "NO_MATCH"}, {"violated_policies": []}, {"signals": []})
    assert dec2["decision"] == "HOLD"

    # T9: Exceeds simulation ceiling (₹10,00,000) -> HOLD
    ceiling_payment = {"recipient": "Luxury Goods", "amount": 999_999_999, "category": "Shopping"}
    dec3 = evaluate_decision(ceiling_payment, {"result": "NO_MATCH"}, {"violated_policies": []}, {"signals": []})
    assert dec3["decision"] == "HOLD"
    assert any("ceiling" in r.lower() for r in dec3["reasons"])

# ----------------- Impact and What-If Tests -----------------
def test_impact_and_what_if():
    # User balance 36000, upcoming 15500 -> available 20500
    impact = calculate_payment_impact(
        amount=5000,
        current_balance=36000,
        upcoming_expenses=15500,
        monthly_income=50000
    )
    assert impact["available_balance"] == 20500
    assert impact["projected_balance"] == 15500
    assert impact["monthly_impact_pct"] == 10.0 # 5000/50000 = 10%
    assert impact["impact_level"] == "LOW"

    # Exceeding available
    impact_high = calculate_payment_impact(25000, 36000, 15500, 50000)
    assert impact_high["impact_level"] == "EXCEEDS_AVAILABLE"

    # What-If
    scenario = calculate_what_if_scenario(
        payment_amount=5000,
        current_balance=36000,
        monthly_income=50000,
        upcoming_expenses=15500,
        loan_amount=4000
    )
    assert scenario["after"]["loan_emi"] == 4000
    assert scenario["after"]["net_monthly_cash_flow"] == 50000 - (15500 + 4000)

# ----------------- Recurring Detection Test -----------------
def test_recurring_detection():
    # 3 distinct months of ₹999 on day 5 to "Broadband ISP"
    rec_history = [
        {"status": "EXECUTED_SIMULATED", "amount": 999, "category": "Internet", "recipient": "Broadband ISP", "timestamp": "2026-07-05T10:00:00Z"},
        {"status": "EXECUTED_SIMULATED", "amount": 999, "category": "Internet", "recipient": "Broadband ISP", "timestamp": "2026-08-05T11:00:00Z"},
        {"status": "EXECUTED_SIMULATED", "amount": 1000, "category": "Internet", "recipient": "Broadband ISP", "timestamp": "2026-09-05T09:30:00Z"},
    ]
    suggestions = detect_recurring_suggestions(rec_history, SAMPLE_INTENTS)
    assert len(suggestions) == 1
    assert suggestions[0]["recipient"] == "Broadband ISP"
    assert suggestions[0]["suggested_amount"] in (999, 1000)
