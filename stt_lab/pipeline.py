"""Dictate pipeline: policy gate → STT → cleanup → optional polish."""

from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy.orm import Session

from .policy import PrivacyTrace, mode_from_policy
from .profiles import RunnableProfile
from .providers.registry import get_providers_by_ids

_FILLER = re.compile(
    r"\b(um+|uh+|erm+|like|you know|sort of|kind of)\b[,.]?\s*",
    re.IGNORECASE,
)


def _cleanup(text: str, profile: RunnableProfile) -> str:
    out = text.strip()
    if profile.cleanup.filler_words:
        out = _FILLER.sub("", out)
        out = re.sub(r"\s{2,}", " ", out).strip()
    if profile.cleanup.dictionary_path:
        path = Path(profile.cleanup.dictionary_path)
        if path.exists():
            # simple replacements file: each line "from=>to"
            for line in path.read_text().splitlines():
                if "=>" not in line or line.strip().startswith("#"):
                    continue
                src, dst = line.split("=>", 1)
                out = re.sub(re.escape(src.strip()), dst.strip(), out, flags=re.IGNORECASE)
    return out


async def run_dictate(
    db: Session,
    profile: RunnableProfile,
    audio_path: str | Path,
) -> tuple[str, PrivacyTrace]:
    """Run one dictation through the configured profile.

    Polish LLM backends are stubbed (pass-through) until implemented.
    """
    profile.validate_consistency()
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(path)

    stt_ids = [profile.stt.provider]
    # Convenience: allow whisper size names in profile.provider
    if profile.stt.provider in {"tiny", "base", "small", "medium"}:
        stt_ids = [f"whisper-{profile.stt.provider}"]
    if profile.stt.adapter_id and not profile.stt.provider.startswith("adapted-"):
        stt_ids = [f"adapted-{profile.stt.adapter_id}"]

    providers = get_providers_by_ids(db, stt_ids)
    provider = providers[0]
    ready, reason = provider.ready()
    if not ready:
        raise RuntimeError(reason or f"Provider not ready: {provider.id}")

    if provider.provider in {"openai", "deepgram", "assemblyai"} or profile.stt.location == "cloud":
        if not profile.policy.allows_cloud_stt():
            raise PermissionError("Policy blocks cloud STT (allow_cloud_audio=false)")
        stt_location: str = "cloud"
        audio_left = True
        endpoint = profile.cloud.stt_base_url
    else:
        stt_location = "local"
        audio_left = False
        endpoint = None

    result = await provider.transcribe(str(path), language=profile.stt.language)
    if result.error:
        raise RuntimeError(result.error)

    text = _cleanup(result.transcript, profile)
    polish_location = "off"
    transcript_left = False

    if profile.polish.provider == "cloud_llm":
        if not profile.policy.allows_cloud_polish():
            raise PermissionError("Policy blocks cloud polish")
        # Stub: real LLM polish lands later
        polish_location = "cloud"
        transcript_left = True
    elif profile.polish.provider == "local_llm":
        polish_location = "local"

    mode = mode_from_policy(profile.policy, "cloud" if stt_location == "cloud" else "local")
    trace = PrivacyTrace(
        mode=mode,  # type: ignore[arg-type]
        audio_left_device=audio_left,
        transcript_left_device=transcript_left,
        stt_location=stt_location,  # type: ignore[arg-type]
        polish_location=polish_location,  # type: ignore[arg-type]
        endpoint=endpoint,
    )
    return text, trace
