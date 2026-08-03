# STT / ASR models catalog (comprehensive)

Living research inventory for STT Lab.  
Last expanded: **2026-08-03**. Sources drift quickly — verify HF cards / provider docs before committing experiments.

**Status in this repo**

| Status | Meaning |
|---|---|
| `wired` | Selectable in Compare / notebook today |
| `easy` | Fits current provider pattern with modest work |
| `medium` | New runtime or SDK (NeMo, FunASR, Riva, etc.) |
| `hard` | Enterprise / niche / heavy infra |
| `n/a` | Hosted-only or not applicable |

**Experiment roles**

| Role | Intent |
|---|---|
| baseline | Always-include reference |
| accuracy | Lowest WER candidates |
| speed | Throughput / RTF / streaming latency |
| multilingual | Non-English / many languages |
| edge | On-device / tiny footprint |
| adapt | Personal voice fine-tune friendly |
| commercial | Paid API ceiling / product baseline |
| domain | Medical, phone, finance, meetings |

Also see machine-readable: [`models_catalog.json`](models_catalog.json).

---

## 0. Wired in STT Lab today

| ID | Display | Family | Mode | Adapt here? | Needs |
|---|---|---|---|---|---|
| `whisper-tiny` | Whisper tiny | OpenAI Whisper | local | yes LoRA | none |
| `whisper-base` | Whisper base | OpenAI Whisper | local | yes LoRA | none |
| `whisper-small` | Whisper small | OpenAI Whisper | local | yes LoRA | none |
| `whisper-medium` | Whisper medium | OpenAI Whisper | local | yes LoRA | none |
| `openai-whisper-1` | OpenAI Whisper | OpenAI API | cloud | no | `OPENAI_API_KEY` |
| `deepgram-nova-2` | Deepgram Nova-2 | Deepgram | cloud | no* | `DEEPGRAM_API_KEY` |
| `assemblyai-best` | AssemblyAI Best | AssemblyAI | cloud | no* | `ASSEMBLYAI_API_KEY` |
| `adapted-<job_id>` | Adapted Whisper | Whisper+LoRA | local | n/a | completed Adapt job |

\* Provider may offer their own vocab/model adaptation APIs — not the same as exporting a Whisper LoRA into this lab.

---

## 1. OpenAI Whisper family (local + hosted)

Canonical research lineage. Best ecosystem for this repo’s LoRA path.

| Model | HF / ID | Params (approx) | Langs | Role | STT Lab status | Notes |
|---|---|---|---|---|---|---|
| Whisper tiny | `openai/whisper-tiny` | 39M | 99 | edge, adapt | wired | fastest smoke |
| Whisper tiny.en | `openai/whisper-tiny.en` | 39M | en | edge | easy | English-only |
| Whisper base | `openai/whisper-base` | 74M | 99 | baseline, adapt | wired | Mac default |
| Whisper base.en | `openai/whisper-base.en` | 74M | en | baseline | easy | |
| Whisper small | `openai/whisper-small` | 244M | 99 | accuracy, adapt | wired | good personal FT |
| Whisper small.en | `openai/whisper-small.en` | 244M | en | accuracy | easy | |
| Whisper medium | `openai/whisper-medium` | 769M | 99 | accuracy, adapt | wired | heavier local |
| Whisper medium.en | `openai/whisper-medium.en` | 769M | en | accuracy | easy | |
| Whisper large-v2 | `openai/whisper-large-v2` | 1550M | 99 | baseline | easy | superseded by v3 |
| Whisper large-v3 | `openai/whisper-large-v3` | 1550M | 99 | multilingual, baseline | easy | still best “any language” default |
| Whisper large-v3-turbo | `openai/whisper-large-v3-turbo` | ~809M | 99 | speed, multilingual | easy | pruned decoder; high priority add |
| Distil-Whisper large-v2 | `distil-whisper/distil-large-v2` | ~756M | en | speed | easy | English |
| Distil-Whisper large-v3 | `distil-whisper/distil-large-v3` | ~756M | en | speed | easy | ~5–6× Whisper speed |
| Distil-Whisper large-v3.5 | `distil-whisper/distil-large-v3.5` | ~756M | en | speed | easy | newer distill |
| Distil-Whisper medium.en | `distil-whisper/distil-medium.en` | — | en | speed | easy | |
| Distil-Whisper small.en | `distil-whisper/distil-small.en` | — | en | edge | easy | |
| CrisperWhisper | `nyrahealth/CrisperWhisper` (and variants) | Whisper-FT | en | accuracy | medium | verbatim / disfluency-oriented |
| Whisper API `whisper-1` | OpenAI API | hosted | many | commercial | wired | batch API |
| Whisper large-v3 (Groq) | Groq hosted | hosted | many | speed, commercial | easy | OpenAI-compatible hosts |
| Whisper large-v3-turbo (Groq) | Groq hosted | hosted | many | speed | easy | often cheapest Whisper host |
| Ink-Whisper | Cartesia | hosted | many | speed, commercial | easy | Whisper re-arch for realtime |

