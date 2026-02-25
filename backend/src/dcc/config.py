from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "dcc.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    claude_bin: str = "claude"

    # Tenant defaults (can be overridden per tenant in DB)
    default_config_dir: str = str(Path.home() / ".claude-personal")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
