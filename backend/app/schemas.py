from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# ----------------- Condition Schema -----------------
class IntentCondition(BaseModel):
    field: Literal["amount", "bill_amount", "bill_increase_pct"]
    operator: Literal["<=", "<", ">=", ">", "=="]
    value: float

# ----------------- User Schemas -----------------
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    monthly_income: int
    current_balance: int
    upcoming_expenses: int
    available_balance: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Recipient Schemas -----------------
class RecipientSchema(BaseModel):
    id: str
    name: str
    is_verified: bool
    category_hint: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Intent Schemas -----------------
class IntentDraft(BaseModel):
    purpose: str = Field(..., min_length=1)
    recipient: Optional[str] = None
    category: str = Field(..., min_length=1)
    amount: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    max_amount: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    currency: str = "INR"
    frequency: Literal["ONCE", "WEEKLY", "MONTHLY"] = "MONTHLY"
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    trigger: Literal["NONE", "SALARY_RECEIVED"] = "NONE"
    action: Literal["AUTO_PAY", "ASK_FIRST", "BLOCK"] = "AUTO_PAY"
    conditions: List[IntentCondition] = Field(default_factory=list)

    @field_validator("recipient", mode="before")
    def clean_recipient(cls, v):
        if isinstance(v, str):
            val = " ".join(v.split()).strip()
            return val if val else None
        return v

    @field_validator("category", mode="before")
    def clean_category(cls, v):
        if isinstance(v, str):
            val = v.strip()
            return val if val else "General"
        return "General"

class IntentCreate(IntentDraft):
    confirmed: bool = Field(False, description="Must be true to persist")

class IntentUpdate(BaseModel):
    purpose: Optional[str] = None
    recipient: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    max_amount: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    frequency: Optional[Literal["ONCE", "WEEKLY", "MONTHLY"]] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    trigger: Optional[Literal["NONE", "SALARY_RECEIVED"]] = None
    action: Optional[Literal["AUTO_PAY", "ASK_FIRST", "BLOCK"]] = None
    conditions: Optional[List[IntentCondition]] = None
    status: Optional[Literal["ACTIVE", "PAUSED", "DELETED"]] = None

class IntentResponse(IntentDraft):
    id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Policy Schemas -----------------
class PolicyDraft(BaseModel):
    policy_type: Literal["MAX_TRANSACTION_AMOUNT", "NEW_RECIPIENT_LIMIT", "PERIOD_LIMIT"]
    threshold: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    scope: Optional[Literal["CATEGORY", "RECIPIENT"]] = None
    scope_value: Optional[str] = None
    period: Optional[Literal["WEEK", "MONTH"]] = None
    limit: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    action: Literal["VERIFY", "HOLD"] = "VERIFY"
    description: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_policy_rules(self):
        if self.policy_type == "MAX_TRANSACTION_AMOUNT":
            if not self.threshold:
                raise ValueError("threshold is required for MAX_TRANSACTION_AMOUNT")
        elif self.policy_type == "NEW_RECIPIENT_LIMIT":
            if not self.threshold:
                raise ValueError("threshold is required for NEW_RECIPIENT_LIMIT")
        elif self.policy_type == "PERIOD_LIMIT":
            if not self.scope or not self.scope_value or not self.period or not self.limit:
                raise ValueError("scope, scope_value, period, and limit are required for PERIOD_LIMIT")
        return self

class PolicyCreate(PolicyDraft):
    confirmed: bool = Field(False, description="Must be true to persist")

class PolicyUpdate(BaseModel):
    threshold: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    scope: Optional[Literal["CATEGORY", "RECIPIENT"]] = None
    scope_value: Optional[str] = None
    period: Optional[Literal["WEEK", "MONTH"]] = None
    limit: Optional[int] = Field(None, ge=1, le=1_000_000_000)
    action: Optional[Literal["VERIFY", "HOLD"]] = None
    description: Optional[str] = None
    status: Optional[Literal["ACTIVE", "PAUSED", "DELETED"]] = None

