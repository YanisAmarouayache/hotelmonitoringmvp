import sys
import asyncio

# Fix spécifique pour Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # ← headless pour éviter erreurs GUI
        page = await browser.new_page()
        await page.goto("https://example.com")
        print(await page.title())
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
