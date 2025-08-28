# BETTY Memory System - Database Initialization

This directory contains all the database initialization scripts for the BETTY Memory System, Claude's cross-project memory and intelligence platform.

## Architecture Overview

BETTY uses a multi-database architecture for optimal performance and functionality:

- **PostgreSQL**: Source of truth for structured data (sessions, messages, knowledge items)
- **Neo4j**: Temporal knowledge graph via Graphiti framework (entities, relationships, patterns)
- **Qdrant**: Vector embeddings for semantic search (knowledge similarity, conversation search)
- **Redis**: Caching layer for performance optimization (context caching, session data)

## Initialization Scripts

### 1. PostgreSQL Schema (`01-postgresql-schema.sql`)

Creates the complete PostgreSQL schema with:
- **Core Tables**: projects, users, sessions, messages, knowledge_items, knowledge_relationships
- **System Tables**: tool_usage, audit_log, system_metrics
- **Performance Indexes**: 50+ optimized indexes for fast queries
- **Full-text Search**: Indexes on knowledge content and messages
- **Temporal Support**: Bi-temporal tracking with valid_from/valid_until
- **Triggers**: Automatic timestamp updates and message counting
- **Views**: Enriched views for common queries
- **Functions**: Statistics, cleanup, and monitoring functions

Key Features:
- UUIDs for all primary keys
- JSONB columns for flexible metadata
- Project boundary enforcement
- Comprehensive audit logging
- Performance-optimized for >100K knowledge items

### 2. Neo4j Constraints (`02-neo4j-constraints.cypher`)

Sets up Neo4j for Graphiti integration with:
- **Node Constraints**: Unique constraints for Projects, Entities, Knowledge, Users
- **Performance Indexes**: 25+ indexes for graph traversal optimization
- **Temporal Indexes**: Bi-temporal support for knowledge evolution
- **Full-text Search**: Content discovery across knowledge and entities
- **Initial Data**: Core domains, technologies, and project structure
- **Procedures**: Temporal queries, similarity detection, maintenance

Key Features:
- Graphiti framework compatibility
- Cross-project relationship tracking
- Temporal knowledge evolution
- Pattern recognition support
- Intelligence metrics collection

### 3. Qdrant Collections (`03-qdrant-collections.py`)

Creates optimized vector collections:
- **knowledge_embeddings**: 768-dim vectors for knowledge items
- **conversation_embeddings**: Chat message semantic search
- **pattern_embeddings**: Code pattern and solution clustering
- **cross_project_embeddings**: Cross-project relationship vectors

Key Features:
- Cosine similarity for semantic search
- Project-scoped filtering via metadata
- Quantization for memory efficiency
- Performance-tuned for <200ms queries
- Automatic payload indexing

### 4. Initialization Scripts

- **`init-neo4j.sh`**: Neo4j-specific initialization with connection waiting
- **`init-all-databases.sh`**: Master script for complete system initialization

## Usage

### Quick Start

```bash
# Initialize all databases
./init-db/init-all-databases.sh

# Force re-initialization
./init-db/init-all-databases.sh --force

# Verify existing setup
./init-db/init-all-databases.sh --verify-only
```

### Docker Integration

The PostgreSQL schema is automatically loaded via docker-compose:

```yml
postgres:
  volumes:
    - ./init-db:/docker-entrypoint-initdb.d
```

For Neo4j and Qdrant, run the initialization after containers start:

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Initialize databases
./init-db/init-all-databases.sh
```

### Manual Initialization

Each database can be initialized separately:

```bash
# PostgreSQL only
PGPASSWORD=bettypassword psql -h localhost -U betty -d betty_memory -f 01-postgresql-schema.sql

# Neo4j only
cypher-shell -a bolt://localhost:7687 -u neo4j -p bettypassword --file 02-neo4j-constraints.cypher

# Qdrant only
python3 03-qdrant-collections.py

