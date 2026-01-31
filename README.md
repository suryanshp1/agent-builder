# AgentBuilder

**AI Agent Orchestration Platform with Generative UI**

AgentBuilder is a production-grade platform for creating, orchestrating, and monitoring AI agents through intuitive visual interfaces and deep observability. Built with React, FastAPI, LangChain/LangGraph, and PostgreSQL.

## Features

- 🤖 **UI-First Agent Builder**: Create sophisticated agents through form-based configuration
- 🔄 **Multi-Agent Workflows**: Orchestrate complex workflows with LangGraph (sequential, conditional, parallel)
- 🎨 **Generative UI**: Dynamic rendering of tool results using CopilotKit patterns
- 📊 **Deep Observability**: Real-time execution logs, token tracking, and cost analysis
- 🧠 **RAG & Memory**: Vector database integration with pgvector for semantic search
- 🔧 **Extensible Tools**: Prebuilt tools (web search, RAG, code execution) + custom tool creation
- 🏢 **Enterprise-Ready**: Multi-tenancy, RBAC, audit logging
- 🐳 **Docker Infrastructure**: Complete containerized stack with Docker Compose

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                       Nginx (Reverse Proxy)               │
└────────┬─────────────────────────────────────┬───────────┘
         │                                     │
    ┌────▼──────┐                         ┌────▼──────────┐
    │  Frontend │                         │    Backend    │
    │  (React)  │                         │   (FastAPI)   │
    └───────────┘                         └────┬──────────┘
                                               │
                    ┌──────────────────────────┼────────────────┐
                    │                          │                │
             ┌──────▼──────┐         ┌─────────▼─────┐  ┌──────▼──────┐
             │  PostgreSQL │         │     Redis     │  │   Celery    │
             │  + pgvector │         │  (Cache/Queue) │  │   Workers   │
             └─────────────┘         └───────────────┘  └─────────────┘
```

## Tech Stack

### Frontend
- **React 19** + TypeScript
- **CopilotKit** for generative UI
- **Zustand** for state management
- **React Flow** for workflow visualization
- **Tailwind CSS** for styling
- **Socket.io** for real-time updates

### Backend
- **FastAPI** (Python 3.11)
- **LangChain** + **LangGraph** for agent orchestration
- **OpenRouter AI** (Qwen3 model)
- **SQLAlchemy** ORM + **Alembic** migrations
- **Celery** for async tasks
- **JWT** authentication

### Infrastructure
- **PostgreSQL 16** with **pgvector** extension
- **Redis 7** for caching and Celery broker
- **Nginx** as reverse proxy
- **Docker Compose** for orchestration

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone and Setup

```bash
cd agentbuilder
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and set your API keys:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here
SERPER_API_KEY=your_serper_api_key_here

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
```

### 3. Start the Application

```bash
cd infra
docker-compose up -d
```

This will start all services:
- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Verify Services

```bash
# Check all containers are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# The frontend will be available at http://localhost:5173
```

### Database Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Project Structure

```
agentbuilder/
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # UI components (agents, workflows, tools, etc.)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── stores/            # Zustand state stores
│   │   ├── services/          # API client, WebSocket
│   │   └── types/             # TypeScript type definitions
│   ├── Dockerfile
│   └── package.json
│
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── routers/           # API endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic (agent engine, workflow engine)
│   │   ├── tasks/             # Celery async tasks
│   │   ├── middleware/        # Authentication, RBAC
│   │   └── websockets/        # Real-time log streaming
│   ├── alembic/               # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── infra/                     # Infrastructure
│   ├── docker-compose.yml
│   ├── nginx/                 # Nginx configuration
│   └── postgres/              # PostgreSQL initialization
│
├── .env.example
└── README.md
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### Key Endpoints

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent
- `POST /api/executions/agent/{id}` - Execute agent
- `GET /api/executions/{id}` - Get execution details
- `WS /ws/executions/{id}` - Real-time execution logs

## Demo Agents

The platform includes 3 demo agents (to be implemented in Phase 6):

1. **Research & Insight Agent**: Web search + RAG for comprehensive reports
2. **Data Operations Agent**: CSV processing + Python code execution + insights
3. **Multi-Agent Orchestrator**: Planner → Executor → Critic workflow

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run test
npm run test:coverage
```

## Deployment

### Production Deployment

1. Update environment variables for production:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ```

2. Configure SSL certificates in `infra/nginx/ssl/`

3. Build and deploy:
   ```bash
   docker-compose -f infra/docker-compose.yml up -d --build
   ```

### Scaling

- **Horizontal Scaling**: Add more Celery workers
  ```bash
  docker-compose up -d --scale celery_worker=3
  ```

- **Database**: Consider PostgreSQL replication for read-heavy workloads
- **Redis**: Implement Redis Cluster for high-availability
- **Load Balancing**: Add multiple backend instances behind Nginx

## Troubleshooting

### Container Issues

```bash
# Restart all services
docker-compose restart

# View logs
docker-compose logs -f [service_name]

# Rebuild containers
docker-compose up -d --build
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Connect to database
docker exec -it agentbuilder-postgres psql -U agentbuilder -d agentbuilder

# Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Port Conflicts

If ports are already in use, modify the port mappings in `infra/docker-compose.yml`:

```yaml
ports:
  - "8080:80"   # Instead of 80:80
  - "8001:8000" # Instead of 8000:8000
```

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **JWT Secret**: Generate a strong random secret for production
- **Python Executor**: Code execution is sandboxed in Docker containers
- **Rate Limiting**: Implement rate limiting for production
- **HTTPS**: Always use SSL/TLS in production

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [x] Phase 1: Core Infrastructure
- [ ] Phase 2: Agent Engine & Tool Registry
- [ ] Phase 3: Workflow Orchestration
- [ ] Phase 4: Execution & Observability
- [ ] Phase 5: Memory & RAG System
- [ ] Phase 6: Demo Agents
- [ ] Phase 7: Multi-Tenancy & Advanced Features
- [ ] Phase 8: Polish, Testing & Deployment

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using modern agentic AI patterns**
