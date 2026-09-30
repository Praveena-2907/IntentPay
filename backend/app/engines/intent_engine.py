"""
Intent Evaluation Engine (Pure Python, No DB, No Network)
Evaluates a payment request against user-defined Payment Intents.
"""

from typing import Dict, Any, List, Optional

def normalize_string(val: Optional[str]) -> str:
    if not val:
        return ""
    return " ".join(val.strip().split()).lower()

def match_intent(payment: Dict[str, Any], intents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find matching active intent for a payment:
    Category must match (case-insensitive).
    Recipient must either be null in intent OR match normalized recipient.
    Prefers specific recipient match over null recipient match.
    """
    pay_cat = normalize_string(payment.get("category", ""))
    pay_rec = normalize_string(payment.get("recipient", ""))

    matched = []
    for intent in intents:
        if intent.get("status") != "ACTIVE":
            continue
        intent_cat = normalize_string(intent.get("category", ""))
        intent_rec = normalize_string(intent.get("recipient"))

        if intent_cat == pay_cat:
            if not intent_rec: # Category-wide intent
                matched.append((1, intent))
            elif intent_rec == pay_rec: # Specific recipient match
                matched.append((2, intent))

    if not matched:
        return None

    # Sort descending by priority (specific recipient first)
    matched.sort(key=lambda x: x[0], reverse=True)
    return matched[0][1]

def evaluate_condition(condition: Dict[str, Any], payment: Dict[str, Any]) -> tuple[bool, str]:
    field = condition.get("field")
    op = condition.get("operator")
    target_val = condition.get("value")

    # Map field from payment
    if field == "amount":
        val = payment.get("amount")
    elif field == "bill_amount":
        val = payment.get("bill_amount") if payment.get("bill_amount") is not None else payment.get("amount")
    elif field == "bill_increase_pct":
        val = payment.get("bill_increase_pct")
    else:
        return False, f"Unknown condition field '{field}'"

    if val is None:
        return False, f"Missing field '{field}' required for condition evaluation"

    try:
        val = float(val)
        target_val = float(target_val)
    except (ValueError, TypeError):
        return False, f"Invalid numeric comparison for {field}"

    passed = False
    if op == "<=":
        passed = val <= target_val
    elif op == "<":
        passed = val < target_val
    elif op == ">=":
        passed = val >= target_val
    elif op == ">":
        passed = val > target_val
    elif op == "==":
        passed = abs(val - target_val) < 1e-6
    else:
        return False, f"Unsupported operator '{op}'"

    if not passed:
        return False, f"Condition failed: {field} ({val}) {op} {target_val}"
    return True, f"Condition passed: {field} ({val}) {op} {target_val}"

def evaluate_intent(payment: Dict[str, Any], intents: List[Dict[str, Any]]) -> Dict[str, Any]:
    matched = match_intent(payment, intents)

    if not matched:
        return {
            "result": "NO_MATCH",
            "matched_intent": None,
            "requires_confirmation": False,
            "reasons": ["No active payment intent matched this category and recipient"],
            "rules_evaluated": [
                {
                    "id": "INTENT-MATCH",
                    "label": "Intent Matching",
                    "result": "WARN",
                    "detail": "No matching active intent configured"
                }
            ]
        }

    rules_eval = []
    reasons = []
    passed = True
    action = matched.get("action", "AUTO_PAY")

    if action == "BLOCK":
        return {
            "result": "BLOCKED",
            "matched_intent": matched,
            "requires_confirmation": False,
            "reasons": [f"Payment explicitly blocked by intent '{matched.get('purpose', 'Active Intent')}' (ID: {matched.get('id')})"],
            "rules_evaluated": [
                {
                    "id": f"INTENT-{matched.get('id', 'BLOCK')}",
                    "label": f"Intent Block: {matched.get('purpose')}",
                    "result": "FAIL",
                    "detail": "Action configured as BLOCK"
                }
            ]
        }

    amount = payment.get("amount", 0)

    # 1. Fixed amount check
    fixed_amt = matched.get("amount")
    if fixed_amt is not None:
        if amount == fixed_amt:
            rules_eval.append({
                "id": f"INTENT-AMT-{matched.get('id')}",
                "label": "Exact Amount Match",
                "result": "PASS",
                "detail": f"Amount ₹{amount} equals configured intent amount ₹{fixed_amt}"
            })
        else:
            passed = False
            reason = f"Payment amount ₹{amount} does not match required fixed amount ₹{fixed_amt}"
            reasons.append(reason)
            rules_eval.append({
                "id": f"INTENT-AMT-{matched.get('id')}",
                "label": "Exact Amount Match",
                "result": "FAIL",
                "detail": reason
            })

    # 2. Max amount check
    max_amt = matched.get("max_amount")
    if max_amt is not None:
        if amount <= max_amt:
            rules_eval.append({
                "id": f"INTENT-MAX-{matched.get('id')}",
                "label": "Maximum Amount Ceiling",
                "result": "PASS",
                "detail": f"Amount ₹{amount} is within intent ceiling of ₹{max_amt}"
            })
        else:
            passed = False
            reason = f"Payment amount ₹{amount} exceeds intent maximum limit ₹{max_amt}"
            reasons.append(reason)
            rules_eval.append({
                "id": f"INTENT-MAX-{matched.get('id')}",
                "label": "Maximum Amount Ceiling",
                "result": "FAIL",
                "detail": reason
            })

    # 3. Dynamic Conditions
    conditions = matched.get("conditions", []) or []
    for idx, cond in enumerate(conditions):
        cond_ok, cond_msg = evaluate_condition(cond, payment)
        if cond_ok:
            rules_eval.append({
                "id": f"INTENT-COND-{matched.get('id')}-{idx+1}",
                "label": f"Condition #{idx+1}",
                "result": "PASS",
                "detail": cond_msg
            })
        else:
            passed = False
            reasons.append(cond_msg)
            rules_eval.append({
                "id": f"INTENT-COND-{matched.get('id')}-{idx+1}",
                "label": f"Condition #{idx+1}",
                "result": "FAIL",
                "detail": cond_msg
            })

    requires_confirmation = (action == "ASK_FIRST")
    final_result = "PASS" if passed else "FAIL"

    return {
        "result": final_result,
        "matched_intent": matched,
        "requires_confirmation": requires_confirmation,
        "reasons": reasons if not passed else [f"Payment matches intent '{matched.get('purpose')}' rules"],
        "rules_evaluated": rules_eval
    }
