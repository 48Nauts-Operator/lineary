# BETTY Testing Scripts

Test scripts for validating BETTY functionality and integrations.

## Test Categories

### API Tests
- **`test_api.py`** - Core API endpoint testing
- **`test_betty_integration.py`** - Full integration testing
- **`test_simple_ingestion.py`** - Ingestion system validation

### Component Tests  
- **`test_betty_claude.py`** - Claude Code integration testing
- **`test_betty_quick.py`** - Quick smoke tests
- **`test_error_handling.js`** - Error handling validation

### System Tests
- **`final_test.py`** - Comprehensive system validation

### Test Data
- **`test_*.json`** - Test data files for various scenarios
- **`test_batch_ingestion.json`** - Batch ingestion test data
- **`test_results.json`** - Test result storage

## Running Tests

```bash
# Quick validation
python3 test_betty_quick.py

# Full integration test
python3 test_betty_integration.py

# API endpoint testing
python3 test_api.py

# Comprehensive system test
python3 final_test.py
```

## Test Requirements

- BETTY memory API running on port 8001
- All database services (PostgreSQL, Neo4j, Qdrant, Redis)
- Valid API credentials and configuration

---
*Tests organized for systematic validation*