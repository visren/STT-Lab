from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
DATASETS_DIR = DATA_DIR / "datasets"
ADAPTERS_DIR = DATA_DIR / "adapters"
RUNS_DIR = DATA_DIR / "runs"
PROFILES_DIR = DATA_DIR / "profiles"
HISTORY_DIR = DATA_DIR / "history"
DB_PATH = DATA_DIR / "stt_lab.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    deepgram_api_key: str = ""
    assemblyai_api_key: str = ""
    whisper_device: str = "auto"  # auto | cpu | cuda
    # Reserved for future cloud training backends (Modal / HF Jobs / RunPod)
    cloud_finetune_backend: str = ""  # e.g. modal | hf_jobs | runpod
    cloud_finetune_token: str = ""
    # Dataset vault (MinIO / S3-compatible)
    vault_endpoint: str = ""  # e.g. http://127.0.0.1:9000
    vault_access_key: str = ""
    vault_secret_key: str = ""
    vault_bucket: str = "stt-datasets"
    vault_secure: bool = False


settings = Settings()


def ensure_dirs() -> None:
    for path in (
        DATA_DIR,
        AUDIO_DIR,
        DATASETS_DIR,
        ADAPTERS_DIR,
        RUNS_DIR,
        PROFILES_DIR,
        HISTORY_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
