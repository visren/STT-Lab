#!/usr/bin/env bash
# Restore a vault backup archive into the running dataset-vault.
#
# Usage:
#   ./envs/vault/scripts/restore.sh data/vault-backups/vault-stt-datasets-….tar.gz
#   ./envs/vault/scripts/restore.sh data/vault-backups/….tar.gz.gpg
set -euo pipefail

ARCHIVE="${1:?Usage: restore.sh <backup.tar.gz|.gpg>}"
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/envs/.env}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

SRC="$ARCHIVE"
if [[ "$ARCHIVE" == *.gpg ]]; then
  SRC="$WORKDIR/restore.tar.gz"
  if [[ -n "${VAULT_BACKUP_PASSPHRASE:-}" ]]; then
    gpg --batch --yes --passphrase "$VAULT_BACKUP_PASSPHRASE" -o "$SRC" -d "$ARCHIVE"
  else
    gpg -o "$SRC" -d "$ARCHIVE"
  fi
fi

mkdir -p "$WORKDIR/data"
tar -C "$WORKDIR" -xzf "$SRC"

echo "Restoring into vault/${VAULT_BUCKET} (overwrite)…"
docker compose -f "$ROOT/envs/docker-compose.yml" --env-file "$ENV_FILE" run --rm \
  -v "$WORKDIR/data:/backup/data:ro" \
  --entrypoint /bin/sh \
  dataset-vault-init -c "
    set -e
    mc alias set vault http://dataset-vault:9000 \"\$VAULT_ROOT_USER\" \"\$VAULT_ROOT_PASSWORD\"
    mc mirror --overwrite /backup/data \"vault/\${VAULT_BUCKET}\"
  "
echo "Restore complete"
