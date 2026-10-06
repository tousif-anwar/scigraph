# Retrieval Experiments

Retrieval experiments are implemented in the project modules rather than as ad hoc notebooks.

Current retrieval outputs:

- Sparse baseline: `../../reports/results/retrieval_report.json`
- Advanced retrieval comparison: `../../reports/results/advanced_retrieval_results.json`
- Demo query artifact: `../../reports/results/demo_results.json`
- Retrieval documentation: `../../docs/RETRIEVAL.md` and `../../docs/ADVANCED_RETRIEVAL.md`
- Retrieval figure: `../../reports/figures/retrieval_ablation.png`

Commands:

```powershell
python -m scigraph.retrieval.sparse --config configs/dev.yaml
python -m scigraph.retrieval.advanced --config configs/dev.yaml
```

