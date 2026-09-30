from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.schemas import PaymentImpactRequest, WhatIfRequest
from app.engines.impact import calculate_payment_impact, calculate_what_if_scenario

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])

@router.post("/payment-impact")
def get_payment_impact(payload: PaymentImpactRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == "usr_demo").first() or db.query(User).first()
    income = user.monthly_income if user else 50000
    balance = user.current_balance if user else 36000
    upcoming = user.upcoming_expenses if user else 15500

    return calculate_payment_impact(payload.amount, balance, upcoming, income)

@router.post("/what-if")
def simulate_what_if(payload: WhatIfRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == "usr_demo").first() or db.query(User).first()
    income = payload.monthly_income if payload.monthly_income is not None else (user.monthly_income if user else 50000)
    balance = user.current_balance if user else 36000
    upcoming = payload.monthly_expense if payload.monthly_expense is not None else (user.upcoming_expenses if user else 15500)

    return calculate_what_if_scenario(
        payment_amount=payload.payment_amount,
        current_balance=balance,
        monthly_income=income,
        upcoming_expenses=upcoming,
        loan_amount=payload.loan_amount or 0,
        recurring_expense_delta=payload.recurring_expense_delta or 0
    )
