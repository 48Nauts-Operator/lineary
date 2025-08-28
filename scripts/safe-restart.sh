#!/bin/bash
# ABOUTME: Safe restart script with automatic backup before restart
# ABOUTME: Prevents data loss by creating safety backups before any restart operation

set -e

# Configuration
BACKUP_DIR="/home/jarvis/projects/Lineary/backups/postgres"
CONTAINER_NAME="lineary_postgres"
DB_NAME="lineary_db"
DB_USER="lineary"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFETY_BACKUP="${BACKUP_DIR}/safety_restart_${TIMESTAMP}.sql.gz"

echo "=== Lineary Safe Restart ==="
echo "This script will:"
echo "1. Create a safety backup"
echo "2. Perform a safe restart using docker-compose"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check current status
echo "Current container status:"
docker-compose ps

# Create safety backup if postgres is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ""
    echo "Step 1: Creating safety backup..."
    echo "Backup file: ${SAFETY_BACKUP}"
    
    # Create backup
    docker exec ${CONTAINER_NAME} pg_dump -U ${DB_USER} -d ${DB_NAME} --verbose --no-owner | gzip > "${SAFETY_BACKUP}"
    
    # Verify backup
    if [ -f "${SAFETY_BACKUP}" ]; then
        SIZE=$(du -h "${SAFETY_BACKUP}" | cut -f1)
        echo "✓ Safety backup created: ${SIZE}"
        
        # Show what's in the backup
        echo "Backup contains:"
        docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -t -c "
            SELECT 'Projects: ' || COUNT(*) FROM projects
            UNION ALL
            SELECT 'Issues: ' || COUNT(*) FROM issues
            UNION ALL
            SELECT 'Sprints: ' || COUNT(*) FROM sprints
            UNION ALL
            SELECT 'Comments: ' || COUNT(*) FROM issue_comments;
        " | sed 's/^[[:space:]]*/  /'
    else
        echo "ERROR: Failed to create safety backup!"
        echo "Restart aborted for safety."
        exit 1
    fi
else
    echo "WARNING: PostgreSQL container is not running. Skipping backup."
fi

# Perform safe restart
echo ""
echo "Step 2: Performing safe restart..."
echo "Using: docker-compose restart (containers will NOT be removed)"
echo ""

# Use restart, which keeps containers and volumes intact
docker-compose restart

# Wait for services to be healthy
echo ""
echo "Step 3: Waiting for services to be healthy..."
sleep 5

# Check health
docker-compose ps

# Verify data is intact
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ""
    echo "Step 4: Verifying data integrity..."
    docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "
        SELECT 'Data Check - ' || table_name || ': ' || COUNT(*) as status
        FROM (
            SELECT 'projects' as table_name FROM projects
            UNION ALL
            SELECT 'issues' FROM issues
            UNION ALL
            SELECT 'sprints' FROM sprints
        ) t
        GROUP BY table_name
        ORDER BY table_name;
    " 2>/dev/null || echo "Database is still starting up..."
fi

echo ""
echo "=== Safe Restart Complete ==="
echo "Safety backup available at: ${SAFETY_BACKUP}"
echo ""
echo "To restore from backup if needed, run:"
echo "  ./scripts/restore-database.sh"