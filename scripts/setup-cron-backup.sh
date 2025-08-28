#!/bin/bash
# ABOUTME: Sets up daily automated backups via cron
# ABOUTME: Installs a cron job to run backups daily at 2 AM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-database.sh"
CRON_LOG_DIR="/home/jarvis/projects/Lineary/logs"
CRON_LOG="${CRON_LOG_DIR}/backup-cron.log"

echo "=== Setting up Lineary Daily Backup Cron Job ==="

# Create log directory
mkdir -p "${CRON_LOG_DIR}"

# Make backup script executable
chmod +x "${BACKUP_SCRIPT}"
chmod +x "${SCRIPT_DIR}/restore-database.sh"
chmod +x "${SCRIPT_DIR}/safe-restart.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "lineary.*backup-database.sh"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l | grep -v "lineary.*backup-database.sh" | crontab -
fi

# Add new cron job (2 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * ${BACKUP_SCRIPT} >> ${CRON_LOG} 2>&1") | crontab -

echo "Cron job installed successfully!"
echo ""
echo "Current crontab:"
crontab -l | grep lineary || echo "No Lineary cron jobs found"

echo ""
echo "Daily backups will run at 2:00 AM"
echo "Logs will be saved to: ${CRON_LOG}"
echo "Backups will be stored in: /home/jarvis/projects/Lineary/backups/postgres"
echo "Retention: 7 days"
echo ""
echo "To test the backup now, run:"
echo "  ${BACKUP_SCRIPT}"
echo ""
echo "=== Setup Complete ===">