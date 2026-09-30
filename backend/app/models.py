import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default="usr_demo")
    name = Column(String, nullable=False, default="Demo User")
    email = Column(String, nullable=False, default="demo@intentpay.local")
    monthly_income = Column(Integer, nullable=False, default=50000)
    current_balance = Column(Integer, nullable=False, default=36000)
    upcoming_expenses = Column(Integer, nullable=False, default=15500)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    is_verified = Column(Boolean, default=True)
    category_hint = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id = Column(String, primary_key=True, index=True)
    purpose = Column(String, nullable=False)
    recipient = Column(String, nullable=True, index=True)
    category = Column(String, nullable=False, index=True)
    amount = Column(Integer, nullable=True)
    max_amount = Column(Integer, nullable=True)
    currency = Column(String, default="INR")
    frequency = Column(String, nullable=False, default="MONTHLY") # ONCE, WEEKLY, MONTHLY
    day_of_month = Column(Integer, nullable=True) # 1-31
    trigger = Column(String, default="NONE") # NONE, SALARY_RECEIVED
    action = Column(String, default="AUTO_PAY") # AUTO_PAY, ASK_FIRST, BLOCK
    conditions = Column(JSON, default=list) # [{field, operator, value}]
    status = Column(String, default="ACTIVE", index=True) # ACTIVE, PAUSED, DELETED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class PaymentPolicy(Base):
    __tablename__ = "payment_policies"

    id = Column(String, primary_key=True, index=True) # e.g. PD-001
    policy_type = Column(String, nullable=False) # MAX_TRANSACTION_AMOUNT, NEW_RECIPIENT_LIMIT, PERIOD_LIMIT
    threshold = Column(Integer, nullable=True)
    scope = Column(String, nullable=True) # CATEGORY, RECIPIENT
    scope_value = Column(String, nullable=True) # e.g. Shopping, Mother
    period = Column(String, nullable=True) # WEEK, MONTH
    limit = Column(Integer, nullable=True)
    action = Column(String, default="VERIFY") # VERIFY, HOLD
    status = Column(String, default="ACTIVE", index=True) # ACTIVE, PAUSED, DELETED
    description = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True) # e.g. TX-0001
    client_request_id = Column(String, nullable=True, unique=True, index=True)
    recipient = Column(String, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default="INR")
    category = Column(String, nullable=False, index=True)
    purpose = Column(String, nullable=True)
    status = Column(String, nullable=False, default="EXECUTED_SIMULATED", index=True) # EXECUTED_SIMULATED, PENDING_VERIFICATION, HELD, REJECTED
    decision = Column(String, nullable=False) # ALLOW, VERIFY, HOLD
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    trace = relationship("DecisionTrace", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

class DecisionTrace(Base):
    __tablename__ = "decision_traces"

    id = Column(String, primary_key=True, index=True) # e.g. TR-0001
    transaction_id = Column(String, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    decision = Column(String, nullable=False) # ALLOW, VERIFY, HOLD
    reasons = Column(JSON, default=list) # List[str]
    rules_evaluated = Column(JSON, default=list) # List[Dict]
    intent_evaluation = Column(JSON, default=dict)
    policy_evaluation = Column(JSON, default=dict)
    behavior_signals = Column(JSON, default=list)
    cash_flow_impact = Column(JSON, default=dict)
    raw_input = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    transaction = relationship("Transaction", back_populates="trace")

class PaymentSuggestion(Base):
    __tablename__ = "payment_suggestions"

    id = Column(String, primary_key=True, index=True) # e.g. PSG-001
    recipient = Column(String, nullable=False)
    suggested_amount = Column(Integer, nullable=False)
    frequency = Column(String, default="MONTHLY")
    day_of_month = Column(Integer, nullable=True)
    category = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING", index=True) # PENDING, DISMISSED, ACCEPTED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