**Runtimes:** faster-whisper, whisper.cpp, WhisperKit (Apple), transformers, OpenAI API, Groq, Fireworks, Together, DeepInfra, etc.

---

## 2. NVIDIA NeMo / Parakeet / Canary

Top open-weight accuracy & throughput on HF Open ASR Leaderboard. Runtime: **NeMo** (not faster-whisper).

### Parakeet

| Model | HF ID | Decoder | Langs | Role | Status |
|---|---|---|---|---|---|
| Parakeet TDT 0.6B v2 | `nvidia/parakeet-tdt-0.6b-v2` | TDT | en | accuracy, speed | medium |
| Parakeet TDT 0.6B v3 | `nvidia/parakeet-tdt-0.6b-v3` | TDT | ~25 EU | multilingual, speed | medium |
| Parakeet TDT 1.1B | `nvidia/parakeet-tdt-1.1b` | TDT | en | accuracy, speed | medium |
| Parakeet TDT+CTC 1.1B | `nvidia/parakeet-tdt_ctc-1.1b` | TDT/CTC | en | speed | medium |
| Parakeet TDT+CTC 0.6B JA | `nvidia/parakeet-tdt_ctc-0.6b-ja` | TDT/CTC | ja | multilingual | medium |
| Parakeet CTC 0.6B | `nvidia/parakeet-ctc-0.6b` | CTC | en | speed | medium |
| Parakeet CTC 1.1B | `nvidia/parakeet-ctc-1.1b` | CTC | en | speed | medium |
| Parakeet RNNT 0.6B | `nvidia/parakeet-rnnt-0.6b` | RNNT | en | accuracy | medium |
| Parakeet RNNT 1.1B | `nvidia/parakeet-rnnt-1.1b` | RNNT | en | accuracy | medium |
| Multitalker Parakeet streaming 0.6B | `nvidia/multitalker-parakeet-streaming-0.6b-v1` | RNNT | en | streaming, diarization-ish | medium |

### Canary (ASR + AST multitask)

| Model | HF ID | Langs / tasks | Role | Status |
|---|---|---|---|---|
| Canary 1B | `nvidia/canary-1b` | en/de/fr/es + translation | accuracy, multilingual | medium |
| Canary 1B v2 | `nvidia/canary-1b-v2` | broader EU / Granary | accuracy, multilingual | medium |
| Canary 1B Flash | `nvidia/canary-1b-flash` | 4-lang fast | speed | medium |
| Canary 180M Flash | `nvidia/canary-180m-flash` | smaller | edge, speed | medium |
| Canary-Qwen 2.5B | `nvidia/canary-qwen-2.5b` (verify card) | en (+ LLM decode modes) | accuracy | medium |

### Classic NeMo English Conformers (still useful baselines)

Examples (many more on NGC/NeMo checkpoints list):

- `stt_en_fastconformer_ctc_large` / `_xlarge` / `_xxlarge`
- `stt_en_fastconformer_transducer_large` / `_xlarge`
- `stt_en_conformer_ctc_large` / `_small`
- `stt_en_citrinet_1024_gamma_0_25`
- Language-specific FastConformer hybrids: `stt_{ar,de,es,fr,it,nl,pl,pt,ru,ua,...}_fastconformer_hybrid_large_pc`

