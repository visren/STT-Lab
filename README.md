# STT Lab

Compare speech-to-text models (local Whisper + cloud APIs), build a personal voice↔transcript dataset, and LoRA-fine-tune Whisper on your own samples.

## Layout

```
stt-lab/
  apps/web/       # Next.js UI
  apps/api/       # FastAPI
  stt_lab/        # core library (providers, metrics, fine-tune)
  notebooks/      # optional research notebook
  data/           # runtime audio, datasets, adapters, sqlite
  requirements.txt
  .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional cloud keys

cd apps/web && npm install && cd ../..
```

## Run

Terminal 1 — API:

```bash
source .venv/bin/activate
python -m apps.api
# or: uvicorn apps.api.main:app --reload --port 8000
```

Terminal 2 — Web:

```bash
cd apps/web && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Workflow

1. **Compare** — upload/record audio, select models, run side-by-side (WER/CER when you provide a reference)
2. **Datasets** — save clips + ground-truth transcripts; mark train / val
3. **Fine-tune** — LoRA-adapt Whisper locally; cancel anytime; evaluate before/after on val
4. **Settings** — cloud API keys + model readiness (also via `.env`)

Adapted adapters appear in the Compare model list as `adapted-…`.

## Models

| Kind | IDs |
|---|---|
| Local | `whisper-tiny`, `whisper-base`, `whisper-small`, `whisper-medium` |
| Cloud | `openai-whisper-1`, `deepgram-nova-2`, `assemblyai-best` |
| Adapted | completed LoRA jobs |

## Notes

- Prefer ~30+ train samples and at least one val sample before serious fine-tunes
- First Whisper run downloads weights
- Keys in `.env` or Settings (`data/local_keys.json`, gitignored)
- Notebook workflow remains available under `notebooks/`
