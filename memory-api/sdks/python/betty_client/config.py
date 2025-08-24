"""
BETTY Memory System Python SDK - Configuration

This module provides configuration management for the BETTY Python SDK,
including environment-based configuration and validation.
"""

import os
import yaml
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import BettyException


@dataclass
class ClientConfig:
    """
    Configuration for BETTY client with validation and environment support.
    
    Supports loading configuration from:
    - Constructor parameters
    - Environment variables
    - Configuration files (YAML/JSON)
    - Default values
    """
    
    # Authentication
    api_key: Optional[str] = None
    
    # Connection settings
    base_url: str = "http://localhost:3034/api/v2"
    timeout: int = 30
    connection_pool_size: int = 10
    
    # Rate limiting
    rate_limit_per_minute: int = 100
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0
    
    # Feature flags
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    enable_websockets: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = False
    
    # Validation
    validate_ssl: bool = True
    validate_responses: bool = True
    
    # Additional headers
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        
        # Validate timeout
        if self.timeout <= 0:
            raise BettyException("Timeout must be positive")
        
        # Validate rate limiting
        if self.rate_limit_per_minute <= 0:
            raise BettyException("Rate limit must be positive")
        
        # Validate retry configuration
        if self.max_retries < 0:
            raise BettyException("Max retries cannot be negative")
        
        if self.retry_delay <= 0:
            raise BettyException("Retry delay must be positive")
        
        if self.retry_backoff_factor < 1:
            raise BettyException("Retry backoff factor must be >= 1")
        
        # Validate cache TTL
        if self.cache_ttl <= 0:
            raise BettyException("Cache TTL must be positive")
        
        # Validate connection pool size
        if self.connection_pool_size <= 0:
            raise BettyException("Connection pool size must be positive")
        
        # Validate base URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise BettyException("Base URL must start with http:// or https://")
    
    @classmethod
    def from_env(cls, prefix: str = "BETTY_") -> 'ClientConfig':
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: "BETTY_")
            
        Returns:
            ClientConfig instance with values from environment
            
        Environment Variables:
            BETTY_API_KEY: JWT token for authentication
            BETTY_BASE_URL: API base URL
            BETTY_TIMEOUT: Request timeout in seconds
            BETTY_RATE_LIMIT: Rate limit per minute
            BETTY_MAX_RETRIES: Maximum retry attempts
            BETTY_LOG_LEVEL: Logging level
            BETTY_ENABLE_CACHING: Enable response caching
            BETTY_CACHE_TTL: Cache time-to-live in seconds
        """
        
        config_values = {}
        
        # Map environment variables to config fields
        env_mappings = {
            f"{prefix}API_KEY": "api_key",
            f"{prefix}BASE_URL": "base_url", 
            f"{prefix}TIMEOUT": ("timeout", int),
            f"{prefix}CONNECTION_POOL_SIZE": ("connection_pool_size", int),
            f"{prefix}RATE_LIMIT": ("rate_limit_per_minute", int),
            f"{prefix}MAX_RETRIES": ("max_retries", int),
            f"{prefix}RETRY_DELAY": ("retry_delay", float),
            f"{prefix}RETRY_BACKOFF_FACTOR": ("retry_backoff_factor", float),
            f"{prefix}ENABLE_CACHING": ("enable_caching", lambda x: x.lower() == 'true'),
            f"{prefix}CACHE_TTL": ("cache_ttl", int),
            f"{prefix}ENABLE_WEBSOCKETS": ("enable_websockets", lambda x: x.lower() == 'true'),
            f"{prefix}LOG_LEVEL": "log_level",
            f"{prefix}LOG_REQUESTS": ("log_requests", lambda x: x.lower() == 'true'),
            f"{prefix}VALIDATE_SSL": ("validate_ssl", lambda x: x.lower() == 'true'),
            f"{prefix}VALIDATE_RESPONSES": ("validate_responses", lambda x: x.lower() == 'true'),
        }
        
        for env_var, config_field in env_mappings.items():
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                if isinstance(config_field, tuple):
                    field_name, converter = config_field
                    try:
                        config_values[field_name] = converter(env_value)
                    except (ValueError, TypeError) as e:
                        raise BettyException(f"Invalid value for {env_var}: {env_value}") from e
                else:
                    config_values[config_field] = env_value
        
        return cls(**config_values)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ClientConfig':
        """
        Create configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            ClientConfig instance with values from file
            
        Example YAML:
            api_key: "your-jwt-token"
            base_url: "https://api.betty-memory.com/v2"
            timeout: 30
            rate_limit_per_minute: 100
            enable_caching: true
            cache_ttl: 300
        
        Example JSON:
            {
                "api_key": "your-jwt-token",
                "base_url": "https://api.betty-memory.com/v2",
                "timeout": 30,
                "rate_limit_per_minute": 100,
                "enable_caching": true,
                "cache_ttl": 300
            }
        """
        
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise BettyException(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yml', '.yaml']:
                    config_data = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise BettyException(f"Unsupported config file format: {config_file.suffix}")
                    
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise BettyException(f"Failed to parse configuration file: {e}") from e
        
        if not isinstance(config_data, dict):
            raise BettyException("Configuration file must contain a dictionary/object")
        
        return cls(**config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ClientConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            ClientConfig instance
        """
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "connection_pool_size": self.connection_pool_size,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff_factor": self.retry_backoff_factor,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "enable_websockets": self.enable_websockets,
            "log_level": self.log_level,
            "log_requests": self.log_requests,
            "validate_ssl": self.validate_ssl,
            "validate_responses": self.validate_responses,
            "custom_headers": self.custom_headers
        }
    
    def save(self, config_path: str, format: str = "yaml"):
        """
        Save configuration to file.
        
        Args:
            config_path: Path to save configuration
            format: File format ('yaml' or 'json')
        """
        
        config_data = self.to_dict()
        
        # Remove None values and sensitive data
        clean_config = {}
        for key, value in config_data.items():
            if value is not None:
                if key == "api_key" and value:
                    # Mask API key for security
                    clean_config[key] = f"{value[:10]}...{value[-4:]}"
                else:
                    clean_config[key] = value
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.safe_dump(clean_config, f, indent=2, sort_keys=True)
                elif format.lower() == "json":
                    json.dump(clean_config, f, indent=2, sort_keys=True)
                else:
                    raise BettyException(f"Unsupported format: {format}")
                    
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise BettyException(f"Failed to save configuration: {e}") from e
    
    def copy(self, **overrides) -> 'ClientConfig':
        """
        Create a copy of configuration with optional overrides.
        
        Args:
            **overrides: Fields to override
            
        Returns:
            New ClientConfig instance with overrides applied
        """
        
        config_dict = self.to_dict()
        config_dict.update(overrides)
        return ClientConfig(**config_dict)
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        
        # Mask sensitive information
        safe_dict = self.to_dict()
        if safe_dict.get("api_key"):
            safe_dict["api_key"] = f"{safe_dict['api_key'][:10]}...{safe_dict['api_key'][-4:]}"
        
        return f"ClientConfig({safe_dict})"


