# Command-Line Commands for Runnable Workflows

This file collects copyable Terminal commands for the scripts in
`scripts/runnable_workflows/`. Run the commands from the repository root, for
example:

```bash
cd ~/Documents/methodsNET_vlop-course-materials
```

If your local folder has a different name, use that folder instead.

## 0. Check the Python Setup

Use this first to check whether the main teaching packages are available:

```bash
python scripts/runnable_workflows/00_setup_check.py
```

## 1. Wikipedia API Collection

Small test run:

```bash
python scripts/runnable_workflows/01_api_wikipedia.py \
  --query "digital services act" \
  --pages 1 \
  --page-size 2 \
  --extract-chars 300 \
  --outdir /tmp/methodsnet_api_test
```

Larger classroom run:

```bash
python scripts/runnable_workflows/01_api_wikipedia.py \
  --query "digital services act" \
  --pages 3 \
  --page-size 25 \
  --extract-chars 2500 \
  --outdir data
```

Full article extracts instead of shortened extracts:

```bash
python scripts/runnable_workflows/01_api_wikipedia.py \
  --query "platform governance" \
  --pages 2 \
  --page-size 20 \
  --extract-chars 0 \
  --outdir data
```

## 2. YouTube Data API Collection

This script requires a YouTube Data API key stored in an environment variable.
Set it in Terminal before running the script:

```bash
export YOUTUBE_API_KEY="paste-your-key-here"
```

Then run:

```bash
python scripts/runnable_workflows/02_api_youtube_template.py \
  --query "digital services act" \
  --pages 1 \
  --page-size 10 \
  --outdir data
```

For a larger run:

```bash
python scripts/runnable_workflows/02_api_youtube_template.py \
  --query "platform regulation" \
  --pages 3 \
  --page-size 25 \
  --outdir data
```

## 3. Static Web Scraping

Simple classroom page:

```bash
python scripts/runnable_workflows/03_static_scraper.py \
  --url https://quotes.toscrape.com/ \
  --outdir data
```

If the robots.txt check blocks a page during a controlled teaching demo, use a
different URL. The script also has an override flag, but students should not use
it casually:

```bash
python scripts/runnable_workflows/03_static_scraper.py \
  --url https://quotes.toscrape.com/ \
  --outdir data \
  --ignore-robots
```

## 4. Dynamic Browser Collection with Selenium

Run a small browser-automation collection:

```bash
python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
  --url https://quotes.toscrape.com/js/ \
  --scrolls 2 \
  --wait-seconds 1 \
  --outdir data
```

To show the browser window during a live demo:

```bash
python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
  --url https://quotes.toscrape.com/js/ \
  --scrolls 2 \
  --wait-seconds 1 \
  --outdir data \
  --show-browser
```

With an explicit robots override for a controlled classroom example:

```bash
python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
  --url https://quotes.toscrape.com/js/ \
  --scrolls 2 \
  --wait-seconds 1 \
  --outdir data \
  --ignore-robots
```

## 4b. Optional Playwright Comparison

Install the browser once before the first run:

```bash
playwright install chromium
```

Then run a small browser-automation collection:

```bash
python scripts/runnable_workflows/04_dynamic_browser_playwright.py \
  --url https://quotes.toscrape.com/js/ \
  --scrolls 2 \
  --wait-ms 1000 \
  --outdir data
```

With an explicit robots override for a controlled classroom example:

```bash
python scripts/runnable_workflows/04_dynamic_browser_playwright.py \
  --url https://quotes.toscrape.com/js/ \
  --scrolls 2 \
  --wait-ms 1000 \
  --outdir data \
  --ignore-robots
```

## 5. DSA Transparency Workflow

Template run without an input file:

```bash
python scripts/runnable_workflows/05_dsa_transparency_workflow.py \
  --start 2025-01-01 \
  --end 2025-01-03 \
  --outdir data
```

Run using the synthetic example extract:

```bash
python scripts/runnable_workflows/05_dsa_transparency_workflow.py \
  --input examples/data/synthetic_dsa_tdb_extract.csv \
  --start 2025-01-01 \
  --end 2025-01-03 \
  --outdir data
```

## 6. Data Quality Audit

Use the synthetic reference and observed datasets:

```bash
python scripts/runnable_workflows/06_data_quality_audit.py \
  --reference examples/data/platform_public_reference.csv \
  --observed examples/data/platform_api_observed.csv \
  --id-col post_id \
  --outdir data
```

## 7. AI-Augmented Collection Planning

Template run:

```bash
python scripts/runnable_workflows/07_ai_augmented_collection.py \
  --outdir data
```

More realistic run with explicit method details:

```bash
python scripts/runnable_workflows/07_ai_augmented_collection.py \
  --research-question "How do platforms describe Digital Services Act compliance?" \
  --platform "Wikipedia and YouTube" \
  --docs "https://www.mediawiki.org/wiki/API:Search; https://developers.google.com/youtube/v3/docs/search/list" \
  --problem "Need to collect search results, page/video identifiers, and provenance without treating API search as a complete population." \
  --html-excerpt "Small non-sensitive excerpt pasted here if debugging selectors." \
  --access-route "API collection with optional scraping for page-level inspection" \
  --columns "source, query, pageid_or_video_id, title, url, timestamp, text_excerpt" \
  --known-risks "Search ranking bias, rate limits, missing metadata, credentials, and reproducibility." \
  --outdir data
```

## 8. Reproducible Workflow from Config

Run with the example config:

```bash
python scripts/runnable_workflows/08_reproducible_workflow.py \
  --config examples/configs/wikipedia_workflow.yml
```

Run without a config to create a generic workflow note:

```bash
python scripts/runnable_workflows/08_reproducible_workflow.py
```

## Useful Checks After Running

See which output files were created:

```bash
find data -maxdepth 2 -type f
```

Check whether running scripts changed tracked repository files:

```bash
git status
```
