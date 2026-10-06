# Notebooks

The project is intentionally implemented as reproducible Python modules and CLI commands. This directory contains a lightweight visual summary notebook for review convenience, while the source modules and `docs/PROJECT_REPORT.md` remain the authoritative deliverables.

Notebook:

- `scigraph_visual_summary.ipynb` summarizes the generated report tables and embeds the project figures.

To regenerate the data before opening the notebook:

```powershell
python -m scigraph.visualization.figures --config configs/dev.yaml
```

