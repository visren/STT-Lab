"""Reserved real-provider skeletons (not wired yet)."""

from __future__ import annotations

from pathlib import Path

from .base import CloudTrainProvider
from .types import RemoteJobRef, RemoteJobStatus, TrainRecipe


class _UnimplementedProvider(CloudTrainProvider):
    def validate_config(self) -> None:
        from ..config import settings

        if not settings.cloud_finetune_token:
            raise RuntimeError(
                f"{self.name} requires CLOUD_FINETUNE_TOKEN in .env"
            )
        raise RuntimeError(
            f"Cloud provider '{self.name}' is not implemented yet. "
            "Use CLOUD_FINETUNE_BACKEND=stub for lifecycle testing, or backend='local'."
        )

    def submit(self, recipe: TrainRecipe, dataset_dir: Path) -> RemoteJobRef:
        self.validate_config()
        raise AssertionError("unreachable")

    def poll(self, ref: RemoteJobRef) -> RemoteJobStatus:
        raise RuntimeError(f"{self.name} not implemented")

    def download_adapter(self, ref: RemoteJobRef, dest_dir: Path) -> Path:
        raise RuntimeError(f"{self.name} not implemented")


class ModalProvider(_UnimplementedProvider):
    name = "modal"


class HfJobsProvider(_UnimplementedProvider):
    name = "hf_jobs"


class RunpodProvider(_UnimplementedProvider):
    name = "runpod"
