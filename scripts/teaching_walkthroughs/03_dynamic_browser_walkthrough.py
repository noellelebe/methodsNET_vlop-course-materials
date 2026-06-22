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
# This user agent is attached to both the simple requests call and the browser
# page. Keeping it consistent helps compare the two access routes.
USER_AGENT = "methodsNET-VLOP-course/1.0 dynamic walkthrough"


# %% 2. Fetch with requests first

# This is the "static" view. For JavaScript-heavy pages, it may contain the app
# shell but not the content users see after rendering.
static_response = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
static_response.raise_for_status()

static_html = static_response.text
print("Static HTML characters:", len(static_html))
# This test searches the raw HTML for text that should appear after JavaScript
# renders the quotes. If it prints False, requests did not receive the user-
# visible quote text in the initial server response.
print("Does static HTML contain quote text?", "The world as we have created it" in static_html)


# %% 3. Define an async browser function

async def collect_rendered_page(url: str):
    # Playwright is imported inside the function so the rest of the file can be
    # read even on machines where Playwright has not yet been installed.
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        # In live teaching, change headless=False to let students watch.
        # chromium.launch() starts a browser process controlled by Python.
        browser = await p.chromium.launch(headless=True)
        # new_page() opens a browser tab. user_agent makes the browser request
        # identify itself with the same teaching string used above.
        page = await browser.new_page(user_agent=USER_AGENT)

        # Waiting is a methodological choice. Too short and data may be missing;
        # too long and the script becomes slow or brittle.
        # wait_until="networkidle" waits until network activity has quieted down,
        # which is often useful after JavaScript-driven loading.
        await page.goto(url, wait_until="networkidle")

        # Extract visible quote blocks after JavaScript has rendered them.
        quotes = await page.eval_on_selector_all(
            # ".quote" selects all rendered elements with class="quote".
            ".quote",
            # The string below is JavaScript executed inside the browser page.
            # blocks is the list of .quote elements. For each block:
            # - querySelector(".text") finds the quote text element;
            # - querySelector(".author") finds the author element;
            # - querySelectorAll(".tag") finds all tag elements;
            # - ?. means "if this element exists, read from it; otherwise null";
            # - ?? null replaces missing values with null for Python.
            """blocks => blocks.map(block => ({
                quote: block.querySelector(".text")?.innerText ?? null,
                author: block.querySelector(".author")?.innerText ?? null,
                tags: Array.from(block.querySelectorAll(".tag")).map(t => t.innerText)
            }))""",
        )

        # page.content() saves the rendered DOM after JavaScript execution, not
        # just the original server HTML.
        html = await page.content()
        # A full-page screenshot is visual evidence of what the automated browser
        # saw. It can reveal cookie banners, failed rendering, or layout changes.
        screenshot = await page.screenshot(full_page=True)
        # Always close automated browsers so scripts do not leave background
        # browser processes running.
        await browser.close()

    return html, quotes, screenshot


# %% 4. Run the browser collection

rendered_html, quotes, screenshot = asyncio.run(collect_rendered_page(URL))

print("Rendered HTML characters:", len(rendered_html))
print("Quotes extracted:", len(quotes))
# Converting quotes to a DataFrame is only for display here; the same conversion
# is repeated below when saving the processed CSV.
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

# Rendered HTML and screenshot are raw evidence: they preserve what the browser
# saw before our extraction code reduced it to a table.
rendered_path.write_text(rendered_html, encoding="utf-8")
screenshot_path.write_bytes(screenshot)
# The CSV is processed data: convenient for analysis, but less complete than the
# rendered HTML and screenshot.
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
