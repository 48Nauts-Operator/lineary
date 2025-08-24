# BETTY Memory System Python SDK

Official Python SDK for BETTY Memory System v2.0. Provides comprehensive async access to advanced knowledge management capabilities including semantic search, pattern matching, batch operations, and real-time features.

## Features

- 🔍 **Advanced Search**: Semantic, keyword, and hybrid search with intelligent filtering
- 🧠 **Pattern Matching**: Discover patterns in knowledge graphs using advanced algorithms
- 📊 **Semantic Clustering**: Organize knowledge items into meaningful clusters
- ⚡ **Batch Operations**: Bulk import/export with real-time progress tracking
- 🌐 **Cross-Project Intelligence**: Knowledge sharing and transfer between projects
- 🔄 **Real-time Updates**: WebSocket support for live progress monitoring
- 🛡️ **Type Safety**: Complete type hints with Pydantic models
- 🔄 **Automatic Retries**: Intelligent retry logic with exponential backoff
- 📊 **Comprehensive Error Handling**: Detailed exceptions with context

## Installation

```bash
# Install from PyPI
pip install betty-memory-sdk

# Install with optional dependencies
pip install betty-memory-sdk[websocket,cache,all]

# Development installation
git clone https://github.com/your-org/betty-python-sdk.git
cd betty-python-sdk
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
import asyncio
from betty_client import BettyClient

async def main():
    # Initialize client
    async with BettyClient(api_key="your-jwt-token") as client:
        # Simple search
        results = await client.advanced_search(
            query="machine learning optimization",
            search_type="hybrid",
            max_results=20
        )
        
        print(f"Found {len(results.data.results)} results")
        for result in results.data.results:
            print(f"- {result.title} (score: {result.similarity_score:.3f})")

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration

```python
from betty_client import BettyClient, ClientConfig

# From environment variables
config = ClientConfig.from_env()
client = BettyClient(config=config)

# From configuration file
config = ClientConfig.from_file("betty-config.yaml")
client = BettyClient(config=config)

# Direct configuration
client = BettyClient(
    api_key="your-jwt-token",
    base_url="https://api.betty-memory.com/v2",
    timeout=30,
    rate_limit_per_minute=100
)
```

## Core Functionality

### Advanced Search

```python
# Semantic search with filters
results = await client.advanced_search(
    query="neural network optimization techniques",
    search_type="semantic",
    similarity_threshold=0.8,
    max_results=25,
    filters=[
        {
            "field": "knowledge_type",
            "operator": "in",
            "value": ["research_paper", "documentation"]
        },
        {
            "field": "quality_score",
            "operator": "gte",
            "value": 0.8
        }
    ],
    time_range={
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-08-08T23:59:59Z"
    }
)

# Process results
for result in results.data.results:
    print(f"Title: {result.title}")
    print(f"Type: {result.knowledge_type}")
    print(f"Score: {result.similarity_score:.3f}")
    print(f"Tags: {', '.join(result.metadata.tags or [])}")
    print("---")
```

### Pattern Matching

```python
# Find path patterns in knowledge graphs
patterns = await client.pattern_matching(
    pattern_type="path",
    pattern_definition={
        "path_structure": "A->B->C",
        "relationship_types": ["influences", "leads_to", "depends_on"],
        "node_constraints": {
            "A": {"knowledge_type": "concept"},
            "B": {"knowledge_type": "method"},
            "C": {"knowledge_type": "result"}
        }
    },
    max_depth=5,
    min_confidence=0.7,
    max_results=20
)

# Analyze discovered patterns
for pattern in patterns.data.patterns:
    print(f"Pattern: {pattern.pattern_description}")
    print(f"Confidence: {pattern.confidence_score:.3f}")
    print(f"Support: {pattern.support_count}")
    
    # Show pattern structure
    for node in pattern.nodes:
        print(f"  Node: {node.title} ({node.type})")
    
    for relationship in pattern.relationships:
        print(f"  Edge: {relationship.type} (strength: {relationship.strength:.3f})")
```

### Semantic Clustering

```python
# Create knowledge clusters
clusters = await client.semantic_clustering(
    algorithm="hierarchical",
    auto_clusters=True,
    min_cluster_size=5,
    include_topics=True,
    include_visualization=True
)

# Explore clusters
for cluster in clusters.data.clusters:
    print(f"\nCluster: {cluster.label}")
    print(f"Size: {cluster.size} items")
    print(f"Coherence: {cluster.coherence_score:.3f}")
    
    # Show top topics
    print("Topics:")
    for topic in cluster.topics[:5]:
        print(f"  - {topic.term} ({topic.weight:.3f})")
    
    # Show representative items
    print("Representative items:")
    for item in cluster.representative_items[:3]:
        print(f"  - {item.title}")
