"""
Deterministic Templated Decision Explanation (Pure Python, No LLM)
Produces clear, operational system language explaining decisions.
"""

from typing import List, Dict, Any

def generate_explanation(
    decision: str,
    reasons: List[str],
    payment: Dict[str, Any],
    pipeline_status: Dict[str, str]
) -> str:
    amount = payment.get("amount", 0)
    recipient = payment.get("recipient", "Unknown")
    category = payment.get("category", "General")

    if decision == "HOLD":
        primary = reasons[0] if reasons else "Policy or simulation ceiling exceeded"
        return f"Payment of ₹{amount:,} to {recipient} [{category}] has been HELD. Reason: {primary}."

    if decision == "VERIFY":
        if len(reasons) == 1:
            return f"Payment of ₹{amount:,} to {recipient} [{category}] requires manual confirmation: {reasons[0]}."
        details = "; ".join(f"({i+1}) {r}" for i, r in enumerate(reasons))
        return f"Payment of ₹{amount:,} to {recipient} [{category}] requires user verification due to {len(reasons)} security trigger(s): {details}."

    # ALLOW
    if pipeline_status.get("intent") == "PASS":
        return f"Payment of ₹{amount:,} to {recipient} [{category}] is permitted. Pre-approved intent criteria and PayDNA policies verified."
    return f"Payment of ₹{amount:,} to {recipient} [{category}] is permitted. All PayDNA policies satisfied with no behavioral anomaly detected."
