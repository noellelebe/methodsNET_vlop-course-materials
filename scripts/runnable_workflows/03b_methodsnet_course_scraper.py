"""Scrape public course information from methodsnet.org.

Example:
    python scripts/runnable_workflows/03b_methodsnet_course_scraper.py \
      --details 3 \
      --outdir data

This script is a domain-specific version of the static scraping workflow:

1. fetch the public MethodsNET course-list page;
2. save the raw HTML;
3. extract course detail links from the list page;
4. optionally fetch a small number of individual course pages;
5. save processed CSVs and a provenance file.

The selectors are intentionally commented because this is a teaching script.
If the MethodsNET website changes, inspect the saved raw HTML
and adapt the selectors rather than blindly increasing collection scale.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from common import polite_get, provenance, robots_allowed, write_json


DEFAULT_COURSE_LIST_URL = "https://methodsnet.org/course-list/"
METHODSNET_NETLOC = "methodsnet.org"


COURSE_LINK_FIELDS = [
    "source_url",
    "course_url",
    "link_text",
    "listing_context",
    "code_guess",
    "title_guess",
    "instructor_guess",
    "week_guess",
    "status_guess",
]

COURSE_DETAIL_FIELDS = [
    "course_url",
    "title",
    "course_code",
    "date_time",
    "course_time",
    "instructor",
    "ects",
    "overview",
    "short_description",
    "long_description",
    "learning_objectives",
    "outline_text",
    "pricing_text",
]

HEADING_ROW_FIELDS = [
    "source_url",
    "level",
    "heading",
]


def write_table(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> Path:
    """Write a CSV with stable headers, even if there are no rows.

    Stable headers are useful because you can open the file
    and see what the script expected to produce, even if a selector returned
    nothing.
    """

    # Convert a string path into a Path object so we can use Path methods below.
    path = Path(path)
    # Create the output folder if needed.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        # extrasaction="ignore" means extra keys in row dictionaries are skipped
        # instead of raising an error.
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        # Always write headers so an empty extraction still documents its schema.
        writer.writeheader()
        writer.writerows(rows)
    return path


def safe_stem(url: str, max_length: int = 80) -> str:
    """Turn a URL into a filesystem-safe filename stem."""

    # urlparse splits the URL into parts such as netloc and path.
    parsed = urlparse(url)
    # Combine domain and path because both help distinguish output files.
    text = f"{parsed.netloc}_{parsed.path}".strip("_")
    # Replace punctuation and slashes with underscores so the value is safe as a
    # filename on different operating systems.
    return "".join(ch if ch.isalnum() else "_" for ch in text)[:max_length]


def clean_text(text: str | None) -> str:
    """Normalize whitespace from HTML text."""

    if not text:
        return ""
    # split() without arguments collapses any run of whitespace; join() puts one
    # normal space between words.
    return " ".join(text.split())


def is_methodsnet_course_url(url: str) -> bool:
    """Return True for public MethodsNET individual course pages."""

    parsed = urlparse(url)
    # Keep only MethodsNET course-detail URLs and exclude the listing page.
    return (
        parsed.netloc in {"methodsnet.org", "www.methodsnet.org"}
        and parsed.path.startswith("/course/")
        and parsed.path != "/course-list/"
    )


def guess_course_code(text: str) -> str | None:
    """Guess a course code such as D04, B01, C06, O2, or 03 from nearby text."""

    # The regular expression looks for common MethodsNET course-code patterns.
    match = re.search(r"\b([A-Z]\d{2}|O\d|0\d)\b", text)
    return match.group(1) if match else None


def guess_status(text: str) -> str | None:
    """Guess a booking/status label from nearby listing text."""

    status_patterns = [
        "FULLY BOOKED",
        "ALMOST FULLY BOOKED",
        "Confirmed",
        "Cancelled",
    ]
    # Lowercase matching makes the rule robust to capitalization differences.
    lower_text = text.lower()
    for status in status_patterns:
        if status.lower() in lower_text:
            return status
    return None


def guess_week(text: str) -> str | None:
    """Guess the week column from nearby listing text."""

    if "Pre-week" in text or "Pre Week" in text:
        return "Pre-week"
    # Fall back to a simple week number guess when the listing contains 1 or 2.
    match = re.search(r"\b([12])\b", text)
    return match.group(1) if match else None


def parent_context_for_link(a_tag) -> str:
    """Get a compact text context around a link.

    Course-list pages are often built from tables, blocks, or page-builder
    widgets. Instead of assuming one exact structure, we try a few likely
    containers and keep their visible text as a diagnostic field.
    """

    # If the link sits inside a table row, the row is the best local context.
    row = a_tag.find_parent("tr")
    if row:
        return clean_text(row.get_text(" ", strip=True))

    # Otherwise, try common HTML containers from most specific to broad.
    for container_name in ["li", "article", "section", "div", "p"]:
        container = a_tag.find_parent(container_name)
        if container:
            text = clean_text(container.get_text(" ", strip=True))
            if text:
                return text[:600]

    return clean_text(a_tag.get_text(" ", strip=True))


def table_cells_for_link(a_tag) -> list[str]:
    """Return cleaned table cells for the row containing a link, if present."""

    row = a_tag.find_parent("tr")
    if not row:
        return []
    # th and td cover both header cells and normal table cells.
    return [
        clean_text(cell.get_text(" ", strip=True))
        for cell in row.select("th, td")
    ]


def title_guess_from_context(context: str, code_guess: str | None) -> str | None:
    """Extract a rough title from the listing context.

    This is deliberately only a guess. The detail-page scraper is more reliable
    for final titles because the course page has a clear h1.
    """

    if not context:
        return None

    # Remove repeated interface text so it does not become part of the title.
    text = context.replace("Click for details", " ")
    text = clean_text(text)

    if code_guess and code_guess in text:
        # Keep only the text after the course code, because the title often
        # follows the code in listing rows.
        text = text.split(code_guess, 1)[1].strip()

    # Remove common trailing fields when they are present in the listing row.
    for status in ["ALMOST FULLY BOOKED", "FULLY BOOKED", "Confirmed", "Cancelled"]:
        text = text.replace(status, " ")
    text = clean_text(text)

    # The listing row usually continues with instructor/week/status. This cannot
    # be parsed perfectly without stable table cells, so we keep a conservative
    # short guess and preserve listing_context for auditing.
    return text[:180] if text else None


def listing_fields_from_cells(cells: list[str]) -> dict[str, str | None]:
    """Parse course-list fields from table cells when the page provides them.

    On the current MethodsNET course-list page, the visible columns are:

        Full Details | Code | Courses | Instructor name | Week | Confirmation

    We still treat this as a best-effort parser because public websites can
    change. The full listing_context is always saved for auditing.
    """

    if len(cells) >= 6:
        # Use known column positions when the listing is represented as a table.
        return {
            "code_guess": cells[1] or None,
            "title_guess": cells[2] or None,
            "instructor_guess": cells[3] or None,
            "week_guess": cells[4] or None,
            "status_guess": cells[5] or None,
        }
    return {
        "code_guess": None,
        "title_guess": None,
        "instructor_guess": None,
        "week_guess": None,
        "status_guess": None,
    }


def parse_course_links(course_list_url: str, html: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse course links and headings from the MethodsNET course-list page."""

    # Parse the list-page HTML into a searchable tree.
    soup = BeautifulSoup(html, "html.parser")

    course_rows: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # a[href] means every link with an href attribute. We then filter down to
    # methodsnet.org/course/... URLs, because the page also contains navigation,
    # registration, privacy, and footer links.
    for a in soup.select("a[href]"):
        # urljoin turns relative href values into full absolute URLs.
        href = urljoin(course_list_url, a.get("href"))
        if not is_methodsnet_course_url(href):
            continue
        if href in seen_urls:
            continue
        seen_urls.add(href)

        # Keep the surrounding text as an audit field for selector debugging.
        context = parent_context_for_link(a)
        cells = table_cells_for_link(a)
        cell_fields = listing_fields_from_cells(cells)
        # Prefer table-derived code; otherwise guess from surrounding text.
        code_guess = cell_fields["code_guess"] or guess_course_code(context)

        course_rows.append(
            {
                "source_url": course_list_url,
                "course_url": href,
                "link_text": clean_text(a.get_text(" ", strip=True)),
                "listing_context": context,
                "code_guess": code_guess,
                "title_guess": cell_fields["title_guess"] or title_guess_from_context(context, code_guess),
                "instructor_guess": cell_fields["instructor_guess"],
                "week_guess": cell_fields["week_guess"] or guess_week(context),
                "status_guess": cell_fields["status_guess"] or guess_status(context),
            }
        )

    headings = []
    for level in ["h1", "h2", "h3", "h4"]:
        for heading in soup.select(level):
            # Headings are saved as a lightweight map of the page structure.
            headings.append(
                {
                    "source_url": course_list_url,
                    "level": level,
                    "heading": clean_text(heading.get_text(" ", strip=True)),
                }
            )

    return course_rows, headings


