"""Secure dataset vault client (S3-compatible / MinIO).

Voice↔transcript datasets are stored privately with server-side encryption.
Uploads/downloads are explicit — nothing syncs without a call.
"""

from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DATASETS_DIR, settings


@dataclass
class VaultObject:
    key: str
    size: int
    etag: str | None = None


def _client():
    from minio import Minio

    if not settings.vault_endpoint:
        raise RuntimeError(
            "VAULT_ENDPOINT not configured. Start dataset-vault and set envs/.env "
            "(see envs/.env.example)."
        )
    if not settings.vault_access_key or not settings.vault_secret_key:
        raise RuntimeError("VAULT_ACCESS_KEY / VAULT_SECRET_KEY not configured")

    endpoint = settings.vault_endpoint.replace("https://", "").replace("http://", "")
    return Minio(
        endpoint,
        access_key=settings.vault_access_key,
        secret_key=settings.vault_secret_key,
        secure=settings.vault_secure,
    )


def vault_configured() -> bool:
    return bool(
        settings.vault_endpoint
        and settings.vault_access_key
        and settings.vault_secret_key
        and settings.vault_bucket
    )


def ensure_bucket() -> None:
    client = _client()
    bucket = settings.vault_bucket
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_file(local_path: str | Path, key: str, metadata: dict[str, str] | None = None) -> str:
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(path)
    client = _client()
    ensure_bucket()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    client.fput_object(
        settings.vault_bucket,
        key,
        str(path),
        content_type=content_type,
        metadata=metadata or {},
    )
    return f"s3://{settings.vault_bucket}/{key}"


def download_file(key: str, dest: str | Path) -> Path:
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    client = _client()
    client.fget_object(settings.vault_bucket, key, str(dest_path))
    return dest_path


def list_prefix(prefix: str = "") -> list[VaultObject]:
    client = _client()
    ensure_bucket()
    out: list[VaultObject] = []
    for obj in client.list_objects(settings.vault_bucket, prefix=prefix, recursive=True):
        out.append(VaultObject(key=obj.object_name, size=obj.size or 0, etag=obj.etag))
    return out


def delete_key(key: str) -> None:
    client = _client()
    client.remove_object(settings.vault_bucket, key)


def push_dataset(dataset_id: str, local_dir: str | Path | None = None) -> dict[str, Any]:
    """Upload a local dataset folder to vault under datasets/{id}/."""
    root = Path(local_dir) if local_dir else DATASETS_DIR / dataset_id
    if not root.exists():
        raise FileNotFoundError(root)
    uploaded: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            key = f"datasets/{dataset_id}/{rel}"
            uploaded.append(upload_file(path, key))
    manifest = {
        "dataset_id": dataset_id,
        "object_count": len(uploaded),
        "objects": uploaded,
    }
    manifest_path = root / "_vault_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    upload_file(manifest_path, f"datasets/{dataset_id}/_vault_manifest.json")
    return manifest


def pull_dataset(dataset_id: str, dest_dir: str | Path | None = None) -> Path:
    """Download datasets/{id}/ from vault into local data/datasets/{id}."""
    dest = Path(dest_dir) if dest_dir else DATASETS_DIR / dataset_id
    dest.mkdir(parents=True, exist_ok=True)
    prefix = f"datasets/{dataset_id}/"
    for obj in list_prefix(prefix):
        rel = obj.key[len(prefix) :]
        if not rel:
            continue
        download_file(obj.key, dest / rel)
    return dest
