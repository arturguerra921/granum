import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:8050/")
        await page.wait_for_timeout(2000)

        # Go to results tab (by id, it might be main-tabs)
        # We probably can't get to results tab without filling data and running model,
        # but let's see if we can just verify the columns by triggering the callback manually or
        # inspecting the results page if there are default results.
        # Actually, let's just make a small test to verify `src/view/view.py` callback is correct.

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
