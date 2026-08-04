"""Provider contract for remote LoRA training."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .types import RemoteJobRef, RemoteJobStatus, TrainRecipe


class CloudTrainProvider(ABC):
    """Upload dataset + recipe, poll remote job, download adapter artifacts."""

    name: str

    @abstractmethod
    def validate_config(self) -> None:
        """Raise RuntimeError if env/config is incomplete."""

    @abstractmethod
    def submit(self, recipe: TrainRecipe, dataset_dir: Path) -> RemoteJobRef:
        """Start a remote training job. ``dataset_dir`` holds wav + manifests."""

    @abstractmethod
    def poll(self, ref: RemoteJobRef) -> RemoteJobStatus:
        ...

    @abstractmethod
    def download_adapter(self, ref: RemoteJobRef, dest_dir: Path) -> Path:
        """Write adapter files under ``dest_dir``; return that path."""

    def cancel(self, ref: RemoteJobRef) -> None:
        """Best-effort cancel; default no-op."""
