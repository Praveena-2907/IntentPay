from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import PaymentIntent, PaymentPolicy, Recipient
from app.engines.conflict import find_conflicts

router = APIRouter(prefix="/api/conflicts", tags=["Conflicts"])

@router.get("", response_model=List[Dict[str, Any]])
def get_conflicts(db: Session = Depends(get_db)):
    active_intents = [
        {
            "id": i.id,
            "purpose": i.purpose,
            "recipient": i.recipient,
            "category": i.category,
            "amount": i.amount,
            "max_amount": i.max_amount,
            "frequency": i.frequency,
            "action": i.action,
            "status": i.status
        }
        for i in db.query(PaymentIntent).filter(PaymentIntent.status == "ACTIVE").all()
    ]

    active_policies = [
        {
            "id": p.id,
            "policy_type": p.policy_type,
            "threshold": p.threshold,
            "scope": p.scope,
            "scope_value": p.scope_value,
            "period": p.period,
            "limit": p.limit,
            "action": p.action,
            "status": p.status,
            "description": p.description
        }
        for p in db.query(PaymentPolicy).filter(PaymentPolicy.status == "ACTIVE").all()
    ]

    known_recipients = [r.name for r in db.query(Recipient).all()]
    return find_conflicts(active_intents, active_policies, known_recipients)