def text_after_heading(soup: BeautifulSoup, heading_pattern: str, *, max_parts: int = 6) -> str | None:
    """Collect nearby text after a heading whose text matches heading_pattern.

    This is a pragmatic parser for course-detail pages. It is not a universal
    rule for all websites. The raw HTML is saved so you can revise this
    function if MethodsNET changes its page structure.
    """

    # Compile the heading text pattern once and match case-insensitively.
    pattern = re.compile(heading_pattern, re.I)
    heading = soup.find(
        lambda tag: tag.name in {"h2", "h3", "h4", "h5"}
        and pattern.search(clean_text(tag.get_text(" ", strip=True)))
    )
    if not heading:
        return None

    parts = []
    for sibling in heading.find_all_next():
        # Stop when the next major heading begins; this keeps sections separate.
        if sibling.name in {"h2", "h3", "h4"} and sibling is not heading:
            break
        if sibling.name in {"p", "li"}:
            # Collect paragraph/list-item text that belongs to this section.
            text = clean_text(sibling.get_text(" ", strip=True))
            if text:
                parts.append(text)
        if len(parts) >= max_parts:
            break

    return " ".join(parts) if parts else None


def detail_value_by_label(soup: BeautifulSoup, label: str) -> str | None:
    """Find values in detail boxes such as Date & Time, Instructor, or ECTS."""

    # re.escape protects labels such as "Date & Time" from being interpreted as
    # special regular-expression syntax.
    label_pattern = re.compile(rf"^{re.escape(label)}$", re.I)
    heading = soup.find(
        lambda tag: tag.name in {"h2", "h3", "h4", "h5"}
        and label_pattern.search(clean_text(tag.get_text(" ", strip=True)))
    )
    if not heading:
        return None

    for sibling in heading.find_all_next():
        # Stop at the next label-like heading.
        if sibling.name in {"h2", "h3", "h4", "h5"}:
            break
        text = clean_text(sibling.get_text(" ", strip=True))
        if text and text.lower() != label.lower():
            return text
    return None


