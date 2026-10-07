# Notebooks

The project is intentionally implemented as reproducible Python modules and CLI commands. This directory contains a guided walkthrough notebook for review convenience, while the source modules and `docs/PROJECT_REPORT.md` remain the authoritative deliverables.

Notebook:

- `scigraph_visual_summary.ipynb` walks through the project milestone map, core metrics, retrieval comparison, and generated figures.

To regenerate the data before opening the notebook:

```powershell
python -m scigraph.visualization.figures --config configs/dev.yaml
```
