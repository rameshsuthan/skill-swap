from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore", populate_by_name=True)
    google_api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY")
    )
    gemini_model: str = "gemini-3.5-flash-lite"
    domain_db: Path = Field(
        default=ROOT / "storage/skillswap.sqlite", validation_alias="SKILLSWAP_DOMAIN_DB"
    )
    checkpoint_db: Path = Field(
        default=ROOT / "storage/checkpoints.sqlite", validation_alias="SKILLSWAP_CHECKPOINT_DB"
    )
    mem0_api_key: SecretStr = Field(default=SecretStr(""), validation_alias="MEM0_API_KEY")
    mem0_enabled: bool = Field(default=False, validation_alias="SKILLSWAP_MEM0_ENABLED")
    cohort_id: str = "global-2026"
    demo_mode: bool = True
