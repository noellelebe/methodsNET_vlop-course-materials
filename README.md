# VLOP Data Collection Course Pack

This pack contains two kinds of teaching material:

- `book/textbook.md`: a textbook-style student reader for the one-week course.
- `book/daily_textbook/`: expanded day-by-day textbook chapters matching the
  five-day course schedule.
- `scripts/runnable_workflows/`: Python scripts for hands-on exercises in API collection, scraping, browser automation, DSA transparency data planning, data-quality auditing, AI-assisted collection, and reproducible workflow logging.
- `scripts/teaching_walkthroughs/`: heavily annotated, cell-style Python scripts for live teaching. These are meant to be opened and run section by section while you explain the concepts.
- `examples/`: small configs, synthetic data, and templates for teaching exercises.

The materials assume a one-week intensive course. They are designed to be modular: you can assign the book as preparatory reading, then use one or two scripts per day in class.

## Quick Start

### 1. Get the Course Files

If you have never used Git before, install it first:

- macOS: install Xcode Command Line Tools by opening Terminal and running `xcode-select --install`.
- Windows: install Git from https://git-scm.com/downloads.
- Linux: install Git with your package manager, for example `sudo apt install git`.

Then open Terminal, choose where you want the course folder to live, and clone
the repository:

```bash
cd ~/Documents
git clone https://github.com/noellelebe/methodsNET_vlop-course-materials.git
cd methodsNET_vlop-course-materials
```

This creates a folder called `methodsNET_vlop-course-materials`, which is the
local copy of the GitHub repository.

### 2. Update the Course Files Later

If the course materials change on GitHub, you can update your local folder from
Terminal:

```bash
cd ~/Documents/methodsNET_vlop-course-materials
git status
git pull
```

`git status` tells you whether you have local changes. If it says `nothing to
commit, working tree clean`, it is safe to run `git pull`.

If `git status` lists files you changed, save a copy of your edits before
pulling, or ask for help. Git may need you to decide how to combine your changes
with the updated course files.

### 3. Set Up Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python "scripts/runnable_workflows/00_setup_check.py"
```

Some scripts use live websites or APIs. They include polite defaults and explicit notes where credentials, platform approval, or local files are required.

## Directory Layout

```text
methodsNET_vlop-course-materials/
  book/
    textbook.md
    handouts/
      beautifulsoup_extraction_patterns.md
  scripts/
    runnable_workflows/
      00_setup_check.py
      01_api_wikipedia.py
      02_api_youtube_template.py
      03_static_scraper.py
      04_dynamic_browser_selenium.py
      04_dynamic_browser_playwright.py
      05_dsa_transparency_workflow.py
      06_data_quality_audit.py
      07_ai_augmented_collection.py
      08_reproducible_workflow.py
      common.py
    teaching_walkthroughs/
      00_parameter_discovery_walkthrough.py
      01_api_collection_walkthrough.py
      02_static_scraping_walkthrough.py
      02b_beautifulsoup_extraction_patterns.py
      03_dynamic_browser_walkthrough.py
      04_dsa_transparency_walkthrough.py
      05_data_quality_audit_walkthrough.py
      06_ai_assisted_collection_walkthrough.py
      07_reproducible_project_walkthrough.py
  examples/
    configs/
    data/
    templates/
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
python scripts/teaching_walkthroughs/00_parameter_discovery_walkthrough.py
python scripts/teaching_walkthroughs/01_api_collection_walkthrough.py
python scripts/teaching_walkthroughs/02_static_scraping_walkthrough.py
python scripts/teaching_walkthroughs/02b_beautifulsoup_extraction_patterns.py
python scripts/teaching_walkthroughs/03_dynamic_browser_walkthrough.py
python scripts/teaching_walkthroughs/04_dsa_transparency_walkthrough.py
python scripts/teaching_walkthroughs/05_data_quality_audit_walkthrough.py
python scripts/teaching_walkthroughs/06_ai_assisted_collection_walkthrough.py
python scripts/teaching_walkthroughs/07_reproducible_project_walkthrough.py
```

The dynamic browser walkthrough is optional because it requires Selenium and a local browser. The course starts with Selenium and mentions Playwright as a modern alternative. If you want to compare the Playwright version, install the browser once:

```bash
playwright install chromium
python scripts/runnable_workflows/04_dynamic_browser_playwright.py --url https://quotes.toscrape.com/js/
```

### 2. Runnable Exercise Scripts

Use these when students are ready to run more reusable command-line workflows:

```bash
python "scripts/runnable_workflows/01_api_wikipedia.py" --query "digital services act" --pages 2
python "scripts/runnable_workflows/03_static_scraper.py" --url https://quotes.toscrape.com/
python "scripts/runnable_workflows/04_dynamic_browser_selenium.py" --url https://quotes.toscrape.com/js/
python "scripts/runnable_workflows/05_dsa_transparency_workflow.py" --start 2025-01-01 --end 2025-01-03
python "scripts/runnable_workflows/07_ai_augmented_collection.py"
```

The runnable scripts are more compact than the walkthroughs, but they now include methodological comments explaining key design choices: pagination, raw vs processed data, robots checks, rendered DOMs, screenshots, provenance, and missingness.

## Example Inputs

The `examples/` folder contains small files for teaching and testing without
depending on live platform access:

- `examples/configs/`: YAML configuration examples for command-line workflows.
- `examples/data/`: tiny synthetic CSVs for data-quality and DSA transparency exercises.
- `examples/templates/`: DSA request, audit report, AI log, and codebook templates.

Useful commands:

```bash
python "scripts/runnable_workflows/06_data_quality_audit.py" \
  --reference examples/data/platform_public_reference.csv \
  --observed examples/data/platform_api_observed.csv \
  --id-col post_id

python "scripts/runnable_workflows/05_dsa_transparency_workflow.py" \
  --input examples/data/synthetic_dsa_tdb_extract.csv

python "scripts/runnable_workflows/08_reproducible_workflow.py" \
  --config examples/configs/wikipedia_workflow.yml
```

## Ethical Use

These examples are for research training. Students should adapt them only after checking:

- applicable law and institutional review requirements;
- platform terms and documented developer policies;
- robots.txt and rate limits where relevant;
- whether personal data, sensitive data, or vulnerable populations are involved;
- whether access is allowed under an API, platform research tool, or DSA mechanism.

The core methodological message of the course is that every access regime gives a partial view of platforms. Good platform research documents those limits rather than hiding them.
