# VLOP Data Collection Course Pack

Teaching materials for the methodsNET course on collecting data from online
platforms, with examples for APIs, static scraping, browser automation,
DSA/transparency data, AI-assisted collection, and reproducible workflows.

The current course pack is organized around **notebooks for teaching** and
**runnable Python workflows for exercises or demos**.

## Quick Start

### 1. Get the Course Files

If you have never used Git before, install it first:

- macOS: install Xcode Command Line Tools by opening Terminal and running
  `xcode-select --install`.
- Windows: install Git from https://git-scm.com/downloads.
- Linux: install Git with your package manager, for example
  `sudo apt install git`.

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

If the course materials change on GitHub, update your local folder from
Terminal:

```bash
cd ~/Documents/methodsNET_vlop-course-materials
git status
git pull
```

`git status` tells you whether you have local changes. If it says
`nothing to commit, working tree clean`, it is safe to run `git pull`.

If `git status` lists files you changed, save a copy of your edits before
pulling, or ask for help. Git may need you to decide how to combine your changes
with the updated course files.

### 3. Set Up Python

You can use any editor or IDE that can run Python, for example VS Code,
PyCharm, Spyder, or JupyterLab.

One possible setup is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/runnable_workflows/00_setup_check.py
```

If you use conda, activate your environment first and then run:

```bash
pip install -r requirements.txt
python scripts/runnable_workflows/00_setup_check.py
```

Some scripts use live websites or APIs. They include polite defaults and notes
where credentials, platform approval, local browsers, or local files are
required.

## Directory Layout

```text
methodsNET_vlop-course-materials/
  notebooks/
    python_basics_for_course_scripts.ipynb
    day_0_parameter_discovery.ipynb
    day_1_api_walkthrough.ipynb
    day_2_static_scraping_walkthrough.ipynb
    day_2_beautifulsoup_extraction_patterns.ipynb
    day_2_beautifulsoup_extraction_patterns_solutions.ipynb
    day_3_dynamic_browser_walkthrough.ipynb
    day_4_dsa_transparency_walkthrough.ipynb
    day_4_data_quality_audit.ipynb
    day_5_ai_assisted_collection.ipynb
    day_5_practical_collection_workflows.ipynb
    day_5_reproducible_project.ipynb
    in_class_exercise_solutions.ipynb
  scripts/
    runnable_workflows/
      00_setup_check.py
      01_api_wikipedia.py
      02_api_github.py
      02_api_youtube_template.py
      03_static_scraper.py
      03b_methodsnet_course_scraper.py
      04_dynamic_browser_selenium.py
      04_dynamic_browser_playwright.py
      05_dsa_transparency_workflow.py
      06_data_quality_audit.py
      07_ai_augmented_collection.py
      08_reproducible_workflow.py
      09_practical_collection_workflow.py
      common.py
      COMMANDS.md
  examples/
    configs/
    data/
    templates/
  data/
    raw/
    processed/
    reports/
  slides/
    day1_intro.pptx
