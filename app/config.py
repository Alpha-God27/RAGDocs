"""Configurations used in the application"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
import os

load_dotenv()


SQLALCHEMY_DATABASE_URL = "sqlite:///app/data/northwind_small.sqlite"

class Settings(BaseSettings):
    app_name: str = Field(default="DBmind")
    debug: bool = Field(default=True)

    # Database
    sqlite_path: str = Field(default="./data/db.sqlite3")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3")
    ollama_timeout_seconds: int = Field(default=120)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()