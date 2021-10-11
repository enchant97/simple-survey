from functools import cache
from typing import Optional
from pydantic import BaseSettings
from secrets import token_urlsafe


class Settings(BaseSettings):
    DB_URI: str
    SECRET_KEY: Optional[str] = token_urlsafe(32)
    TITLE_NAME: Optional[str] = "Simple Polls"

    class Config:
        case_sensitive = True


@cache
def get_settings():
    """
    returns the Settings obj
    """
    return Settings()
