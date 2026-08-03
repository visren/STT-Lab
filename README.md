# STT Lab

Compare speech-to-text models side-by-side, collect personal voice↔transcript pairs, and LoRA-fine-tune Whisper on your own samples.

## Stack

- **Web**: Next.js (App Router) + TypeScript + Tailwind — `apps/web`
- **Notebook**: Jupyter Lab — `notebooks/stt_lab.ipynb`
- **Model catalog**: `notebooks/models_catalog.md` (+ `.json`)
- **API**: FastAPI — `apps/api`
- **Local STT**: faster-whisper (`tiny` / `base` / `small` / `medium`)
- **Cloud STT**: OpenAI Whisper, Deepgram Nova-2, AssemblyAI (API keys optional)
- **Adaptation**: Hugging Face Transformers + PEFT LoRA
- **Storage**: SQLite + `data/` for audio, datasets, adapters

## Quick start

### 1. API

```bash
cd apps/api
python3.13 -m venv .venv   # or another 3.11+ interpreter
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # add cloud keys if desired
uvicorn app.main:app --reload --port 8000
```

### 2. Web

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The UI talks to the API at `http://localhost:8000` (`NEXT_PUBLIC_API_URL` to override).

### 3. Notebook (alternative UI)

No web server required — the notebook imports the same Python backend.

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name=stt-lab --display-name="STT Lab"

cd ../../notebooks
jupyter lab stt_lab.ipynb
```

Pick the **STT Lab** kernel. Workflow cells cover compare → dataset → LoRA adapt → evaluate.

## Workflow

1. **Compare** — upload or record audio, select models, optional reference text → WER/CER, latency, word diffs
2. **Datasets** — save clips from Compare or upload new ones; edit transcripts; mark train/val
3. **Adapt** — pick a dataset + Whisper size, start LoRA job, watch logs, evaluate before/after on val
4. **Settings** — cloud API keys and model readiness

Adapted adapters appear under **Compare** as selectable models once a job completes.

## Notes

- First local Whisper run downloads model weights (cached by faster-whisper / Hugging Face).
- Fine-tuning on CPU is allowed but very slow; prefer CUDA. On Apple Silicon, training uses MPS when available; faster-whisper inference uses CPU/CTranslate2.
- Keep secrets in `apps/api/.env` (gitignored).
- Aim for ~30+ train samples and at least one val sample before fine-tuning.

## Project layout

```
stt-lab/
  apps/web/       # Next.js UI
  apps/api/       # FastAPI backend
  notebooks/      # Jupyter Lab interface
  data/           # runtime audio, datasets, adapters, sqlite
  README.md
```
