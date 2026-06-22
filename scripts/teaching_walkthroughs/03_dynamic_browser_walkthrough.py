"""Teaching walkthrough: dynamic pages with Playwright.

This script is optional because it requires Playwright and a browser install:
    pip install playwright
    playwright install chromium

Teaching goals:
1. Show why requests may miss JavaScript-rendered content.
2. Use a real browser to collect rendered DOM.
3. Save screenshots as visual audit evidence.
4. Discuss waiting, scrolling, and automation ethics.
"""

# %% 1. Imports and classroom URL

import asyncio
from pathlib import Path

import pandas as pd
import requests


URL = "https://quotes.toscrape.com/js/"
USER_AGENT = "methodsNET-VLOP-course/1.0 dynamic walkthrough"


# %% 2. Fetch with requests first

# This is the "static" view. For JavaScript-heavy pages, it may contain the app
# shell but not the content users see after rendering.
static_response = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
static_response.raise_for_status()

static_html = static_response.text
print("Static HTML characters:", len(static_html))
print("Does static HTML contain quote text?", "The world as we have created it" in static_html)


# %% 3. Define an async browser function

async def collect_rendered_page(url: str):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # In live teaching, change headless=False to let students watch.
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=USER_AGENT)

        # Waiting is a methodological choice. Too short and data may be missing;
        # too long and the script becomes slow or brittle.
        await page.goto(url, wait_until="networkidle")

        # Extract visible quote blocks after JavaScript has rendered them.
        quotes = await page.eval_on_selector_all(
            ".quote",
            """blocks => blocks.map(block => ({
                quote: block.querySelector(".text")?.innerText ?? null,
                author: block.querySelector(".author")?.innerText ?? null,
                tags: Array.from(block.querySelectorAll(".tag")).map(t => t.innerText)
            }))""",
        )

        html = await page.content()
        screenshot = await page.screenshot(full_page=True)
        await browser.close()

    return html, quotes, screenshot


# %% 4. Run the browser collection

rendered_html, quotes, screenshot = asyncio.run(collect_rendered_page(URL))

print("Rendered HTML characters:", len(rendered_html))
print("Quotes extracted:", len(quotes))
print(pd.DataFrame(quotes).head())


# %% 5. Save rendered evidence

outdir = Path("../data") if Path.cwd().name == "teaching_walkthroughs" else Path("data")
raw_dir = outdir / "raw"
processed_dir = outdir / "processed"

raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)

rendered_path = raw_dir / "walkthrough_rendered_quotes.html"
screenshot_path = raw_dir / "walkthrough_rendered_quotes.png"
quotes_path = processed_dir / "walkthrough_rendered_quotes.csv"

rendered_path.write_text(rendered_html, encoding="utf-8")
screenshot_path.write_bytes(screenshot)
pd.DataFrame(quotes).to_csv(quotes_path, index=False)

print("Saved rendered HTML:", rendered_path)
print("Saved screenshot:", screenshot_path)
print("Saved quote table:", quotes_path)


# %% 6. Teaching prompts

questions = [
    "What did requests miss that the rendered browser could see?",
    "What evidence does the screenshot provide that a CSV cannot?",
    "When is browser automation justified instead of an API?",
    "How could infinite scroll introduce missingness?",
    "What would count as bypassing controls rather than observing a public interface?",
]

for question in questions:
    print("-", question)
