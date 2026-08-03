from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResult:
    transcript: str
    latency_ms: float
    error: str | None = None


class STTProvider(ABC):
    id: str
    name: str
    provider: str

    @abstractmethod
    def ready(self) -> tuple[bool, str | None]:
        ...

    @abstractmethod
    async def transcribe(self, audio_path: str, language: str | None = None) -> ProviderResult:
        ...
