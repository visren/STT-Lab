# Environments

Two isolated environments support the product architecture:

| Environment | Purpose | How it runs |
|---|---|---|
| **model-lab** | Build, smoke-test, and fine-tune models | Docker image + CLI |
| **dataset-vault** | Privately host voice↔transcript datasets | MinIO (S3 API), private bucket + SSE |

```text
notebook / dictation ──► stt_lab
                           ├─ model-lab (train/test compute)
                           └─ dataset-vault (secure dataset objects)
```

## Quick start

```bash
# from repo root
cp envs/.env.example envs/.env
# edit VAULT_ROOT_PASSWORD and VAULT_SECRET_KEY to strong values

# 1) Start secure dataset vault
docker compose -f envs/docker-compose.yml --env-file envs/.env up -d dataset-vault dataset-vault-init

# Console UI: http://localhost:9001  (root user/password from envs/.env)
# S3 API:     http://localhost:9000

# 2) Enter model-lab shell
docker compose -f envs/docker-compose.yml --env-file envs/.env run --rm model-lab

# inside model-lab:
python -m envs.model_lab.cli models
python -m envs.model_lab.cli smoke --audio data/audio/your.wav --models whisper-tiny
```

Also copy vault keys into the repo root `.env` so the notebook can push/pull datasets:

```bash
# root .env
VAULT_ENDPOINT=http://127.0.0.1:9000
VAULT_ACCESS_KEY=stt_vault_app
VAULT_SECRET_KEY=...same as envs/.env...
VAULT_BUCKET=stt-datasets
VAULT_SECURE=false
```

## model-lab

- Isolated Python image with `stt_lab` + training deps  
- Repo mounted at `/workspace`  
- Commands:
  - `python -m envs.model_lab.cli models`
  - `python -m envs.model_lab.cli smoke --audio ... --models whisper-tiny,whisper-base`
  - `python -m envs.model_lab.cli finetune --dataset-id ... --wait`

GPU: uncomment the `deploy.resources` section in `docker-compose.yml` when NVIDIA Container Toolkit is available, and set `WHISPER_DEVICE=cuda`.

## dataset-vault

Security defaults on init:

- Bucket is **private** (`anonymous none`)  
- App user gets `readwrite` (not anonymous public)  
- Credentials only in `envs/.env` (gitignored)  
- Optional **SSE-S3**: set `VAULT_KMS_SECRET_KEY=keyname:$(openssl rand -base64 32)` then recreate vault

Notebook / library usage:

```python
import helpers as h
h.vault_status()
h.vault_push_dataset(dataset_id)
h.vault_pull_dataset(dataset_id)
h.vault_list("datasets/")
```

### Production hardening (recommended)

- Put vault behind TLS (Caddy/nginx or MinIO certs)  
- Use distinct least-privilege keys per machine/user  
- Disable console port on public networks  
- Back up the `dataset_vault_data` volume encrypted  
- For cloud: point `VAULT_ENDPOINT` at private S3/MinIO with the same client  

## Stop

```bash
docker compose -f envs/docker-compose.yml --env-file envs/.env down
# add -v to wipe vault volume (destructive)
```