# Convenience class alias
Config = ClientConfig


def get_default_config() -> ClientConfig:
    """
    Get default configuration instance.
    
    Returns:
        Default ClientConfig instance
    """
    
    return ClientConfig()


def load_config(config_path: str = None, 
               use_env: bool = True,
               env_prefix: str = "BETTY_",
               **overrides) -> ClientConfig:
    """
    Load configuration from multiple sources with precedence.
    
    Precedence order (highest to lowest):
    1. Function overrides
    2. Environment variables (if use_env=True)
    3. Configuration file (if config_path provided)
    4. Default values
    
    Args:
        config_path: Path to configuration file (optional)
        use_env: Whether to load from environment variables
        env_prefix: Environment variable prefix
        **overrides: Direct configuration overrides
        
    Returns:
        ClientConfig instance with merged configuration
        
    Example:
        # Load from file and environment, with overrides
        config = load_config(
            config_path="config.yaml",
            use_env=True,
            timeout=60,  # Override timeout
            log_level="DEBUG"  # Override log level
        )
    """
    
    # Start with defaults
    config = ClientConfig()
    
    # Load from file if provided
    if config_path:
        file_config = ClientConfig.from_file(config_path)
        config = config.copy(**file_config.to_dict())
    
    # Load from environment variables
    if use_env:
        env_config = ClientConfig.from_env(prefix=env_prefix)
        non_none_env = {k: v for k, v in env_config.to_dict().items() if v is not None}
        if non_none_env:
            config = config.copy(**non_none_env)
    
    # Apply direct overrides
    if overrides:
        config = config.copy(**overrides)
    
    return config