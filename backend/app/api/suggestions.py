from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import PaymentSuggestion, Transaction, PaymentIntent
from app.schemas import SuggestionResponse
from app.engines.recurring import detect_recurring_suggestions

router = APIRouter(prefix="/api/suggestions", tags=["Suggestions"])

@router.get("", response_model=List[SuggestionResponse])
def get_suggestions(db: Session = Depends(get_db)):
    suggestions = db.query(PaymentSuggestion).filter(PaymentSuggestion.status == "PENDING").all()
    if not suggestions:
        # Detect suggestions from history
        history = [
            {
                "status": t.status,
                "amount": t.amount,
                "category": t.category,
                "recipient": t.recipient,
                "timestamp": t.timestamp.isoformat()
            }
            for t in db.query(Transaction).all()
        ]
        intents = [
            {"recipient": i.recipient, "status": i.status}
            for i in db.query(PaymentIntent).all()
        ]
        detected = detect_recurring_suggestions(history, intents)
        for d in detected:
            s_id = f"PSG-{db.query(PaymentSuggestion).count() + 1:03d}"
            s = PaymentSuggestion(
                id=s_id,
                recipient=d["recipient"],
                suggested_amount=d["suggested_amount"],
                frequency=d["frequency"],
                day_of_month=d.get("day_of_month"),
                category=d["category"],
                reason=d["reason"],
                status="PENDING"
            )
            db.add(s)
            suggestions.append(s)
        if detected:
            db.commit()

    return suggestions

@router.post("/{id}/dismiss")
def dismiss_suggestion(id: str, db: Session = Depends(get_db)):
    s = db.query(PaymentSuggestion).filter(PaymentSuggestion.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Suggestion {id} not found")
    s.status = "DISMISSED"
    db.commit()
    return {"status": "dismissed", "id": id}
