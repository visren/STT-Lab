# Notebooks

Primary research UI for STT Lab.

## Launch

```bash
# from repo root
source .venv/bin/activate
cd notebooks
jupyter lab stt_lab.ipynb
```

## Files

- `stt_lab.ipynb` — catalog → compare → dataset → finetune → evaluate → export profile
- `helpers.py` — thin notebook API over `stt_lab`
- `models_catalog.md` / `.json` — experiment inventory

```python
import helpers as h
h.catalog_df(status="easy", role="adapt")
h.compare("data/audio/clip.wav", ["whisper-tiny"], reference="…")
h.start_finetune(dataset_id, base_model="tiny", backend="local")
h.vault_status()
h.export_profile(profile_id="demo", name="Demo", base_model="tiny")
```
