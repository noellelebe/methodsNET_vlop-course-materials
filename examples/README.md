# Examples

This folder contains small, safe teaching inputs. They are meant to make the
scripts and walkthroughs concrete without requiring live platform access.

## Folders

- `configs/`: reusable YAML examples for command-line workflows.
- `data/`: tiny synthetic or classroom-safe CSV files.
- `templates/`: forms and scaffolds for DSA requests, audits, AI logs, and codebooks.

## Useful Commands

Run the data-quality audit with bundled synthetic data:

```bash
python "scripts/runnable_workflows/06_data_quality_audit.py" \
  --reference examples/data/platform_public_reference.csv \
  --observed examples/data/platform_api_observed.csv \
  --id-col post_id
```

Summarize the synthetic DSA transparency extract:

```bash
python "scripts/runnable_workflows/05_dsa_transparency_workflow.py" \
  --input examples/data/synthetic_dsa_tdb_extract.csv
```

Run the reproducible Wikipedia workflow:

```bash
python "scripts/runnable_workflows/08_reproducible_workflow.py" \
  --config examples/configs/wikipedia_workflow.yml
```

## Teaching Note

The files in `data/` are deliberately tiny. Their purpose is not statistical
analysis; it is to make methodological problems visible: missing rows, duplicate
IDs, stripped metadata, field completeness, and the difference between source
data and processed data.
