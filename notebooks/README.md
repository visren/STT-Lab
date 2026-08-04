# Notebooks

## Launch

```bash
# from repo root
source .venv/bin/activate
cd notebooks
jupyter lab stt_lab.ipynb
```

Kernel: **STT Lab**

## Files

- `stt_lab.ipynb` — research → compare → pick → finetune → evaluate
- `helpers.py` — notebook API over `stt_lab`
- `models_catalog.md` / `.json` — experiment inventory

```python
import helpers as h
h.catalog_df(status="easy", role="adapt")
h.start_finetune(dataset_id, base_model="tiny", backend="local")
```
