"""
PayDNA Policy Engine (Pure Python, No DB, No Network)
Evaluates transactions against user PayDNA policies.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

def normalize_text(val: Optional[str]) -> str:
    if not val:
        return ""
    return " ".join(val.strip().split()).lower()

def parse_iso_datetime(dt_val: Any) -> datetime:
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val
    if isinstance(dt_val, str):
        try:
            # Handle ISO string with trailing Z or timezone offset
            cleaned = dt_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.now(timezone.utc)

def evaluate_policies(
    payment: Dict[str, Any],
    policies: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
    known_recipients: List[str]
) -> Dict[str, Any]:
    """
    Evaluates payment against all ACTIVE PayDNA policies.
    """
    amount = payment.get("amount", 0)
    category = normalize_text(payment.get("category", ""))
    recipient = normalize_text(payment.get("recipient", ""))
    payment_time = parse_iso_datetime(payment.get("timestamp"))

    # Determine if recipient is known server-side
    known_normalized = {normalize_text(r) for r in known_recipients if r}
    is_new = recipient not in known_normalized

    evaluated_rules = []
    violated = []
    hold_policies = []
    verify_policies = []
    reasons = []

    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]

    for policy in active_policies:
        pid = policy.get("id", "PD-UNKNOWN")
        ptype = policy.get("policy_type")
        action = policy.get("action", "VERIFY").upper()
        desc = policy.get("description", ptype)

        is_violated = False
        detail = ""

        if ptype == "MAX_TRANSACTION_AMOUNT":
            threshold = policy.get("threshold", 0)
            if amount > threshold:
                is_violated = True
                detail = f"Amount ₹{amount} exceeds single transaction limit of ₹{threshold}"

        elif ptype == "NEW_RECIPIENT_LIMIT":
            threshold = policy.get("threshold", 0)
            if is_new and amount > threshold:
                is_violated = True
                detail = f"Recipient '{payment.get('recipient')}' is new and amount ₹{amount} exceeds new recipient limit of ₹{threshold}"

        elif ptype == "PERIOD_LIMIT":
            scope = policy.get("scope", "CATEGORY").upper()
            scope_val = normalize_text(policy.get("scope_value", ""))
            period = policy.get("period", "WEEK").upper()
            limit = policy.get("limit", 0)

            # Rolling window: WEEK = 7 days, MONTH = 30 days
            window_days = 7 if period == "WEEK" else 30
            cutoff = payment_time - timedelta(days=window_days)

            # Sum prior EXECUTED_SIMULATED transactions within window
            prior_spend = 0
            for tx in history:
                # Only EXECUTED_SIMULATED counts
                if tx.get("status") != "EXECUTED_SIMULATED":
                    continue
                tx_time = parse_iso_datetime(tx.get("timestamp") or tx.get("created_at"))
                if tx_time < cutoff or tx_time > payment_time:
                    continue

                if scope == "CATEGORY":
                    if normalize_text(tx.get("category")) == scope_val:
                        prior_spend += tx.get("amount", 0)
                elif scope == "RECIPIENT":
                    if normalize_text(tx.get("recipient")) == scope_val:
                        prior_spend += tx.get("amount", 0)

            # Check if this policy even applies to the current payment
            applies = False
            if scope == "CATEGORY" and category == scope_val:
                applies = True
            elif scope == "RECIPIENT" and recipient == scope_val:
                applies = True

            if applies:
                projected_total = prior_spend + amount
                if projected_total > limit:
                    is_violated = True
                    period_name = "weekly" if period == "WEEK" else "monthly"
                    detail = (
                        f"Projected {period_name} spend ₹{projected_total} "
                        f"(prior ₹{prior_spend} + ₹{amount}) exceeds limit of ₹{limit} for {policy.get('scope_value')}"
                    )
            else:
                detail = f"Policy applies to {policy.get('scope_value')}; current payment is {payment.get('category')} / {payment.get('recipient')}"

        result_status = "FAIL" if is_violated else "PASS"
        rule_eval = {
            "id": pid,
            "label": f"{pid} · {desc}",
            "result": result_status,
            "detail": detail or f"Policy satisfied (action: {action})"
        }
        evaluated_rules.append(rule_eval)

        if is_violated:
            violation_info = {
                "policy_id": pid,
                "policy_type": ptype,
                "action": action,
                "detail": detail,
                "description": desc
            }
            violated.append(violation_info)
            reasons.append(f"{pid}: {detail}")
            if action == "HOLD":
                hold_policies.append(violation_info)
            else:
                verify_policies.append(violation_info)

    return {
        "is_new_recipient": is_new,
        "evaluated_rules": evaluated_rules,
        "violated_policies": violated,
        "hold_policies": hold_policies,
        "verify_policies": verify_policies,
        "reasons": reasons
    }
