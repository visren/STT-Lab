from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TrainRecipe:
    job_id: str
    dataset_id: str
    base_model: str
    epochs: int = 3
    lora_rank: int = 16
    learning_rate: float = 1e-4
    batch_size: int = 1
    language: str = "en"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemoteJobRef:
    provider: str
    remote_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


RemoteStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


@dataclass
class RemoteJobStatus:
    status: RemoteStatus
    progress: float = 0.0
    error: str | None = None
    adapter_uri: str | None = None
    logs_tail: str = ""
