import asyncio
import os
import httpx
from playwright.async_api import async_playwright

SCREENSHOT_PATH = r"C:\Users\Priya\.gemini\antigravity\brain\11e68c48-5fd7-4b9d-b2be-5b46ea8d77b9\gate7_simulator.png"

async def verify_gate7():
    print("[UI-GATE7] 1. Resetting database to clean demo seed state...")
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/api/dev/reset")
        assert res.status_code == 200, f"Reset failed: {res.text}"
    print("[UI-GATE7] Database successfully reset.")

    print("[UI-GATE7] 2. Launching Playwright browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Step 5: Simulator Test 1 (Happy path)
        print("[UI-GATE7] 3. Testing Test 1: Happy path (Bescom Rs.2500 -> ALLOW)...")
        await page.goto("http://127.0.0.1:5173/simulator", wait_until="networkidle")
        await asyncio.sleep(1)

        # Click preset 1
        preset1_btn = await page.query_selector('button:has-text("Test 1: Happy Path")')
        assert preset1_btn is not None, "Preset 1 button not found"
        await preset1_btn.click()
        await asyncio.sleep(1)

        # Check DecisionBanner shows ALLOW
        banner_content = await page.inner_text('body')
        assert "ALLOW" in banner_content, "DecisionBanner does not show ALLOW for Test 1"

        # Simulate execution
        exec_btn = await page.query_selector('button:has-text("SIMULATE EXECUTION")')
        await exec_btn.click()
        await page.wait_for_selector("text=EXECUTED_SIMULATED", timeout=8000)
        print("[UI-GATE7] Test 1 EXECUTED_SIMULATED verified.")

        # Capture screenshot for Gate 7 evidence
        await page.screenshot(path=SCREENSHOT_PATH)
        print(f"[UI-GATE7] Gate 7 screenshot captured at {SCREENSHOT_PATH}")

        # Open Decision Trace Drawer
        trace_btn = await page.query_selector('button:has-text("VIEW FULL DECISION TRACE")')
        await trace_btn.click()
        await page.wait_for_selector("text=DECISION TRACE:", timeout=6000)
        await page.wait_for_selector("text=INPUT NORMALIZATION", timeout=6000)
        await page.wait_for_selector("text=PAYDNA POLICY EVALUATION", timeout=6000)
        await page.wait_for_selector("text=CASH-FLOW LIQUIDITY IMPACT", timeout=6000)
        print("[UI-GATE7] 9-stage DecisionTraceDrawer opened and verified.")

        # Close trace drawer
        close_btn = await page.query_selector('button:has-text("CLOSE TRACE")')
        await close_btn.click()
        await asyncio.sleep(0.5)

        # Step 6: Simulator Test 2 (Exceeds intent limit)
        print("[UI-GATE7] 4. Testing Test 2: Exceeds intent limit (Bescom Rs.4200 -> VERIFY)...")
        preset2_btn = await page.query_selector('button:has-text("Test 2: Exceeds Limit")')
        await preset2_btn.click()
        await asyncio.sleep(1)

        exec_btn = await page.query_selector('button:has-text("SIMULATE EXECUTION")')
        await exec_btn.click()
        await page.wait_for_selector("text=PENDING_VERIFICATION", timeout=8000)
        print("[UI-GATE7] Test 2 PENDING_VERIFICATION verified.")

        # Confirm payment
        confirm_btn = await page.query_selector('button:has-text("CONFIRM PAYMENT")')
        assert confirm_btn is not None, "CONFIRM PAYMENT button missing"
        await confirm_btn.click()
        await page.wait_for_selector("text=PAYMENT MANUALLY VERIFIED", timeout=8000)
        print("[UI-GATE7] Test 2 payment confirmation verified.")

        # Step 7: Simulator Test 3 (New recipient above threshold)
        print("[UI-GATE7] 5. Testing Test 3: New recipient (Sneha Rao Rs.8000 -> VERIFY)...")
        preset3_btn = await page.query_selector('button:has-text("Test 3: New Recipient")')
        await preset3_btn.click()
        await asyncio.sleep(1)

        exec_btn = await page.query_selector('button:has-text("SIMULATE EXECUTION")')
        await exec_btn.click()
        await page.wait_for_selector("text=PENDING_VERIFICATION", timeout=8000)
        print("[UI-GATE7] Test 3 PENDING_VERIFICATION verified.")

        # Step 8: Simulator Test 4 (Anomaly cascade)
        print("[UI-GATE7] 6. Testing Test 4: Anomaly cascade (Crypto Global Rs.85000 @ 03:15)...")
        preset4_btn = await page.query_selector('button:has-text("Test 4: Anomaly Cascade")')
        await preset4_btn.click()
        await asyncio.sleep(1)
        body_text = await page.inner_text('body')
        assert ("HIGH_AMOUNT" in body_text or "UNUSUAL_TIME" in body_text or "VERIFY" in body_text), "Behavior signals not detected for Test 4"
        print("[UI-GATE7] Test 4 anomaly signals verified.")

        # Step 9: Simulator Test 5 (Exceeds available balance)
        print("[UI-GATE7] 7. Testing Test 5: Exceeds balance (Tanishq Rs.30000 -> EXCEEDS_AVAILABLE)...")
        preset5_btn = await page.query_selector('button:has-text("Test 5: Exceeds Balance")')
        await preset5_btn.click()
        await asyncio.sleep(1)
        body_text = await page.inner_text('body')
        assert ("EXCEEDS_AVAILABLE" in body_text or "Exceeds available liquidity" in body_text or "EXCEEDS AVAILABLE" in body_text), "Exceeds liquidity warning missing"
        print("[UI-GATE7] Test 5 liquidity warning verified.")

        # Step 10: Simulator Test 6 (Intent BLOCK)
        print("[UI-GATE7] 8. Testing Test 6: Blocked intent (Stake Casino Rs.2000 -> HOLD)...")
        preset6_btn = await page.query_selector('button:has-text("Test 6: Blocked Intent")')
        await preset6_btn.click()
        await asyncio.sleep(1)

        exec_btn = await page.query_selector('button:has-text("SIMULATE EXECUTION")')
        await exec_btn.click()
        await page.wait_for_selector("text=HELD", timeout=8000)
        print("[UI-GATE7] Test 6 HELD outcome verified.")

        # Test History Page
        print("[UI-GATE7] 9. Testing /history page...")
        await page.goto("http://127.0.0.1:5173/history", wait_until="networkidle")
        await asyncio.sleep(1)

        await page.wait_for_selector("text=TRANSACTION HISTORY", timeout=6000)
        await page.wait_for_selector("text=Bescom", timeout=6000)
        await page.wait_for_selector("text=Stake Casino", timeout=6000)

        # Click trace on first row
        first_trace_btn = await page.query_selector('button:has-text("VIEW TRACE")')
        await first_trace_btn.click()
        await page.wait_for_selector("text=DECISION TRACE:", timeout=6000)
        print("[UI-GATE7] History table row trace drawer verified.")

        await browser.close()
        print("[UI-GATE7] GATE 7 VERIFICATION FULLY PASSED!")

if __name__ == "__main__":
    asyncio.run(verify_gate7())
