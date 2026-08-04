# Dictation app

Local push-to-talk dictation on top of `stt_lab` profiles.

## Features (MVP)

- Global **push-to-talk** hotkey (default `Ctrl+Alt+Space`)
- **Insert text** into the focused app (clipboard + paste)
- **Local / cloud toggle** (`Ctrl+Alt+L` / `Ctrl+Alt+C`)
- Privacy banner when audio will leave the device
- On-device history under `data/history/` (policy-gated)

## Setup

```bash
# from repo root
source .venv/bin/activate
pip install -r requirements.txt

# macOS mic backend
brew install portaudio
```

macOS permissions for your terminal (or Python):

1. **Microphone**
2. **Accessibility** (for global hotkeys + paste)

## Run

```bash
python -m apps.dictation --profile demo-local
python -m apps.dictation --list-profiles
python -m apps.dictation --mode cloud --profile demo-local
python -m apps.dictation --once data/audio/smoke.wav --mode local
```

Export a profile from the notebook first if you want a personal adapter:

```python
h.export_profile(profile_id="mine", name="Mine", base_model="tiny", adapter_id="…")
```

For cloud mode, set `OPENAI_API_KEY` (or another provider key) and optionally
`meta.cloud_provider` / `cloud.stt_base_url` on the profile.
