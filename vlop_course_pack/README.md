# VLOP Data Collection Course Pack

This pack contains two kinds of teaching material:

- `book/textbook.md`: a textbook-style student reader for the one-week course.
- `scripts/`: Python scripts for hands-on exercises in API collection, scraping, browser automation, DSA transparency data planning, data-quality auditing, AI-assisted collection, and reproducible workflow logging.
- `teaching_walkthroughs/`: heavily annotated, cell-style Python scripts for live teaching. These are meant to be opened and run section by section while you explain the concepts.

The materials assume a one-week intensive course. They are designed to be modular: you can assign the book as preparatory reading, then use one or two scripts per day in class.

## Quick Start

```bash
cd vlop_course_pack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/00_setup_check.py
```

Some scripts use live websites or APIs. They include polite defaults and explicit notes where credentials, platform approval, or local files are required.

## Directory Layout

```text
vlop_course_pack/
  book/
    textbook.md
  scripts/
    00_setup_check.py
    01_api_wikipedia.py
    02_api_youtube_template.py
    03_static_scraper.py
    04_dynamic_browser_playwright.py
    05_dsa_transparency_workflow.py
    06_data_quality_audit.py
    07_ai_augmented_collection.py
    08_reproducible_workflow.py
    common.py
  teaching_walkthroughs/
    01_api_collection_walkthrough.py
    02_static_scraping_walkthrough.py
    03_dynamic_browser_walkthrough.py
    04_dsa_transparency_walkthrough.py
    05_data_quality_audit_walkthrough.py
    06_ai_assisted_collection_walkthrough.py
    07_reproducible_project_walkthrough.py
  data/
    raw/
    processed/
    reports/
```

## Two Types of Scripts

The course pack now has two script layers.

### 1. Teaching Walkthroughs

Use these in class when you want to guide students through the logic line by line. They use `# %%` cell markers, so many editors let you run them section by section.

Suggested sequence:

```bash
python teaching_walkthroughs/01_api_collection_walkthrough.py
python teaching_walkthroughs/02_static_scraping_walkthrough.py
python teaching_walkthroughs/04_dsa_transparency_walkthrough.py
python teaching_walkthroughs/05_data_quality_audit_walkthrough.py
python teaching_walkthroughs/06_ai_assisted_collection_walkthrough.py
python teaching_walkthroughs/07_reproducible_project_walkthrough.py
```

The dynamic browser walkthrough is optional because it requires Playwright browser installation:

```bash
playwright install chromium
python teaching_walkthroughs/03_dynamic_browser_walkthrough.py
```

### 2. Runnable Exercise Scripts

Use these when students are ready to run more reusable command-line workflows:

```bash
python scripts/01_api_wikipedia.py --query "digital services act" --pages 2
python scripts/03_static_scraper.py --url https://quotes.toscrape.com/
python scripts/05_dsa_transparency_workflow.py --start 2025-01-01 --end 2025-01-03
python scripts/07_ai_augmented_collection.py
```

The runnable scripts are more compact than the walkthroughs, but they now include methodological comments explaining key design choices: pagination, raw vs processed data, robots checks, rendered DOMs, screenshots, provenance, and missingness.

## Ethical Use

These examples are for research training. Students should adapt them only after checking:

- applicable law and institutional review requirements;
- platform terms and documented developer policies;
- robots.txt and rate limits where relevant;
- whether personal data, sensitive data, or vulnerable populations are involved;
- whether access is allowed under an API, platform research tool, or DSA mechanism.

The core methodological message of the course is that every access regime gives a partial view of platforms. Good platform research documents those limits rather than hiding them.
