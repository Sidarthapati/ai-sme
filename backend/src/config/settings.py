"""
Configuration management for the AI SME application.
Loads settings from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="AI SME Assistant", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    
    # Azure OpenAI (optional)
    azure_openai_api_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: Optional[str] = Field(default=None, env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: Optional[str] = Field(default=None, env="AZURE_OPENAI_API_VERSION")
    
    # Vector Database
    vector_db_type: str = Field(default="chroma", env="VECTOR_DB_TYPE")
    vector_db_path: str = Field(default="./chroma_db", env="VECTOR_DB_PATH")
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    # Pinecone (optional)
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = Field(default=None, env="PINECONE_INDEX_NAME")
    
    # Data Sources
    confluence_base_url: str = Field(
        default="https://cwiki.apache.org/confluence",
        env="CONFLUENCE_BASE_URL"
    )
    github_org: str = Field(default="apache", env="GITHUB_ORG")
    github_repos: str = Field(default="kafka", env="GITHUB_REPOS")
    
    # GitHub Authentication (optional)
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Confluence Authentication (optional)
    confluence_username: Optional[str] = Field(default=None, env="CONFLUENCE_USERNAME")
    confluence_api_token: Optional[str] = Field(default=None, env="CONFLUENCE_API_TOKEN")
    
    # RAG Configuration
    chunk_size: int = Field(default=800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(default=5, env="RETRIEVAL_TOP_K")
    llm_temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    max_response_tokens: int = Field(default=1000, env="MAX_RESPONSE_TOKENS")
    
    # Document Upload
    max_upload_size_mb: int = Field(default=10, env="MAX_UPLOAD_SIZE_MB")
    allowed_file_types: List[str] = Field(
        default=[".txt", ".md", ".pdf", ".docx", ".doc"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Redis (optional)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_file_types', pre=True)
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from comma-separated string."""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(',')]
        return v
    
    @property
    def is_azure_openai(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return all([
            self.azure_openai_api_key,
            self.azure_openai_endpoint,
            self.azure_openai_deployment_name
        ])
    
    @property
    def github_repos_list(self) -> List[str]:
        """Get list of GitHub repos to index."""
        return [repo.strip() for repo in self.github_repos.split(',')]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience function
settings = get_settings()
