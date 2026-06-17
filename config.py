from functools import lru_cache
from typing import Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ChannelRef = Union[str, int]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_id: int = Field(..., description="my.telegram.org → api_id")
    api_hash: str = Field(..., description="my.telegram.org → api_hash")
    session_string: str = Field("", description="Pyrogram string-session пользователя-читателя")

    bot_token: str = Field(..., description="Токен бота от @BotFather")

    deepseek_api_key: str = Field(..., description="Ключ DeepSeek")
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_temperature: float = 0.7
    deepseek_max_tokens: int = 2048

    source_channels: list[ChannelRef] = Field(
        default_factory=list,
        description="Исходные каналы: @username или ID, через запятую",
    )
    target_channel: ChannelRef = Field(..., description="Канал назначения (@username или ID)")

    min_post_interval: float = Field(3.0, description="Минимальная пауза между постами, сек")
    log_level: str = "INFO"

    @field_validator("source_channels", mode="before")
    @classmethod
    def _split_channels(cls, v):
        if isinstance(v, str):
            items = [c.strip() for c in v.split(",") if c.strip()]
            parsed: list[ChannelRef] = []
            for item in items:
                parsed.append(int(item) if item.lstrip("-").isdigit() else item)
            return parsed
        return v

    @field_validator("target_channel", mode="before")
    @classmethod
    def _parse_target(cls, v):
        if isinstance(v, str) and v.lstrip("-").isdigit():
            return int(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
