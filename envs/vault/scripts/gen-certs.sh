#!/usr/bin/env bash
# Generate a local TLS cert for vault.local (or VAULT_TLS_DOMAIN).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
CERT_DIR="${VAULT_CERT_DIR:-$ROOT/envs/vault/certs}"
DOMAIN="${VAULT_TLS_DOMAIN:-vault.local}"
mkdir -p "$CERT_DIR"

if [[ -f "$CERT_DIR/vault.crt" && -f "$CERT_DIR/vault.key" ]]; then
  echo "Certs already exist in $CERT_DIR (delete to regenerate)"
  exit 0
fi

openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
  -keyout "$CERT_DIR/vault.key" \
  -out "$CERT_DIR/vault.crt" \
  -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"

chmod 600 "$CERT_DIR/vault.key"
echo "Wrote $CERT_DIR/vault.crt and vault.key"
echo "Trust the cert in your OS keychain for local clients, or use VAULT_SECURE=true with verify disabled only in dev."