**Fine-tune:** NeMo training recipes (not current PEFT Whisper runner).  
**Hosted:** NVIDIA Riva / NIM endpoints for some Canary/Parakeet variants.

---

## 3. Speech LLM / multimodal ASR (open)

Encoder + LLM decoder systems; strong leaderboard accuracy, heavier to run.

| Model | Org | HF / ID (verify) | Langs | Role | Status |
|---|---|---|---|---|---|
| Granite Speech 3.3 2B | IBM | `ibm-granite/granite-speech-3.3-2b` | multi | accuracy | medium |
| Granite Speech 3.3 8B | IBM | `ibm-granite/granite-speech-3.3-8b` | multi + AST | accuracy | medium |
| Granite Speech 4.1 2B | IBM | check HF `ibm-granite/*` | multi | accuracy | medium |
| Granite Speech 4.1 plus | IBM | check HF | timestamps etc. | accuracy | medium |
| Phi-4 Multimodal Instruct | Microsoft | `microsoft/Phi-4-multimodal-instruct` | multi | accuracy | medium |
| Voxtral Mini / Small | Mistral | `mistralai/Voxtral-*` | multi | accuracy, commercial API too | medium |
| Qwen3-ASR 0.6B / 1.7B | Alibaba | `Qwen/Qwen3-ASR-*` | 50+ | multilingual | medium |
| Qwen3-ASR Flash (API) | Alibaba Model Studio | hosted | 25+ | commercial | easy |
| Cohere Transcribe (~2B) | Cohere | check release card | en-focused | accuracy | medium |
| ARK-ASR / MOSS-Transcribe | various | check HF | en/zh | accuracy | research |
| Kyutai STT | Kyutai | check HF | — | streaming research | medium |

---

## 4. Edge / on-device / tiny ASR

| Model | ID / project | Size | Role | Status |
|---|---|---|---|---|
| Moonshine tiny/base | Useful Sensors (`UsefulSensors/moonshine-*`) | 27M–331M | edge | medium |
| Whisper tiny/base via whisper.cpp | ggerganov/whisper.cpp | tiny→large | edge | medium |
| WhisperKit | argmaxinc/WhisperKit | Apple Silicon | edge | medium |
| MLX Whisper | mlx-community Whisper ports | Apple Silicon | edge | medium |
| Sherpa-ONNX ports | k2-fsa/sherpa-onnx | many | edge | medium |
| Vosk models | alphacephei.com/vosk | tiny–large | edge, offline | medium |
| Coqui STT (legacy) | coqui-ai | — | legacy | hard |
| DeepSpeech (legacy) | Mozilla | — | legacy — skip | n/a |

---

## 5. Self-supervised / classic research ASR

Useful for academic baselines and domain FT, less “drop-in product STT”.

| Family | Examples | Role | Status |
|---|---|---|---|
| wav2vec 2.0 | `facebook/wav2vec2-base-960h`, `wav2vec2-large-960h-lv60-self` | research baseline | medium |
| HuBERT | `facebook/hubert-large-ls960-ft` | research | medium |
| WavLM | `microsoft/wavlm-libri-clean-100h-base-plus` | research | medium |
| data2vec | Facebook data2vec audio FT heads | research | medium |
| MMS | `facebook/mms-1b-all`, language adapters | multilingual | medium |
| SeamlessM4T v2 | Meta Seamless | ASR+AST+MT | medium |
| SpeechBrain recipes | LibriSpeech ASR, CommonVoice | research toolkit | medium |
| ESPnet recipes | Whisper finetune, Conformer ASR | research toolkit | medium |
| Kaldi | tdnn/chain recipes | legacy research | hard |
| OWSM / OWSM-CTC | CMU | multilingual open whisper-style | medium |

---

## 6. Chinese / Asian open ASR stacks

| Model / stack | Examples | Role | Status |
|---|---|---|---|
| FunASR / SenseVoice | `FunAudioLLM/SenseVoiceSmall`, Paraformer, SeACo | multilingual, emotion tags | medium / easy via SiliconFlow |
| TeleSpeechASR | `TeleAI/TeleSpeechASR` | ASR | easy via SiliconFlow |
| Whisper-medium/large zh FT | community HF finetunes | domain zh | easy |
| FireRedASR | FireRedTeam models | zh ASR | medium |
| WeNet | U2++ Conformer | streaming zh | medium |
| Paraformer-zh | ModelScope | zh batch | medium |

