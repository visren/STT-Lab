# STT Lab Notebook

Jupyter interface for compare → dataset → LoRA adapt → evaluate.

## Launch

```bash
# from repo root
npm run dev:notebook

# or
cd notebooks
../apps/api/.venv/bin/jupyter lab stt_lab.ipynb
```

Select the **STT Lab** kernel (project venv).

## Files

- [`stt_lab.ipynb`](stt_lab.ipynb) — main workflow
- [`helpers.py`](helpers.py) — thin wrappers over `apps/api` services (no HTTP server)
- [`models_catalog.md`](models_catalog.md) — comprehensive human-readable model inventory
- [`models_catalog.json`](models_catalog.json) — machine-readable catalog for filtering in notebooks

```python
import helpers as h
h.catalog_df(status="easy", role="accuracy").head(20)
h.catalog_df(mode="cloud", family="deepgram")
```
