from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
DATASETS_DIR = DATA_DIR / "datasets"
ADAPTERS_DIR = DATA_DIR / "adapters"
RUNS_DIR = DATA_DIR / "runs"
DB_PATH = DATA_DIR / "stt_lab.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    deepgram_api_key: str = ""
    assemblyai_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    whisper_device: str = "auto"  # auto | cpu | cuda | mps
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()


def ensure_dirs() -> None:
    for path in (DATA_DIR, AUDIO_DIR, DATASETS_DIR, ADAPTERS_DIR, RUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)
