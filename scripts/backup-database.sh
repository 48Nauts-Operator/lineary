#!/bin/bash
# ABOUTME: Automated database backup script with 7-day retention
# ABOUTME: Creates timestamped PostgreSQL dumps and manages retention policy

set -e

# Configuration
BACKUP_DIR="/home/jarvis/projects/Lineary/backups/postgres"
CONTAINER_NAME="lineary_postgres"
DB_NAME="lineary_db"
DB_USER="lineary"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/lineary_backup_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "=== Starting Lineary Database Backup ==="
echo "Timestamp: ${TIMESTAMP}"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container ${CONTAINER_NAME} is not running!"
    exit 1
fi

# Create backup
echo "Creating backup: ${BACKUP_FILE}"
docker exec ${CONTAINER_NAME} pg_dump -U ${DB_USER} -d ${DB_NAME} --verbose --no-owner | gzip > "${BACKUP_FILE}"

# Verify backup was created and has content
if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "Backup created successfully: ${BACKUP_FILE} (${SIZE})"
    
    # List table counts for verification
    echo "Backup contents summary:"
    docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "
        SELECT 'projects' as table_name, COUNT(*) as count FROM projects
        UNION ALL
        SELECT 'issues', COUNT(*) FROM issues
        UNION ALL
        SELECT 'sprints', COUNT(*) FROM sprints
        UNION ALL
        SELECT 'issue_comments', COUNT(*) FROM issue_comments
        ORDER BY table_name;
    "
else
    echo "ERROR: Backup file was not created!"
    exit 1
fi

# Remove backups older than retention period
echo "Cleaning up old backups (keeping ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "lineary_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete -print | while read file; do
    echo "Deleted old backup: $(basename $file)"
done

# List current backups
echo "Current backups:"
ls -lh "${BACKUP_DIR}"/lineary_backup_*.sql.gz 2>/dev/null | tail -5 || echo "No backups found"

echo "=== Backup Complete ==="