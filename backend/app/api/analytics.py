from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Transaction, User
from app.engines.behavior_engine import evaluate_behavior_signals

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/spending")
def get_spending_analytics(db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.status == "EXECUTED_SIMULATED").all()

    category_map: Dict[str, int] = {}
    monthly_map: Dict[str, int] = {}

    for t in txs:
        cat = t.category or "Other"
        category_map[cat] = category_map.get(cat, 0) + t.amount
        month_key = t.timestamp.strftime("%b %Y") if t.timestamp else "Current"
        monthly_map[month_key] = monthly_map.get(month_key, 0) + t.amount

    category_breakdown = [
        {"category": k, "amount": v}
        for k, v in sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    ]

    monthly_trend = [
        {"month": k, "amount": v}
        for k, v in monthly_map.items()
    ]

    total_spend = sum(category_map.values())
    avg_per_tx = int(total_spend / max(1, len(txs)))

    return {
        "total_spend": total_spend,
        "transaction_count": len(txs),
        "average_transaction": avg_per_tx,
        "category_breakdown": category_breakdown,
        "monthly_trend": monthly_trend
    }

@router.get("/behavior")
def get_behavior_analytics(db: Session = Depends(get_db)):
    txs = db.query(Transaction).all()
    history = [
        {
            "id": t.id,
            "amount": t.amount,
            "category": t.category,
            "recipient": t.recipient,
            "status": t.status,
            "timestamp": t.timestamp.isoformat()
        }
        for t in txs
    ]

    recipients_list = list({t.recipient for t in txs if t.recipient})
    sample_payment = {"amount": 2500, "category": "Food", "recipient": "Big Bazaar"}
    eval_res = evaluate_behavior_signals(sample_payment, history, recipients_list)

    return {
        "stats": eval_res.get("stats", {}),
        "total_evaluated": len(txs),
        "typical_hour_band": "08:00 - 22:00"
    }