def parse_course_detail(url: str, html: str) -> dict[str, Any]:
    """Parse an individual MethodsNET course page."""

    # Parse one individual course page.
    soup = BeautifulSoup(html, "html.parser")
    # The page title is usually in h1; if no h1 exists, store None.
    title = clean_text(soup.select_one("h1").get_text(" ", strip=True)) if soup.select_one("h1") else None
    # Pull text from named sections using the helper above.
    overview = text_after_heading(soup, r"Overview", max_parts=2)
    short_description = text_after_heading(soup, r"Short Description", max_parts=3)
    long_description = text_after_heading(soup, r"Long Description", max_parts=8)
    learning_objectives = text_after_heading(soup, r"Learning Objectives", max_parts=12)

    # The course outline uses day headings rather than a simple table. We keep a
    # broad text excerpt that can be inspected or parsed further in class.
    outline_parts = []
    for text_node in soup.find_all(string=re.compile(r"Day\\s+[1-5]|09:00|13:30")):
        # This searches text nodes for day/time signals and keeps a compact
        # excerpt rather than attempting a perfect timetable parser.
        text = clean_text(str(text_node))
        if text:
            outline_parts.append(text)
    outline_text = " | ".join(outline_parts[:40]) if outline_parts else None

    pricing_text = text_after_heading(soup, r"Pricing", max_parts=12)

    return {
        # The returned dictionary is one processed row for the course-details CSV.
        "course_url": url,
        "title": title,
        "course_code": guess_course_code(title or url),
        "date_time": detail_value_by_label(soup, "Date & Time"),
        "course_time": detail_value_by_label(soup, "Course Time"),
        "instructor": detail_value_by_label(soup, "Instructor"),
        "ects": detail_value_by_label(soup, "ECTS"),
        "overview": overview,
        "short_description": short_description,
        "long_description": long_description,
        "learning_objectives": learning_objectives,
        "outline_text": outline_text,
        "pricing_text": pricing_text,
    }


