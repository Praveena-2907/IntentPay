import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal, Base, engine
from app.models import User, PaymentIntent, PaymentPolicy, Transaction, DecisionTrace, PaymentSuggestion, Recipient
from app.seed import seed_database

client = TestClient(app)

def setup_module(module):
    # Ensure tables and seed exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db, force=True)
    db.close()

def test_user_me_endpoint():
    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Demo User"
    assert data["monthly_income"] == 50000
    assert data["current_balance"] == 36000
    assert data["upcoming_expenses"] == 15500
    assert data["available_balance"] == 20500 # 36000 - 15500

def test_seed_counts_exact():
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        assert user_count == 1

        recipients_count = db.query(Recipient).count()
        assert recipients_count == 10

        intents = db.query(PaymentIntent).filter(PaymentIntent.status == "ACTIVE").all()
        assert len(intents) == 4

        policies = db.query(PaymentPolicy).filter(PaymentPolicy.status == "ACTIVE").all()
        assert len(policies) == 5

        transactions = db.query(Transaction).all()
        assert len(transactions) == 27

        traces = db.query(DecisionTrace).all()
        assert len(traces) == 27

        # Verify outcomes distribution: 21 ALLOW, 5 VERIFY, 1 HOLD
        allow_count = db.query(Transaction).filter(Transaction.decision == "ALLOW").count()
        verify_count = db.query(Transaction).filter(Transaction.decision == "VERIFY").count()
        hold_count = db.query(Transaction).filter(Transaction.decision == "HOLD").count()

        assert allow_count == 21, f"Expected 21 ALLOW, got {allow_count}"
        assert verify_count == 5, f"Expected 5 VERIFY, got {verify_count}"
        assert hold_count == 1, f"Expected 1 HOLD, got {hold_count}"

        suggestions = db.query(PaymentSuggestion).filter(PaymentSuggestion.status == "PENDING").all()
        assert len(suggestions) == 1
    finally:
        db.close()

def test_dev_reset_endpoint():
    response = client.post("/api/dev/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reset_successful"
    assert data["counts"]["intents"] == 4
    assert data["counts"]["policies"] == 5
    assert data["counts"]["transactions"] == 27
    assert data["counts"]["suggestions"] == 1
