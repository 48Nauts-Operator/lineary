#!/bin/bash

# BETTY Memory System - Complete Database Initialization
# Purpose: Initialize all databases (PostgreSQL, Neo4j, Qdrant, Redis) for BETTY Memory System
# Usage: ./init-all-databases.sh [--force] [--verify-only]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Database configurations
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-betty_memory}"
POSTGRES_USER="${POSTGRES_USER:-betty}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-bettypassword}"

NEO4J_HOST="${NEO4J_HOST:-localhost}"
NEO4J_PORT="${NEO4J_PORT:-7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-bettypassword}"

QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Script options
FORCE_INIT=false
VERIFY_ONLY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_INIT=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
            echo "BETTY Memory System - Database Initialization"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --force        Force re-initialization even if databases exist"
            echo "  --verify-only  Only verify existing databases, don't initialize"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  POSTGRES_HOST     PostgreSQL host (default: localhost)"
            echo "  POSTGRES_PORT     PostgreSQL port (default: 5432)"
            echo "  POSTGRES_DB       PostgreSQL database (default: betty_memory)"
            echo "  POSTGRES_USER     PostgreSQL user (default: betty)"
            echo "  POSTGRES_PASSWORD PostgreSQL password (default: bettypassword)"
            echo "  NEO4J_HOST        Neo4j host (default: localhost)"
            echo "  NEO4J_PORT        Neo4j port (default: 7687)"
            echo "  NEO4J_USER        Neo4j user (default: neo4j)"
            echo "  NEO4J_PASSWORD    Neo4j password (default: bettypassword)"
            echo "  QDRANT_HOST       Qdrant host (default: localhost)"
            echo "  QDRANT_PORT       Qdrant port (default: 6333)"
            echo "  REDIS_HOST        Redis host (default: localhost)"
            echo "  REDIS_PORT        Redis port (default: 6379)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# Wait for service functions
wait_for_postgres() {
    log_info "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" > /dev/null 2>&1; then
            log_success "PostgreSQL is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "PostgreSQL not ready yet (attempt $attempt/$max_attempts). Waiting 3 seconds..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log_error "PostgreSQL did not become ready within $((max_attempts * 3)) seconds"
    return 1
}

wait_for_neo4j() {
    log_info "Waiting for Neo4j to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                        -u "$NEO4J_USER" \
                        -p "$NEO4J_PASSWORD" \
                        "RETURN 'ready' AS status;" > /dev/null 2>&1; then
            log_success "Neo4j is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "Neo4j not ready yet (attempt $attempt/$max_attempts). Waiting 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    log_error "Neo4j did not become ready within $((max_attempts * 5)) seconds"
    return 1
}

wait_for_qdrant() {
    log_info "Waiting for Qdrant to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$QDRANT_HOST:$QDRANT_PORT/health" > /dev/null 2>&1; then
            log_success "Qdrant is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "Qdrant not ready yet (attempt $attempt/$max_attempts). Waiting 3 seconds..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    log_error "Qdrant did not become ready within $((max_attempts * 3)) seconds"
    return 1
}

wait_for_redis() {
    log_info "Waiting for Redis to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            log_success "Redis is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_info "Redis not ready yet (attempt $attempt/$max_attempts). Waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Redis did not become ready within $((max_attempts * 2)) seconds"
    return 1
}

# Database initialization functions
init_postgresql() {
    log_header "PostgreSQL Initialization"
    
    if ! wait_for_postgres; then
        log_error "PostgreSQL is not available"
        return 1
    fi
    
    # Check if database is already initialized
    local table_count
    table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
                  -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
                  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
    
    if [ "$table_count" -gt 0 ] && [ "$FORCE_INIT" = false ]; then
        log_warning "PostgreSQL database already initialized ($table_count tables found)"
        log_info "Use --force to re-initialize"
        return 0
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        log_info "PostgreSQL verification: $table_count tables found"
        return 0
    fi
    
    log_info "Initializing PostgreSQL schema..."
    
    # Execute PostgreSQL initialization script
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
                                           -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                                           -f "$SCRIPT_DIR/01-postgresql-schema.sql" > /dev/null; then
        log_success "PostgreSQL initialization completed"
        
        # Verify initialization
        table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
                      -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
                      "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
        log_success "Created $table_count tables with indexes and constraints"
        return 0
    else
        log_error "PostgreSQL initialization failed"
        return 1
    fi
}

