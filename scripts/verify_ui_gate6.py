import asyncio
from playwright.async_api import async_playwright

async def verify_gate6():
    print("[UI-GATE6] Launching browser for Gate 6 Verification...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # 1. Test Intents Page
        print("[UI-GATE6] 1. Navigating to /intents ...")
        await page.goto("http://127.0.0.1:5173/intents", wait_until="networkidle")
        await asyncio.sleep(1)

        content = await page.content()
        assert "PAYMENT INTENT MANAGER" in content, "Intents title missing"

        # Type preset prompt
        input_elem = await page.query_selector('input[type="text"]')
        await input_elem.fill("Pay my broadband bill automatically if it is under ₹1200.")
        parse_btn = await page.query_selector('button:has-text("PARSE INTENT")')
        await parse_btn.click()

        # Wait for draft card
        await page.wait_for_selector("text=STRUCTURED INTENT DRAFT", timeout=6000)
        print("[UI-GATE6] Draft parsed successfully.")

        # Confirm & Persist
        confirm_btn = await page.query_selector('button:has-text("CONFIRM & PERSIST TO DB")')
        await confirm_btn.click()

        # Wait for success feedback or intent in list
        await page.wait_for_selector("text=Internet Provider Bill", timeout=6000)
        print("[UI-GATE6] Intent created and visible in table.")

        # Hard refresh to verify persistence
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(1)
        refreshed_content = await page.content()
        assert "Internet Provider Bill" in refreshed_content, "Intent did not persist after hard refresh!"
        print("[UI-GATE6] Persistence after hard refresh VERIFIED.")

        # 2. Test Policies Page (Duplicate Prevention 409)
        print("[UI-GATE6] 2. Navigating to /policies ...")
        await page.goto("http://127.0.0.1:5173/policies", wait_until="networkidle")
        await asyncio.sleep(1)

        pol_input = await page.query_selector('input[type="text"]')
        await pol_input.fill("Any new recipient above ₹5000 requires confirmation.")
        pol_btn = await page.query_selector('button:has-text("PARSE POLICY")')
        await pol_btn.click()

        await page.wait_for_selector("text=STRUCTURED POLICY DRAFT", timeout=6000)
        pol_confirm_btn = await page.query_selector('button:has-text("CONFIRM & PERSIST TO DB")')
        await pol_confirm_btn.click()

        # Wait for duplicate policy 409 feedback
        await page.wait_for_selector("text=PD-001", timeout=6000)
        print("[UI-GATE6] Duplicate policy prevention (409) friendly feedback VERIFIED.")

        # 3. Test Constitution Page
        print("[UI-GATE6] 3. Navigating to /constitution ...")
        await page.goto("http://127.0.0.1:5173/constitution", wait_until="networkidle")
        await asyncio.sleep(1)

        const_content = await page.content()
        assert "ARTICLE I" in const_content, "Constitution Article I missing"
        assert "ARTICLE II" in const_content, "Constitution Article II missing"
        assert "ARTICLE III" in const_content, "Constitution Article III missing"
        assert "ARTICLE IV" in const_content, "Constitution Article IV missing"
        print("[UI-GATE6] Constitution articles I - IV VERIFIED.")

        await browser.close()
        print("[UI-GATE6] GATE 6 VERIFICATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(verify_gate6())
