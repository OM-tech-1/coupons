# Tests Directory

This directory contains all test files for the coupon application.

## Test Files

- `test_models.py` - Database model tests
- `test_postman_repro.py` - Postman collection reproduction tests
- `test_prod_full.py` - Full production API tests

## Running Tests

```bash
# From project root
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_models.py

# With verbose output
python -m pytest tests/ -v
```