init_neo4j() {
    log_header "Neo4j Initialization"
    
    if ! wait_for_neo4j; then
        log_error "Neo4j is not available"
        return 1
    fi
    
    # Check if Neo4j is already initialized
    local constraint_count
    constraint_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                   -u "$NEO4J_USER" \
                                   -p "$NEO4J_PASSWORD" \
                                   "SHOW CONSTRAINTS YIELD name RETURN count(name) AS count;" 2>/dev/null | \
                       grep -o '[0-9]*' | head -1 || echo "0")
    
    if [ "$constraint_count" -gt 0 ] && [ "$FORCE_INIT" = false ]; then
        log_warning "Neo4j already initialized ($constraint_count constraints found)"
        log_info "Use --force to re-initialize"
        return 0
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        log_info "Neo4j verification: $constraint_count constraints found"
        return 0
    fi
    
    log_info "Initializing Neo4j constraints and indexes..."
    
    # Execute Neo4j initialization script
    if cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                    -u "$NEO4J_USER" \
                    -p "$NEO4J_PASSWORD" \
                    --file "$SCRIPT_DIR/02-neo4j-constraints.cypher" > /dev/null; then
        log_success "Neo4j initialization completed"
        
        # Verify initialization
        constraint_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                       -u "$NEO4J_USER" \
                                       -p "$NEO4J_PASSWORD" \
                                       "SHOW CONSTRAINTS YIELD name RETURN count(name) AS count;" | \
                           grep -o '[0-9]*' | head -1)
        
        local index_count
        index_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                   -u "$NEO4J_USER" \
                                   -p "$NEO4J_PASSWORD" \
                                   "SHOW INDEXES YIELD name RETURN count(name) AS count;" | \
                      grep -o '[0-9]*' | head -1)
        
        log_success "Created $constraint_count constraints and $index_count indexes"
        return 0
    else
        log_error "Neo4j initialization failed"
        return 1
    fi
}

init_qdrant() {
    log_header "Qdrant Initialization"
    
    if ! wait_for_qdrant; then
        log_error "Qdrant is not available"
        return 1
    fi
    
    # Check if Qdrant collections exist
    local collection_count
    collection_count=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | \
                       python3 -c "import sys, json; print(len(json.load(sys.stdin)['result']['collections']))" 2>/dev/null || echo "0")
    
    if [ "$collection_count" -gt 0 ] && [ "$FORCE_INIT" = false ]; then
        log_warning "Qdrant already initialized ($collection_count collections found)"
        log_info "Use --force to re-initialize"
        return 0
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        log_info "Qdrant verification: $collection_count collections found"
        return 0
    fi
    
    log_info "Initializing Qdrant collections..."
    
    # Check if Python script exists and required packages are available
    if [ ! -f "$SCRIPT_DIR/03-qdrant-collections.py" ]; then
        log_error "Qdrant initialization script not found"
        return 1
    fi
    
    # Execute Qdrant initialization script
    if cd "$SCRIPT_DIR" && python3 03-qdrant-collections.py; then
        log_success "Qdrant initialization completed"
        
        # Verify initialization
        collection_count=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | \
                           python3 -c "import sys, json; print(len(json.load(sys.stdin)['result']['collections']))" 2>/dev/null || echo "0")
        log_success "Created $collection_count collections with optimized configurations"
        return 0
    else
        log_error "Qdrant initialization failed"
        log_info "Make sure Python dependencies are installed: pip install qdrant-client httpx"
        return 1
    fi
}

init_redis() {
    log_header "Redis Initialization"
    
    if ! wait_for_redis; then
        log_error "Redis is not available"
        return 1
    fi
    
    if [ "$VERIFY_ONLY" = true ]; then
        local redis_info
        redis_info=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info server | grep redis_version | cut -d: -f2 | tr -d '\r')
        log_info "Redis verification: version $redis_info"
        return 0
    fi
    
    log_info "Configuring Redis for BETTY Memory System..."
    
    # Set Redis configuration for optimal caching
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" config set maxmemory-policy allkeys-lru > /dev/null
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" config set save "900 1 300 10 60 10000" > /dev/null
    
    # Test Redis functionality
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" set betty:init:test "initialized" > /dev/null && \
       redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" get betty:init:test > /dev/null; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" del betty:init:test > /dev/null
        log_success "Redis initialization and configuration completed"
        return 0
    else
        log_error "Redis initialization failed"
        return 1
    fi
}

