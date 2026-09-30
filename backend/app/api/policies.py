from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import PaymentPolicy, PaymentIntent
from app.schemas import (
    PolicyParseRequest, PolicyParseResponse,
    PolicyCreate, PolicyUpdate, PolicyResponse
)
from app.ai.parser_service import parse_policy_text
from app.engines.policy_engine import normalize_text

router = APIRouter(prefix="/api/policies", tags=["Policies"])

@router.post("/parse", response_model=PolicyParseResponse)
async def parse_policy_endpoint(payload: PolicyParseRequest, db: Session = Depends(get_db)):
    active_intents = db.query(PaymentIntent).filter(PaymentIntent.status == "ACTIVE").all()
    intents_dicts = [
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
        for i in active_intents
    ]
    return await parse_policy_text(payload.text, existing_intents=intents_dicts)

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)):
    if not payload.confirmed:
        raise HTTPException(
            status_code=422,
            detail="Confirmation is required to persist a policy. Set confirmed: true."
        )

    # Duplicate prevention check (Section 3.4)
    # same policy_type + scope + scope_value + period + threshold/limit among non-deleted
    query = db.query(PaymentPolicy).filter(
        PaymentPolicy.status != "DELETED",
        PaymentPolicy.policy_type == payload.policy_type
    )

    if payload.policy_type in ("MAX_TRANSACTION_AMOUNT", "NEW_RECIPIENT_LIMIT"):
        query = query.filter(PaymentPolicy.threshold == payload.threshold)
    elif payload.policy_type == "PERIOD_LIMIT":
        query = query.filter(
            PaymentPolicy.scope == payload.scope,
            PaymentPolicy.period == payload.period,
            PaymentPolicy.limit == payload.limit
        )

    existing = query.all()
    # Check scope_value normalization if PERIOD_LIMIT
    for ex in existing:
        if payload.policy_type == "PERIOD_LIMIT":
            if normalize_text(ex.scope_value) == normalize_text(payload.scope_value):
                raise HTTPException(
                    status_code=409,
                    detail=f"Duplicate policy: Identical policy already exists with ID {ex.id} ({ex.description})"
                )
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate policy: Identical policy already exists with ID {ex.id} ({ex.description})"
            )

    count = db.query(PaymentPolicy).count() + 1
    policy_id = f"PD-{count:03d}"
    while db.query(PaymentPolicy).filter(PaymentPolicy.id == policy_id).first():
        count += 1
        policy_id = f"PD-{count:03d}"

    policy = PaymentPolicy(
        id=policy_id,
        policy_type=payload.policy_type,
        threshold=payload.threshold,
        scope=payload.scope,
        scope_value=payload.scope_value,
        period=payload.period,
        limit=payload.limit,
        action=payload.action,
        status="ACTIVE",
        description=payload.description
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("", response_model=List[PolicyResponse])
def list_policies(db: Session = Depends(get_db)):
    return db.query(PaymentPolicy).filter(PaymentPolicy.status != "DELETED").order_by(PaymentPolicy.id.asc()).all()

@router.get("/{id}", response_model=PolicyResponse)
def get_policy(id: str, db: Session = Depends(get_db)):
    policy = db.query(PaymentPolicy).filter(PaymentPolicy.id == id, PaymentPolicy.status != "DELETED").first()
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {id} not found")
    return policy

@router.put("/{id}", response_model=PolicyResponse)
def update_policy(id: str, payload: PolicyUpdate, db: Session = Depends(get_db)):
    policy = db.query(PaymentPolicy).filter(PaymentPolicy.id == id, PaymentPolicy.status != "DELETED").first()
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)
    return policy

@router.delete("/{id}")
def delete_policy(id: str, db: Session = Depends(get_db)):
    policy = db.query(PaymentPolicy).filter(PaymentPolicy.id == id).first()
    if not policy or policy.status == "DELETED":
        raise HTTPException(status_code=404, detail=f"Policy {id} not found")

    policy.status = "DELETED"
    db.commit()
    return {"status": "deleted", "id": id}
