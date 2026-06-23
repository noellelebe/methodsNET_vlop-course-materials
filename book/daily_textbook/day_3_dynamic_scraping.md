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

This distinction is one of the most important technical ideas in scraping.
`requests` is not a browser. It does not execute JavaScript, respond to clicks,
maintain the same rendering state, or wait for client-side application logic.
It asks the server for a resource and returns the response. A browser does much
more: it parses HTML, applies CSS, executes JavaScript, makes follow-up network
requests, stores cookies, manages sessions, and updates the DOM.

The rendered DOM is what exists after the browser has executed JavaScript. It
may contain elements that were not present in the initial HTML. A dynamic
scraping workflow often needs to compare the static response with the rendered
page.

A useful diagnostic is to search the static HTML for text that appears visibly
in the browser. If the text is absent from the static HTML but visible in the
browser, static scraping is not enough.

The opposite is also possible. Some information may exist in the raw HTML but
not be visible on screen. Hidden metadata, embedded JSON, accessibility labels,
or structured data can appear in source. Researchers should not assume that
"visible page" and "available HTML" are identical.

## 2. Browser Automation

Browser automation controls a real browser from code. Playwright and Selenium
can open pages, wait for loading, click buttons, scroll, extract rendered DOM,
capture screenshots, and monitor network requests.

Browser automation is powerful but slower and more fragile than API collection.
It should be used when the research question requires the browser-visible state
or when no appropriate API exists. It should not be used to bypass access
controls, CAPTCHAs, or anti-bot systems.

Important browser parameters include `headless`, `wait_until`, timeout, viewport
size, scroll count, and selectors. Each parameter changes what the script sees.
For example, `wait_until="networkidle"` waits until network activity quiets
down. This may help dynamic content load, but it can also be slow or unreliable
on pages that continuously poll servers.

Browser automation therefore creates an observational protocol. It is closer to
instructing a research assistant to open a browser, wait, scroll, click, and
record what appears than to querying a clean database. The protocol should be
written down. If two researchers use different viewport sizes, wait conditions,
login states, or scroll depths, they may observe different pages.

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

Network inspection is especially useful for teaching because it reveals that
modern web pages are not single documents. They are sequences of requests and
responses. A feed may first load a shell, then a configuration file, then a JSON
batch of posts, then images, then more posts after scrolling. Understanding this
sequence helps students see why dynamic scraping can fail and why APIs or
official data exports are often preferable when available.

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

Students should also distinguish between making a workflow robust and making it
evasive. Robustness means logging, checking, waiting for legitimate content to
load, and failing visibly. Evasion means disguising the client, bypassing access
controls, defeating CAPTCHAs, or ignoring explicit restrictions. This course is
about the first, not the second.

## End-of-Day Questions

- What did the static request miss?
- What did the rendered browser reveal?
- Which browser parameters shaped the observed page state?
- What does the screenshot prove or fail to prove?
- What would count as debugging, and what would count as evasion?
- How would you know if a dynamic scraper silently failed?