# Redis (no schema needed, just configuration)
redis-cli -h localhost -p 6379 config set maxmemory-policy allkeys-lru
```

## Environment Variables

Configure database connections via environment variables:

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=betty_memory
POSTGRES_USER=betty
POSTGRES_PASSWORD=bettypassword

# Neo4j
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=bettypassword

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Database Schema Details

### PostgreSQL Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `projects` | Project definitions | Privacy controls, technology stacks |
| `users` | User profiles | Preferences, behavioral patterns |
| `sessions` | Claude interactions | Context, outcomes, tool usage |
| `messages` | Conversation history | Full-text search, embeddings |
| `knowledge_items` | Core knowledge | Bi-temporal, quality scoring |
| `knowledge_relationships` | Knowledge connections | Strength, confidence scoring |
| `tool_usage` | Tool interaction audit | Complete tool call history |
| `audit_log` | System audit trail | All actions and changes |
| `system_metrics` | Performance monitoring | Intelligence metrics |

### Neo4j Node Types

| Node Type | Purpose | Key Properties |
|-----------|---------|----------------|
| `Project` | Project organization | name, domain, technology_stack |
| `Entity` | Extracted entities | name, type, confidence_score |
| `Knowledge` | Knowledge items | title, domain, quality_score |
| `User` | System users | username, preferences |
| `Technology` | Tech stack items | name, category, ecosystem |
| `Domain` | Problem domains | name, business_area |
| `Pattern` | Code patterns | name, complexity_level |

### Qdrant Collections

| Collection | Vectors | Purpose |
|------------|---------|---------|
| `knowledge_embeddings` | 768-dim | Knowledge semantic search |
| `conversation_embeddings` | 768-dim | Chat history search |
| `pattern_embeddings` | 768-dim | Code pattern matching |
| `cross_project_embeddings` | 768-dim | Cross-project intelligence |

## Performance Specifications

- **Context Loading**: <100ms (95th percentile)
- **Knowledge Search**: <200ms (95th percentile)
- **Tool Interception**: <5ms (zero impact)
- **Background Processing**: 100+ items/minute
- **Concurrent Sessions**: 10+ simultaneous users
- **Storage Capacity**: >100K knowledge items

## Monitoring & Maintenance

### Health Checks

```bash
# Check all databases
./init-db/init-all-databases.sh --verify-only

# Individual health checks
pg_isready -h localhost -U betty -d betty_memory
cypher-shell -a bolt://localhost:7687 -u neo4j -p bettypassword "RETURN 'healthy'"
curl http://localhost:6333/health
redis-cli -h localhost ping
```

### Maintenance Functions

PostgreSQL includes automated maintenance:
- `update_updated_at_column()`: Automatic timestamp updates
- `get_knowledge_stats()`: Knowledge repository statistics
- `cleanup_old_audit_logs()`: Audit log retention policy

Neo4j procedures:
- `getTemporalKnowledge()`: Time-based knowledge queries
- `findSimilarKnowledge()`: Cross-project similarity detection
- `getGraphStats()`: Graph relationship metrics
- `cleanupTemporalVersions()`: Old version cleanup

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   # Check logs
   docker-compose logs postgres
   ```

2. **Neo4j Initialization Timeout**
   ```bash
   # Neo4j can take time to start with APOC plugins
   # Wait 60+ seconds after container start
   docker-compose logs neo4j
   ```

3. **Qdrant Collections Failed**
   ```bash
   # Install Python dependencies
   pip install qdrant-client httpx
   # Check Qdrant status
   curl http://localhost:6333/health
   ```

4. **Redis Configuration Issues**
   ```bash
   # Check Redis configuration
   redis-cli -h localhost config get maxmemory-policy
   ```

### Reset Procedures

```bash
# Reset PostgreSQL
docker-compose down -v
docker-compose up -d postgres
./init-db/init-all-databases.sh --force

# Reset Neo4j
docker-compose down
docker volume rm betty_neo4j_data
docker-compose up -d neo4j
./init-db/init-all-databases.sh --force

# Reset Qdrant
docker-compose down
docker volume rm betty_qdrant_data
docker-compose up -d qdrant
./init-db/init-all-databases.sh --force
```

## Integration with BETTY

These databases provide the foundation for BETTY's core capabilities:

1. **Knowledge Capture**: Tool usage → PostgreSQL audit trail
2. **Relationship Discovery**: Graphiti → Neo4j temporal graphs  
3. **Semantic Search**: Embeddings → Qdrant similarity search
4. **Performance Cache**: Context → Redis fast retrieval
5. **Cross-Project Intelligence**: Multi-DB queries → Unified insights

The initialization scripts ensure all databases are properly configured for seamless integration with the BETTY Memory API and Claude Code tool interception.

## Schema Version

Current schema version: **1.0.0**

Schema updates will be versioned and include migration scripts for existing deployments.