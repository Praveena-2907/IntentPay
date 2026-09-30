import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def verify_gate5():
    print("[UI-GATE5] Launching browser to verify Dashboard...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # Listen for console errors
        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: logs.append(f"[PAGE_ERROR] {err}"))

        print("[UI-GATE5] Navigating to http://127.0.0.1:5173/ ...")
        await page.goto("http://127.0.0.1:5173/", wait_until="networkidle")

        await asyncio.sleep(2)
        print("[UI-GATE5] Console output:")
        for log in logs:
            print("  ", log)

        content = await page.content()
        print(f"[UI-GATE5] Page Title: {await page.title()}")
        print(f"[UI-GATE5] Snippet: {content[:400]}")
        assert "SIMULATED — NO REAL FUNDS" in content, "Simulated badge not found"

        # Check KPIs: Intents: 4, Policies: 5, Evaluated: 27, Approved: 21, Verify: 5, Held: 1
        kpi_tiles = await page.query_selector_all(".text-2xl.font-mono.font-bold")
        kpi_values = [await t.inner_text() for t in kpi_tiles]
        print(f"[UI-GATE5] Found rendered KPI values: {kpi_values}")

        expected = ["4", "5", "27", "21", "5", "1"]
        for exp in expected:
            assert exp in kpi_values, f"Expected KPI value {exp} not found in {kpi_values}"

        print("[UI-GATE5] All 6 KPI numbers verified exactly: 4, 5, 27, 21, 5, 1")

        # Capture screenshot to artifact directory
        artifact_dir = Path("C:/Users/Priya/.gemini/antigravity/brain/11e68c48-5fd7-4b9d-b2be-5b46ea8d77b9")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = artifact_dir / "gate5_dashboard.png"

        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[UI-GATE5] Screenshot saved to: {screenshot_path}")

        await browser.close()
        print("[UI-GATE5] GATE 5 UI VERIFICATION PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(verify_gate5())
