# Research Agent

An intelligent AI-powered research assistant built with **LangGraph**, **Django**, and modern ML/AI technologies. Orchestrates research workflows: paper ingestion → semantic search → reranking → LLM-powered analysis.

**Status:** ✅ Production Ready | 11 Features | OLLAMA + Quality Metrics

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Setup Options](#setup-options)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## Features

- 🤖 **LangGraph Orchestration** - Stateful, deterministic workflow management
- 📚 **Paper Ingestion** - Multi-source support (ArXiv, MCP-ready), PDF parsing, deduplication
- 🔍 **Intelligent Retrieval** - Vector search + ensemble reranking (cross-encoder + MMR)
- 🧠 **LLM Analysis** - OLLAMA local models (qwen3:4b, deepseek-r1:1.5b) + cloud fallbacks
- ✨ **Quality Metrics** - Confidence & faithfulness scoring, source tracking
- 💾 **Data Persistence** - Qdrant (vectors), PostgreSQL (metadata), Redis (cache)
- 📊 **Real-time Updates** - WebSocket streaming for ingestion progress

---

## Quick Start

**Full Docker (Recommended):**
```bash
git clone <repo-url> && cd Research_Agent
cp .env.example .env
docker-compose up --build

# In another terminal, pull OLLAMA models (one-time)
docker-compose exec ollama ollama pull qwen3:4b
docker-compose exec ollama ollama pull deepseek-r1:1.5b

# Access at http://localhost:8000
```

**Local OLLAMA + Python:**
```bash
git clone <repo-url> && cd Research_Agent
python -m venv venv && source venv/bin/activate
pip install poetry && poetry install

# Terminal 1: Start OLLAMA
ollama serve

# Terminal 2: Start backend services
docker-compose up -d postgres qdrant redis

# Terminal 3: Run Django
cd src/web && python manage.py migrate && python manage.py runserver
```

**Minimal Setup (OLLAMA + SQLite):**
```bash
git clone <repo-url> && cd Research_Agent
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Configure for local OLLAMA
cat > .env << EOF
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_CHAT=qwen3:4b
EOF

# Terminal 1: OLLAMA
ollama serve

# Terminal 2: Django with SQLite
cd src/web && python manage.py migrate && python manage.py runserver
```

---

## Configuration

**Environment Variables (.env):**

```env
# LLM Configuration
LLM_PROVIDER=ollama              # or: openai, anthropic, google
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_CHAT=qwen3:4b
OLLAMA_MODEL_REASONING=deepseek-r1:1.5b

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=research_agent

# Vector/Cache
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_HOST=localhost
REDIS_PORT=6379

# Quality Metrics
QUALITY_METRICS_ENABLED=true
RELEVANCE_THRESHOLD=0.3
MAX_SOURCES_PER_ANSWER=5

# Reranking
RERANK_STRATEGY=ensemble        # or: cross_encoder, semantic_diversity
RERANK_MODEL=mixedbread-ai/mxbai-rerank-xsmall-v1

# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

**OLLAMA Models:**

| Model | Purpose | Speed |
|-------|---------|-------|
| qwen3:4b | Chat & analysis | 2-3 sec |
| deepseek-r1:1.5b | Reasoning & faithfulness | 5-10 sec |
| nomic-embed-text | Embeddings | Fast |

**LLM Provider Options:**

| Provider | Cost | Setup | Speed |
|----------|------|-------|-------|
| OLLAMA (Local) | Free | Easiest | Medium |
| OpenAI | $$ | Key needed | Fast |
| Anthropic | $$$ | Key needed | Medium |
| Google | $ | Key needed | Very Fast |

---

## Usage

**Web Interface:**
1. Open http://localhost:8000
2. **Ingest**: Add papers from ArXiv (set days back & max results)
3. **Search**: Query papers by keywords
4. **Analyze**: Select analysis type (Gap Analysis, Design Suggestions, Pattern Detection, Comprehensive)
5. **View Quality Metrics**: See confidence, faithfulness scores & sources

**REST API Examples:**

```bash
# Ingest papers
curl -X POST http://localhost:8000/api/ingest/start/ \
  -H "Content-Type: application/json" \
  -d '{"days": 7, "max_results": 100}'

# Search papers
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention", "limit": 20}'

# Analyze (with quality metrics)
curl -X POST http://localhost:8000/api/research/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "transformers", "analysis_type": "comprehensive"}'

# Health check
curl http://localhost:8000/api/health/

# System stats
curl http://localhost:8000/api/stats/
```

**WebSocket (Real-time):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ingest/');
ws.onopen = () => ws.send(JSON.stringify({
  type: 'start_ingestion', days: 7, max_results: 100
}));
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

**Django CLI:**
```bash
cd src/web

# Ingest papers
python manage.py run_ingestion --days 7 --max_results 100

# Database operations
python manage.py shell
python manage.py migrate

# View logs
tail -f ../../logs/research_agent.log
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/ingest/start/` | Start paper ingestion |
| GET | `/api/ingest/status/` | Get ingestion progress |
| POST | `/api/search/` | Search papers |
| POST | `/api/research/query/` | Execute analysis (with quality metrics) |
| GET | `/api/health/` | System health check |
| GET | `/api/stats/` | System statistics |

**Response Example (Analysis with Quality Metrics):**
```json
{
  "gap_analysis": {
    "identified_gaps": ["Limited work on efficiency", "Few studies on interpretability"],
    "confidence_score": 0.85,
    "faithfulness_score": 0.88,
    "sources": [
      {
        "chunk_id": "chunk_456",
        "paper_id": "arxiv_2024_001",
        "text_snippet": "We analyze attention mechanisms...",
        "confidence": 0.95
      }
    ]
  }
}
```

---

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src/backend --cov-report=html

# Specific test file
pytest src/tests/unit/test_llm_client.py

# Run integration tests only
pytest src/tests/integration/

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Code Quality Tools

```bash
# Format code with Black
black src/

# Type checking
mypy src/backend/

# Linting
flake8 src/
pylint src/

# Security check
bandit -r src/

# All checks
make quality
```

### Running Local Development Server

```bash
# Terminal 1: Django development server
cd src/web
python manage.py runserver

# Terminal 2: Monitor logs (optional)
tail -f ../../logs/research_agent.log

# Terminal 3: Run tests while developing
pytest --watch
```

### Building Docker Image

```bash
# Build image
docker build -t research-agent:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  research-agent:latest

# With volume mounts for development
docker run -p 8000:8000 \
  -v $(pwd)/src:/app/src \
  --env-file .env \
  research-agent:latest
```

---

## Troubleshooting

**Database Connection Error:**
```bash
# Check PostgreSQL running
psql -U postgres -c "SELECT 1"

# Create database if missing
createdb research_agent

# Verify connection string in .env
# POSTGRES_URL=postgresql://user:password@localhost:5432/research_agent
```

**Qdrant Connection Failed:**
```bash
# Check if running
docker ps | grep qdrant

# Test connection
curl http://localhost:6333/health

# Restart if needed
docker restart qdrant
```

**LLM API Errors:**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test cloud provider
# For OpenAI:
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Switch to OLLAMA temporarily (no API key needed)
```

**Port Already in Use:**
```bash
# Find process
lsof -i :8000  # Unix
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
python manage.py runserver 8001
```

**Slow Performance:**
```bash
# Check resource usage
docker stats

# Verify caching enabled
grep ENABLE_CACHING .env

# Optimize Qdrant
curl -X PUT http://localhost:6333/collections/papers/optimize
```

**More Help:**
- See [CODEBASE.md](CODEBASE.md) for architecture & design patterns
- See [DOCS_INDEX.md](DOCS_INDEX.md) for navigation guide
