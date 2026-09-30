import asyncio
import pytest
from unittest.mock import patch
from app.ai.parser_service import parse_intent_text, parse_policy_text
from app.ai.fallback_parser import parse_intent_fallback, parse_policy_fallback
from app.config import settings

def test_fallback_intent_without_key():
    # Test 1 & 2 NL sentences
    # T1: "Pay my electricity bill automatically if it is below ₹3000."
    res1 = asyncio.run(parse_intent_text("Pay my electricity bill automatically if it is below ₹3000."))
    assert res1.source == "fallback"
    assert res1.draft.category == "Utilities"
    assert res1.draft.recipient == "Bescom"
    assert res1.draft.max_amount == 3000
    assert res1.draft.action == "AUTO_PAY"
    assert any("AI UNAVAILABLE" in w for w in res1.warnings)

    # T2: "Send my mother ₹10000 every month."
    res2 = asyncio.run(parse_intent_text("Send my mother ₹10000 every month."))
    assert res2.source == "fallback"
    assert res2.draft.recipient == "Mother"
    assert res2.draft.amount == 10000
    assert res2.draft.frequency == "MONTHLY"

def test_fallback_policy_without_key():
    # "Any new recipient above ₹5000 requires confirmation."
    res1 = asyncio.run(parse_policy_text("Any new recipient above ₹5000 requires confirmation."))
    assert res1.source == "fallback"
    assert res1.draft.policy_type == "NEW_RECIPIENT_LIMIT"
    assert res1.draft.threshold == 5000
    assert res1.draft.action == "VERIFY"

    # "Payments above ₹25,000 require verification."
    res2 = asyncio.run(parse_policy_text("Payments above ₹25,000 require verification."))
    assert res2.source == "fallback"
    assert res2.draft.policy_type == "MAX_TRANSACTION_AMOUNT"
    assert res2.draft.threshold == 25000
    assert res2.draft.action == "VERIFY"

def test_mocked_gemini_failures_failover():
    # 1. Mock HTTP 500
    with patch("app.config.settings.GEMINI_API_KEY", "dummy_key"):
        with patch("app.ai.gemini_client.call_gemini_raw", side_effect=RuntimeError("HTTP 500 Internal Error")):
            res = asyncio.run(parse_intent_text("Pay rent ₹15000 automatically."))
            assert res.source == "fallback"
            assert res.draft.category == "Rent"
            assert res.draft.amount == 15000
            assert any("AI UNAVAILABLE" in w for w in res.warnings)

    # 2. Mock Timeout
    with patch("app.config.settings.GEMINI_API_KEY", "dummy_key"):
        with patch("app.ai.gemini_client.call_gemini_raw", side_effect=TimeoutError("Request timed out after 8s")):
            res = asyncio.run(parse_intent_text("Pay rent ₹15000 automatically."))
            assert res.source == "fallback"
            assert res.draft.amount == 15000

    # 3. Mock Malformed JSON / Invalid Pydantic schema
    with patch("app.config.settings.GEMINI_API_KEY", "dummy_key"):
        with patch("app.ai.gemini_client.call_gemini_raw", return_value={"invalid_key": "junk_data"}):
            res = asyncio.run(parse_intent_text("Pay rent ₹15000 automatically."))
            assert res.source == "fallback"
            assert res.draft.category == "Rent"
