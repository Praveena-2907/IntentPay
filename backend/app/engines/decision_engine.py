"""
Decision Engine (Pure Python, No DB, No Network)
Deterministic priority hierarchy for payment evaluation.
"""

from typing import Dict, Any, List
from app.engines.explain import generate_explanation

SIMULATION_CEILING = 1_000_000 # ₹10,00,000 simulation ceiling

def evaluate_decision(
    payment: Dict[str, Any],
    intent_eval: Dict[str, Any],
    policy_eval: Dict[str, Any],
    behavior_eval: Dict[str, Any]
) -> Dict[str, Any]:
    amount = payment.get("amount", 0)
    recipient = str(payment.get("recipient", "")).strip()

    reasons: List[str] = []
    rules_evaluated: List[Dict[str, Any]] = []

    # 1. Base validation and Simulation Ceiling Check
    is_ceiling_breached = amount > SIMULATION_CEILING
    is_invalid_data = (not recipient) or (amount <= 0)

    rules_evaluated.append({
        "id": "RULE-SIM-CEILING",
        "label": "Simulation Ceiling Check (₹10,00,000)",
        "result": "FAIL" if is_ceiling_breached else "PASS",
        "detail": f"Amount ₹{amount:,} exceeds simulation ceiling ₹{SIMULATION_CEILING:,}" if is_ceiling_breached else f"Within simulation ceiling (₹{amount:,} <= ₹{SIMULATION_CEILING:,})"
    })

    # Collect evaluated rules from sub-engines
    rules_evaluated.extend(intent_eval.get("rules_evaluated", []))
    rules_evaluated.extend(policy_eval.get("evaluated_rules", []))
    rules_evaluated.extend(behavior_eval.get("rules_evaluated", []))

    # Determine pipeline statuses
    intent_res = intent_eval.get("result", "NO_MATCH")
    intent_requires_confirm = intent_eval.get("requires_confirmation", False)

    hold_policies = policy_eval.get("hold_policies", [])
    verify_policies = policy_eval.get("verify_policies", [])
    violated_policies = policy_eval.get("violated_policies", [])

    signals = behavior_eval.get("signals", [])
    high_signals = [s for s in signals if s.get("level") == "HIGH"]
    med_signals = [s for s in signals if s.get("level") == "MEDIUM"]

    # Calculate status per stage for PipelineStrip
    # Intent stage:
    if intent_res == "PASS":
        intent_stage_status = "PASS"
    elif intent_res == "BLOCKED":
        intent_stage_status = "FAIL"
    elif intent_res == "FAIL":
        intent_stage_status = "FAIL"
    else:
        intent_stage_status = "NO_MATCH"

    # PayDNA stage:
    if hold_policies or verify_policies:
        paydna_stage_status = "FAIL"
    else:
        paydna_stage_status = "PASS"

    # Behavior stage:
    if high_signals:
        behavior_stage_status = "FAIL"
    elif med_signals:
        behavior_stage_status = "WARN"
    else:
        behavior_stage_status = "PASS"

    # Priority 1: Invalid data or amount > ₹10,00,000 (simulation ceiling) -> HOLD
    if is_invalid_data:
        decision = "HOLD"
        reasons.append("Invalid payment data or empty recipient specified")
    elif is_ceiling_breached:
        decision = "HOLD"
        reasons.append(f"Amount ₹{amount:,} exceeds maximum simulation ceiling of ₹{SIMULATION_CEILING:,}")

    # Priority 2: Any violated policy with action=HOLD -> HOLD
    elif hold_policies:
        decision = "HOLD"
        for p in hold_policies:
            reasons.append(f"PayDNA Security Policy {p.get('policy_id')} HOLD: {p.get('detail')}")

    # Priority 3: Intent result BLOCKED -> HOLD
    elif intent_res == "BLOCKED":
        decision = "HOLD"
        reasons.extend(intent_eval.get("reasons", ["Payment explicitly blocked by intent rule"]))

    # Priority 4: Any violated policy with action=VERIFY -> VERIFY
    elif verify_policies:
        decision = "VERIFY"
        for p in verify_policies:
            reasons.append(f"PayDNA Policy {p.get('policy_id')}: {p.get('detail')}")

    # Priority 5: Intent result FAIL, or requires_confirmation -> VERIFY
    elif intent_res == "FAIL" or intent_requires_confirm:
        decision = "VERIFY"
        if intent_res == "FAIL":
            reasons.extend(intent_eval.get("reasons", ["Intent evaluation failed"]))
        if intent_requires_confirm:
            reasons.append("Intent rule requires user confirmation (ASK_FIRST)")

    # Priority 6: Any HIGH behavioral signal, or >= 2 MEDIUM signals -> VERIFY
    elif high_signals or len(med_signals) >= 2:
        decision = "VERIFY"
        if high_signals:
            for s in high_signals:
                reasons.append(f"Behavioral Anomaly Signal (HIGH): {s.get('rule')}")
        if len(med_signals) >= 2:
            reasons.append(f"Multiple behavioral anomalies detected ({len(med_signals)} medium signals)")
            for s in med_signals:
                reasons.append(f"Behavioral Anomaly Signal (MEDIUM): {s.get('rule')}")

    # Priority 7: Otherwise -> ALLOW
    else:
        decision = "ALLOW"
        if intent_res == "PASS":
            reasons.append(f"Payment matches intent '{intent_eval.get('matched_intent', {}).get('purpose')}'")
        else:
            reasons.append("All PayDNA security policies satisfied with no behavioral anomaly detected")

    pipeline_status = {
        "intent": intent_stage_status,
        "paydna": paydna_stage_status,
        "behavior": behavior_stage_status,
        "decision": decision
    }

    explanation = generate_explanation(decision, reasons, payment, pipeline_status)

    return {
        "decision": decision,
        "reasons": reasons,
        "explanation": explanation,
        "rules_evaluated": rules_evaluated,
        "pipeline_status": pipeline_status
    }
