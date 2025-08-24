#!/bin/bash
# ABOUTME: Database restore script for recovering from backups
# ABOUTME: Provides interactive restore with safety confirmations

set -e

# Configuration
BACKUP_DIR="/home/jarvis/projects/Lineary/backups/postgres"
CONTAINER_NAME="lineary_postgres"
DB_NAME="lineary_db"
DB_USER="lineary"

echo "=== Lineary Database Restore Tool ==="

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "ERROR: Container ${CONTAINER_NAME} is not running!"
    exit 1
fi

# List available backups
echo "Available backups:"
BACKUPS=($(ls -t "${BACKUP_DIR}"/lineary_backup_*.sql.gz 2>/dev/null))

if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "No backups found in ${BACKUP_DIR}"
    exit 1
fi

for i in "${!BACKUPS[@]}"; do
    FILE="${BACKUPS[$i]}"
    SIZE=$(du -h "${FILE}" | cut -f1)
    DATE=$(basename "${FILE}" | sed 's/lineary_backup_\(.*\)\.sql\.gz/\1/' | sed 's/_/ /')
    echo "  $((i+1)). $(basename ${FILE}) - ${SIZE} - Created: ${DATE}"
done

# Select backup
echo -n "Select backup to restore (1-${#BACKUPS[@]}) or 'q' to quit: "
read choice

if [ "$choice" = "q" ]; then
    echo "Restore cancelled"
    exit 0
fi

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#BACKUPS[@]} ]; then
    echo "Invalid selection"
    exit 1
fi

SELECTED_BACKUP="${BACKUPS[$((choice-1))]}"
echo "Selected: $(basename ${SELECTED_BACKUP})"

# Show current database state
echo ""
echo "Current database state:"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "
    SELECT 'projects' as table_name, COUNT(*) as count FROM projects
    UNION ALL
    SELECT 'issues', COUNT(*) FROM issues
    UNION ALL
    SELECT 'sprints', COUNT(*) FROM sprints
    ORDER BY table_name;
"

# Final confirmation
echo ""
echo "WARNING: This will REPLACE ALL CURRENT DATA with the backup!"
echo -n "Type 'RESTORE' to confirm: "
read confirm

if [ "$confirm" != "RESTORE" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Create safety backup before restore
SAFETY_BACKUP="${BACKUP_DIR}/pre_restore_safety_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "Creating safety backup before restore: ${SAFETY_BACKUP}"
docker exec ${CONTAINER_NAME} pg_dump -U ${DB_USER} -d ${DB_NAME} --no-owner | gzip > "${SAFETY_BACKUP}"

# Perform restore
echo "Restoring database from ${SELECTED_BACKUP}..."

# Drop and recreate database
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "DROP DATABASE IF EXISTS ${DB_NAME}_temp;"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "CREATE DATABASE ${DB_NAME}_temp;"

# Restore to temp database first
gunzip -c "${SELECTED_BACKUP}" | docker exec -i ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}_temp

# If successful, swap databases
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "
    SELECT pg_terminate_backend(pid) 
    FROM pg_stat_activity 
    WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();
"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "DROP DATABASE IF EXISTS ${DB_NAME}_old;"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "ALTER DATABASE ${DB_NAME} RENAME TO ${DB_NAME}_old;"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -c "ALTER DATABASE ${DB_NAME}_temp RENAME TO ${DB_NAME};"

# Show restored state
echo ""
echo "Restored database state:"
docker exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME} -c "
    SELECT 'projects' as table_name, COUNT(*) as count FROM projects
    UNION ALL
    SELECT 'issues', COUNT(*) FROM issues
    UNION ALL
    SELECT 'sprints', COUNT(*) FROM sprints
    ORDER BY table_name;
"

echo "=== Restore Complete ==="
echo "Safety backup saved at: ${SAFETY_BACKUP}"