import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import PaymentIntent, PaymentPolicy
from app.schemas import (
    IntentParseRequest, IntentParseResponse,
    IntentCreate, IntentUpdate, IntentResponse
)
from app.ai.parser_service import parse_intent_text

router = APIRouter(prefix="/api/intents", tags=["Intents"])

@router.post("/parse", response_model=IntentParseResponse)
async def parse_intent_endpoint(payload: IntentParseRequest, db: Session = Depends(get_db)):
    # Fetch active policies for conflict checking
    active_policies = db.query(PaymentPolicy).filter(PaymentPolicy.status == "ACTIVE").all()
    policies_dicts = [
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
        for p in active_policies
    ]
    return await parse_intent_text(payload.text, existing_policies=policies_dicts)

@router.post("", response_model=IntentResponse, status_code=status.HTTP_201_CREATED)
def create_intent(payload: IntentCreate, db: Session = Depends(get_db)):
    if not payload.confirmed:
        raise HTTPException(
            status_code=422,
            detail="Confirmation is required to persist an intent. Set confirmed: true."
        )

    # Generate sequential or unique ID
    count = db.query(PaymentIntent).count() + 1
    intent_id = f"PI-{count:03d}"
    # Verify uniqueness
    while db.query(PaymentIntent).filter(PaymentIntent.id == intent_id).first():
        count += 1
        intent_id = f"PI-{count:03d}"

    conditions_data = [c.model_dump() for c in payload.conditions]

    intent = PaymentIntent(
        id=intent_id,
        purpose=payload.purpose,
        recipient=payload.recipient,
        category=payload.category,
        amount=payload.amount,
        max_amount=payload.max_amount,
        currency=payload.currency,
        frequency=payload.frequency,
        day_of_month=payload.day_of_month,
        trigger=payload.trigger,
        action=payload.action,
        conditions=conditions_data,
        status="ACTIVE"
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)
    return intent

@router.get("", response_model=List[IntentResponse])
def list_intents(db: Session = Depends(get_db)):
    return db.query(PaymentIntent).filter(PaymentIntent.status != "DELETED").order_by(PaymentIntent.created_at.desc()).all()

@router.get("/{id}", response_model=IntentResponse)
def get_intent(id: str, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == id, PaymentIntent.status != "DELETED").first()
    if not intent:
        raise HTTPException(status_code=404, detail=f"Payment intent {id} not found")
    return intent

@router.put("/{id}", response_model=IntentResponse)
def update_intent(id: str, payload: IntentUpdate, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == id, PaymentIntent.status != "DELETED").first()
    if not intent:
        raise HTTPException(status_code=404, detail=f"Payment intent {id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "conditions" in update_data and update_data["conditions"] is not None:
        update_data["conditions"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in update_data["conditions"]]

    for key, value in update_data.items():
        setattr(intent, key, value)

    db.commit()
    db.refresh(intent)
    return intent

@router.delete("/{id}")
def delete_intent(id: str, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == id).first()
    if not intent or intent.status == "DELETED":
        raise HTTPException(status_code=404, detail=f"Payment intent {id} not found")

    intent.status = "DELETED"
    db.commit()
    return {"status": "deleted", "id": id}

@router.post("/{id}/pause", response_model=IntentResponse)
def pause_intent(id: str, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == id, PaymentIntent.status != "DELETED").first()
    if not intent:
        raise HTTPException(status_code=404, detail=f"Payment intent {id} not found")
    intent.status = "PAUSED"
    db.commit()
    db.refresh(intent)
    return intent

@router.post("/{id}/resume", response_model=IntentResponse)
def resume_intent(id: str, db: Session = Depends(get_db)):
    intent = db.query(PaymentIntent).filter(PaymentIntent.id == id, PaymentIntent.status != "DELETED").first()
    if not intent:
        raise HTTPException(status_code=404, detail=f"Payment intent {id} not found")
    intent.status = "ACTIVE"
    db.commit()
    db.refresh(intent)
    return intent
