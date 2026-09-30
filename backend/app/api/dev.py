from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.config import settings
from app.seed import seed_database
from app.models import User, PaymentIntent, PaymentPolicy, Transaction, PaymentSuggestion

router = APIRouter(prefix="/api/dev", tags=["Dev"])

@router.post("/reset")
def reset_database(db: Session = Depends(get_db)):
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Reset is only permitted when DEMO_MODE is true")

    seed_database(db, force=True)

    intents_count = db.query(PaymentIntent).filter(PaymentIntent.status != "DELETED").count()
    policies_count = db.query(PaymentPolicy).filter(PaymentPolicy.status != "DELETED").count()
    transactions_count = db.query(Transaction).count()
    suggestions_count = db.query(PaymentSuggestion).count()

    return {
        "status": "reset_successful",
        "demo_mode": settings.DEMO_MODE,
        "counts": {
            "intents": intents_count,
            "policies": policies_count,
            "transactions": transactions_count,
            "suggestions": suggestions_count
        }
    }
