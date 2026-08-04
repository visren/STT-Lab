from __future__ import annotations

from .base import CloudTrainProvider
from .providers import HfJobsProvider, ModalProvider, RunpodProvider
from .stub import StubCloudProvider


def get_cloud_provider(name: str | None = None) -> CloudTrainProvider:
    from ..config import settings

    key = (name or settings.cloud_finetune_backend or "stub").strip().lower()
    mapping: dict[str, CloudTrainProvider] = {
        "stub": StubCloudProvider(),
        "modal": ModalProvider(),
        "hf_jobs": HfJobsProvider(),
        "hf-jobs": HfJobsProvider(),
        "runpod": RunpodProvider(),
    }
    if key not in mapping:
        raise ValueError(
            f"Unknown CLOUD_FINETUNE_BACKEND={key!r}. "
            "Expected stub|modal|hf_jobs|runpod"
        )
    return mapping[key]
