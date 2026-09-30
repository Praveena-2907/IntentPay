"""
Gemini Client via plain HTTPX REST (No SDK, 8s timeout, JSON response mode)
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("intentpay.gemini")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

INTENT_SYSTEM_PROMPT = """
You are a precise payment intent parsing assistant. Parse the user's natural language payment rule into structured JSON.
Return ONLY valid JSON matching this schema:
{
  "purpose": string (brief description of purpose),
  "recipient": string or null (e.g. "Landlord", "TNEB Electricity", "Netflix", "Mother"),
  "category": string (e.g. "Rent", "Utilities", "Food", "Travel", "Entertainment", "Shopping", "Family"),
  "amount": integer or null (fixed amount in INR rupees if exact),
  "max_amount": integer or null (maximum ceiling amount in INR rupees if conditional/capped),
  "currency": "INR",
  "frequency": "ONCE" | "WEEKLY" | "MONTHLY",
  "day_of_month": integer (1-31) or null,
  "trigger": "NONE" | "SALARY_RECEIVED",
  "action": "AUTO_PAY" | "ASK_FIRST" | "BLOCK",
  "conditions": [
    {"field": "amount" | "bill_amount" | "bill_increase_pct", "operator": "<=" | "<" | ">=" | ">" | "==", "value": number}
  ]
}
Amounts must be integers in INR. Do not include markdown code fences if returning JSON mode.
"""

POLICY_SYSTEM_PROMPT = """
You are a precise security policy parsing assistant. Parse the user's security rule into structured JSON.
Return ONLY valid JSON matching this schema:
{
  "policy_type": "MAX_TRANSACTION_AMOUNT" | "NEW_RECIPIENT_LIMIT" | "PERIOD_LIMIT",
  "threshold": integer or null,
  "scope": "CATEGORY" | "RECIPIENT" | null,
  "scope_value": string or null,
  "period": "WEEK" | "MONTH" | null,
  "limit": integer or null,
  "action": "VERIFY" | "HOLD",
  "description": string (clear summary of the policy rule)
}
Rules:
- For MAX_TRANSACTION_AMOUNT, threshold is required.
- For NEW_RECIPIENT_LIMIT, threshold is required.
- For PERIOD_LIMIT, scope, scope_value, period, and limit are required.
Amounts must be integers in INR.
"""

async def call_gemini_raw(prompt: str, system_prompt: str) -> Dict[str, Any]:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    url = GEMINI_API_URL.format(model=settings.GEMINI_MODEL) + f"?key={api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {response.status_code}: {response.text}")

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned empty candidates")

        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
        # Strip potential markdown code fences just in case
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        return json.loads(clean_text.strip())
