from pydantic import (
    Field,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    output_dir: str = Field(..., env="OUTPUT_DIR")
    allowed_user_ids: list[int] = Field(..., env="ALLOWED_USER_IDS")


settings = Settings()
