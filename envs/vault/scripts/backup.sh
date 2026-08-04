#!/usr/bin/env bash
# Backup the dataset-vault bucket to an encrypted local archive (or plain tar).
#
# Usage:
#   ./envs/vault/scripts/backup.sh
#   BACKUP_DIR=/secure/backups ./envs/vault/scripts/backup.sh
#
# Requires: docker compose vault running + mc inside a one-shot container,
# or host `mc` configured. Uses compose network by default.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/envs/.env}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/data/vault-backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

mkdir -p "$BACKUP_DIR"

# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

BUCKET="${VAULT_BUCKET:-stt-datasets}"
OUT_TAR="$BACKUP_DIR/vault-${BUCKET}-${STAMP}.tar.gz"

echo "Mirroring s3://${BUCKET} → staging…"
docker compose -f "$ROOT/envs/docker-compose.yml" --env-file "$ENV_FILE" run --rm \
  -v "$WORKDIR:/backup" \
  --entrypoint /bin/sh \
  dataset-vault-init -c "
    set -e
    mc alias set vault http://dataset-vault:9000 \"\$VAULT_ROOT_USER\" \"\$VAULT_ROOT_PASSWORD\"
    mc mirror --overwrite \"vault/\${VAULT_BUCKET}\" /backup/data
    mc admin info vault > /backup/minio-info.txt || true
  "

tar -C "$WORKDIR" -czf "$OUT_TAR" .
echo "Wrote $OUT_TAR"

if [[ -n "${VAULT_BACKUP_GPG_RECIPIENT:-}" ]] && command -v gpg >/dev/null; then
  gpg --encrypt --recipient "$VAULT_BACKUP_GPG_RECIPIENT" --output "${OUT_TAR}.gpg" "$OUT_TAR"
  rm -f "$OUT_TAR"
  echo "Encrypted → ${OUT_TAR}.gpg"
elif [[ -n "${VAULT_BACKUP_PASSPHRASE:-}" ]] && command -v gpg >/dev/null; then
  gpg --batch --yes --passphrase "$VAULT_BACKUP_PASSPHRASE" \
    --symmetric --cipher-algo AES256 \
    --output "${OUT_TAR}.gpg" "$OUT_TAR"
  rm -f "$OUT_TAR"
  echo "Encrypted (symmetric) → ${OUT_TAR}.gpg"
else
  echo "Tip: set VAULT_BACKUP_GPG_RECIPIENT or VAULT_BACKUP_PASSPHRASE for at-rest encryption"
fi

# Retention: keep last N backups
KEEP="${VAULT_BACKUP_KEEP:-14}"
i=0
while IFS= read -r f; do
  i=$((i + 1))
  if [[ "$i" -gt "$KEEP" ]]; then
    rm -f "$f"
  fi
done < <(ls -1t "$BACKUP_DIR"/vault-*.tar.gz* 2>/dev/null || true)
echo "Backup complete (keeping last ${KEEP})"
