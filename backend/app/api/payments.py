import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Transaction, DecisionTrace, User, Recipient, PaymentIntent, PaymentPolicy
from app.schemas import (
    PaymentRequest, DecisionResponse, TransactionResponse, DecisionTraceResponse
)
from app.engines.intent_engine import evaluate_intent
from app.engines.policy_engine import evaluate_policies, normalize_text
from app.engines.behavior_engine import evaluate_behavior_signals
from app.engines.decision_engine import evaluate_decision
from app.engines.impact import calculate_payment_impact

router = APIRouter(prefix="/api/payments", tags=["Payments"])

def _run_pipeline(payment_dict: Dict[str, Any], db: Session) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    # 1. Fetch user data
    user = db.query(User).filter(User.id == "usr_demo").first()
    if not user:
        user = db.query(User).first()
    income = user.monthly_income if user else 50000
    balance = user.current_balance if user else 36000
    upcoming = user.upcoming_expenses if user else 15500

    # 2. Fetch active intents, active policies, known recipients, and history
    active_intents = [
        {
            "id": i.id,
            "purpose": i.purpose,
            "recipient": i.recipient,
            "category": i.category,
            "amount": i.amount,
            "max_amount": i.max_amount,
            "frequency": i.frequency,
            "trigger": i.trigger,
            "action": i.action,
            "conditions": i.conditions,
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

    recipients_list = [r.name for r in db.query(Recipient).all()]

    history_txs = [
        {
            "id": t.id,
            "recipient": t.recipient,
            "amount": t.amount,
            "category": t.category,
            "status": t.status,
            "timestamp": t.timestamp.isoformat() if t.timestamp else t.created_at.isoformat()
        }
        for t in db.query(Transaction).all()
    ]

    # Evaluate Engines
    intent_eval = evaluate_intent(payment_dict, active_intents)
    policy_eval = evaluate_policies(payment_dict, active_policies, history_txs, recipients_list)
    behavior_eval = evaluate_behavior_signals(payment_dict, history_txs, recipients_list)
    decision_eval = evaluate_decision(payment_dict, intent_eval, policy_eval, behavior_eval)
    impact_eval = calculate_payment_impact(payment_dict.get("amount", 0), balance, upcoming, income)

    return decision_eval, intent_eval, policy_eval, behavior_eval, impact_eval

@router.post("/analyze", response_model=DecisionResponse)
def analyze_payment(payload: PaymentRequest, db: Session = Depends(get_db)):
    pay_dict = payload.model_dump()
    if not pay_dict.get("timestamp"):
        pay_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    elif isinstance(pay_dict["timestamp"], datetime):
        pay_dict["timestamp"] = pay_dict["timestamp"].isoformat()

    dec_eval, int_eval, pol_eval, beh_eval, imp_eval = _run_pipeline(pay_dict, db)

    return DecisionResponse(
        decision=dec_eval["decision"],
        reasons=dec_eval["reasons"],
        explanation=dec_eval["explanation"],
        rules_evaluated=dec_eval["rules_evaluated"],
        pipeline_status=dec_eval["pipeline_status"],
        cash_flow_impact=imp_eval,
        behavior_signals=beh_eval.get("signals", []),
        intent_evaluation=int_eval,
        policy_evaluation=pol_eval
    )

@router.post("/simulate")
def simulate_payment(payload: PaymentRequest, db: Session = Depends(get_db)):
    # Idempotency check with client_request_id (T15)
    if payload.client_request_id:
        existing_tx = db.query(Transaction).filter(Transaction.client_request_id == payload.client_request_id).first()
        if existing_tx:
            trace = db.query(DecisionTrace).filter(DecisionTrace.transaction_id == existing_tx.id).first()
            return {
                "transaction": {
                    "id": existing_tx.id,
                    "recipient": existing_tx.recipient,
                    "amount": existing_tx.amount,
                    "category": existing_tx.category,
                    "status": existing_tx.status,
                    "decision": existing_tx.decision,
                    "timestamp": existing_tx.timestamp.isoformat()
                },
                "trace_id": trace.id if trace else None,
                "decision": existing_tx.decision,
                "reasons": trace.reasons if trace else []
            }

    pay_dict = payload.model_dump()
    pay_time = payload.timestamp or datetime.now(timezone.utc)
    pay_dict["timestamp"] = pay_time.isoformat()

    # Re-evaluate completely server-side
    dec_eval, int_eval, pol_eval, beh_eval, imp_eval = _run_pipeline(pay_dict, db)
    decision = dec_eval["decision"]

    user = db.query(User).filter(User.id == "usr_demo").first() or db.query(User).first()

    # Assign transaction status based on decision
    if decision == "ALLOW":
        status_val = "EXECUTED_SIMULATED"
        if user:
            user.current_balance -= payload.amount
        # Add recipient to directory if not present
        norm_r = normalize_text(payload.recipient)
        exists = db.query(Recipient).filter(Recipient.name.ilike(payload.recipient)).first()
        if not exists:
            db.add(Recipient(
                id=f"rcp_{uuid.uuid4().hex[:6]}",
                name=payload.recipient,
                is_verified=True,
                category_hint=payload.category
            ))
    elif decision == "VERIFY":
        status_val = "PENDING_VERIFICATION"
    else: # HOLD
        status_val = "HELD"

    # Generate sequential transaction ID: TX-00XX
    tx_count = db.query(Transaction).count() + 1
    tx_id = f"TX-{tx_count:04d}"
    while db.query(Transaction).filter(Transaction.id == tx_id).first():
        tx_count += 1
        tx_id = f"TX-{tx_count:04d}"

    tx = Transaction(
        id=tx_id,
        client_request_id=payload.client_request_id,
        recipient=payload.recipient,
        amount=payload.amount,
        currency="INR",
        category=payload.category,
        purpose=payload.purpose or f"Payment to {payload.recipient}",
        status=status_val,
        decision=decision,
        timestamp=pay_time
    )
    db.add(tx)

    # Persist DecisionTrace
    trace_id = f"TR-{tx_id[3:]}"
    trace = DecisionTrace(
        id=trace_id,
        transaction_id=tx_id,
        decision=decision,
        reasons=dec_eval["reasons"],
        rules_evaluated=dec_eval["rules_evaluated"],
        intent_evaluation=int_eval,
        policy_evaluation=pol_eval,
        behavior_signals=beh_eval.get("signals", []),
        cash_flow_impact=imp_eval,
        raw_input=pay_dict
    )
    db.add(trace)

    db.commit()
    db.refresh(tx)

    return {
        "transaction": {
            "id": tx.id,
            "recipient": tx.recipient,
            "amount": tx.amount,
            "category": tx.category,
            "status": tx.status,
            "decision": tx.decision,
            "timestamp": tx.timestamp.isoformat()
        },
        "trace_id": trace_id,
        "decision": decision,
        "explanation": dec_eval["explanation"],
        "reasons": dec_eval["reasons"],
        "pipeline_status": dec_eval["pipeline_status"],
        "cash_flow_impact": imp_eval,
        "rules_evaluated": dec_eval["rules_evaluated"]
    }

@router.post("/{id}/confirm")
def confirm_payment(id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {id} not found")

    if tx.status != "PENDING_VERIFICATION":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm transaction with status '{tx.status}'. Only PENDING_VERIFICATION transactions can be confirmed."
        )

    tx.status = "EXECUTED_SIMULATED"
    user = db.query(User).filter(User.id == "usr_demo").first() or db.query(User).first()
    if user:
        user.current_balance -= tx.amount

    # Ensure recipient added
    exists = db.query(Recipient).filter(Recipient.name.ilike(tx.recipient)).first()
    if not exists:
        db.add(Recipient(
            id=f"rcp_{uuid.uuid4().hex[:6]}",
            name=tx.recipient,
            is_verified=True,
            category_hint=tx.category
        ))

    # Update trace
    trace = db.query(DecisionTrace).filter(DecisionTrace.transaction_id == tx.id).first()
    if trace:
        reasons_list = list(trace.reasons or [])
        reasons_list.append("Payment manually verified and approved by user")
        trace.reasons = reasons_list

    db.commit()
    db.refresh(tx)
    return {
        "status": "confirmed",
        "transaction_id": tx.id,
        "new_status": tx.status,
        "message": f"Transaction {tx.id} confirmed and executed in simulation"
    }

@router.post("/{id}/reject")
def reject_payment(id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {id} not found")

    if tx.status != "PENDING_VERIFICATION":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject transaction with status '{tx.status}'. Only PENDING_VERIFICATION transactions can be rejected."
        )

    tx.status = "REJECTED"
    trace = db.query(DecisionTrace).filter(DecisionTrace.transaction_id == tx.id).first()
    if trace:
        reasons_list = list(trace.reasons or [])
        reasons_list.append("Payment rejected by user during security verification")
        trace.reasons = reasons_list

    db.commit()
    db.refresh(tx)
    return {
        "status": "rejected",
        "transaction_id": tx.id,
        "new_status": tx.status,
        "message": f"Transaction {tx.id} rejected by user"
    }

@router.get("", response_model=List[TransactionResponse])
def list_payments(db: Session = Depends(get_db)):
    return db.query(Transaction).order_by(Transaction.timestamp.desc(), Transaction.id.desc()).all()

@router.get("/{id}/trace")
def get_payment_trace(id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {id} not found")

    trace = db.query(DecisionTrace).filter(DecisionTrace.transaction_id == id).first()
    if not trace:
        raise HTTPException(status_code=404, detail=f"Decision trace for transaction {id} not found")

    return {
        "id": trace.id,
        "transaction_id": trace.transaction_id,
        "transaction": {
            "id": tx.id,
            "recipient": tx.recipient,
            "amount": tx.amount,
            "category": tx.category,
            "purpose": tx.purpose,
            "status": tx.status,
            "decision": tx.decision,
            "timestamp": tx.timestamp.isoformat()
        },
        "decision": trace.decision,
        "reasons": trace.reasons,
        "rules_evaluated": trace.rules_evaluated,
        "intent_evaluation": trace.intent_evaluation,
        "policy_evaluation": trace.policy_evaluation,
        "behavior_signals": trace.behavior_signals,
        "cash_flow_impact": trace.cash_flow_impact,
        "raw_input": trace.raw_input,
        "created_at": trace.created_at.isoformat()
    }
