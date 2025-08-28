# CRITICAL: Lineary Restart Procedures

## ⚠️ PRODUCTION DATA WARNING
This system contains PRODUCTION DATA. Never use destructive commands.

## Safe Restart Commands

### 1. ALWAYS USE SAFE RESTART SCRIPT (RECOMMENDED)
```bash
./scripts/safe-restart.sh
```
This script:
- Creates automatic safety backup before restart
- Uses non-destructive `docker-compose restart`
- Verifies data integrity after restart
- Provides backup location for recovery if needed

### 2. Simple Restart (if script unavailable)
```bash
docker-compose restart
```

### 3. Stop and Start (if restart doesn't work)
```bash
docker-compose stop
docker-compose start
```

## ❌ NEVER USE THESE COMMANDS
```bash
# NEVER DO THIS - IT DESTROYS DATA
docker-compose down
docker rm [container_name]
docker-compose up --force-recreate
```

## Backup System

### Automatic Backups
- **Schedule**: Daily at 2:00 AM
- **Retention**: 7 days
- **Location**: `/home/jarvis/projects/Lineary/backups/postgres/`

### Manual Backup
```bash
./scripts/backup-database.sh
```

### Restore from Backup
```bash
./scripts/restore-database.sh
# Interactive menu will guide you through restoration
```

## Data Recovery

If data is lost:

1. **Check for recent backups**:
   ```bash
   ls -lh /home/jarvis/projects/Lineary/backups/postgres/
   ```

2. **Restore from backup**:
   ```bash
   ./scripts/restore-database.sh
   ```

3. **Verify restoration**:
   ```bash
   docker exec lineary_postgres psql -U lineary -d lineary_db -c "
   SELECT 'Projects:' as type, COUNT(*) FROM projects
   UNION ALL
   SELECT 'Issues:', COUNT(*) FROM issues;"
   ```

## Container Health Check

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker logs lineary_backend --tail 20
docker logs lineary_postgres --tail 20

# Verify database connection
docker exec lineary_postgres pg_isready -U lineary -d lineary_db
```

## Emergency Contacts

If critical data loss occurs:
- Immediately check backups
- DO NOT attempt further operations
- Contact system administrator

## Lessons Learned

### 2024-08-24 Incident
- **What happened**: Production data (40+ issues, multiple projects) was lost
- **Cause**: Used `docker rm` instead of `docker-compose restart`
- **Impact**: Complete data loss, no recovery possible
- **Prevention**: This documentation and safety scripts were created

Remember: Production data is irreplaceable. Always backup before any operation.