def fetch_html(url: str, *, delay_seconds: float, ignore_robots: bool) -> tuple[str, str, bool | None]:
    """Fetch a URL after checking robots.txt."""

    # Check robots.txt before making the request.
    allowed = robots_allowed(url)
    if allowed is False and not ignore_robots:
        raise SystemExit(
            f"robots.txt check disallows this URL: {url}. "
            "Choose another page or discuss the issue before overriding."
        )

    # polite_get adds a user agent, waits between requests, and checks HTTP errors.
    response = polite_get(url, delay_seconds=delay_seconds)
    # response.url may differ from url after redirects; save the final URL.
    return response.text, response.url, allowed


def parse_args() -> argparse.Namespace:
    # Keep argument parsing in its own function so main() stays readable.
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_COURSE_LIST_URL)
    parser.add_argument(
        "--details",
        default="5",
        help=(
            "Number of individual course detail pages to fetch after the list page, "
            "or 'all' to fetch every course detail page found."
        ),
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="Optional case-insensitive text filter for course URLs/context before detail fetching.",
    )
    parser.add_argument("--delay-seconds", type=float, default=1.5)
    parser.add_argument("--outdir", default="data")
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Do not block collection if robots.txt disallows the URL.",
    )
    return parser.parse_args()


def main() -> None:
    # Parse terminal options such as --details, --filter, and --outdir.
    args = parse_args()
    outdir = Path(args.outdir)

    # Fetch the course-list page once and save the exact HTML snapshot.
    list_html, final_list_url, list_robots_allowed = fetch_html(
        args.url,
        delay_seconds=args.delay_seconds,
        ignore_robots=args.ignore_robots,
    )

    stem = safe_stem(final_list_url)
    raw_list_path = outdir / "raw" / f"methodsnet_{stem}.html"
    raw_list_path.parent.mkdir(parents=True, exist_ok=True)
    raw_list_path.write_text(list_html, encoding="utf-8")

    # Extract links to individual course pages and headings from the list page.
    course_rows, heading_rows = parse_course_links(final_list_url, list_html)

    if args.filter:
        # Apply a case-insensitive text filter before requesting detail pages.
        needle = args.filter.lower()
        course_rows_for_details = [
            row
            for row in course_rows
            if needle in " ".join(str(value) for value in row.values()).lower()
        ]
    else:
        # Without a filter, all discovered course links are eligible for details.
        course_rows_for_details = course_rows

    # --details controls how many course-detail pages we follow after scraping
    # the course-list page. You may expect "all" to be possible, so the
    # argument accepts either an integer string such as "10" or the word "all".
    if str(args.details).lower() == "all":
        detail_limit = len(course_rows_for_details)
    else:
        try:
            detail_limit = max(int(args.details), 0)
        except ValueError:
            raise SystemExit("--details must be an integer such as 10, or the word 'all'.")

    detail_rows: list[dict[str, Any]] = []
    raw_detail_paths: list[Path] = []
    detail_errors: list[dict[str, Any]] = []

    for row in course_rows_for_details[:detail_limit]:
        detail_url = row["course_url"]
        try:
            # Fetch each selected course-detail page.
            detail_html, final_detail_url, _allowed = fetch_html(
                detail_url,
                delay_seconds=args.delay_seconds,
                ignore_robots=args.ignore_robots,
            )
        except Exception as exc:
            # Record detail-page failures and continue with the remaining pages.
            detail_errors.append({"course_url": detail_url, "error": repr(exc)})
            continue

        # Save a raw HTML snapshot for every fetched detail page.
        detail_stem = safe_stem(final_detail_url)
        raw_detail_path = outdir / "raw" / f"methodsnet_detail_{detail_stem}.html"
        raw_detail_path.parent.mkdir(parents=True, exist_ok=True)
        raw_detail_path.write_text(detail_html, encoding="utf-8")
        raw_detail_paths.append(raw_detail_path)

        # Parse the detail page into one row of structured course metadata.
        parsed_detail = parse_course_detail(final_detail_url, detail_html)
        # Add listing guesses so you can compare list-page and detail-page
        # extraction. This is useful for teaching multi-page scraping workflows.
        parsed_detail.update(
            {
                "listing_code_guess": row.get("code_guess"),
                "listing_title_guess": row.get("title_guess"),
                "listing_status_guess": row.get("status_guess"),
            }
        )
        detail_rows.append(parsed_detail)

    # Write processed tables and reports into the standard folder structure.
    processed_dir = outdir / "processed"
    reports_dir = outdir / "reports"
    course_links_path = write_table(
        processed_dir / "methodsnet_course_links.csv",
        course_rows,
        COURSE_LINK_FIELDS,
    )
    headings_path = write_table(
        processed_dir / "methodsnet_course_list_headings.csv",
        heading_rows,
        HEADING_ROW_FIELDS,
    )
    detail_fieldnames = COURSE_DETAIL_FIELDS + [
        "listing_code_guess",
        "listing_title_guess",
        "listing_status_guess",
    ]
    course_details_path = write_table(
        processed_dir / "methodsnet_course_details.csv",
        detail_rows,
        detail_fieldnames,
    )
    diagnostics_path = reports_dir / "methodsnet_course_scrape_diagnostics.json"
    provenance_path = reports_dir / "methodsnet_course_scrape_provenance.json"

    # Diagnostics are operational facts about the run, especially useful when a
    # selector returns fewer records than expected.
    write_json(
        diagnostics_path,
        {
            "course_list_url": final_list_url,
            "robots_allowed_course_list": list_robots_allowed,
            "course_links_found": len(course_rows),
            "detail_pages_requested": detail_limit,
            "detail_pages_parsed": len(detail_rows),
            "detail_errors": detail_errors,
            "filter": args.filter,
            "notes": [
                "The course-link table preserves listing_context so selector guesses can be audited.",
                "If detail fields are empty, inspect the saved raw HTML and adapt parse_course_detail().",
            ],
        },
    )

    # Provenance records how this dataset was produced.
    write_json(
        provenance_path,
        provenance(
            script=__file__,
            parameters=vars(args),
            outputs=[
                raw_list_path,
                *raw_detail_paths,
                course_links_path,
                headings_path,
                course_details_path,
                diagnostics_path,
            ],
            notes=[
                "This script scraped public MethodsNET course information for a teaching exercise.",
                "It checked robots.txt before fetching unless --ignore-robots was used.",
                "Raw HTML snapshots are saved to support selector debugging and reproducibility.",
                "The script is intentionally small-scale by default.",
            ],
        ),
    )

    print(f"Course links found: {len(course_rows)}")
    print(f"Detail pages parsed: {len(detail_rows)}")
    print(f"Course links CSV: {course_links_path}")
    print(f"Course details CSV: {course_details_path}")
    if detail_errors:
        print(f"Detail errors: {len(detail_errors)}; see {diagnostics_path}")

    # A tiny pause at the end makes it visible in classroom demos that scripted
    # collection is a process with timing and politeness considerations.
    time.sleep(0.1)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# How to run this script from the command line
