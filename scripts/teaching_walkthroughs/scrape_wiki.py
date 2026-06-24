
# %% 9. Scrape the individual page URL

# Sometimes an API does not provide the field you need, or there is no API at
# all. Then researchers may collect the HTML page itself. This is web scraping:
# instead of asking for JSON, we download the browser-facing page and parse HTML.
scrape_url = page_record.get("fullurl") or page_browser_url

html_response = requests.get(scrape_url, headers=headers, timeout=30)
html_response.raise_for_status()

print("Scraped URL:", html_response.url)
print("Content type:", html_response.headers.get("content-type"))

# BeautifulSoup parses the HTML string into a searchable document tree. It does
# not know what is substantively meaningful; we decide that with selectors.
soup = BeautifulSoup(html_response.text, "html.parser")

# h1 selects the main page heading. On Wikipedia, that is usually the article
# title shown to readers.
h1 = soup.select_one("h1")
scraped_title = h1.get_text(" ", strip=True) if h1 else None

# div.mw-parser-output > p selects paragraph elements that are direct children
# of the main article content container. This is intentionally specific: it
# avoids many navigation and footer paragraphs, but it may break if Wikipedia's
# HTML structure changes.
paragraph_tags = soup.select("div.mw-parser-output > p")

# If the specific selector returns nothing, we fall back to all paragraphs. This
# is useful in a live demo because page markup can vary, but the fallback is less
# clean and should be documented in real collection work.
if not paragraph_tags:
    paragraph_tags = soup.select("p")

paragraphs = []
for tag in paragraph_tags:
    text = tag.get_text(" ", strip=True)
    # Empty paragraphs and citation-only fragments are not useful article text.
    if text:
        paragraphs.append(text)

print("Scraped title:", scraped_title)
print("Number of non-empty scraped paragraphs:", len(paragraphs))
print("\nFirst scraped paragraph:")
print(paragraphs[0] if paragraphs else "No paragraph text found.")

# Teaching point:
# The API extract and the scraped paragraph are related, but they are not the
# same data source. The API may remove formatting and references; the HTML may
# include navigation, citation markers, and layout artifacts. A reproducible
# project should state which route was used and why.

