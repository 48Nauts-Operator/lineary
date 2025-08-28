"""
BETTY Memory System Python SDK

Official Python client library for BETTY Memory System v2.0 API.
Provides comprehensive access to advanced knowledge management capabilities
including semantic search, pattern matching, batch operations, and real-time features.

Example usage:
    import asyncio
    from betty_client import BettyClient

    async def main():
        client = BettyClient(api_key="your-jwt-token")
        
        results = await client.advanced_search(
            query="machine learning optimization",
            search_type="hybrid",
            max_results=20
        )
        
        print(f"Found {len(results.data.results)} results")

    asyncio.run(main())
"""

__version__ = "2.0.0"
__author__ = "BETTY Development Team"
__email__ = "dev@betty-memory.com"

# Core client
from .client import BettyClient

# Configuration
from .config import Config, ClientConfig

# Models
from .models import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    PatternMatchRequest,
    PatternMatchResponse,
    SemanticClusteringRequest, 
    SemanticClusteringResponse,
    BatchImportRequest,
    BatchImportResponse,
    KnowledgeItem,
    SearchResult,
    Pattern,
    Cluster,
    WebSocketMessage
)

# Exceptions
from .exceptions import (
    BettyException,
    BettyAPIException,
    AuthenticationException,
    PermissionException,
    RateLimitException,
    ValidationException,
    WebSocketException
)

# Utilities
from .utils import (
    validate_jwt_token,
    extract_permissions_from_token,
    format_filters,
    merge_search_results
)

# WebSocket client (optional import)
try:
    from .websocket import WebSocketClient
    __all__ = [
        # Core
        "BettyClient", "Config", "ClientConfig",
        # Models
        "AdvancedSearchRequest", "AdvancedSearchResponse",
        "PatternMatchRequest", "PatternMatchResponse", 
        "SemanticClusteringRequest", "SemanticClusteringResponse",
        "BatchImportRequest", "BatchImportResponse",
        "KnowledgeItem", "SearchResult", "Pattern", "Cluster",
        "WebSocketMessage",
        # Exceptions
        "BettyException", "BettyAPIException",
        "AuthenticationException", "PermissionException",
        "RateLimitException", "ValidationException",
        "WebSocketException",
        # Utilities
        "validate_jwt_token", "extract_permissions_from_token",
        "format_filters", "merge_search_results",
        # WebSocket
        "WebSocketClient"
    ]
except ImportError:
    # WebSocket dependencies not installed
    __all__ = [
        # Core
        "BettyClient", "Config", "ClientConfig", 
        # Models
        "AdvancedSearchRequest", "AdvancedSearchResponse",
        "PatternMatchRequest", "PatternMatchResponse",
        "SemanticClusteringRequest", "SemanticClusteringResponse", 
        "BatchImportRequest", "BatchImportResponse",
        "KnowledgeItem", "SearchResult", "Pattern", "Cluster",
        "WebSocketMessage",
        # Exceptions
        "BettyException", "BettyAPIException",
        "AuthenticationException", "PermissionException",
        "RateLimitException", "ValidationException",
        # Utilities
        "validate_jwt_token", "extract_permissions_from_token",
        "format_filters", "merge_search_results"
    ]

# Version info
VERSION_INFO = {
    "major": 2,
    "minor": 0,
    "patch": 0,
    "pre_release": None
}

def get_version() -> str:
    """Get the current version string."""
    version = f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"
    if VERSION_INFO['pre_release']:
        version += f"-{VERSION_INFO['pre_release']}"
    return version