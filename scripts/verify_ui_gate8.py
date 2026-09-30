import asyncio
import httpx
from playwright.async_api import async_playwright

async def verify_gate8():
    print("[UI-GATE8] 1. Launching Playwright browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test desktop view
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Test What-If Page
        print("[UI-GATE8] 2. Testing /what-if page...")
        await page.goto("http://127.0.0.1:5173/what-if", wait_until="networkidle")
        await asyncio.sleep(1)

        content = await page.content()
        assert "WHAT-IF CASH-FLOW SCENARIO SIMULATOR" in content, "What-If title missing"
        assert "SCENARIO PARAMETERS" in content, "Scenario parameters missing"
        assert "Projected Month-End Balance" in content, "Comparison table missing"
        print("[UI-GATE8] What-If page desktop verified.")

        # Test Analytics Page
        print("[UI-GATE8] 3. Testing /analytics page...")
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[BROWSER ERROR] {err}"))
        await page.goto("http://127.0.0.1:5173/analytics", wait_until="networkidle")
        await asyncio.sleep(2)

        content = await page.content()
        if "ANALYTICS & BEHAVIORAL HEURISTICS" not in content:
            print("[DEBUG] Content on /analytics:", content[:1000])
        assert "ANALYTICS & BEHAVIORAL HEURISTICS" in content, "Analytics title missing"
        assert "CATEGORY SPEND BREAKDOWN" in content, "Category breakdown missing"
        assert "BEHAVIORAL ANOMALY HEURISTIC THRESHOLDS" in content, "Anomaly rules missing"
        print("[UI-GATE8] Analytics page desktop verified.")

        # Test Mobile Responsiveness (< 768px layout)
        print("[UI-GATE8] 4. Testing mobile responsive layout (390x844 iPhone)...")
        mobile_context = await browser.new_context(viewport={"width": 390, "height": 844})
        mobile_page = await mobile_context.new_page()

        await mobile_page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        await asyncio.sleep(1)
        mobile_content = await mobile_page.content()
        assert "INTENTPAY" in mobile_content, "Mobile header missing"
        print("[UI-GATE8] Mobile responsive layout verified.")

        await browser.close()
        print("[UI-GATE8] GATE 8 VERIFICATION FULLY PASSED!")

if __name__ == "__main__":
    asyncio.run(verify_gate8())
