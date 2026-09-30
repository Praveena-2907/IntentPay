"""
Conflict Detection Engine (Pure Python, No DB, No Network)
Detects conflicts between ACTIVE AUTO_PAY intents and PayDNA security policies.
"""

from typing import List, Dict, Any
from app.engines.policy_engine import normalize_text

def find_conflicts(
    intents: List[Dict[str, Any]],
    policies: List[Dict[str, Any]],
    known_recipients: List[str] = None
) -> List[Dict[str, Any]]:
    if known_recipients is None:
        known_recipients = []
    known_set = {normalize_text(r) for r in known_recipients if r}

    conflicts = []
    active_intents = [i for i in intents if i.get("status") == "ACTIVE" and i.get("action") == "AUTO_PAY"]
    active_policies = [p for p in policies if p.get("status") == "ACTIVE"]

    for intent in active_intents:
        # Determine intent target amount
        intent_amt = intent.get("amount") or intent.get("max_amount")
        if not intent_amt:
            continue

        intent_rec = normalize_text(intent.get("recipient"))
        intent_cat = normalize_text(intent.get("category"))
        is_new_rec = intent_rec and (intent_rec not in known_set)

        for policy in active_policies:
            ptype = policy.get("policy_type")
            action = policy.get("action", "VERIFY")
            conflict_detected = False
            reason = ""

            if ptype == "MAX_TRANSACTION_AMOUNT":
                threshold = policy.get("threshold", 0)
                if intent_amt > threshold:
                    conflict_detected = True
                    reason = (
                        f"Intent '{intent.get('purpose')}' auto-pays up to ₹{intent_amt:,}, "
                        f"which exceeds policy {policy.get('id')} single limit of ₹{threshold:,} ({action})"
                    )

            elif ptype == "NEW_RECIPIENT_LIMIT":
                threshold = policy.get("threshold", 0)
                if is_new_rec and intent_amt > threshold:
                    conflict_detected = True
                    reason = (
                        f"Intent recipient '{intent.get('recipient')}' is unverified, "
                        f"and auto-pay ₹{intent_amt:,} exceeds new recipient limit ₹{threshold:,} ({action})"
                    )

            elif ptype == "PERIOD_LIMIT":
                scope = policy.get("scope", "CATEGORY")
                scope_val = normalize_text(policy.get("scope_value", ""))
                limit = policy.get("limit", 0)

                if scope == "CATEGORY" and intent_cat == scope_val:
                    if intent_amt > limit:
                        conflict_detected = True
                        reason = (
                            f"Intent '{intent.get('purpose')}' amount ₹{intent_amt:,} exceeds "
                            f"{policy.get('period', 'WEEK').lower()} category limit of ₹{limit:,} for {policy.get('scope_value')}"
                        )
                elif scope == "RECIPIENT" and intent_rec == scope_val:
                    if intent_amt > limit:
                        conflict_detected = True
                        reason = (
                            f"Intent '{intent.get('purpose')}' amount ₹{intent_amt:,} exceeds "
                            f"{policy.get('period', 'MONTH').lower()} recipient limit of ₹{limit:,} for {policy.get('scope_value')}"
                        )

            if conflict_detected:
                conflicts.append({
                    "intent": {
                        "id": intent.get("id"),
                        "purpose": intent.get("purpose"),
                        "amount": intent_amt,
                        "recipient": intent.get("recipient"),
                        "category": intent.get("category"),
                        "action": intent.get("action")
                    },
                    "policy": {
                        "id": policy.get("id"),
                        "policy_type": policy.get("policy_type"),
                        "threshold": policy.get("threshold") or policy.get("limit"),
                        "action": policy.get("action"),
                        "description": policy.get("description")
                    },
                    "reason": reason,
                    "resolutions": ["KEEP_POLICY", "UPDATE_INTENT", "CANCEL"]
                })

    return conflicts
