"""
Behavioral Anomaly Signal Engine (Pure Python, No DB, No Network)
Label everywhere: "Behavioral Anomaly Signal", never "fraud".
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.engines.policy_engine import normalize_text, parse_iso_datetime

def evaluate_behavior_signals(
    payment: Dict[str, Any],
    history: List[Dict[str, Any]],
    known_recipients: List[str]
) -> Dict[str, Any]:
    amount = payment.get("amount", 0)
    category = normalize_text(payment.get("category", ""))
    recipient = normalize_text(payment.get("recipient", ""))
    payment_time = parse_iso_datetime(payment.get("timestamp"))

    known_set = {normalize_text(r) for r in known_recipients if r}
    is_new_recipient = recipient not in known_set

    # Filter historical executed payments
    executed_txs = [tx for tx in history if tx.get("status") == "EXECUTED_SIMULATED"]
    total_tx_count = len(executed_txs)

    signals: List[Dict[str, Any]] = []
    rules_eval: List[Dict[str, Any]] = []
    notes: List[str] = []

    # 1. Baseline Calculation
    category_txs = [tx for tx in executed_txs if normalize_text(tx.get("category")) == category]
    cat_count = len(category_txs)

    if total_tx_count < 5:
        notes.append("Insufficient history (< 5 transactions); amount anomaly signal skipped")
        rules_eval.append({
            "id": "SIG-AMOUNT-SKIP",
            "label": "Behavioral Anomaly Signal · Amount",
            "result": "PASS",
            "detail": "Insufficient history (< 5 transactions); signal skipped"
        })
    else:
        if cat_count >= 3:
            baseline = sum(tx.get("amount", 0) for tx in category_txs) / cat_count
            baseline_source = f"category '{payment.get('category')}' average ({cat_count} samples)"
        else:
            baseline = sum(tx.get("amount", 0) for tx in executed_txs) / total_tx_count
            baseline_source = f"overall average ({total_tx_count} samples)"

        # Check HIGH_AMOUNT
        if baseline > 0:
            ratio = amount / baseline
            if ratio >= 5.0:
                signals.append({
                    "signal": "HIGH_AMOUNT",
                    "level": "HIGH",
                    "rule": f"Amount ₹{amount} is >= 5× {baseline_source} (₹{int(baseline)})",
                    "detail": f"Observed ratio: {ratio:.1f}×"
                })
                rules_eval.append({
                    "id": "SIG-HIGH-AMOUNT",
                    "label": "Behavioral Anomaly Signal · High Amount",
                    "result": "FAIL",
                    "detail": f"High anomaly: amount ₹{amount} is {ratio:.1f}× baseline ₹{int(baseline)}"
                })
            elif ratio >= 2.5:
                signals.append({
                    "signal": "HIGH_AMOUNT",
                    "level": "MEDIUM",
                    "rule": f"Amount ₹{amount} is >= 2.5× {baseline_source} (₹{int(baseline)})",
                    "detail": f"Observed ratio: {ratio:.1f}×"
                })
                rules_eval.append({
                    "id": "SIG-MED-AMOUNT",
                    "label": "Behavioral Anomaly Signal · Elevated Amount",
                    "result": "WARN",
                    "detail": f"Elevated anomaly: amount ₹{amount} is {ratio:.1f}× baseline ₹{int(baseline)}"
                })
            else:
                rules_eval.append({
                    "id": "SIG-NORM-AMOUNT",
                    "label": "Behavioral Anomaly Signal · Amount",
                    "result": "PASS",
                    "detail": f"Amount ₹{amount} is consistent with baseline ₹{int(baseline)} ({ratio:.1f}×)"
                })

    # 2. NEW_RECIPIENT Signal
    if is_new_recipient:
        signals.append({
            "signal": "NEW_RECIPIENT",
            "level": "MEDIUM",
            "rule": f"Recipient '{payment.get('recipient')}' not in verified or known directory",
            "detail": "First interaction with this recipient name"
        })
        rules_eval.append({
            "id": "SIG-NEW-RECIP",
            "label": "Behavioral Anomaly Signal · New Recipient",
            "result": "WARN",
            "detail": f"Recipient '{payment.get('recipient')}' is unverified / new"
        })
    else:
        rules_eval.append({
            "id": "SIG-KNOWN-RECIP",
            "label": "Behavioral Anomaly Signal · Recipient",
            "result": "PASS",
            "detail": f"Recipient '{payment.get('recipient')}' is a recognized contact"
        })

    # 3. UNUSUAL_TIME Signal (typical band seeded 08:00 - 22:00)
    tx_hour = payment_time.hour
    if tx_hour < 8 or tx_hour >= 22:
        signals.append({
            "signal": "UNUSUAL_TIME",
            "level": "MEDIUM",
            "rule": f"Payment initiated at {payment_time.strftime('%H:%M')} outside typical band (08:00–22:00)",
            "detail": f"Hour {tx_hour:02d}:00 is outside standard daytime hours"
        })
        rules_eval.append({
            "id": "SIG-TIME-UNUSUAL",
            "label": "Behavioral Anomaly Signal · Payment Time",
            "result": "WARN",
            "detail": f"Unusual hour: {payment_time.strftime('%H:%M')} (typical: 08:00–22:00)"
        })
    else:
        rules_eval.append({
            "id": "SIG-TIME-NORMAL",
            "label": "Behavioral Anomaly Signal · Payment Time",
            "result": "PASS",
            "detail": f"Time {payment_time.strftime('%H:%M')} is within standard active hours"
        })

    # 4. FREQUENCY_SPIKE (>= 4 payments in trailing 24h)
    cutoff_24h = payment_time - timedelta(hours=24)
    recent_24h_txs = [
        tx for tx in executed_txs
        if cutoff_24h <= parse_iso_datetime(tx.get("timestamp") or tx.get("created_at")) <= payment_time
    ]
    count_24h = len(recent_24h_txs)
    if count_24h >= 4:
        signals.append({
            "signal": "FREQUENCY_SPIKE",
            "level": "MEDIUM",
            "rule": f"{count_24h} payments executed in trailing 24 hours (threshold: >= 4)",
            "detail": "Rapid succession of outgoing transactions"
        })
        rules_eval.append({
            "id": "SIG-FREQ-SPIKE",
            "label": "Behavioral Anomaly Signal · Frequency",
            "result": "WARN",
            "detail": f"High volume: {count_24h} payments in trailing 24h"
        })
    else:
        rules_eval.append({
            "id": "SIG-FREQ-NORM",
            "label": "Behavioral Anomaly Signal · Frequency",
            "result": "PASS",
            "detail": f"Standard frequency: {count_24h} payments in trailing 24h"
        })

    # 5. CATEGORY_SPIKE (trailing 7-day category total + amount >= 2× weekly category average)
    if cat_count >= 3:
        cutoff_7d = payment_time - timedelta(days=7)
        cat_7d_spend = sum(
            tx.get("amount", 0) for tx in category_txs
            if cutoff_7d <= parse_iso_datetime(tx.get("timestamp") or tx.get("created_at")) < payment_time
        )
        total_cat_spend = sum(tx.get("amount", 0) for tx in category_txs)

        # Approximate number of weeks in history
        first_tx_time = min(parse_iso_datetime(tx.get("timestamp") or tx.get("created_at")) for tx in executed_txs)
        span_days = max(14, (payment_time - first_tx_time).days)
        weekly_cat_avg = total_cat_spend / (span_days / 7.0)

        projected_7d = cat_7d_spend + amount
        # A true category spike occurs when compounding prior trailing-7d spend or exceeding 2x weekly average
        if cat_7d_spend > 0 and weekly_cat_avg > 0 and projected_7d >= 2.0 * weekly_cat_avg:
            signals.append({
                "signal": "CATEGORY_SPIKE",
                "level": "MEDIUM",
                "rule": f"Trailing 7-day category spend ₹{projected_7d} >= 2× weekly category average (₹{int(weekly_cat_avg)})",
                "detail": f"Category '{payment.get('category')}' is experiencing sharp surge"
            })
            rules_eval.append({
                "id": "SIG-CAT-SPIKE",
                "label": "Behavioral Anomaly Signal · Category Spike",
                "result": "WARN",
                "detail": f"Category spend surge: projected ₹{projected_7d} vs weekly avg ₹{int(weekly_cat_avg)}"
            })

    # Stats for UI and analytics
    avg_amt = int(sum(tx.get("amount", 0) for tx in executed_txs) / total_tx_count) if total_tx_count else 0
    max_amt = max((tx.get("amount", 0) for tx in executed_txs), default=0)

    category_totals: Dict[str, int] = {}
    for tx in executed_txs:
        c = tx.get("category", "Other")
        category_totals[c] = category_totals.get(c, 0) + tx.get("amount", 0)

    recipient_counts: Dict[str, int] = {}
    for tx in executed_txs:
        r = tx.get("recipient", "Unknown")
        recipient_counts[r] = recipient_counts.get(r, 0) + 1
    common_recips = sorted(recipient_counts.keys(), key=lambda k: recipient_counts[k], reverse=True)[:5]

    stats = {
        "average_amount": avg_amt,
        "max_amount": max_amt,
        "typical_hour_band": "08:00 - 22:00",
        "frequency_last_24h": count_24h,
        "common_recipients": common_recips,
        "category_totals": category_totals,
        "notes": notes
    }

    return {
        "signals": signals,
        "rules_evaluated": rules_eval,
        "stats": stats
    }
