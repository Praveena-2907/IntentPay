from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import PaymentIntent, PaymentPolicy, Transaction, PaymentSuggestion

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("")
def get_dashboard_summary(db: Session = Depends(get_db)):
    intents_count = db.query(PaymentIntent).filter(PaymentIntent.status == "ACTIVE").count()
    policies_count = db.query(PaymentPolicy).filter(PaymentPolicy.status == "ACTIVE").count()
    total_evaluated = db.query(Transaction).count()

    approved_count = db.query(Transaction).filter(Transaction.decision == "ALLOW").count()
    verify_count = db.query(Transaction).filter(Transaction.decision == "VERIFY").count()
    held_count = db.query(Transaction).filter(Transaction.decision == "HOLD").count()

    # Total simulated executed volume
    executed_vol = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == "EXECUTED_SIMULATED"
    ).scalar() or 0

    # Spending by category (EXECUTED_SIMULATED)
    category_rows = db.query(
        Transaction.category,
        func.sum(Transaction.amount).label("total_amt"),
        func.count(Transaction.id).label("tx_count")
    ).filter(
        Transaction.status == "EXECUTED_SIMULATED"
    ).group_by(Transaction.category).all()

    spending_by_cat = [
        {"category": row[0], "amount": int(row[1]), "count": int(row[2])}
        for row in category_rows
    ]
    spending_by_cat.sort(key=lambda x: x["amount"], reverse=True)

    # Decision distribution
    dist = [
        {"decision": "ALLOW", "count": approved_count, "color": "#22C55E"},
        {"decision": "VERIFY", "count": verify_count, "color": "#F59E0B"},
        {"decision": "HOLD", "count": held_count, "color": "#EF4444"}
    ]

    # Recent decisions (latest 5)
    recent_txs = db.query(Transaction).order_by(Transaction.timestamp.desc(), Transaction.id.desc()).limit(7).all()
    recent_list = []
    for tx in recent_txs:
        reason = tx.trace.reasons[0] if (tx.trace and tx.trace.reasons) else f"Decision: {tx.decision}"
        recent_list.append({
            "id": tx.id,
            "recipient": tx.recipient,
            "amount": tx.amount,
            "category": tx.category,
            "decision": tx.decision,
            "status": tx.status,
            "timestamp": tx.timestamp.isoformat(),
            "reason": reason
        })

    # Active intents & policies
    active_intents = db.query(PaymentIntent).filter(PaymentIntent.status == "ACTIVE").order_by(PaymentIntent.id.asc()).all()
    active_policies = db.query(PaymentPolicy).filter(PaymentPolicy.status == "ACTIVE").order_by(PaymentPolicy.id.asc()).all()
    suggestions = db.query(PaymentSuggestion).filter(PaymentSuggestion.status == "PENDING").all()

    return {
        "kpis": {
            "intents": intents_count,
            "policies": policies_count,
            "evaluated": total_evaluated,
            "approved": approved_count,
            "verify": verify_count,
            "held": held_count,
            "simulated_volume": int(executed_vol)
        },
        "spending_by_category": spending_by_cat,
        "decision_distribution": dist,
        "recent_decisions": recent_list,
        "active_intents": [
            {"id": i.id, "purpose": i.purpose, "recipient": i.recipient, "category": i.category, "amount": i.amount or i.max_amount, "action": i.action, "frequency": i.frequency}
            for i in active_intents
        ],
        "active_policies": [
            {"id": p.id, "policy_type": p.policy_type, "threshold": p.threshold or p.limit, "action": p.action, "description": p.description}
            for p in active_policies
        ],
        "pending_suggestions": [
            {"id": s.id, "recipient": s.recipient, "amount": s.suggested_amount, "frequency": s.frequency, "reason": s.reason}
            for s in suggestions
        ]
    }
