# BETTY Memory System v2.0 - Migration Tools

This directory contains comprehensive migration tools for upgrading from BETTY Memory System v1.x to v2.0. These tools provide automated migration, compatibility checking, and validation to ensure a smooth transition between versions.

## Overview

The migration tools consist of four main components:

1. **Schema Migrator** (`schema_migrator.py`) - Database schema migration
2. **Data Converter** (`data_converter.py`) - Data format transformation  
3. **API Mapper** (`api_mapper.py`) - API endpoint mapping and compatibility
4. **Compatibility Checker** (`compatibility_checker.py`) - Integration testing and validation

## Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install asyncpg aiosqlite aiohttp pydantic

# Ensure you have:
# - Access to v1.x SQLite database
# - PostgreSQL v2.0 database credentials
# - Network access to both API endpoints
```

### Basic Migration Workflow

```bash
# 1. Check compatibility first
python3 compatibility_checker.py \
    --v1-url http://localhost:3033/api/v1 \
    --v2-url http://localhost:3034/api/v2 \
    --output compatibility_report.json

# 2. Migrate database schema
python3 schema_migrator.py \
    --v2-host localhost \
    --v2-user betty_user \
    --v2-password your_password \
    --v2-database betty_v2 \
    --backup-path ./migration_backup

# 3. Convert and migrate data
python3 data_converter.py \
    --v1-db /path/to/v1/betty.db \
    --v2-host localhost \
    --v2-user betty_user \
    --v2-password your_password \
    --v2-database betty_v2 \
    --error-report conversion_errors.json

# 4. Generate API migration guide
python3 api_mapper.py \
    --action report \
    --output api_migration_guide.json
```

## Tool Documentation

### Schema Migrator

Handles database schema migration from v1.x SQLite to v2.0 PostgreSQL.

**Features:**
- Step-by-step schema creation
- Dependency resolution between tables
- Index and constraint creation
- Rollback capability
- Comprehensive backup and restore

**Usage:**
```bash
python3 schema_migrator.py \
    --v2-host localhost \
    --v2-port 5432 \
    --v2-user betty_user \
    --v2-password your_password \
    --v2-database betty_v2 \
    --backup-path ./backup \
    --log-level INFO
```

**Key Features:**
- Creates all v2.0 tables with proper relationships
- Sets up indexes for optimal performance
- Handles PostgreSQL-specific features (JSON columns, UUIDs)
- Validates migration success
- Provides rollback for failed migrations

### Data Converter

Transforms data from v1.x format to v2.0 format with comprehensive error handling.

**Features:**
- Batch processing for large datasets
- Field mapping and transformation
- Metadata format conversion
- Relationship preservation
- Progress tracking and error reporting

**Usage:**
```bash
python3 data_converter.py \
    --v1-db /path/to/v1/betty.db \
    --v2-host localhost \
    --v2-port 5432 \
    --v2-user betty_user \
    --v2-password your_password \
    --v2-database betty_v2 \
    --batch-size 100 \
    --error-report errors.json \
    --log-level INFO
```

**Data Transformations:**
- `type` → `knowledge_type` field mapping
- Tags moved to `metadata.tags` structure
- Timestamp format standardization
- User role and permission mapping
- Relationship type normalization

### API Mapper

Provides mapping between v1.x and v2.0 API endpoints with transformation support.

**Features:**
- Complete endpoint mapping documentation
- Request/response transformation
- Breaking change identification
- Migration guide generation
- Code examples and recommendations

**Usage:**
```bash
# Find mapping for specific endpoint
python3 api_mapper.py \
    --action map \
    --method GET \
    --path "/api/v1/search"

# Generate migration guide for endpoint
python3 api_mapper.py \
    --action guide \
    --method POST \
    --path "/api/v1/knowledge/add"

# Generate comprehensive compatibility report
python3 api_mapper.py \
    --action report \
    --output api_compatibility.json