# Verification functions
verify_all_databases() {
    log_header "Database Verification"
    
    local all_healthy=true
    
    # Verify PostgreSQL
    log_info "Verifying PostgreSQL..."
    if wait_for_postgres; then
        local table_count
        table_count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
                      -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
                      "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
        
        if [ "$table_count" -gt 0 ]; then
            log_success "PostgreSQL: $table_count tables found"
        else
            log_error "PostgreSQL: No tables found"
            all_healthy=false
        fi
    else
        log_error "PostgreSQL: Not accessible"
        all_healthy=false
    fi
    
    # Verify Neo4j
    log_info "Verifying Neo4j..."
    if wait_for_neo4j; then
        local constraint_count
        constraint_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                       -u "$NEO4J_USER" \
                                       -p "$NEO4J_PASSWORD" \
                                       "SHOW CONSTRAINTS YIELD name RETURN count(name) AS count;" 2>/dev/null | \
                           grep -o '[0-9]*' | head -1 || echo "0")
        
        if [ "$constraint_count" -gt 0 ]; then
            log_success "Neo4j: $constraint_count constraints found"
        else
            log_error "Neo4j: No constraints found"
            all_healthy=false
        fi
    else
        log_error "Neo4j: Not accessible"
        all_healthy=false
    fi
    
    # Verify Qdrant
    log_info "Verifying Qdrant..."
    if wait_for_qdrant; then
        local collection_count
        collection_count=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | \
                           python3 -c "import sys, json; print(len(json.load(sys.stdin)['result']['collections']))" 2>/dev/null || echo "0")
        
        if [ "$collection_count" -gt 0 ]; then
            log_success "Qdrant: $collection_count collections found"
        else
            log_error "Qdrant: No collections found"
            all_healthy=false
        fi
    else
        log_error "Qdrant: Not accessible"
        all_healthy=false
    fi
    
    # Verify Redis
    log_info "Verifying Redis..."
    if wait_for_redis; then
        local redis_info
        redis_info=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info server | grep redis_version | cut -d: -f2 | tr -d '\r')
        log_success "Redis: Version $redis_info"
    else
        log_error "Redis: Not accessible"
        all_healthy=false
    fi
    
    return $all_healthy
}

# Main execution
main() {
    log_header "BETTY Memory System - Database Initialization"
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Script Directory: $SCRIPT_DIR"
    log_info "Force Initialization: $FORCE_INIT"
    log_info "Verify Only: $VERIFY_ONLY"
    
    if [ "$VERIFY_ONLY" = true ]; then
        log_info "Running in verification mode only..."
        if verify_all_databases; then
            log_header "✓ All databases are healthy and initialized"
            exit 0
        else
            log_header "✗ Some databases have issues"
            exit 1
        fi
    fi
    
    # Initialize databases in order
    local init_success=true
    
    # PostgreSQL first (source of truth)
    if ! init_postgresql; then
        init_success=false
    fi
    
    # Neo4j second (knowledge graph)
    if ! init_neo4j; then
        init_success=false
    fi
    
    # Qdrant third (vector embeddings)
    if ! init_qdrant; then
        init_success=false
    fi
    
    # Redis last (caching)
    if ! init_redis; then
        init_success=false
    fi
    
    # Final verification
    log_header "Final Verification"
    if verify_all_databases; then
        log_header "✓ BETTY Memory System Database Initialization Complete"
        log_success "All databases initialized and verified successfully"
        log_success "PostgreSQL: Structured data storage ready"
        log_success "Neo4j: Temporal knowledge graph ready"
        log_success "Qdrant: Vector embeddings collections ready"
        log_success "Redis: Caching layer ready"
        log_success ""
        log_success "BETTY Memory System is ready for cross-project intelligence!"
        exit 0
    else
        log_header "✗ BETTY Memory System Database Initialization Failed"
        log_error "Some databases could not be initialized or verified"
        log_error "Check the logs above for specific issues"
        exit 1
    fi
}

# Run main function
main "$@"