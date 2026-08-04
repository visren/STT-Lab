# Dataset vault — production hardening

Local defaults (`docker-compose.yml`) already:

- Private bucket (`anonymous none`)
- App user with `readwrite` (not root for clients)
- Loopback-only published ports (`127.0.0.1`)
- Optional SSE-S3 via `VAULT_KMS_SECRET_KEY`
- Healthcheck + restart policy

## TLS (recommended)

```bash
./envs/vault/scripts/gen-certs.sh
# edit envs/.env: VAULT_TLS_DOMAIN=vault.local

docker compose \
  -f envs/docker-compose.yml \
  -f envs/docker-compose.prod.yml \
  --env-file envs/.env up -d
```

- MinIO is **not** published on the host in the prod overlay  
- Caddy terminates HTTPS and reverse-proxies the S3 API  
- Point clients at `https://vault.local` with:

```bash
VAULT_ENDPOINT=https://vault.local
VAULT_SECURE=true
```

For public DNS + Let’s Encrypt, swap the Caddyfile volume to `envs/vault/Caddyfile` and set `VAULT_TLS_EMAIL`.

## Backups

```bash
./envs/vault/scripts/backup.sh
# optional encryption:
VAULT_BACKUP_PASSPHRASE='…' ./envs/vault/scripts/backup.sh

./envs/vault/scripts/restore.sh data/vault-backups/vault-….tar.gz
```

Or run the compose backup profile:

```bash
VAULT_BACKUP_HOST_DIR="$PWD/data/vault-backups" \
docker compose -f envs/docker-compose.yml -f envs/docker-compose.prod.yml \
  --env-file envs/.env --profile backup up -d vault-backup
```

## Checklist

- [ ] Strong unique `VAULT_ROOT_PASSWORD` / `VAULT_SECRET_KEY` (hex, no leading `-`)
- [ ] `VAULT_KMS_SECRET_KEY` set for SSE-S3
- [ ] TLS via Caddy (prod overlay) or private network only
- [ ] Console not exposed publicly (`MINIO_BROWSER=off` in prod overlay)
- [ ] Encrypted off-host backups + restore drill
- [ ] Least-privilege app keys per machine/user
- [ ] Rotate keys when laptops leave the trust boundary
