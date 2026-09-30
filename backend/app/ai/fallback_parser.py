"""
Secure Deterministic AI Fallback Parser (Pure Python, Zero External Dependencies)
Parses natural language intents and policies into structured Pydantic schemas.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from app.schemas import IntentDraft, PolicyDraft

# Regex for numbers with k, commas, ₹, Rs, INR
NUM_REGEX = re.compile(r'(?:₹|rs\.?|inr)?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)\s*(k)?\b', re.IGNORECASE)

def extract_amounts(text: str) -> List[int]:
    amounts = []
    for match in NUM_REGEX.finditer(text):
        val_str = match.group(1).replace(",", "")
        try:
            val = int(val_str)
            if match.group(2) and match.group(2).lower() == 'k':
                val *= 1000
            if 1 <= val <= 1_000_000_000:
                amounts.append(val)
        except ValueError:
            pass
    return amounts

def extract_day_of_month(text: str) -> Optional[int]:
    match = re.search(r'\b([1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?\s*(?:day|of\s+the\s+month|\b)', text, re.IGNORECASE)
    if match:
        try:
            day = int(match.group(1))
            if 1 <= day <= 31:
                return day
        except ValueError:
            pass
    return None

def parse_intent_fallback(text: str) -> IntentDraft:
    t = text.lower()
    amounts = extract_amounts(text)
    day = extract_day_of_month(text)

    # 1. Recipient and Category keyword mapping
    recipient = None
    category = "General"
    purpose = "Automated Payment Intent"

    if "rent" in t:
        recipient = "Landlord"
        category = "Rent"
        purpose = "Monthly Apartment Rent"
    elif "electricity" in t or "power" in t or "bescom" in t or "tneb" in t:
        recipient = "Bescom"
        category = "Utilities"
        purpose = "Electricity Bill"
    elif "water" in t:
        recipient = "Water Board"
        category = "Utilities"
        purpose = "Water Utility Bill"
    elif "internet" in t or "wifi" in t or "broadband" in t or "fibernet" in t:
        recipient = "ACT Fibernet"
        category = "Internet"
        purpose = "Internet Provider Bill"
    elif "netflix" in t or "subscription" in t or "spotify" in t:
        recipient = "Netflix"
        category = "Entertainment"
        purpose = "Digital Subscription"
    elif "mother" in t or "mom" in t:
        recipient = "Mother"
        category = "Family"
        purpose = "Transfer to Mother"
    elif "father" in t or "dad" in t or "parent" in t:
        recipient = "Family"
        category = "Family"
        purpose = "Family Support Transfer"
    elif "food" in t or "grocery" in t or "groceries" in t:
        recipient = "Big Bazaar"
        category = "Food"
        purpose = "Food and Groceries"
    elif "travel" in t or "cab" in t or "uber" in t or "ola" in t:
        recipient = "Uber"
        category = "Travel"
        purpose = "Transportation Fare"
    elif "shopping" in t or "amazon" in t:
        recipient = "Amazon"
        category = "Shopping"
        purpose = "Shopping Purchase"

    # 2. Trigger
    trigger = "SALARY_RECEIVED" if ("salary" in t) else "NONE"

    # 3. Action
    if "block" in t or "never pay" in t or "prevent" in t:
        action = "BLOCK"
    elif "ask" in t or "confirm" in t or "verify" in t:
        action = "ASK_FIRST"
    else:
        action = "AUTO_PAY"

    # 4. Frequency
    if "week" in t:
        frequency = "WEEKLY"
    elif "once" in t or "one-time" in t:
        frequency = "ONCE"
    else:
        frequency = "MONTHLY"

    # 5. Amount and Conditions
    amount = None
    max_amount = None
    conditions = []

    # Check for conditional keywords like below / under / at most / max / up to
    has_cap = any(w in t for w in ["below", "under", "at most", "atmost", "less than", "up to", "max", "capped"])

    if amounts:
        primary_amt = amounts[0]
        if has_cap:
            max_amount = primary_amt
            conditions.append({
                "field": "bill_amount",
                "operator": "<=",
                "value": float(primary_amt)
            })
        else:
            amount = primary_amt
            conditions.append({
                "field": "amount",
                "operator": "==",
                "value": float(primary_amt)
            })

    # Check for percentage increase condition: "increases by more than N percent"
    pct_match = re.search(r'increase[s]?\s*(?:by\s+more\s+than)?\s*([0-9]+)\s*%', t)
    if pct_match:
        pct_val = float(pct_match.group(1))
        conditions.append({
            "field": "bill_increase_pct",
            "operator": "<=",
            "value": pct_val
        })

    return IntentDraft(
        purpose=purpose,
        recipient=recipient,
        category=category,
        amount=amount,
        max_amount=max_amount,
        currency="INR",
        frequency=frequency,
        day_of_month=day,
        trigger=trigger,
        action=action,
        conditions=conditions
    )

def parse_policy_fallback(text: str) -> PolicyDraft:
    t = text.lower()
    amounts = extract_amounts(text)
    threshold_or_limit = amounts[0] if amounts else 5000

    # Determine action: HOLD vs VERIFY
    action = "HOLD" if ("hold" in t or "block" in t) else "VERIFY"

    # Check NEW_RECIPIENT_LIMIT
    if "new recipient" in t or "first time" in t or "unknown recipient" in t:
        return PolicyDraft(
            policy_type="NEW_RECIPIENT_LIMIT",
            threshold=threshold_or_limit,
            action=action,
            description=f"Require verification for payments over ₹{threshold_or_limit:,} to new recipients"
        )

    # Check PERIOD_LIMIT (week or month)
    is_period = ("per week" in t or "weekly" in t or "per month" in t or "monthly" in t or "/week" in t or "/month" in t)
    period = "WEEK" if ("week" in t) else "MONTH"

    if is_period or "limit" in t:
        scope = "CATEGORY"
        scope_value = "Shopping"

        if "mother" in t or "mom" in t:
            scope = "RECIPIENT"
            scope_value = "Mother"
        elif "family" in t or "parents" in t:
            scope = "CATEGORY"
            scope_value = "Family"
        elif "food" in t or "grocery" in t:
            scope = "CATEGORY"
            scope_value = "Food"
        elif "shopping" in t:
            scope = "CATEGORY"
            scope_value = "Shopping"
        elif "travel" in t:
            scope = "CATEGORY"
            scope_value = "Travel"

        return PolicyDraft(
            policy_type="PERIOD_LIMIT",
            scope=scope,
            scope_value=scope_value,
            period=period,
            limit=threshold_or_limit,
            action=action,
            description=f"Require verification if {period.lower()}ly {scope_value} spend exceeds ₹{threshold_or_limit:,}"
        )

    # Default to MAX_TRANSACTION_AMOUNT
    return PolicyDraft(
        policy_type="MAX_TRANSACTION_AMOUNT",
        threshold=threshold_or_limit,
        action=action,
        description=f"Require verification for any single transaction above ₹{threshold_or_limit:,}"
    )