---

## 7. Cloud / commercial APIs (comprehensive)

### OpenAI
| Model | Mode | Role | Status |
|---|---|---|---|
| `whisper-1` | batch | commercial baseline | wired |
| `gpt-4o-transcribe` | batch (+ streaming variants) | accuracy | easy |
| `gpt-4o-mini-transcribe` | batch/stream | speed, cost | easy |
| `gpt-4o-transcribe-diarize` | batch | diarization | easy |
| Realtime / S2S stacks | realtime | agents | medium |

### Deepgram
| Model | Mode | Role | Status |
|---|---|---|---|
| Nova-3 | batch + realtime | accuracy, noisy, commercial | easy (upgrade from nova-2) |
| Nova-3 Medical | domain | medical | easy |
| Nova-2 | batch + realtime | commercial | wired |
| Nova-2 conversationalai | realtime | agents | easy |
| Nova-2 phonecall / voicemail / meeting / finance | domain | domain | easy |
| Flux (multilingual streaming) | realtime | streaming, multilingual | easy |
| Enhanced / Base (legacy tiers) | batch | cost ladder | easy |

### AssemblyAI
| Model | Mode | Role | Status |
|---|---|---|---|
| Universal-3.5 Pro | batch | accuracy | easy (upgrade) |
| Universal-3 Pro | batch | accuracy | easy |
| Universal-2 | batch | multilingual fallback | easy |
| Universal-3.5 Pro Streaming | realtime | agents | medium |
| Universal Streaming / Multilingual Streaming | realtime | streaming | medium |
| Slam-1 / audio intelligence add-ons | post | NLU | n/a for pure WER |

### Google Cloud Speech-to-Text
| Model | Mode | Role | Status |
|---|---|---|---|
| Chirp 3 | batch/stream | multilingual, accuracy | medium |
| Chirp 2 | batch/stream | multilingual | medium |
| latest_long / latest_short | batch | long/short form | medium |
| telephony / command_and_search / default | batch | domain | medium |
| Medical models | domain | medical | medium |

### Microsoft Azure Speech
| Model | Mode | Role | Status |
|---|---|---|---|
| Latest Azure STT (locale models) | batch/stream | commercial, 100+ locales | medium |
| Custom Speech | adapt | cloud adaptation | medium |
| Fast transcription API | batch | speed | medium |

### Amazon
| Model | Mode | Role | Status |
|---|---|---|---|
| Amazon Transcribe (standard) | batch/stream | commercial | medium |
| Transcribe Medical | domain | medical HIPAA | medium |
| Call Analytics variants | domain | contact center | medium |

### Others (worth benchmarking)
| Provider | Models | Role | Status |
|---|---|---|---|
| SiliconFlow | `FunAudioLLM/SenseVoiceSmall`, `TeleAI/TeleSpeechASR` | open-weight hosted | easy |
| Speechmatics | Ursa 2 Enhanced / Standard, Flow realtime | accuracy, on-prem option | medium |
| Gladia | Solaria-1 (realtime), Solaria-3 (batch) | multilingual EU host | medium |
| ElevenLabs | Scribe / Scribe realtime | accuracy, tags | medium |
| Rev AI | Reverb, Turbo, Whisper Fusion | long-form | medium |
| Cartesia | Ink-Whisper, newer streaming STT | speed | easy |
| Soniox | async + realtime multilingual | cost, multilingual | medium |
| Mistral | Voxtral Mini Transcribe (API) | EU, value | easy |
| Alibaba Model Studio | Qwen3-ASR Flash | multilingual | easy |
| Groq | whisper-large-v3, large-v3-turbo | speed/cost Whisper host | easy |
| Fireworks / Together / DeepInfra / Replicate | various Whisper & open ASR | hosted open weights | easy |
| NVIDIA NIM / Riva | Canary, Parakeet, etc. | hosted NeMo | medium |
| IBM Watson STT | legacy+current | enterprise | hard |
| Tencent / Baidu / iFlytek ASR APIs | zh-focused | regional | medium |

