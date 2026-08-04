"""Cloud fine-tune providers (pluggable).

Configured via ``CLOUD_FINETUNE_BACKEND``:
  - ``stub`` — full job lifecycle dry-run (writes a marker adapter)
  - ``modal`` / ``hf_jobs`` / ``runpod`` — reserved provider skeletons
"""

from .registry import get_cloud_provider
from .types import RemoteJobRef, RemoteJobStatus, TrainRecipe

__all__ = [
    "TrainRecipe",
    "RemoteJobRef",
    "RemoteJobStatus",
    "get_cloud_provider",
]
