# STT Lab — Product Requirements

Status: draft  
Last updated: 2026-08-03

## 1. Vision

Help users **research, customize, and use** speech-to-text on their own terms:

1. Experiment with models (local and cloud)  
2. Fine-tune on personal voice/data  
3. Run a daily dictation app that can stay **fully local** or use the **cloud**, with full control over **data** and **models**

STT Lab is not a single locked pipeline. It is a lab + runtime where privacy, compute location, and model choice are user decisions.

## 2. Product surfaces

### 2.1 Research lab (exists)
- Notebook-first workflow (`notebooks/stt_lab.ipynb`)
- Model catalog and side-by-side compare  
- Personal dataset collection (audio ↔ transcript)  
- Fine-tune Whisper (LoRA) locally; cloud training hook reserved  
- Before/after evaluation (WER/CER, latency)

### 2.2 Model lab environment
- Isolated compute env to **build and test** models (`envs/model-lab`)  
- Same `stt_lab` APIs as the notebook (compare smoke, fine-tune, evaluate)  
- Optional GPU; can pull training data from the dataset vault  

### 2.3 Dataset vault environment
- Secure host for voice↔transcript datasets (`dataset-vault` / MinIO)  
- Private bucket, encryption at rest, explicit push/pull only  
- Local `data/datasets/` remains a working cache; vault is durable/shared store  

### 2.4 Dictation app (to build)
- Local frontend always (hotkey, mic, UI, insert text into focused app)  
- Pluggable STT runtime: **local** or **cloud**  
- Optional polish/rewrite layer (local or cloud LLM)  
- Loads user-chosen base model + optional adapter from the lab  

```text
[Local frontend]
    → capture audio / hotkey / paste text
    → STT runtime (local | cloud)   [user choice]
    → optional polish (local | cloud | off)
    → insert into active application
```

## 3. Core principles

1. **Frontend is fully local** — capture, UX, and text insertion never require a vendor desktop cloud UI.  
2. **Compute is optional cloud** — transcription and polish may run local or remote.  
3. **Fully customizable models** — users pick base model, adapter, cloud endpoint, and polish model.  
4. **Fully customizable data** — users decide what (if anything) leaves the device and what is retained.  
5. **Same UX either mode** — switching local ↔ cloud must not change the dictation workflow.  
6. **Lab feeds the app** — models/adapters produced in research are first-class runtimes in dictation.

## 4. Operating modes

| Mode | Audio leaves device? | Models | Typical use |
|---|---|---|---|
| **Fully local** | No | On-device STT (+ optional local polish) | Privacy-sensitive, offline, personal adapter |
| **Hybrid** | Yes (user-approved) | Local STT + cloud polish, or cloud STT + local UI | Best quality / low local GPU |
| **Cloud STT** | Yes | Remote transcription endpoint | Convenience, shared team endpoint |

Mode is a **user setting** (default should be explicit; recommend defaulting to local for this product).

## 5. Customization requirements

### 5.1 Models
Users must be able to configure:

- STT engine/provider (e.g. faster-whisper local, OpenAI-compatible cloud, Deepgram, custom URL)  
- Base model id/size (e.g. `whisper-small`, `large-v3-turbo`)  
- Personal adapter path / id (from lab fine-tune)  
- Language / prompt / vocabulary bias (where supported)  
- Optional polish model (off | local LLM | cloud LLM)  
- Per-app style profiles later (email vs chat vs code) — nice-to-have

### 5.2 Data
Users must be able to configure:

- Whether raw audio may be sent off-device  
- Whether transcripts may be sent off-device (e.g. polish-only cloud)  
- Local retention: keep history / timed delete / never store  
- Export of clips + transcripts into lab datasets for fine-tune  
- Clear indicator in UI when a run will leave the device  

### 5.3 Cloud endpoints
When cloud is enabled, users bring their own:

- API base URL and key, **or**  
- A project-hosted endpoint they control (e.g. Modal / HF / private API)  

No hard dependency on a single commercial vendor for core STT.

## 6. User journeys

### 6.1 Research → personal model
1. Compare models on own voice samples in the notebook  
2. Build train/val dataset  
3. Fine-tune (local now; cloud training when implemented)  
4. Evaluate before/after  
5. Register adapter as a runnable model for dictation  

### 6.2 Daily dictation (local)
1. Set mode = fully local  
2. Select base + adapter  
3. Hold hotkey → speak → release  
4. Text inserted at cursor; audio never uploaded  

### 6.3 Daily dictation (cloud)
1. Set mode = cloud (or hybrid)  
2. Configure endpoint + keys  
3. Same hotkey UX  
4. UI shows “sending audio to &lt;endpoint&gt;” before/while processing  

## 7. Functional requirements

### Research lab
- [x] Catalog of experiment models  
- [x] Multi-model compare with WER/CER/latency  
- [x] Dataset CRUD for personal pairs  
- [x] Local LoRA fine-tune + job status  
- [ ] Cloud fine-tune backend (Modal / HF Jobs / RunPod)  
- [x] Evaluate adapted vs base  
- [x] Export “runnable profile” (model + adapter + defaults) for the dictation app  

### Dictation app (MVP)
- [ ] Global hotkey record/stop  
- [ ] Local STT via chosen Whisper (+ adapter)  
- [ ] Cloud STT via configurable OpenAI-compatible (or provider) endpoint  
- [ ] Mode toggle: local / cloud / hybrid  
- [ ] Insert transcript into focused field  
- [ ] Basic filler-word cleanup (local rules)  
- [ ] Custom dictionary / replacements  
- [ ] On-device history with retention policy  
- [ ] Privacy indicator (local vs leaving device)  

### Dictation app (later)
- [ ] Optional LLM polish (local or cloud)  
- [ ] Tone / style presets  
- [ ] Per-app profiles  
- [ ] Streaming partials  
- [ ] Team shared endpoints + SSO (enterprise)  

## 8. Non-goals (near term)

- Replacing Wispr Flow feature-for-feature on day one  
- Forcing all users through a hosted SaaS STT we operate as the only option  
- Mobile keyboard v1 (desktop-first)  
- Training non-Whisper families in-lab until local Whisper path is solid  

## 9. Success criteria

- User can complete research → fine-tune → dictate loop on one machine with **zero cloud**  
- User can point the same dictation UX at a **cloud endpoint** without changing hotkey habits  
- User can swap models/adapters without reinstalling the app  
- User always knows whether audio/transcripts leave the device  

## 10. Relationship to current codebase

| Area | Role |
|---|---|
| `stt_lab/` | Core library: providers, policy, pipeline, profiles, LoRA, evaluate |
| `notebooks/` | Research UI |
| `docs/PRODUCT_REQUIREMENTS.md` | Product requirements |
| `docs/ARCHITECTURE.md` | System architecture (refined from these requirements) |
| Dictation app (future) | Local frontend + sidecar calling `stt_lab.pipeline` |

## 11. Open decisions

Working defaults are recorded in [`ARCHITECTURE.md`](ARCHITECTURE.md). Still open:

- Desktop shell: Mac-first Tauri/Swift + Python sidecar (default lean) vs pure native  
- Default mode on first launch: `fully_local` vs ask-on-first-run  
- Cloud training provider priority (Modal vs HF Jobs vs RunPod)  
- Whether polish LLM is in MVP or post-MVP (architecture: post-MVP stub)

---

These requirements govern design choices: if a feature reduces model/data customizability or removes the local-only path, it does not ship.
