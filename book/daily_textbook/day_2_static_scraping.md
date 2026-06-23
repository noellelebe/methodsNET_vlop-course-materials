# Day 2: Static Web Scraping Foundations

## What This Day Is About

Day 2 introduces web scraping as a way to collect data from browser-visible web
pages. Scraping is not a replacement for APIs, and it is not a shortcut around
legal or ethical constraints. It is one possible access route when the relevant
data are present in public web interfaces and when collection is justified,
proportionate, and documented.

The day focuses on static pages: pages where the relevant content is already
present in the HTML returned by the server. This is the simplest scraping case.
It lets students learn HTML, DOM structure, CSS selectors, raw HTML storage, and
basic parsing before moving to JavaScript-rendered pages on Day 3.

## 1. From Web Page to Data

A web page is not just what appears on screen. It is built from HTML, CSS,
JavaScript, images, and network requests. Static scraping begins with the HTML.
The scraper sends an HTTP request, receives HTML text, parses it into a tree,
and extracts selected elements.

HTML consists of elements such as headings, links, paragraphs, tables, and
containers. Elements can have attributes. For scraping, important attributes
include `class`, `id`, `href`, `src`, and sometimes `data-*` attributes.

The browser turns HTML into the Document Object Model, or DOM. The DOM is a tree
of nodes. Scrapers use selectors to navigate this tree. A selector is a rule for
which nodes to extract.

The methodological step is deciding which HTML structures correspond to research
observations. On a practice page, one `.quote` block may correspond to one quote
record. On a platform, one post card, comment block, advertisement, product
listing, or moderation notice may correspond to one observation. That decision
must be justified.

## 2. CSS Selectors

CSS selectors are a language for selecting elements from the DOM.

The selector `.quote` means every element whose class includes `quote`. The dot
marks a class selector. The selector `.text` means every element with class
`text`. The selector `a[href]` means every link element that has an `href`
attribute. The selector `.tags a.tag` means: inside an element with class
`tags`, find link elements with class `tag`.

Selectors are parameters. They decide what enters the dataset. A selector can be
too broad, collecting navigation links and page furniture. It can be too narrow,
missing records that use a slightly different layout. It can be brittle,
breaking when a site changes class names.

Students should learn to connect selectors to visible page structure. Open the
page in a browser, inspect one record, identify the repeated container, and only
then write the extraction code.

## 3. Fetching vs. Parsing

Fetching and parsing are different tasks.

Fetching means downloading the raw HTML with an HTTP request. In Python, this is
often done with `requests.get()`. A responsible request includes a user agent
and a timeout. The response should be checked with `raise_for_status()` so that
HTTP errors are not accidentally saved as data.

Parsing means interpreting the HTML and extracting fields. In the walkthrough,
BeautifulSoup parses the HTML into a searchable object. Methods such as
`select()` and `select_one()` apply CSS selectors. `get_text()` extracts visible
text from an element.

The separation matters. A researcher should usually fetch once, save the raw
HTML, and then develop parsing code locally. This avoids repeatedly hitting a
website while experimenting with selectors. It also preserves evidence of what
the page looked like at collection time.

## 4. Raw HTML as Evidence

Saving raw HTML is a core reproducibility practice. If a scraper breaks later,
the raw HTML helps answer whether the site changed, the selector was wrong, or
the parser made an incorrect assumption.

Raw HTML is not always safe to share. It may contain personal data, hidden
metadata, or contextual information. But within a controlled research workflow,
raw HTML is often necessary for auditability.

In the teaching example, the raw HTML is saved to `data/raw/`. The extracted
quote table and link table are saved to `data/processed/`. This teaches the
same raw/processed distinction introduced on Day 1.

## 5. Extracting Repeated Records

Many scraping tasks involve repeated structures. A page may contain many posts,
comments, search results, products, or quotes. The first task is to identify the
container for one record.

In the practice example, `.quote` is the record container. Inside each quote
block, `.text` is the quote field, `.author` is the author field, and `.tags
a.tag` returns the tags. The scraper loops over each quote block and extracts
fields from inside that block. This avoids mixing the author from one quote with
the text from another.

This pattern generalizes:

1. Select repeated containers.
2. For each container, select fields inside it.
3. Store one dictionary per record.
4. Convert the list of dictionaries into a table.

This pattern is simple, but it is also where many errors occur. If the container
selector is wrong, every downstream field may be wrong.

## 6. Links and Relative URLs

Links are stored in `href` attributes. Some links are absolute, such as
`https://example.com/page`. Others are relative, such as `/page/2/`. A relative
URL only makes sense in relation to the page where it appeared.

Python's `urljoin()` combines the page URL and the raw `href` value to create an
absolute URL. This is important for reproducibility. If a dataset contains only
relative links, another researcher may not know which domain they came from.

Link extraction also illustrates overcollection. `a[href]` selects all links,
including navigation, login links, tag links, and pagination links. A researcher
must decide which of these are relevant.

## 7. Robots.txt, Terms, and Ethics

Robots.txt is a machine-readable file that gives crawling instructions. It is a
useful first signal, but it is not a complete legal or ethical analysis. A page
may allow crawling but still contain sensitive personal data. A page may
disallow crawling, in which case researchers should not treat that as a puzzle
to defeat.

Terms of service, institutional ethics rules, data protection law, platform
policies, and research harm all matter. "Publicly visible" does not automatically
mean "free to collect, store, analyze, and redistribute."

Before scraping, ask whether an official API exists, whether the data are
necessary, whether less intrusive data could answer the question, whether the
collection could harm users, whether personal data are involved, and how server
load will be controlled.

## 8. Robustness

A robust scraper includes checks. It counts records, checks expected fields,
logs missing values, saves raw input, and stops before doing harm. A fragile
scraper silently returns empty data when a class name changes.

Students should learn to treat missing elements as information. If
`select_one(".author")` returns `None`, that may mean the page structure changed,
the field is absent for some records, or the selector is wrong. A good workflow
records such cases.

## End-of-Day Questions

- What is the unit of observation in the page?
- Which selector defines one record?
- Which selectors define fields?
- What could cause the scraper to miss records?
- What raw evidence did you save?
- What would change if the page contained real user profiles or comments?
