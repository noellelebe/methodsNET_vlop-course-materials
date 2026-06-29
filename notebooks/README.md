# Notebook-Style Teaching Materials

This folder contains the student-facing notebook versions of the course
materials. The `.ipynb` files combine explanation, runnable code cells,
discussion prompts, and small exercises.

The notebooks are the main teaching layer. The reusable command-line scripts are
in `../scripts/runnable_workflows/`.

## Recommended Use

- Use `python_basics_for_course_scripts.ipynb` as a preparatory or support
  notebook for students who need a refresher.
- Teach from the day-specific `.ipynb` notebooks when students should run cells
  with you.
- Use the runnable workflow scripts after students have seen the concepts in
  the notebooks.
- Keep solution notebooks instructor-only until students have tried the
  exercises.

## Available Notebooks

- `python_basics_for_course_scripts.ipynb`
- `day_0_parameter_discovery.ipynb`
- `day_1_api_walkthrough.ipynb`
- `day_2_static_scraping_walkthrough.ipynb`
- `day_2_beautifulsoup_extraction_patterns.ipynb`
- `day_2_beautifulsoup_extraction_patterns_solutions.ipynb`
- `day_3_dynamic_browser_walkthrough.ipynb`
- `day_4_dsa_transparency_walkthrough.ipynb`
- `day_4_data_quality_audit.ipynb`
- `day_5_ai_assisted_collection.ipynb`
- `day_5_practical_collection_workflows.ipynb`
- `day_5_reproducible_project.ipynb`
- `in_class_exercise_solutions.ipynb`

## Rendered HTML

Some notebooks also have pre-rendered `.html` files in this folder. These are
useful for reading in a browser, but the `.ipynb` files are the editable and
runnable source materials.

To render one notebook to HTML:

```bash
jupyter nbconvert --to html notebooks/day_1_api_walkthrough.ipynb
```

To render all notebooks from the repository root:

```bash
jupyter nbconvert --to html notebooks/*.ipynb
```

## Instructor-Only Files

These files contain worked answers and should generally not be released before
the in-class exercises:

- `day_2_beautifulsoup_extraction_patterns_solutions.ipynb`
- `in_class_exercise_solutions.ipynb`
