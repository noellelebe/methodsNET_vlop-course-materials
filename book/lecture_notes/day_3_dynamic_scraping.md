# Day 3: Dynamic Pages and Fragile Scrapers

## What This Day Is About

Day 3 moves from static scraping to dynamic pages. Many modern platforms do not
send all visible content in the first HTML response. Instead, the browser
downloads an application shell, executes JavaScript, makes additional network
requests, renders content, and updates the page as the user scrolls or clicks.

This changes the research workflow. A static scraper may see an almost empty
page even though the browser visibly shows posts, comments, or search results.
Browser automation tools such as Playwright or Selenium can observe rendered
pages, but they also introduce new methodological choices: waiting, scrolling,
clicking, screenshots, network inspection, and automation ethics.

The aim is to teach students how to diagnose dynamic pages and how to document
browser-mediated collection.

## 1. Static HTML vs. Rendered DOM

When `requests.get()` downloads a page, it receives the server's initial
response. For simple pages, that response contains the content of interest. For
JavaScript-heavy pages, it may contain only an app shell: scripts, containers,
and placeholders.

The rendered DOM is what exists after the browser has executed JavaScript. It
may contain elements that were not present in the initial HTML. A dynamic
scraping workflow often needs to compare the static response with the rendered
page.

A useful diagnostic is to search the static HTML for text that appears visibly
in the browser. If the text is absent from the static HTML but visible in the
browser, static scraping is not enough.

## 2. Browser Automation

Browser automation controls a real browser from code. Selenium and Playwright
can open pages, wait for loading, click buttons, scroll, extract rendered DOM,
capture screenshots, and inspect browser-visible page state.

In this course, Selenium is the starting point because it makes the browser
automation logic very concrete: open a URL, wait for an element, find elements,
read text, scroll, and take a screenshot. Playwright is introduced as a modern
alternative with strong auto-waiting, browser contexts, tracing, and
network-oriented debugging.

Browser automation is powerful but slower and more fragile than API collection.
It should be used when the research question requires the browser-visible state
or when no appropriate API exists. It should not be used to bypass access
controls, CAPTCHAs, or anti-bot systems.

Important browser parameters include `headless`, `wait_until`, timeout, viewport
size, scroll count, and selectors. Each parameter changes what the script sees.
For example, a Selenium script may wait until a specific CSS selector appears in
the rendered DOM. A Playwright script may use `wait_until="networkidle"` to wait
until network activity quiets down. Both choices affect what the scraper sees.

## 3. Screenshots and Rendered HTML

Rendered HTML and screenshots are complementary evidence.

Rendered HTML shows the DOM after JavaScript execution. It lets researchers
re-run parsing logic and inspect the elements available to the script.

Screenshots show what the automated browser visually saw. They can reveal cookie
banners, failed loads, login prompts, layout changes, or empty states. A CSV
cannot show these problems.

For dynamic scraping, a good raw evidence bundle often includes the rendered
HTML, a screenshot, request metadata, and extraction logs.

## 4. Infinite Scroll and Dynamic Loading

Infinite scroll pages load more records as the user scrolls. A script that only
opens the page may collect the first screen of content but miss later records. A
script that scrolls too aggressively may overload the page, miss loading events,
or behave unlike a normal user.

Scroll count is a parameter. Wait time after scrolling is a parameter. The
stopping rule is a parameter. A researcher should document all of them.

A careful infinite-scroll workflow records the number of visible items after
each scroll, stops after a predefined rule, and checks whether new records are
actually appearing. If no new records appear after several scrolls, the script
should stop rather than scroll forever.

## 5. Network Inspection

Dynamic pages often load data through background network requests. Browser
developer tools can reveal whether the page is loading JSON, HTML fragments, or
other resources. Network inspection helps researchers understand how the page
works.

However, discovering an internal endpoint in the browser does not automatically
mean researchers are authorized to call it directly at scale. The endpoint may
depend on session cookies, tokens, access controls, or undocumented behavior.
Network inspection is a diagnostic method, not a permission slip.

When network inspection suggests a more structured data route, researchers must
ask whether it is documented, permitted, stable, and ethically appropriate.

## 6. Debugging Dynamic Scrapers

Dynamic scrapers fail in many ways. The page may load slowly. A selector may
target elements before they exist. A cookie banner may hide content. The site may
change its layout. The script may scroll too little or too much. The browser may
be blocked or served different content.

A debugging workflow should proceed systematically:

1. Check the HTTP status and final URL.
2. Compare static HTML with rendered HTML.
3. Save and inspect a screenshot.
4. Count expected elements.
5. Print or log extracted fields.
6. Check whether selectors still match.
7. Reduce the script to a small reproducible case.

Do not jump immediately to more aggressive automation. Often the problem is a
wrong selector, a missing wait, or a page state that was not documented.

## 7. Anti-Fragile Design

No scraper is permanent. Anti-fragile scraper design means expecting change and
making failures visible.

Useful practices include saving raw evidence, logging counts, validating fields,
separating fetching from parsing, using clear stopping rules, keeping selectors
in one place, and writing small tests against saved pages. If a scraper returns
zero records, that should be treated as a warning, not a valid empty dataset by
default.

Anti-patterns include hard-coded sleeps without validation, no screenshots, no
raw HTML, selectors based on visual position only, and scripts that overwrite
previous outputs without a manifest.

## 8. Compliance and Boundaries

Browser automation can look like normal browsing, but it is still automated
collection. Researchers should avoid evasion. They should respect access
controls, rate limits, terms, institutional review, and data protection rules.

The ethical question is not only whether a script can collect data. It is
whether the collection is justified, proportionate, and documented.

## End-of-Day Questions

- What did the static request miss?
- What did the rendered browser reveal?
- Which browser parameters shaped the observed page state?
- What does the screenshot prove or fail to prove?
- What would count as debugging, and what would count as evasion?
- How would you know if a dynamic scraper silently failed?
