# AgentBuilder MVP - Complete Setup Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker & Docker Compose** (v20.10+)
- **Python** 3.11+
- **Node.js** 18+ & npm
- **PostgreSQL** 16 (via Docker)
- **Redis** 7 (via Docker)

### Required API Keys
- **OpenRouter API Key** - For LLM inference: https://openrouter.ai/keys
- **Serper API Key** - For web search tool: https://serper.dev/api-key

---

## Quick Start

```bash
# 1. Clone and navigate
cd agentbuilder

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Initialize database
cd backend
python scripts/init_db.py

# 4. Start all services
cd ../infra
docker-compose up -d

# 5. Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Default Login**:
- Email: `admin@agentbuilder.com`
- Password: `admin123`

---

## Detailed Setup

### Step 1: Environment Configuration

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=postgresql://agentbuilder:agentbuilder123@localhost:5432/agentbuilder

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# Environment
ENV=development
LOG_LEVEL=INFO

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Step 2: Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Initialize database (creates tables + default data)
python scripts/init_db.py

# Expected output:
# ✅ Database tables created
# ✅ 4 prebuilt tools created
# ✅ Default organization created
# ✅ Admin user created
```

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access: http://localhost:5173
```

### Step 4: Start Services

```bash
cd infra

# Start all containers
docker-compose up -d

# Verify all services running
docker-compose ps

# Expected containers:
# - nginx (reverse proxy)
# - frontend (React app)
# - backend (FastAPI server)
# - postgres (database with pgvector)
# - redis (cache/queue)
# - celery (async tasks)
```

---

## Configuration

### Backend Configuration

**File**: `backend/app/config.py`

Key settings:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENROUTER_API_KEY` - LLM provider
- `SERPER_API_KEY` - Web search tool
- `JWT_SECRET_KEY` - Auth token signing

### Frontend Configuration

**File**: `frontend/.env`

```bash
# API endpoint
VITE_API_URL=http://localhost:8000

# WebSocket endpoint (optional)
VITE_WS_URL=ws://localhost:8000
```

### CopilotKit Configuration

**File**: `frontend/src/components/CopilotProvider.tsx`

- `runtimeUrl`: "/api/copilot" (configure backend route)
- `agent`: "agentbuilder-assistant"
- Sidebar labels and behavior

---

## Testing

### Backend API Tests

```bash
cd backend

# Run end-to-end test
python scripts/test_e2e.py

# Run API demo (no API keys required)
python scripts/demo_api.py

# Test WebSocket streaming
python scripts/demo_websocket.py <execution_id>
```

### Frontend Testing

```bash
cd frontend

# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Manual Testing Checklist

- [ ] Login with demo credentials
- [ ] Navigate to Agents page
- [ ] Create new agent with tools
- [ ] Execute agent (requires API keys)
- [ ] View execution in real-time
- [ ] Check execution logs
- [ ] View execution history
- [ ] CopilotKit sidebar opens and responds

---

## Deployment

### Production Environment Variables

```bash
# Backend
ENV=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db:5432/agentbuilder

# Frontend
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Database Migrations

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### SSL/HTTPS Setup

Update `infra/nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    # ... rest of config
}
```

---

## Architecture Overview

### Services

| Service | Port | Purpose |
|---------|------|---------|
| Nginx | 80, 443 | Reverse proxy |
| Frontend | 5173 | React UI |
| Backend | 8000 | FastAPI REST API + WebSocket |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache + task queue |
| Celery | - | Async task worker |

### Data Flow

```
User → Nginx → Frontend (React)
  ↓
  → Backend API (FastAPI)
      ↓
      → PostgreSQL (agent configs, executions)
      → Redis (task queue)
      → Celery (async execution)
      → OpenRouter (LLM inference)
      → Serper (web search)
```

### WebSocket Flow

```
Frontend → WebSocket Connection → Backend
                                     ↓
                              Real-time logs
                                     ↓
                              Client receives:
                              - execution_state
                              - log entries
                              - completion events
```

---

## Troubleshooting

### Backend Issues

**"No module named 'app'"**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"Connection refused" to database**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

**"Tool not found" errors**
```bash
# Re-initialize database
python backend/scripts/init_db.py
```

### Frontend Issues

**"Cannot find module 'axios'"**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**WebSocket connection fails**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check WebSocket endpoint
wscat -c ws://localhost:8000/ws/executions/test-id
```

**Build fails with TypeScript errors**
```bash
# Clear cache
rm -rf .vite dist
npm run build
```

### Docker Issues

**Port already in use**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Container keeps restarting**
```bash
# View logs
docker-compose logs <service-name>

# Inspect container
docker inspect <container-id>
```

---

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- **Frontend**: Vite automatically reloads on file changes
- **Backend**: FastAPI uvicorn with `--reload` flag

### Database UI

Access PostgreSQL via pgAdmin:
```bash
docker run -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@admin.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  dpage/pgadmin4
```

### Redis Monitoring

```bash
# Connect to Redis
docker exec -it <redis-container> redis-cli

# Monitor commands
MONITOR

# View keys
KEYS *
```

### API Documentation

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

---

## Next Steps

### Extend Functionality

1. **Add more prebuilt tools** - Edit `backend/app/services/tool_registry.py`
2. **Create custom agents** - Use Agent Builder UI
3. **Build workflows** - Workflow Builder (coming soon)
4. **Integrate RAG** - Add pgvector embeddings
5. **Add authentication provider** - OAuth, SAML

### Production Checklist

- [ ] Change default admin password
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure CORS origins
- [ ] Enable HTTPS/SSL
- [ ] Set up database backups
- [ ] Configure monitoring (Prometheus, Grafana)
- [ ] Set up logging aggregation
- [ ] Configure rate limiting
- [ ] Run security audit
- [ ] Performance testing

---

## Support

- **Documentation**: See `/docs` folder
- **API Reference**: http://localhost:8000/docs
- **Issues**: Create GitHub issue
- **Testing Guide**: See `TESTING.md`

---

## License

MIT License - See LICENSE file for details
