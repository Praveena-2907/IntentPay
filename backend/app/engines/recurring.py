"""
Recurring Payment Detection Engine (Pure Python, No DB, No Network)
Identifies recurring patterns across history and generates suggestions.
"""

from typing import List, Dict, Any
from app.engines.policy_engine import normalize_text, parse_iso_datetime

def detect_recurring_suggestions(
    history: List[Dict[str, Any]],
    active_intents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rule: Same recipient + amount within ±5%, on >= 3 distinct months,
    day-of-month within ±3 days, and no ACTIVE intent for that recipient
    -> create a PaymentSuggestion. Never auto-create intents.
    """
    # Recipients who already have an active intent
    existing_recipients = {
        normalize_text(i.get("recipient")) for i in active_intents
        if i.get("status") == "ACTIVE" and i.get("recipient")
    }

    # Group executed transactions by normalized recipient
    by_recipient: Dict[str, List[Dict[str, Any]]] = {}
    for tx in history:
        if tx.get("status") != "EXECUTED_SIMULATED":
            continue
        rec = normalize_text(tx.get("recipient"))
        if not rec or rec in existing_recipients:
            continue
        by_recipient.setdefault(rec, []).append(tx)

    suggestions = []
    for rec_norm, txs in by_recipient.items():
        if len(txs) < 3:
            continue

        # Check clusters of amounts within ±5%
        # Sort txs by timestamp
        sorted_txs = sorted(txs, key=lambda t: parse_iso_datetime(t.get("timestamp") or t.get("created_at")))

        # Check for 3 distinct months with day-of-month within ±3 days
        for i in range(len(sorted_txs)):
            cluster = [sorted_txs[i]]
            base_amt = sorted_txs[i].get("amount", 0)
            base_dt = parse_iso_datetime(sorted_txs[i].get("timestamp") or sorted_txs[i].get("created_at"))
            base_day = base_dt.day

            for j in range(i + 1, len(sorted_txs)):
                cand = sorted_txs[j]
                cand_amt = cand.get("amount", 0)
                cand_dt = parse_iso_datetime(cand.get("timestamp") or cand.get("created_at"))

                # Check amount within ±5%
                if abs(cand_amt - base_amt) / max(1, base_amt) <= 0.05:
                    # Check day-of-month within ±3 days
                    if abs(cand_dt.day - base_day) <= 3:
                        cluster.append(cand)

            # Check distinct months in cluster
            distinct_months = {
                (parse_iso_datetime(t.get("timestamp") or t.get("created_at")).year,
                 parse_iso_datetime(t.get("timestamp") or t.get("created_at")).month)
                for t in cluster
            }

            if len(distinct_months) >= 3:
                # Found recurring candidate
                avg_amount = round(sum(t.get("amount", 0) for t in cluster) / len(cluster))
                rep_tx = cluster[-1]
                orig_recipient = rep_tx.get("recipient", rec_norm)
                category = rep_tx.get("category", "General")
                median_day = sorted(parse_iso_datetime(t.get("timestamp") or t.get("created_at")).day for t in cluster)[len(cluster) // 2]

                suggestions.append({
                    "recipient": orig_recipient,
                    "suggested_amount": avg_amount,
                    "frequency": "MONTHLY",
                    "day_of_month": median_day,
                    "category": category,
                    "reason": f"Detected recurring payment of ~₹{avg_amount:,} to {orig_recipient} across {len(distinct_months)} distinct months around day {median_day}."
                })
                break # Avoid duplicate suggestion for the same recipient

    return suggestions