```

**Key Mappings:**
- `GET /api/v1/search` → `POST /api/v2/query/advanced-search`
- `/api/v1/knowledge/*` → `/api/v2/knowledge/*` (with field changes)
- Authentication endpoints with enhanced JWT structure
- New v2.0 endpoints: pattern matching, clustering, batch operations

### Compatibility Checker

Comprehensive testing and validation tool for migration readiness.

**Features:**
- System health verification
- Endpoint compatibility testing
- Data format validation
- Performance impact assessment
- Integration testing
- Migration readiness scoring

**Usage:**
```bash
python3 compatibility_checker.py \
    --v1-url http://localhost:3033/api/v1 \
    --v2-url http://localhost:3034/api/v2 \
    --config test_config.json \
    --output compatibility_report.json \
    --timeout 30 \
    --log-level INFO
```

**Test Categories:**
- System health and availability
- API endpoint compatibility
- Authentication and authorization
- Data format compatibility
- Feature parity verification
- Performance comparison
- Data integrity validation

## Configuration

### Test Configuration File

Create a `test_config.json` file for compatibility checking:

```json
{
  "test_username": "test_user",
  "test_password": "test_password",
  "timeout": 30,
  "retry_attempts": 3,
  "performance_threshold": 2.0
}
```

### Environment Variables

Set these environment variables for easier configuration:

```bash
export BETTY_V1_DB_PATH="/path/to/v1/betty.db"
export BETTY_V2_HOST="localhost"
export BETTY_V2_PORT="5432"
export BETTY_V2_USER="betty_user"
export BETTY_V2_PASSWORD="your_password"
export BETTY_V2_DATABASE="betty_v2"
export BETTY_V1_API_URL="http://localhost:3033/api/v1"
export BETTY_V2_API_URL="http://localhost:3034/api/v2"
```

## Migration Best Practices

### Pre-Migration

1. **Backup Everything**
   ```bash
   # Backup v1.x database
   cp /path/to/betty.db /backup/betty_v1_backup.db
   
   # Backup v2.0 database
   pg_dump betty_v2 > /backup/betty_v2_backup.sql
   ```

2. **Run Compatibility Check**
   ```bash
   python3 compatibility_checker.py \
       --v1-url $BETTY_V1_API_URL \
       --v2-url $BETTY_V2_API_URL \
       --output pre_migration_check.json
   ```

3. **Validate Test Environment**
   - Set up identical production-like staging environment
   - Test migration on subset of data first
   - Verify all client applications work with v2.0

### During Migration

1. **Follow Sequential Order**
   ```bash
   # Step 1: Schema migration
   python3 schema_migrator.py [options]
   
   # Step 2: Data conversion
   python3 data_converter.py [options]
   
   # Step 3: Validation
   python3 compatibility_checker.py [options]
   ```

2. **Monitor Progress**
   - Use log outputs to track progress
   - Monitor system resources (CPU, memory, disk)
   - Check error reports regularly

3. **Validate Each Step**
   - Verify schema creation before data migration
   - Check data integrity after conversion
   - Test API endpoints after each change

### Post-Migration

1. **Comprehensive Testing**
   ```bash
   python3 compatibility_checker.py \
       --v1-url $BETTY_V1_API_URL \
       --v2-url $BETTY_V2_API_URL \
       --output post_migration_check.json
   ```

2. **Performance Verification**
   - Compare response times between versions
   - Monitor system resource usage
   - Check database query performance

3. **User Acceptance Testing**
   - Test all critical user workflows
   - Verify data accuracy and completeness
   - Confirm all features work as expected

## Error Handling and Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL connectivity
   psql -h localhost -U betty_user -d betty_v2 -c "SELECT 1;"
   
   # Verify SQLite database accessibility
   sqlite3 /path/to/betty.db ".tables"
   ```

2. **Data Conversion Errors**
   - Check error report JSON for specific issues
   - Verify data types and constraints
   - Ensure required fields are present

3. **API Compatibility Issues**
   - Review breaking changes documentation
   - Update client code for new endpoints
   - Handle new response formats

### Recovery Procedures

1. **Schema Migration Rollback**
   ```bash
   python3 schema_migrator.py --rollback --backup-path ./backup
   ```

2. **Data Restoration**
   ```bash
   # Restore from backup if needed
   psql betty_v2 < /backup/betty_v2_backup.sql
   ```

3. **Progressive Migration**
   - Migrate in smaller batches
   - Test each batch before proceeding
   - Maintain rollback points

## Advanced Usage

### Custom Transformations

Extend the data converter with custom transformation functions:

```python
async def custom_metadata_transformer(self, value, context):
    # Custom transformation logic
    return transformed_value

# Add to data_converter.py transformers
self.request_transformers['custom_transform'] = custom_metadata_transformer
```

### API Endpoint Extensions

Add new endpoint mappings to the API mapper:

```python
EndpointMapping(
    v1_method="GET",
    v1_path="/api/v1/custom/endpoint",
    v2_method="POST", 
    v2_path="/api/v2/custom/enhanced-endpoint",
    request_transformer="transform_custom_request",
    breaking_changes=["Method changed from GET to POST"]
)
```

### Custom Compatibility Tests

Extend the compatibility checker with domain-specific tests:

```python
async def custom_business_logic_test(self):
    # Test specific business requirements
    result = TestResult(
        test_name="custom_business_logic",
        endpoint="/custom",
        method="internal",
        status="passed",
        message="Custom business logic validated"
    )
    self.test_results.append(result)
```

## Performance Considerations

### Optimization Tips

1. **Batch Size Tuning**
   - Start with smaller batches (50-100 items)
   - Increase based on system performance
   - Monitor memory usage during conversion

2. **Database Optimization**
   ```sql
   -- Disable indexes during bulk insert
   DROP INDEX IF EXISTS idx_knowledge_content;
   
   -- Re-create after migration
   CREATE INDEX idx_knowledge_content ON knowledge_items USING gin(to_tsvector('english', content));
   ```

3. **Connection Pooling**
   - Use connection pooling for large migrations
   - Limit concurrent connections
   - Implement proper connection cleanup

### Monitoring

1. **Progress Tracking**
   - Use built-in progress indicators
   - Monitor log files in real-time
   - Set up alerts for errors

2. **Resource Monitoring**
   ```bash
   # Monitor system resources
   htop
   iotop
   
   # Monitor database performance
   pg_stat_activity
   ```

## Support and Troubleshooting

### Getting Help

1. **Log Analysis**
   - Enable DEBUG logging for detailed information
   - Check error reports in JSON format
   - Review compatibility test results

2. **Documentation References**
   - API documentation: `/docs/api-reference.md`
   - Migration guide: `/docs/migration-v1-to-v2.md`
   - SDK documentation: `/docs/sdk-guide.md`

### Common Solutions

1. **Memory Issues**
   - Reduce batch size
   - Implement streaming for large datasets
   - Clear caches between batches

2. **Performance Issues**
   - Optimize database queries
   - Use parallel processing where safe
   - Implement progress checkpointing

3. **Data Integrity Issues**
   - Validate source data before migration
   - Use transaction boundaries appropriately
   - Implement comprehensive error checking

## Contributing

When extending the migration tools:

1. Follow existing code patterns and error handling
2. Add comprehensive tests for new functionality
3. Update documentation for any new features
4. Ensure backward compatibility where possible
5. Add appropriate logging and progress indicators

## License

These migration tools are part of the BETTY Memory System v2.0 project and follow the same licensing terms as the main project.