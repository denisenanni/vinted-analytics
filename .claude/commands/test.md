Run tests for the project.

## API Tests
```bash
cd api
source venv/bin/activate
pytest
pytest -v  # verbose
pytest tests/test_analytics.py  # specific file
pytest -k "test_function_name"  # specific test
```

## Web Tests (if configured)
```bash
cd web
npm test
npm run test:coverage
```

## Manual API Testing
```bash
# Start server first
uvicorn src.main:app --reload

# Test endpoints
curl http://localhost:8000/api/categories
curl "http://localhost:8000/api/trends?market=IT"
curl "http://localhost:8000/api/lookup?brand=Nike"
curl "http://localhost:8000/api/market-profitability?category=women/dresses"
```

## Type Checking
```bash
cd web
npx tsc --noEmit  # Check TypeScript errors without building
```

## Linting
```bash
cd web
npm run lint
```
