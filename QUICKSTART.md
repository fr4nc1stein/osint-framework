# OSIF v2.0 - Quick Start Guide

## 🚀 One-Command Setup

Everything is automated! Just run:

```bash
cd /Users/alfrancis/Desktop/Projects/osint-framework

# Start all services (migrations run automatically)
docker-compose -f docker-compose.dev.yml up -d
```

That's it! The system will:
- ✅ Start PostgreSQL and Redis
- ✅ Wait for databases to be ready
- ✅ Run database migrations automatically
- ✅ Start the FastAPI server on port **6000**

## 📊 View Logs

```bash
# Watch initialization process
docker-compose -f docker-compose.dev.yml logs -f backend

# You should see:
# 🚀 OSIF v2.0 Backend - Starting initialization...
# ⏳ Waiting for PostgreSQL...
# ✅ PostgreSQL is ready!
# ⏳ Waiting for Redis...
# ✅ Redis is ready!
# 🔄 Running database migrations...
# ✅ Migrations complete!
# 🎯 Starting application...
```

## 🧪 Test the API

```bash
# Health check
curl http://localhost:6000/health

# List available OSINT modules
curl http://localhost:6000/api/v1/modules

# Create a test case
curl -X POST http://localhost:6000/api/v1/cases \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Investigation",
    "description": "Testing OSIF v2.0",
    "priority": "high"
  }'
```

## 📖 API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:6000/api/docs
- **ReDoc**: http://localhost:6000/api/redoc

## 🛑 Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

## 🔧 Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose -f docker-compose.dev.yml up -d --build
```

## 📝 Environment Variables

To configure API keys:

```bash
# Copy example file
cp backend/.env.example backend/.env

# Edit with your API keys
nano backend/.env
```

Then restart:
```bash
docker-compose -f docker-compose.dev.yml restart backend
```

## 🐛 Troubleshooting

### Port 6000 already in use?

```bash
# Check what's using the port
lsof -i :6000

# Kill the process or change the port in docker-compose.dev.yml
```

### Database connection issues?

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps postgres

# View PostgreSQL logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### Reset everything?

```bash
# Stop and remove all data
docker-compose -f docker-compose.dev.yml down -v

# Start fresh
docker-compose -f docker-compose.dev.yml up -d
```

## 📚 Next Steps

1. **Explore API**: http://localhost:6000/api/docs
2. **Read Backend Docs**: `backend/README.md`
3. **Check Architecture**: `docs/architecture.md`
4. **View Spec**: `docs/spec.md`

---

**Port:** 6000  
**Auto-migrations:** ✅ Enabled  
**Hot-reload:** ✅ Enabled (development mode)