# ---------------------------------------------------------------------------
#
# Small run from the repository root:
#
#     python scripts/runnable_workflows/03b_methodsnet_course_scraper.py \
#       --filter "Large Online Platforms" \
#       --details 1 \
#       --outdir data
#
# Larger classroom run:
#
#     python scripts/runnable_workflows/03b_methodsnet_course_scraper.py \
#       --details 10 \
#       --delay-seconds 2 \
#       --outdir data
#
# Fetch all course-detail pages found on the course list:
#
#     python scripts/runnable_workflows/03b_methodsnet_course_scraper.py \
#       --details all \
#       --delay-seconds 1 \
#       --outdir data
#
# What each part means:
#
# - --url
#   The course-list page to scrape. By default this is
#   https://methodsnet.org/course-list/.
#
# - --filter "Large Online Platforms"
#   Keeps only course-list rows whose text contains this phrase before fetching
#   detail pages.
#
# - --details 1 / --details 10 / --details all
#   How many individual course-detail pages to fetch after the course list.
#   Use a number for a small teaching run. Use all to fetch every detail page
#   found after applying the optional filter.
#
# - --delay-seconds 2
#   The pause between requests. This is part of polite collection practice.
#
# - --outdir
#   The folder where raw HTML, processed CSV files, diagnostics, and provenance
#   are saved.
#
# - --ignore-robots
#   Overrides the robots.txt check. Use only after discussing why this is
#   appropriate for the specific teaching/research situation.
