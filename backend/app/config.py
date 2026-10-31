from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The .env file lives in the project root, two folders above this file.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Reads settings from the .env file. Secrets never live in the code."""

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int = 5432
    postgres_host: str = "localhost"

    # Secret that n8n must send in the x-api-key header.
    # min_length=32 refuses weak keys.
    webhook_api_key: str = Field(min_length=32)

    # extra="ignore": the .env file also has n8n settings we don't need here.
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()