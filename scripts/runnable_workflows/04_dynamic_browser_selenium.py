"""Browser automation example with Selenium.

Example:
    python scripts/runnable_workflows/04_dynamic_browser_selenium.py --url https://quotes.toscrape.com/js/
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.parse import urljoin

from common import DEFAULT_USER_AGENT, provenance, robots_allowed, write_csv, write_json


def collect(url: str, scrolls: int, wait_seconds: float, headless: bool) -> tuple[str, list[dict], bytes]:
    # Selenium is imported inside the function so the script can still be opened
    # and inspected before browser dependencies are installed.
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")
    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        # Wait until the browser has at least a document body. Specific projects
        # should wait for a selector that marks the relevant content.
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        # Infinite scroll is an observational protocol: scroll, wait, then later
        # verify whether more records appeared. The defaults are intentionally
        # small for a classroom demonstration.
        for _ in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(wait_seconds)

        html = driver.page_source

        links = []
        for element in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = element.get_attribute("href")
            links.append(
                {
                    "link_text": element.text.strip(),
                    "href": urljoin(url, href) if href else None,
                }
            )

        screenshot = driver.get_screenshot_as_png()
    finally:
        driver.quit()

    rows = [
        {"source_url": url, "link_text": item["link_text"], "href": item["href"]}
        for item in links
    ]
    return html, rows, screenshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--scrolls", type=int, default=2)
    parser.add_argument("--wait-seconds", type=float, default=1.0)
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

    safe_name = args.url.replace("https://", "").replace("http://", "")
    safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)[:80]
    outdir = Path(args.outdir)

    html, links, screenshot = collect(
        args.url,
        args.scrolls,
        args.wait_seconds,
        headless=not args.show_browser,
    )

    # Saving rendered HTML and screenshot together lets students compare "what
    # the browser saw" with "what the parser extracted."
    html_path = outdir / "raw" / f"selenium_{safe_name}.html"
    image_path = outdir / "raw" / f"selenium_{safe_name}.png"
    links_path = outdir / "processed" / f"selenium_{safe_name}_links.csv"
    report_path = outdir / "reports" / f"selenium_{safe_name}_provenance.json"

    html_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    image_path.write_bytes(screenshot)
    write_csv(links_path, links)
    write_json(
        report_path,
        provenance(
            script=__file__,
            parameters={**vars(args), "robots_allowed": allowed},
            outputs=[html_path, image_path, links_path],
            notes=[
                "Selenium captures rendered page state after JavaScript execution.",
                "Check site policies and do not use automation to bypass controls.",
                "Use the screenshot as a visual audit of the collection state.",
            ],
        ),
    )

    print(f"Rendered HTML: {html_path}")
    print(f"Screenshot: {image_path}")
    print(f"Links: {links_path}")


if __name__ == "__main__":
    main()
