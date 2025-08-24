#!/bin/bash

# BETTY Memory System - Neo4j Initialization Script
# Purpose: Initialize Neo4j constraints and indexes for Graphiti integration
# Usage: Run this script after Neo4j container is fully started

set -e

# Configuration
NEO4J_HOST="${NEO4J_HOST:-localhost}"
NEO4J_PORT="${NEO4J_PORT:-7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-bettypassword}"
CYPHER_SCRIPT="/docker-entrypoint-initdb.d/02-neo4j-constraints.cypher"

echo "============================================================"
echo "BETTY Memory System - Neo4j Initialization"
echo "============================================================"
echo "Host: $NEO4J_HOST:$NEO4J_PORT"
echo "User: $NEO4J_USER"
echo "Script: $CYPHER_SCRIPT"
echo ""

# Function to wait for Neo4j to be ready
wait_for_neo4j() {
    echo "Waiting for Neo4j to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                        -u "$NEO4J_USER" \
                        -p "$NEO4J_PASSWORD" \
                        "RETURN 'Neo4j is ready' AS status;" > /dev/null 2>&1; then
            echo "Neo4j is ready (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        echo "Neo4j not ready yet (attempt $attempt/$max_attempts). Waiting 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "ERROR: Neo4j did not become ready within $((max_attempts * 5)) seconds"
    return 1
}

# Function to execute Cypher script
execute_cypher_script() {
    echo "Executing Neo4j initialization script..."
    
    if [ ! -f "$CYPHER_SCRIPT" ]; then
        echo "ERROR: Cypher script not found: $CYPHER_SCRIPT"
        return 1
    fi
    
    # Execute the Cypher script
    if cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                    -u "$NEO4J_USER" \
                    -p "$NEO4J_PASSWORD" \
                    --file "$CYPHER_SCRIPT"; then
        echo "✓ Neo4j initialization script executed successfully"
        return 0
    else
        echo "✗ Failed to execute Neo4j initialization script"
        return 1
    fi
}

# Function to verify initialization
verify_initialization() {
    echo "Verifying Neo4j initialization..."
    
    # Check constraints
    local constraint_count
    constraint_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                   -u "$NEO4J_USER" \
                                   -p "$NEO4J_PASSWORD" \
                                   "SHOW CONSTRAINTS YIELD name RETURN count(name) AS constraint_count;" | \
                      grep -o '[0-9]*' | head -1)
    
    echo "Constraints created: $constraint_count"
    
    # Check indexes
    local index_count
    index_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                               -u "$NEO4J_USER" \
                               -p "$NEO4J_PASSWORD" \
                               "SHOW INDEXES YIELD name RETURN count(name) AS index_count;" | \
                  grep -o '[0-9]*' | head -1)
    
    echo "Indexes created: $index_count"
    
    # Check initial data
    local project_count
    project_count=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                 -u "$NEO4J_USER" \
                                 -p "$NEO4J_PASSWORD" \
                                 "MATCH (p:Project) RETURN count(p) AS project_count;" | \
                    grep -o '[0-9]*' | head -1)
    
    echo "Projects created: $project_count"
    
    # Check system metadata
    local system_check
    system_check=$(cypher-shell -a "bolt://$NEO4J_HOST:$NEO4J_PORT" \
                                -u "$NEO4J_USER" \
                                -p "$NEO4J_PASSWORD" \
                                "MATCH (s:SystemMetadata) RETURN s.schema_version AS version;" | \
                   grep -v "version" | xargs)
    
    echo "Schema version: $system_check"
    
    if [ "$constraint_count" -gt 0 ] && [ "$index_count" -gt 0 ] && [ "$project_count" -gt 0 ]; then
        echo "✓ Neo4j initialization verification successful"
        return 0
    else
        echo "✗ Neo4j initialization verification failed"
        return 1
    fi
}

# Main execution
main() {
    echo "Starting Neo4j initialization process..."
    
    # Wait for Neo4j to be ready
    if ! wait_for_neo4j; then
        echo "ERROR: Neo4j is not available"
        exit 1
    fi
    
    # Execute initialization script
    if ! execute_cypher_script; then
        echo "ERROR: Failed to initialize Neo4j"
        exit 1
    fi
    
    # Verify initialization
    if ! verify_initialization; then
        echo "WARNING: Neo4j initialization verification failed"
        exit 1
    fi
    
    echo ""
    echo "============================================================"
    echo "✓ BETTY Memory System Neo4j initialization completed"
    echo "✓ Graphiti temporal knowledge graph ready"
    echo "✓ All constraints and indexes created"
    echo "✓ Initial data loaded successfully"
    echo "============================================================"
}

# Run main function
main "$@"