class PolicyResponse(PolicyDraft):
    id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- AI Parsing Schemas -----------------
class IntentParseRequest(BaseModel):
    text: str = Field(..., min_length=1)

class PolicyParseRequest(BaseModel):
    text: str = Field(..., min_length=1)

class IntentParseResponse(BaseModel):
    draft: IntentDraft
    source: Literal["gemini", "fallback"]
    warnings: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)

class PolicyParseResponse(BaseModel):
    draft: PolicyDraft
    source: Literal["gemini", "fallback"]
    warnings: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)

# ----------------- Payment Schemas -----------------
class PaymentRequest(BaseModel):
    recipient: str = Field(..., min_length=1)
    amount: int = Field(..., ge=1, le=1_000_000_000)
    category: str = Field(..., min_length=1)
    purpose: Optional[str] = None
    client_request_id: Optional[str] = None
    is_known_recipient: Optional[bool] = None
    bill_amount: Optional[int] = None
    timestamp: Optional[datetime] = None

    @field_validator("recipient", mode="before")
    def clean_recipient(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Recipient cannot be empty or whitespace only")
        return " ".join(v.split()).strip()

    @field_validator("amount", mode="before")
    def validate_amount(cls, v):
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError("Amount must be a valid integer")
        if isinstance(v, float) and not v.is_integer():
            raise ValueError("Amount must be an integer (no paise allowed)")
        v = int(v)
        if v < 1:
            raise ValueError("Amount must be at least ₹1")
        if v > 1_000_000_000:
            raise ValueError("Amount cannot exceed ₹1,000,000,000")
        return v

class RuleEvaluation(BaseModel):
    id: str
    label: str
    result: Literal["PASS", "FAIL", "WARN"]
    detail: str

class DecisionResponse(BaseModel):
    decision: Literal["ALLOW", "VERIFY", "HOLD"]
    reasons: List[str]
    explanation: str
    rules_evaluated: List[RuleEvaluation]
    pipeline_status: Dict[str, str] # e.g. {"intent": "PASS", "paydna": "FAIL", "behavior": "WARN", "decision": "VERIFY"}
    cash_flow_impact: Dict[str, Any]
    behavior_signals: List[Dict[str, Any]]
    intent_evaluation: Dict[str, Any]
    policy_evaluation: Dict[str, Any]

class TransactionResponse(BaseModel):
    id: str
    client_request_id: Optional[str] = None
    recipient: str
    amount: int
    currency: str
    category: str
    purpose: Optional[str] = None
    status: Literal["EXECUTED_SIMULATED", "PENDING_VERIFICATION", "HELD", "REJECTED"]
    decision: Literal["ALLOW", "VERIFY", "HOLD"]
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DecisionTraceResponse(BaseModel):
    id: str
    transaction_id: str
    decision: Literal["ALLOW", "VERIFY", "HOLD"]
    reasons: List[str]
    rules_evaluated: List[Dict[str, Any]]
    intent_evaluation: Dict[str, Any]
    policy_evaluation: Dict[str, Any]
    behavior_signals: List[Dict[str, Any]]
    cash_flow_impact: Dict[str, Any]
    raw_input: Dict[str, Any]
    explanation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Impact & What-If -----------------
class PaymentImpactRequest(BaseModel):
    amount: int = Field(..., ge=1, le=1_000_000_000)

class WhatIfRequest(BaseModel):
    payment_amount: int = Field(..., ge=0)
    monthly_income: Optional[int] = None
    monthly_expense: Optional[int] = None
    loan_amount: Optional[int] = Field(0, description="Monthly EMI")
    recurring_expense_delta: Optional[int] = Field(0, description="Change in recurring expenses")

class SuggestionResponse(BaseModel):
    id: str
    recipient: str
    suggested_amount: int
    frequency: str
    day_of_month: Optional[int]
    category: str
    reason: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
