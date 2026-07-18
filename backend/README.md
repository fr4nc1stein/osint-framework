# OSIF v2.0 Backend

FastAPI-based backend for the Open Source Intelligence Framework.

## Quick Start

### Docker Development (Recommended)

**Everything is automated - just run:**

```bash
# Start all services (migrations run automatically)
docker-compose -f ../docker-compose.dev.yml up -d

# View logs
docker-compose -f ../docker-compose.dev.yml logs -f backend

# Stop services
docker-compose -f ../docker-compose.dev.yml down
```

The entrypoint script automatically:
- ✅ Waits for PostgreSQL and Redis
- ✅ Runs database migrations
- ✅ Starts the API server

### Local Development (Manual)

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start PostgreSQL and Redis (via Docker)
docker-compose -f ../docker-compose.dev.yml up -d postgres redis

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 6000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:6000/api/docs
- ReDoc: http://localhost:6000/api/redoc
- OpenAPI JSON: http://localhost:6000/api/openapi.json

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── modules/         # OSINT modules
│   └── main.py          # FastAPI app factory
├── alembic/             # Database migrations
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── Dockerfile           # Container image
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Adding New OSINT Modules

1. Create module file in `app/modules/<category>/`
2. Inherit from `BaseOSINTModule`
3. Add `@register_module` decorator
4. Implement `execute()` method

Example:

```python
from app.modules.base import BaseOSINTModule
from app.modules.registry import register_module

@register_module
class MyModule(BaseOSINTModule):
    MODULE_ID = "my_module"
    DISPLAY_NAME = "My Module"
    DESCRIPTION = "Does something cool"
    CATEGORY = "domain"
    ACCEPTS = ["domain"]
    
    async def execute(self, target, kind, **kwargs):
        # Your logic here
        return []
```

Module will auto-register on startup!

## Environment Variables

See `.env.example` for all configuration options.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_modules.py
```

## Health Checks

- `/health` - Liveness probe (always returns 200)
- `/ready` - Readiness probe (checks DB + Redis)