---

## 8. Fine-tuning & adaptation matrix

| Approach | Models | Fits STT Lab Adapt? | Notes |
|---|---|---|---|
| PEFT LoRA on Whisper | tiny→large-v3 / turbo / Distil-Whisper | **yes (current)** | best personal-voice path here |
| Full FT Whisper | same | possible, heavy | needs more VRAM |
| NeMo FT | Parakeet, Canary, Conformers | not yet | separate trainer |
| SpeechBrain / ESPnet recipes | many | not yet | research |
| Cloud LLM FT (SiliconFlow etc.) | Qwen chat, image | **no for ASR** | wrong modality |
| Provider custom models | Azure Custom Speech, Deepgram keyword/adapt, AssemblyAI keyterms | partial | not portable adapters |
| GPU job hosts | Modal / HF Jobs / RunPod running our LoRA script | yes (infra add) | same adapters into `data/adapters/` |

---

## 9. Suggested experiment matrices

### A. Local speed–accuracy (wire next)
`whisper-tiny`, `base`, `small`, `large-v3-turbo`, Distil-Whisper large-v3

### B. Commercial ceiling
OpenAI `gpt-4o-transcribe` + `whisper-1`, Deepgram Nova-3, AssemblyAI Universal-3.5 Pro, Google Chirp 3

### C. Open SOTA English
Parakeet TDT 0.6B/1.1B, Canary-Qwen 2.5B, Granite Speech 4.1/3.3, Voxtral Mini

### D. Multilingual
Whisper large-v3, Parakeet TDT 0.6B v3, SenseVoice Small, Qwen3-ASR, Chirp 3

### E. Personal voice adapt
Train LoRA on `whisper-small` or `large-v3-turbo`; eval vs base + one cloud baseline

### F. Edge
Moonshine, whisper.cpp tiny/base, MLX Whisper on Apple Silicon

### G. Domain / conditions
Phone: Deepgram phonecall, Google telephony  
Meetings: Nova meeting, diarizing models  
Medical: Nova-3 Medical, AWS/Google medical  
Noisy: Nova-3, Speechmatics Enhanced

---

## 10. Priority add list for this repo

Ordered by research leverage vs integration cost:

1. **Whisper large-v3 + large-v3-turbo** (faster-whisper) — easy, unblocks real baselines  
2. **Distil-Whisper large-v3** — easy English speed baseline  
3. **Deepgram Nova-3** (+ domain variants) — easy upgrade of wired provider  
4. **OpenAI gpt-4o-transcribe / mini** — easy cloud ceiling  
5. **SiliconFlow SenseVoice / TeleSpeechASR** — easy OpenAI-compatible  
6. **Groq Whisper hosts** — easy cheap/fast hosted Whisper  
7. **NeMo Parakeet TDT 0.6B v3** — medium, open SOTA speed/multilingual  
8. **NeMo Canary-Qwen or Canary 1B v2** — medium, open SOTA accuracy  
9. **AssemblyAI Universal-3.5 Pro** — easy upgrade  
10. **Moonshine** — medium edge track  

---

## 11. How to use with the notebook

```python
import json
from pathlib import Path
import helpers as h

catalog = json.loads(Path("models_catalog.json").read_text())
# currently runnable
h.models_df()

# filter catalog
open_sota = [m for m in catalog["models"] if "accuracy" in m.get("roles", []) and m.get("license_class") == "open"]
```

Leaderboards to re-check periodically:
- [HF Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard)
- Provider model docs (Deepgram, AssemblyAI, OpenAI, Google Chirp)
- NeMo ASR checkpoints list

---

## 12. License cheat-sheet (high level)

| Class | Examples | Implication |
|---|---|---|
| MIT / Apache | Whisper, Distil-Whisper, Granite (often Apache) | easiest commercial reuse |
| CC-BY-4.0 | many NVIDIA Parakeet/Canary | attribution required |
| Hosted ToS | OpenAI, Deepgram, AssemblyAI, Google… | no weight export; API terms |
| Research / custom | some academic releases | read card carefully |

Always confirm the model card before publishing results or shipping a product.
