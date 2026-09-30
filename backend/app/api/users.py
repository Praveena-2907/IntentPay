from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.schemas import UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == "usr_demo").first()
    if not user:
        # Fallback query any first user
        user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    available = user.current_balance - user.upcoming_expenses
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        monthly_income=user.monthly_income,
        current_balance=user.current_balance,
        upcoming_expenses=user.upcoming_expenses,
        available_balance=available,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