```

### Batch Operations

```python
# Start batch import with progress tracking
operation = await client.batch_import(
    source_type="file",
    format="json",
    source_config={"file_path": "/uploads/knowledge_data.json"},
    target_project_id="your-project-uuid",
    processing_options={
        "generate_embeddings": True,
        "auto_categorize": True,
        "extract_entities": True
    },
    batch_size=100
)

print(f"Operation started: {operation.data.operation_id}")

# Monitor progress with async generator
async for progress in client.track_progress(operation.data.operation_id):
    print(f"Progress: {progress.progress_percentage:.1f}% "
          f"({progress.processed_items}/{progress.total_items})")
    print(f"Phase: {progress.current_phase}")
    
    if progress.status in ["completed", "failed", "cancelled"]:
        if progress.status == "completed":
            print(f"✅ Import completed successfully!")
            print(f"Success: {progress.successful_items}, Failed: {progress.failed_items}")
        else:
            print(f"❌ Import {progress.status}")
        break
```

### WebSocket Real-time Updates

```python
# Real-time progress monitoring via WebSocket
async def monitor_operation(operation_id: str):
    try:
        from betty_client import WebSocketClient
        
        ws_client = WebSocketClient(
            api_key="your-jwt-token",
            base_url="ws://localhost:3034/api/v2"
        )
        
        async with ws_client.connect(f"progress/{operation_id}") as stream:
            async for message in stream:
                if message.type == "progress_update":
                    data = message.data
                    print(f"Progress: {data.progress_percentage}%")
                    print(f"ETA: {data.estimated_time_remaining}s")
                    
                elif message.type == "operation_completed":
                    print("Operation completed!")
                    break
                    
                elif message.type == "error":
                    print(f"Error: {message.data.error_message}")
                    break
                    
    except ImportError:
        print("WebSocket support not available. Install with: pip install betty-memory-sdk[websocket]")

# Usage
await monitor_operation("your-operation-id")
```

### Cross-Project Intelligence

```python
# Search across multiple connected projects
results = await client.cross_project_search(
    query="deployment best practices",
    project_ids=["project1-uuid", "project2-uuid"],
    max_total_results=50,
    merge_strategy="relevance"
)

# Analyze results by project
for project_id, breakdown in results.data.project_breakdown.items():
    print(f"Project {project_id}: {breakdown.results} results")
    print(f"  Max score: {breakdown.max_score:.3f}")

# Show unified results
for result in results.data.results:
    project_info = result.project_context
    print(f"- {result.title}")
    print(f"  From: {project_info.project_name} ({project_info.connection_type})")
    print(f"  Score: {result.similarity_score:.3f}")
```

## Error Handling

The SDK provides comprehensive error handling with specific exception types:

```python
from betty_client.exceptions import (
    BettyAPIException,
    AuthenticationException,
    PermissionException,
    RateLimitException,
    ValidationException
)