```

## Teaching Sequence

### Day 1: APIs with Wikipedia / MediaWiki

Main materials:

- `notebooks/day_1_api_walkthrough.ipynb`
- `scripts/runnable_workflows/01_api_wikipedia.py`

Topics: API endpoints, parameters, headers, JSON, search results, page IDs,
page-level requests, pagination, raw/processed data, and provenance.

### Day 2: Static Web Scraping

Main materials:

- `notebooks/day_2_static_scraping_walkthrough.ipynb`
- `notebooks/day_2_beautifulsoup_extraction_patterns.ipynb`
- `notebooks/day_2_beautifulsoup_extraction_patterns_solutions.ipynb`
- `scripts/runnable_workflows/03_static_scraper.py`
- `scripts/runnable_workflows/03b_methodsnet_course_scraper.py`

Topics: Wikipedia as static HTML, BeautifulSoup, selectors, text and attribute
extraction, repeated records, MethodsNET exercises, raw HTML, and processed CSVs.

### Day 3: Dynamic Pages and Browser Automation

Main materials:

- `notebooks/day_3_dynamic_browser_walkthrough.ipynb`
- `scripts/runnable_workflows/04_dynamic_browser_selenium.py`
- `scripts/runnable_workflows/04_dynamic_browser_playwright.py`

Topics: rendered browser state, Selenium, waiting, clicking/typing patterns,
screenshots, rendered HTML, scrolling, debugging, bot-compliance boundaries, and
Playwright as a modern alternative.

### Day 4: DSA / Transparency Data and Data Quality

Main materials:

- `notebooks/day_4_dsa_transparency_walkthrough.ipynb`
- `notebooks/day_4_data_quality_audit.ipynb`
- `scripts/runnable_workflows/05_dsa_transparency_workflow.py`
- `scripts/runnable_workflows/06_data_quality_audit.py`

Topics: DSA transparency data, platform reporting artifacts, missingness,
metadata stripping, overlap between datasets, and audit reports.

### Day 5: AI-Assisted and Reproducible Workflows

Main materials:

- `notebooks/day_5_ai_assisted_collection.ipynb`
- `notebooks/day_5_practical_collection_workflows.ipynb`
- `notebooks/day_5_reproducible_project.ipynb`
- `scripts/runnable_workflows/07_ai_augmented_collection.py`
- `scripts/runnable_workflows/08_reproducible_workflow.py`
- `scripts/runnable_workflows/09_practical_collection_workflow.py`

Topics: AI-assisted planning and debugging, verification, provenance, logging,
monitoring, scheduling, manifests, and reproducible project structure.

## Rendering Notebooks to HTML

To render one notebook:

```bash
jupyter nbconvert --to html notebooks/day_1_api_walkthrough.ipynb
```

To render all notebooks:

```bash
jupyter nbconvert --to html notebooks/*.ipynb
```

The repository also contains some pre-rendered `.html` versions of notebooks
for convenience.

## Runnable Workflow Examples

Run commands from the repository root.

```bash
python scripts/runnable_workflows/00_setup_check.py

python scripts/runnable_workflows/01_api_wikipedia.py \
  --query "digital services act" \
  --pages 2 \
  --page-size 10 \
  --outdir data

python scripts/runnable_workflows/03_static_scraper.py \
  --url https://en.wikipedia.org/wiki/Digital_Services_Act \
  --outdir data

python scripts/runnable_workflows/03b_methodsnet_course_scraper.py \
  --details 3 \
  --outdir data

python scripts/runnable_workflows/04_dynamic_browser_selenium.py \
  --url https://quotes.toscrape.com/js/ \
  --wait-selector ".quote" \
  --record-selector ".quote" \
  --outdir data

python scripts/runnable_workflows/05_dsa_transparency_workflow.py \
  --input examples/data/synthetic_dsa_tdb_extract.csv \
  --outdir data

python scripts/runnable_workflows/06_data_quality_audit.py \
  --reference examples/data/platform_public_reference.csv \
  --observed examples/data/platform_api_observed.csv \
  --id-col post_id \
  --outdir data

python scripts/runnable_workflows/07_ai_augmented_collection.py \
  --outdir data

python scripts/runnable_workflows/08_reproducible_workflow.py \
  --config examples/configs/wikipedia_workflow.yml
```

More command examples are in:

- `scripts/runnable_workflows/COMMANDS.md`

## Example Inputs

The `examples/` folder contains small teaching inputs:

- `examples/configs/`: YAML configuration examples.
- `examples/data/`: tiny synthetic CSVs for data-quality and transparency-data exercises.
- `examples/templates/`: DSA request, audit report, AI log, and codebook templates.

These files are deliberately small. Their purpose is not statistical analysis;
it is to make methodological problems visible: missing rows, duplicate IDs,
stripped metadata, field completeness, and the difference between source data
and processed data.

## Ethical Use

These examples are for research training. Students should adapt them only after
checking:

- applicable law and institutional review requirements;
- platform terms and documented developer policies;
- robots.txt and rate limits where relevant;
- whether personal data, sensitive data, or vulnerable populations are involved;
- whether access is allowed under an API, platform research tool, transparency
  database, or DSA mechanism.

The core methodological message of the course is that every access route gives
a partial view of platforms. Good platform research documents those limits
rather than hiding them.
