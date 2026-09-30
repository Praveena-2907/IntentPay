"""
Parser Service: Orchestrates Gemini parsing with automatic failover to deterministic fallback parser.
Never raises; always returns valid draft and source.
"""

import logging
from typing import Dict, Any, List
from app.config import settings
from app.schemas import (
    IntentDraft, PolicyDraft,
    IntentParseResponse, PolicyParseResponse
)
from app.ai.gemini_client import call_gemini_raw, INTENT_SYSTEM_PROMPT, POLICY_SYSTEM_PROMPT
from app.ai.fallback_parser import parse_intent_fallback, parse_policy_fallback
from app.engines.conflict import find_conflicts

logger = logging.getLogger("intentpay.parser")

FALLBACK_BADGE_WARNING = "AI UNAVAILABLE — USING SECURE FALLBACK PARSER"

async def parse_intent_text(text: str, existing_policies: List[Dict[str, Any]] = None) -> IntentParseResponse:
    if existing_policies is None:
        existing_policies = []

    draft = None
    source = "fallback"
    warnings = []

    # Attempt Gemini LLM parsing if key is available
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Attempting Gemini AI intent parsing...")
            raw_data = await call_gemini_raw(text, INTENT_SYSTEM_PROMPT)
            draft = IntentDraft(**raw_data)
            source = "gemini"
        except Exception as e:
            logger.warning(f"Gemini intent parsing failed ({e}); falling back to deterministic parser")
            warnings.append(FALLBACK_BADGE_WARNING)
            draft = None
    else:
        warnings.append(FALLBACK_BADGE_WARNING)

    # Use fallback parser if Gemini failed or was unconfigured
    if draft is None:
        try:
            draft = parse_intent_fallback(text)
            source = "fallback"
        except Exception as e:
            logger.error(f"Fallback parser critical error: {e}")
            # Ensure an absolutely safe default draft
            draft = IntentDraft(
                purpose="Payment Intent",
                category="General",
                amount=None,
                action="AUTO_PAY"
            )

    # Check for conflicts against existing policies
    intent_dict = draft.model_dump()
    intent_dict["status"] = "ACTIVE"
    intent_dict["id"] = "DRAFT-INTENT"
    conflicts = find_conflicts([intent_dict], existing_policies)

    return IntentParseResponse(
        draft=draft,
        source=source,
        warnings=warnings,
        conflicts=conflicts
    )

async def parse_policy_text(text: str, existing_intents: List[Dict[str, Any]] = None) -> PolicyParseResponse:
    if existing_intents is None:
        existing_intents = []

    draft = None
    source = "fallback"
    warnings = []

    # Attempt Gemini LLM parsing if key is available
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Attempting Gemini AI policy parsing...")
            raw_data = await call_gemini_raw(text, POLICY_SYSTEM_PROMPT)
            draft = PolicyDraft(**raw_data)
            source = "gemini"
        except Exception as e:
            logger.warning(f"Gemini policy parsing failed ({e}); falling back to deterministic parser")
            warnings.append(FALLBACK_BADGE_WARNING)
            draft = None
    else:
        warnings.append(FALLBACK_BADGE_WARNING)

    # Use fallback parser if Gemini failed or was unconfigured
    if draft is None:
        try:
            draft = parse_policy_fallback(text)
            source = "fallback"
        except Exception as e:
            logger.error(f"Fallback policy parser critical error: {e}")
            draft = PolicyDraft(
                policy_type="MAX_TRANSACTION_AMOUNT",
                threshold=10000,
                action="VERIFY",
                description="Require verification for transactions above ₹10,000"
            )

    # Check for conflicts against existing intents
    policy_dict = draft.model_dump()
    policy_dict["status"] = "ACTIVE"
    policy_dict["id"] = "DRAFT-POLICY"
    conflicts = find_conflicts(existing_intents, [policy_dict])

    return PolicyParseResponse(
        draft=draft,
        source=source,
        warnings=warnings,
        conflicts=conflicts
    )
