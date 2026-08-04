# STT Lab

Notebook-first lab to compare speech-to-text models, collect personal voice↔transcript data, LoRA-fine-tune Whisper, and run a local dictation app with local/cloud STT.

## Layout

```text
stt-lab/
  stt_lab/            # core library (providers, pipeline, policy, vault, cloud FT)
  notebooks/          # research UI
  apps/dictation/     # local hotkey dictation app
  envs/               # model-lab + dataset-vault (Docker, TLS, backups)
  docs/               # PRD + architecture
  data/               # runtime audio, datasets, adapters, profiles
  requirements.txt
  .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
make install                 # or: pip install -r requirements.txt && pip install -e .
cp .env.example .env         # optional cloud keys + vault client settings

# macOS dictation mic backend
brew install portaudio
```

Fast unit-test install (no torch):

```bash
make install-ci && make test-ci
```

## Build (model-lab)

```bash
cp envs/.env.example envs/.env   # once
make vault-up
make model-lab-build             # BuildKit + CPU torch + multi-stage
make model-lab-doctor
make model-lab                   # interactive shell
```

Dependency layers live under `requirements/` (`base`, `ml`, `research`, `dictation`, `model-lab`, `ci`).


## Research notebook

```bash
source .venv/bin/activate
cd notebooks && jupyter lab stt_lab.ipynb
```

```python
import helpers as h
h.compare("data/audio/clip.wav", ["whisper-tiny"], reference="…")
h.start_finetune(dataset_id, base_model="tiny", backend="local")   # or backend="cloud"
h.export_profile(profile_id="mine", name="Mine", base_model="tiny")
```

## Dictation app

```bash
python -m apps.dictation --profile demo-local
# Hold Ctrl+Alt+Space to talk; Ctrl+Alt+L / Ctrl+Alt+C toggles local/cloud
```

See [`apps/dictation/README.md`](apps/dictation/README.md).

## Environments

See [`envs/README.md`](envs/README.md) and [`envs/HARDENING.md`](envs/HARDENING.md).

```bash
cp envs/.env.example envs/.env   # set vault passwords
docker compose -f envs/docker-compose.yml --env-file envs/.env up -d dataset-vault dataset-vault-init
docker compose -f envs/docker-compose.yml --env-file envs/.env run --rm model-lab
```

- **model-lab** — build/test/fine-tune in Docker  
- **dataset-vault** — private MinIO; prod overlay adds TLS (Caddy) + backups  

## Fine-tune backends

| Backend | Notes |
|---|---|
| `local` | Whisper LoRA via PEFT |
| `cloud` | Uses `CLOUD_FINETUNE_BACKEND` (`stub` dry-run lifecycle; `modal`/`hf_jobs`/`runpod` reserved) |

## Notes

- Prefer ~30+ train samples and at least one val sample before serious fine-tunes  
- Keys / vault credentials live in `.env` (gitignored)  
- Product: [`docs/PRODUCT_REQUIREMENTS.md`](docs/PRODUCT_REQUIREMENTS.md)  
- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