async def robust_search(query: str):
    try:
        results = await client.advanced_search(query=query)
        return results
        
    except AuthenticationException:
        print("Authentication failed - check your API token")
        # Handle re-authentication
        
    except PermissionException as e:
        print(f"Missing permissions: {e.missing_permissions}")
        # Request permission upgrade
        
    except RateLimitException as e:
        print(f"Rate limited - retry after {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        # Retry the operation
        
    except ValidationException as e:
        print("Validation error:")
        for field, errors in e.field_errors.items():
            print(f"  {field}: {', '.join(errors)}")
        # Fix validation issues
        
    except BettyAPIException as e:
        print(f"API error {e.status_code}: {e.message}")
        if e.request_id:
            print(f"Request ID: {e.request_id}")
        # Handle general API errors
```

## Configuration

### Environment Variables

Set up your environment with these variables:

```bash
export BETTY_API_KEY="your-jwt-token"
export BETTY_BASE_URL="https://api.betty-memory.com/v2"
export BETTY_TIMEOUT="30"
export BETTY_RATE_LIMIT="100"
export BETTY_ENABLE_CACHING="true"
export BETTY_CACHE_TTL="300"
```

### Configuration File

Create a `betty-config.yaml` file:

```yaml
api_key: "your-jwt-token"
base_url: "https://api.betty-memory.com/v2"
timeout: 30
rate_limit_per_minute: 100
enable_caching: true
cache_ttl: 300
max_retries: 3
log_level: "INFO"
```

Or use JSON format (`betty-config.json`):

```json
{
    "api_key": "your-jwt-token",
    "base_url": "https://api.betty-memory.com/v2",
    "timeout": 30,
    "rate_limit_per_minute": 100,
    "enable_caching": true,
    "cache_ttl": 300,
    "max_retries": 3,
    "log_level": "INFO"
}
```

## Advanced Features

### Connection Pool Configuration

```python
import aiohttp
from betty_client import BettyClient

# Custom connection pool
connector = aiohttp.TCPConnector(
    limit=100,           # Total connection pool size
    limit_per_host=30,   # Connections per host
    ttl_dns_cache=300,   # DNS cache TTL
    use_dns_cache=True,
    keepalive_timeout=60
)

timeout = aiohttp.ClientTimeout(
    total=60,      # Total timeout
    connect=10,    # Connection timeout
    sock_read=30   # Socket read timeout
)

client = BettyClient(
    api_key="your-jwt-token",
    connector=connector,
    timeout=timeout
)
```

### Caching Support

```python
# Memory caching (built-in)
from betty_client.cache import MemoryCache

cache = MemoryCache(max_size=1000, ttl=300)
client = BettyClient(api_key="token", cache=cache)

# Redis caching (requires redis extra)
try:
    from betty_client.cache import RedisCache
    
    redis_cache = RedisCache(
        host="localhost",
        port=6379,
        db=0,
        ttl=300
    )
    client = BettyClient(api_key="token", cache=redis_cache)
    
except ImportError:
    print("Redis support not available. Install with: pip install betty-memory-sdk[cache]")
```

### Custom Request Headers

```python
# Add custom headers for all requests
client = BettyClient(
    api_key="your-jwt-token",
    custom_headers={
        "X-Client-Version": "1.0.0",
        "X-Application": "my-app"
    }
)
```

## Testing

The SDK includes comprehensive testing utilities:

```python
# Mock client for testing
from betty_client.testing import MockBettyClient

async def test_search():
    # Create mock client
    mock_client = MockBettyClient()
    
    # Add mock responses
    mock_client.add_response(
        "advanced_search",
        {
            "success": True,
            "data": {
                "results": [
                    {
                        "id": "test-id",
                        "title": "Test Result",
                        "similarity_score": 0.95
                    }
                ],
                "total_results": 1
            }
        }
    )
    
    # Test your code
    results = await mock_client.advanced_search(query="test")
    assert len(results.data.results) == 1
    assert results.data.results[0].title == "Test Result"
```

## Examples

The SDK includes comprehensive examples:

- [Basic Usage](examples/basic_usage.py)
- [Advanced Search](examples/advanced_search.py)
- [Pattern Matching](examples/pattern_matching.py)
- [Batch Operations](examples/batch_operations.py)
- [Real-time WebSocket](examples/websocket_monitoring.py)
- [Error Handling](examples/error_handling.py)
- [Configuration](examples/configuration.py)

## API Reference

### BettyClient

Main client class for BETTY Memory System v2.0 API.

#### Methods

- `advanced_search(query, **options)` - Advanced search with semantic capabilities
- `pattern_matching(pattern_type, **options)` - Find patterns in knowledge graphs
- `semantic_clustering(algorithm, **options)` - Create knowledge clusters
- `batch_import(source_type, **options)` - Start batch import operation
- `get_batch_progress(operation_id)` - Get operation progress
- `track_progress(operation_id)` - Track progress with async generator
- `add_knowledge(**data)` - Add new knowledge item
- `get_knowledge(knowledge_id)` - Get knowledge item by ID
- `update_knowledge(knowledge_id, **data)` - Update knowledge item
- `delete_knowledge(knowledge_id)` - Delete knowledge item
- `cross_project_search(query, **options)` - Search across projects
- `health_check()` - Check API health
- `close()` - Close client and cleanup resources

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | str | None | JWT token for authentication |
| `base_url` | str | "http://localhost:3034/api/v2" | API base URL |
| `timeout` | int | 30 | Request timeout in seconds |
| `connection_pool_size` | int | 10 | HTTP connection pool size |
| `rate_limit_per_minute` | int | 100 | Rate limit for requests |
| `max_retries` | int | 3 | Maximum retry attempts |
| `retry_delay` | float | 1.0 | Base retry delay |
| `enable_caching` | bool | True | Enable response caching |
| `cache_ttl` | int | 300 | Cache time-to-live in seconds |
| `log_level` | str | "INFO" | Logging level |

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/betty-python-sdk.git
cd betty-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
mypy betty_client

# Format code
black betty_client
isort betty_client

# Lint code
flake8 betty_client
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=betty_client --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run async tests only
pytest -m asyncio
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [https://docs.betty-memory.com/python-sdk](https://docs.betty-memory.com/python-sdk)
- **Issues**: [https://github.com/your-org/betty-python-sdk/issues](https://github.com/your-org/betty-python-sdk/issues)
- **Discussions**: [https://github.com/your-org/betty-python-sdk/discussions](https://github.com/your-org/betty-python-sdk/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.