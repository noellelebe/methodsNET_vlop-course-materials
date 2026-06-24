"""Teaching walkthrough: dynamic pages with Selenium.

This script is optional because it requires Selenium and a local browser. Recent
Selenium versions include Selenium Manager, which can often find or download the
needed browser driver automatically.

Teaching goals:
1. Show why requests may miss JavaScript-rendered content.
2. Start with Selenium as the classic browser-automation tool.
3. Use a real browser to collect rendered DOM.
4. Save screenshots as visual audit evidence.
5. Mention Playwright as a modern alternative with strong waiting and tracing.
"""

# %% 1. Imports and classroom URL

import time
from pathlib import Path

import pandas as pd
import requests


URL = "https://quotes.toscrape.com/js/"
# This user agent is attached to both the simple requests call and the Selenium
# browser. Keeping it consistent helps compare the two access routes.
USER_AGENT = "methodsNET-VLOP-course/1.0 dynamic walkthrough"


# %% 2. Fetch with requests first

# This is the "static" view. requests asks the server for the HTML document, but
# it does not execute JavaScript, click buttons, scroll, or wait for client-side
# rendering. For JavaScript-heavy pages, the response may contain only an app
# shell rather than the content users see in a browser.
static_response = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
static_response.raise_for_status()

static_html = static_response.text
print("Static HTML characters:", len(static_html))

# This test searches the raw HTML for text that appears visibly after JavaScript
# renders the quotes. If it prints False, requests did not receive the quote text
# in the initial server response.
print("Does static HTML contain quote text?", "The world as we have created it" in static_html)


# %% 3. Define a Selenium browser function

def collect_rendered_page_with_selenium(url: str, headless: bool = True):
    """Open a page in Chrome, wait for rendered content, and extract quote rows."""

    # Selenium imports live inside the function so students can still read the
    # rest of the file even before Selenium is installed.
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument(f"--user-agent={USER_AGENT}")

    # headless=True runs the browser without a visible window. For live teaching,
    # set headless=False so students can watch the browser open and render.
    if headless:
        options.add_argument("--headless=new")

    # webdriver.Chrome() starts a Chrome browser controlled by Python. Selenium
    # Manager usually handles the driver setup for current Selenium versions.
    driver = webdriver.Chrome(options=options)

    try:
        # get() is the browser equivalent of opening a URL. Unlike requests, the
        # browser will execute page JavaScript.
        driver.get(url)

        # Waiting is a methodological choice. Too short and data may be missing;
        # too long and the script becomes slow. Here we wait until at least one
        # rendered quote block exists in the DOM.
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

        # A small scroll is included to show the pattern. On true infinite-scroll
        # pages, this would be repeated with a stopping rule.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # page_source is the rendered DOM after JavaScript execution, not just the
        # original server HTML.
        html = driver.page_source

        quote_blocks = driver.find_elements(By.CSS_SELECTOR, ".quote")
        quotes = []

        for block in quote_blocks:
            # CSS selectors work the same conceptually as in BeautifulSoup, but
            # here Selenium searches the live browser DOM.
            quote_text = block.find_element(By.CSS_SELECTOR, ".text").text
            author = block.find_element(By.CSS_SELECTOR, ".author").text
            tags = [
                tag.text
                for tag in block.find_elements(By.CSS_SELECTOR, ".tag")
            ]

            quotes.append(
                {
                    "quote": quote_text,
                    "author": author,
                    "tags": tags,
                }
            )

        # A screenshot is visual evidence of what the automated browser saw. It
        # can reveal cookie banners, failed rendering, or empty states that a CSV
        # alone cannot show.
        screenshot = driver.get_screenshot_as_png()

    finally:
        # Always close automated browsers so scripts do not leave background
        # browser processes running.
        driver.quit()

    return html, quotes, screenshot


# %% 4. Run the Selenium browser collection

rendered_html, quotes, screenshot = collect_rendered_page_with_selenium(
    URL,
    # Change this to False during live teaching if you want students to see the
    # browser window.
    headless=True,
)

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

rendered_path = raw_dir / "walkthrough_rendered_quotes_selenium.html"
screenshot_path = raw_dir / "walkthrough_rendered_quotes_selenium.png"
quotes_path = processed_dir / "walkthrough_rendered_quotes_selenium.csv"

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


# %% 6. Where Playwright fits

# Selenium is a good starting point because many students have heard of it and it
# makes the idea of "driving a browser" very concrete. Playwright is a newer
# browser-automation library with strong auto-waiting, browser contexts, network
# inspection, and tracing. For more complex modern web apps, Playwright can be
# easier to debug and less flaky.
#
# In this course:
# - start with Selenium to understand the browser-automation idea;
# - mention Playwright as the modern alternative;
# - use the runnable Playwright script if you want to compare APIs or show
#   network-oriented debugging later.


# %% 7. Teaching prompts

questions = [
    "What did requests miss that the rendered browser could see?",
    "Which waiting decision shaped what Selenium observed?",
    "What evidence does the screenshot provide that a CSV cannot?",
    "When is browser automation justified instead of an API?",
    "How could infinite scroll introduce missingness?",
    "What would count as bypassing controls rather than observing a public interface?",
]

for question in questions:
    print("-", question)
