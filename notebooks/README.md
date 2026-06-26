# Notebook-Style Teaching Materials

This folder contains student-facing notebook versions of the teaching
walkthroughs.

The `.ipynb` files are Jupyter notebooks. They combine explanation, runnable
code cells, discussion prompts, and small exercises. They are meant to sit
between the live coding scripts in `scripts/teaching_walkthroughs/` and the
fully reusable command-line workflows in `scripts/runnable_workflows/`.

The `.qmd` files contain the same notebook-style material in Quarto format.
They are optional and mainly useful if the instructor wants to render polished
HTML or PDF handouts with Quarto.

## Recommended Use

- Teach from the `.ipynb` file if you want students to run notebook cells.
- Use the matching `.py` file when live coding in VS Code, Spyder, PyCharm, or
  another Python editor.
- Use the runnable workflow scripts later, once students have seen how the
  pieces fit together.

## Available Notebooks

- `python_basics_for_course_scripts.ipynb`
- `day_0_parameter_discovery.ipynb`
- `day_1_api_walkthrough.ipynb`
- `day_2_static_scraping_walkthrough.ipynb`
- `day_2_beautifulsoup_extraction_patterns.ipynb`
- `day_3_dynamic_browser_walkthrough.ipynb`
- `day_4_dsa_transparency_walkthrough.ipynb`
- `day_4_data_quality_audit.ipynb`
- `day_5_ai_assisted_collection.ipynb`
- `day_5_reproducible_project.ipynb`

## Optional Quarto Rendering

If Quarto is installed, render a notebook with:

```bash
quarto render notebooks/day_1_api_walkthrough.qmd --to html
```

For PDF output:

```bash
quarto render notebooks/day_1_api_walkthrough.qmd --to pdf
```

PDF rendering may require a LaTeX installation. HTML is usually the easiest
format for course handouts.
