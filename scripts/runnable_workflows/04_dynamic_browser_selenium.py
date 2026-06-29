"""Browser automation example with Selenium.

Example:
    python scripts/runnable_workflows/04_dynamic_browser_selenium.py --url https://quotes.toscrape.com/js/

Selenium is useful when a normal requests/BeautifulSoup workflow is not enough:
- JavaScript adds content after the first HTML response;
- public content appears after clicking a tab, menu, or load-more button;
- a page uses infinite scroll;
- you need a screenshot or rendered HTML as evidence;
- you need to inspect the browser DOM rather than the raw server HTML.

Selenium can also type into forms, but login/form automation should only be used
with permission, for example with a test account or an account you are allowed
to automate. Do not use browser automation to bypass CAPTCHAs, paywalls, login
restrictions, rate limits, or other access controls.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.parse import urljoin

from common import DEFAULT_USER_AGENT, provenance, robots_allowed, write_csv, write_json


def classify_rendered_state(html: str) -> dict[str, bool]:
    """Detect common access/compliance signals in rendered HTML.

    These checks are intentionally simple. They do not "solve" blocks. They help
    students recognize when a workflow has reached an access boundary that
    should be documented rather than bypassed.
    """

    # Lowercase once so the checks below are case-insensitive.
    lower_html = html.lower()
    return {
        # These are warning signals, not proof. They help students decide what to
        # inspect and document when rendered collection behaves unexpectedly.
        "mentions_captcha": "captcha" in lower_html,
        "mentions_login": "login" in lower_html or "sign in" in lower_html,
        "mentions_rate_limit": "rate limit" in lower_html or "too many requests" in lower_html,
        "mentions_cookie_or_consent": "cookie" in lower_html or "consent" in lower_html,
        "mentions_paywall": "subscribe" in lower_html or "paywall" in lower_html,
    }


def scroll_until_stable(
    driver,
    *,
    record_selector: str,
    scrolls: int,
    wait_seconds: float,
) -> list[dict]:
    """Scroll with an explicit stopping rule based on record counts."""

    # history records the count after each scroll so the stopping rule is visible.
    history = []
    # Count records before scrolling so we have a baseline.
    previous_count = len(driver.find_elements("css selector", record_selector))
    history.append({"step": "initial", "record_count": previous_count})

    for scroll_number in range(1, scrolls + 1):
        # Run JavaScript in the browser to move to the bottom of the page.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Give the page time to load records triggered by the scroll.
        time.sleep(wait_seconds)

        # Recount records after the wait.
        current_count = len(driver.find_elements("css selector", record_selector))
        history.append({"step": f"scroll_{scroll_number}", "record_count": current_count})

        # Stop early when scrolling no longer reveals new records. This avoids
        # pretending that "more scrolling" is a reproducible collection rule.
        if current_count == previous_count:
            break
        previous_count = current_count

    return history


def collect(
    url: str,
    scrolls: int,
    wait_seconds: float,
    headless: bool,
    *,
    record_selector: str,
    wait_selector: str,
) -> tuple[str, list[dict], bytes, dict]:
    # Selenium is imported inside the function so the script can still be opened
    # and inspected before browser dependencies are installed.
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    # Options configure the Chrome browser session.
    options = Options()
    # Identify the teaching script instead of using Selenium's default user agent.
    options.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")
    if headless:
        # Headless mode runs without showing a browser window.
        options.add_argument("--headless=new")

    # Start a local Chrome browser controlled by Selenium.
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate the browser to the target URL.
        driver.get(url)

        # Wait for a content-specific selector when possible. Waiting only for
        # "body" can be too weak on dynamic pages because the body can exist long
        # before the records we care about have rendered.
        # WebDriverWait repeatedly checks for a condition for up to 15 seconds.
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))

        # Count records before the scroll protocol starts.
        before_scroll_count = len(driver.find_elements(By.CSS_SELECTOR, record_selector))

        # Infinite scroll is an observational protocol: scroll, wait, then later
        # verify whether more records appeared. The defaults are intentionally
        # small for a classroom demonstration.
        scroll_history = scroll_until_stable(
            driver,
            record_selector=record_selector,
            scrolls=scrolls,
            wait_seconds=wait_seconds,
        )

        # page_source is the rendered HTML after JavaScript and scrolling.
        html = driver.page_source
        after_scroll_count = len(driver.find_elements(By.CSS_SELECTOR, record_selector))

        links = []
        for element in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            # Selenium elements expose attributes and visible text through methods.
            href = element.get_attribute("href")
            links.append(
                {
                    "link_text": element.text.strip(),
                    "href": urljoin(url, href) if href else None,
                }
            )

        # A screenshot is a visual audit of what the browser actually displayed.
        screenshot = driver.get_screenshot_as_png()
    finally:
        # Always close the browser, even if an error happens while collecting.
        driver.quit()

    # Diagnostics summarize the browser state and the explicit collection choices.
    diagnostics = {
        "url": url,
        "record_selector": record_selector,
        "wait_selector": wait_selector,
        "before_scroll_count": before_scroll_count,
        "after_scroll_count": after_scroll_count,
        "scroll_history": scroll_history,
        "rendered_html_characters": len(html),
        "link_count": len(links),
        "rendered_state_flags": classify_rendered_state(html),
        "method_note": (
            "Browser automation is used here to observe rendered public content, "
            "not to bypass login, CAPTCHA, paywall, or other access controls."
        ),
    }

    # Convert the link dictionaries into CSV-ready rows with a source URL.
    rows = [
        {"source_url": url, "link_text": item["link_text"], "href": item["href"]}
        for item in links
    ]
    return html, rows, screenshot, diagnostics


def main() -> None:
    # Command-line arguments expose the collection choices students may change.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--scrolls", type=int, default=2)
    parser.add_argument("--wait-seconds", type=float, default=1.0)
    parser.add_argument(
        "--wait-selector",
        default="body",
        help="CSS selector that must appear before extraction begins.",
    )
    parser.add_argument(
        "--record-selector",
        default="a[href]",
        help="CSS selector used to count records while scrolling.",
    )
    parser.add_argument("--outdir", default="data")
    parser.add_argument("--ignore-robots", action="store_true")
    parser.add_argument("--show-browser", action="store_true")
    args = parser.parse_args()

    # robots.txt is a first-line check rather than a complete ethics review.
    allowed = robots_allowed(args.url)
    if allowed is False and not args.ignore_robots:
        raise SystemExit(
            "robots.txt check disallows this URL. Use a different classroom page."
        )

    # Build a filesystem-safe stem from the URL for all output files.
    safe_name = args.url.replace("https://", "").replace("http://", "")
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]
    outdir = Path(args.outdir)

    # Run the browser collection step.
    html, links, screenshot, diagnostics = collect(
        args.url,
        args.scrolls,
        args.wait_seconds,
        headless=not args.show_browser,
        record_selector=args.record_selector,
        wait_selector=args.wait_selector,
    )

    # Saving rendered HTML and screenshot together lets students compare "what
    # the browser saw" with "what the parser extracted."
    html_path = outdir / "raw" / f"selenium_{safe_name}.html"
    image_path = outdir / "raw" / f"selenium_{safe_name}.png"
    links_path = outdir / "processed" / f"selenium_{safe_name}_links.csv"
    diagnostics_path = outdir / "reports" / f"selenium_{safe_name}_diagnostics.json"
    report_path = outdir / "reports" / f"selenium_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    # Write the rendered HTML, screenshot, extracted links, diagnostics, and
    # provenance as separate files.
    html_path.write_text(html, encoding="utf-8")
    image_path.write_bytes(screenshot)
    write_csv(links_path, links)
    write_json(diagnostics_path, diagnostics)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "robots_allowed": allowed},
            outputs=[html_path, image_path, links_path, diagnostics_path],
            notes=[
                "Selenium captures rendered page state after JavaScript execution.",
                "Check site policies and do not use automation to bypass controls.",
                "Use the screenshot as a visual audit of the collection state.",
                "Diagnostics record selector counts, scroll history, and possible block/consent signals.",
            ],
        ),
    )

    print(f"Rendered HTML: {html_path}")
    print(f"Screenshot: {image_path}")
    print(f"Links: {links_path}")
    print(f"Diagnostics: {diagnostics_path}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Browser-automation comparison with the same Wikipedia page:
#
#     python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
#       --url https://en.wikipedia.org/wiki/Digital_Services_Act \
#       --wait-selector "h1" \
#       --record-selector ".mw-parser-output p" \
#       --scrolls 0 \
#       --outdir data
#
# Main JavaScript-rendered classroom example:
#
#     python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
#       --url https://quotes.toscrape.com/js/ \
#       --wait-selector ".quote" \
#       --record-selector ".quote" \
#       --scrolls 2 \
#       --wait-seconds 1 \
#       --outdir data
#
# Show the browser window during a live demo:
#
#     python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
#       --url https://quotes.toscrape.com/js/ \
#       --wait-selector ".quote" \
#       --record-selector ".quote" \
#       --scrolls 2 \
#       --wait-seconds 1 \
#       --outdir data \
#       --show-browser
#
# What each part means:
#
# - --url
#   The page opened in the automated browser.
#
# - --wait-selector ".quote"
#   A CSS selector that should appear after the page has rendered. Selenium waits
#   for this before saving output. For the Wikipedia comparison, use "h1".
#
# - --record-selector ".quote"
#   A CSS selector for repeated records to count as a basic diagnostic. For the
#   Wikipedia comparison, ".mw-parser-output p" counts article paragraphs.
#
# - --scrolls
#   How many times the script scrolls down to trigger dynamic loading.
#
# - --wait-seconds
#   How long to wait after loading/scrolling.
#
# - --outdir
#   The folder where rendered HTML, diagnostics, and provenance are saved.
#
# - --show-browser
#   Runs with a visible browser window instead of headless mode.
#
# - --ignore-robots
#   Overrides the robots.txt check in a controlled demo. Do not use casually.
#
# Other common Selenium patterns students may encounter:
#
# - Click a button:
#     button = driver.find_element("css selector", "button.load-more")
#     button.click()
#
# - Type into a form field:
#     search_box = driver.find_element("css selector", "input[name='q']")
#     search_box.clear()
#     search_box.send_keys("digital services act")
#
# - Read an attribute:
#     href = link.get_attribute("href")
#
# - Use permitted/test credentials without hard-coding them:
#     username = os.getenv("COURSE_DEMO_USERNAME")
#     password = os.getenv("COURSE_DEMO_PASSWORD")
#
#   Only do this where login automation is permitted. Never use Selenium to
#   bypass CAPTCHAs, paywalls, or access restrictions.
