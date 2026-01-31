# Testing & Demo Guide

## Quick Start

### 1. Initialize Database
```bash
cd backend
python scripts/init_db.py
```

This creates:
- Database tables
- 4 prebuilt tools (web_search, calculator, file_reader, current_time)
- Default organization
- Admin user (admin@agentbuilder.com / admin123)

### 2. Start Backend
```bash
cd infra
docker-compose up -d
```

### 3. Run Tests

#### Option A: API Demo (Safe)
```bash
cd backend
python scripts/demo_api.py
```

Shows:
- Health check
- Authentication
- Tool listing
- Agent/workflow configuration examples

#### Option B: End-to-End Test (Full Integration)
```bash
cd backend
python scripts/test_e2e.py
```

Tests:
- Database connection
- Prebuilt tools
- Project creation
- Agent creation
- **Live agent execution with LangChain**

**Note**: Requires valid API keys in `.env`

#### Option C: WebSocket Demo
```bash
# First, create execution via API or test_e2e.py
# Then stream logs:
cd backend
python scripts/demo_websocket.py <execution_id>
```

---

## Manual API Testing

### Using cURL

#### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@agentbuilder.com", "password": "admin123"}'
```

Save the `access_token` from response.

#### 2. List Tools
```bash
curl http://localhost:8000/api/tools/ \
  -H "Authorization: Bearer <your_token>"
```

#### 3. View API Docs
```bash
open http://localhost:8000/docs
```

---

## Using Swagger UI

1. Navigate to: `http://localhost:8000/docs`
2. Click "Authorize" button
3. Login to get token
4. Paste token in format: `Bearer <token>`
5. Try endpoints interactively

---

## WebSocket Testing (Browser)

```javascript
// In browser console:
const ws = new WebSocket('ws://localhost:8000/ws/executions/<execution_id>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

---

## Troubleshooting

### "Connection refused"
- Check if backend is running: `docker-compose ps`
- Check health: `curl http://localhost:8000/health`

### "No tools found"
- Run database init: `python scripts/init_db.py`

### "Agent execution fails"
- Verify API keys in `.env`:
  - `OPENROUTER_API_KEY`
  - `SERPER_API_KEY`
- Check logs: `docker-compose logs backend`

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`

---

## Test Checklist

- [ ] Database initialization works
- [ ] Health check returns 200
- [ ] Login returns JWT token
- [ ] Tools API returns 4 prebuilt tools
- [ ] Agent creation works (with valid project_id)
- [ ] Agent execution works (requires API keys)
- [ ] WebSocket connects and streams logs
- [ ] Swagger UI loads and shows all endpoints

---

## Component Testing

### Test LangChain Integration
```python
from app.services.agent_engine import AgentEngine
# See test_e2e.py for complete example
```

### Test Tool Registry
```python
from app.services.tool_registry import ToolRegistry
registry = ToolRegistry()
# Load tools...
```

### Test Workflow Engine
```python
from app.services.workflow_engine import WorkflowEngine
# See workflow execution in test_e2e.py
```

---

## Performance Testing

### Load Test (100 concurrent requests)
```bash
# Install: pip install locust
locust -f scripts/load_test.py --host=http://localhost:8000
```

### WebSocket Stress Test
```bash
# Connect 100 WebSocket clients
for i in {1..100}; do
  python scripts/demo_websocket.py <execution_id> &
done
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Backend
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d
          python backend/scripts/test_e2e.py
```

---

## Next Steps

1. ✅ Backend fully tested
2. **Build Frontend** → React components
3. **Integration Testing** → E2E with UI
4. **Production Deployment** → AWS/GCP
