# ABOUTME: Configuration management for BETTY Memory System
# ABOUTME: Handles environment variables and settings using Pydantic Settings

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application settings
    app_name: str = "BETTY Memory System API"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # PostgreSQL settings
    postgres_host: str = Field(default="postgres", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="betty_memory", description="PostgreSQL database name")
    postgres_user: str = Field(default="betty", description="PostgreSQL username")
    postgres_password: str = Field(default="bettypassword", description="PostgreSQL password")
    postgres_pool_size: int = Field(default=10, description="PostgreSQL connection pool size")
    postgres_max_overflow: int = Field(default=20, description="PostgreSQL max overflow connections")
    
    # Neo4j settings
    neo4j_uri: str = Field(default="bolt://neo4j:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="bettypassword", description="Neo4j password")
    neo4j_max_connection_lifetime: int = Field(default=300, description="Neo4j max connection lifetime (seconds)")
    neo4j_max_connection_pool_size: int = Field(default=100, description="Neo4j max connection pool size")
    
    # Qdrant settings
    qdrant_host: str = Field(default="qdrant", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_timeout: int = Field(default=60, description="Qdrant timeout (seconds)")
    qdrant_prefer_grpc: bool = Field(default=False, description="Use gRPC for Qdrant connections")
    
    # Redis settings
    redis_host: str = Field(default="redis", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=20, description="Redis max connections")
    redis_retry_on_timeout: bool = Field(default=True, description="Redis retry on timeout")
    
    # API settings
    api_timeout: int = Field(default=30, description="API request timeout (seconds)")
    max_request_size: int = Field(default=10_000_000, description="Max request size in bytes (10MB)")
    
    # Vector settings
    default_embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Default embedding model")
    vector_dimension: int = Field(default=384, description="Vector embedding dimension")
    similarity_threshold: float = Field(default=0.7, description="Similarity threshold for vector search")
    
    # Cache settings
    cache_ttl: int = Field(default=3600, description="Default cache TTL (seconds)")
    cache_max_entries: int = Field(default=10000, description="Max cache entries")
    
    # Graphiti settings
    graphiti_embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Graphiti embedding model")
    graphiti_llm_model: str = Field(default="gpt-4", description="Graphiti LLM model")
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def postgres_sync_url(self) -> str:
        """Construct synchronous PostgreSQL connection URL for migrations"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def qdrant_url(self) -> str:
        """Construct Qdrant connection URL"""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()