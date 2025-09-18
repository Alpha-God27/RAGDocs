"""Configurations used in the RAGDocs application"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
import os

load_dotenv()


class Settings(BaseSettings):
    app_name: str = Field(default="RAGDocs")
    debug: bool = Field(default=True)
    
    # OpenRouter Configuration
    openrouter_api_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_timeout: int = Field(default=60)
    
    # Embedding Model Configuration
    # Using BAAI/bge-base-en-v1.5 for high-quality embeddings
    embedding_model: str = Field(default="BAAI/bge-base-en-v1.5")
    
    # LLM Model Configuration
    default_llm_model: str = Field(default="openai/gpt-3.5-turbo")
    
    # RAG Configuration
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    max_retrieve_docs: int = Field(default=4)
    
    # Vector Database Configuration
    vector_store_path: str = Field(default="./app/data/vector_store")
    
    # Web Scraping Configuration
    request_timeout: int = Field(default=30)
    max_content_length: int = Field(default=1000000)  # 1MB limit
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()