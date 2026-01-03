# Research Agent

An intelligent AI-powered research assistant built with **LangGraph**, **Django**, and modern ML/AI technologies. The system orchestrates complex research workflows including paper ingestion, semantic search, advanced reranking, and LLM-powered analysis to help researchers discover insights from large academic paper collections.

**Status:** ✅ Production Ready | 8 Core Features Implemented | 135+ Tests

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Installation Guide](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Features

### 🤖 Agentic Workflow Orchestration
- **LangGraph-based workflows**: Deterministic, stateful orchestration of research tasks
- **Multi-stage pipelines**: Ingestion → Retrieval → Reranking → Analysis
- **Real-time progress tracking**: WebSocket-based streaming updates
- **Graceful degradation**: Fallback mechanisms for resilience

### 📚 Paper Ingestion
- **Multi-source support**: ArXiv, Google Scholar, IEEE Xplore (MCP-ready)
- **Intelligent chunking**: PDF parsing with intelligent document segmentation
- **Deduplication**: Automatic detection of duplicate papers
- **Progress tracking**: Real-time ingestion status via WebSocket/REST

### 🔍 Intelligent Retrieval & Ranking
- **Vector search**: Semantic similarity using Qdrant vector database
- **Multi-strategy reranking**:
  - Cross-encoder neural ranking (mixedbread model)
  - Semantic diversity optimization (MMR algorithm)
  - Ensemble ranking (weighted combination)
- **Configurable strategies**: Switch ranking algorithms per use case

### 🧠 LLM-Powered Analysis
- **Multi-provider support**: OpenAI GPT-4, Anthropic Claude, Google Generative AI
- **Specialized analysis types**:
  - Gap analysis: Identify research gaps and underexplored areas
  - Design suggestions: Propose methodological improvements
  - Pattern detection: Extract emerging trends and patterns
  - Future directions: Project potential research trajectories
- **Confidence scoring**: Track analysis reliability with fallback mechanisms

### 💾 Data Persistence & Auditing
- **Vector storage**: Qdrant for embeddings and semantic search
- **Metadata store**: PostgreSQL for papers, chunks, analyses
- **Caching layer**: Redis for embeddings and ranking scores
- **Audit trail**: Complete tracking of all operations for compliance

---

## Quick Start

### Minimal Setup (5 minutes)

```bash
# 1. Clone and setup
git clone <repo-url> && cd Research_Agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install poetry && poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env: Add LLM_PROVIDER, API_KEY, POSTGRES_URL, QDRANT_URL

# 4. Start services (Docker)
docker-compose up -d

# 5. Initialize database
cd src/web && python manage.py migrate

# 6. Run server
python manage.py runserver

# 7. Visit http://localhost:8000 and start using the app!
```

### With Docker (Recommended)

```bash
# Single command to start everything
docker-compose up --build

# Application will be available at http://localhost:8000
```

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│           Web Interface & API Layer             │
│  (Django REST API, WebSocket, Web UI)           │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      LangGraph Orchestration Layer              │
│  (Ingestion Graph, Research Graph)              │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│        Service Layer & Business Logic           │
│  (LLM, Reranking, Embeddings, PDF Parser)       │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│            Data Storage Layer                   │
│  (Qdrant | PostgreSQL | Redis)                  │
└─────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Web Server** | REST API + WebSocket + Web UI | Django 5.0 + Channels |
| **Orchestration** | Workflow management & state | LangGraph |
| **Vector DB** | Semantic search & embeddings | Qdrant |
| **Relational DB** | Papers, chunks, metadata | PostgreSQL |
| **Cache** | Fast retrieval of frequent queries | Redis |
| **LLM** | Text generation & analysis | OpenAI/Anthropic/Google |
| **Embeddings** | Semantic vectors | Sentence Transformers |
| **Reranking** | Advanced ranking strategies | Cross-encoders, MMR |

---

## Installation & Setup

### Prerequisites

- **Python 3.12+** - Programming language
- **PostgreSQL 14+** - Relational database
- **Docker & Docker Compose** - Container runtime (optional but recommended)
- **API Keys**: OpenAI, Anthropic, or Google (for LLM)

### Step-by-Step Installation

#### 1. Clone Repository

```bash
git clone <repository-url>
cd Research_Agent
```

#### 2. Create Python Environment

```bash
# Option A: Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Option B: Using conda
conda create -n research_agent python=3.12
conda activate research_agent
```

#### 3. Install Dependencies

```bash
# Using Poetry (recommended)
pip install poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your settings (see Configuration section below)
# Required:
# - LLM_PROVIDER (openai, anthropic, google)
# - API key for chosen provider
# - POSTGRES connection string
# - QDRANT connection details
```

#### 5. Start External Services

```bash
# Option A: Docker Compose (all-in-one)
docker-compose up -d

# Option B: Manual start

# Start Qdrant (vector database)
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

# Start Redis (optional caching)
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# Setup PostgreSQL
# Ensure it's running and create database:
createdb research_agent
```

#### 6. Initialize Database

```bash
cd src/web

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser

# Create logs directory
mkdir -p ../../logs
```

#### 7. Start Application

```bash
# Development server
cd src/web
python manage.py runserver

# For production, use Gunicorn
pip install gunicorn
gunicorn webapp.wsgi --bind 0.0.0.0:8000
```

#### 8. Access Application

Open browser and navigate to:
```
http://localhost:8000
```

---

## Configuration

### Environment Variables (.env)

```env
# ===== LLM PROVIDER =====
LLM_PROVIDER=openai              # Options: openai, anthropic, google
OPENAI_API_KEY=sk-...            # If using OpenAI
ANTHROPIC_API_KEY=sk-ant-...     # If using Anthropic
GOOGLE_API_KEY=...               # If using Google

# ===== DATABASE =====
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=research_agent

REDIS_HOST=localhost
REDIS_PORT=6379

# ===== VECTOR DATABASE =====
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=                  # Leave empty for local

# ===== RERANKING =====
RERANK_STRATEGY=ensemble         # Options: cross_encoder, semantic_diversity, ensemble
RERANK_TOP_K=20                  # Number of results to rerank
RERANK_MODEL=mixedbread-ai/mxbai-rerank-xsmall-v1

# ===== EMBEDDINGS =====
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384

# ===== PAPER SOURCES =====
ARXIV_TIMEOUT=30                 # Timeout for ArXiv API (seconds)
PDF_MAX_PAGES=100               # Max pages to process per PDF

# ===== LOGGING =====
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=../../logs/research_agent.log

# ===== DJANGO =====
SECRET_KEY=your-secret-key-here
DEBUG=False                       # Set to False for production
ALLOWED_HOSTS=localhost,127.0.0.1

# ===== FEATURES =====
ENABLE_MCP_TOOLS=True            # Enable Model Context Protocol tools
ENABLE_CACHING=True              # Enable Redis caching
```

### Reranking Strategies

| Strategy | Best For | Speed | Accuracy |
|----------|----------|-------|----------|
| **cross_encoder** | Accuracy-first scenarios | Slow | Highest |
| **semantic_diversity** | Diverse result sets | Fast | Medium |
| **ensemble** | Balanced approach (default) | Medium | High |

### LLM Provider Comparison

| Provider | Cost | Speed | Quality | Best For |
|----------|------|-------|---------|----------|
| **OpenAI** | Medium | Fast | Excellent | General purpose |
| **Anthropic** | High | Medium | Excellent | Long contexts |
| **Google** | Low | Very Fast | Good | Budget-conscious |

---

## Usage

### Via Web Interface

1. Open http://localhost:8000
2. **Ingest Tab**: Configure paper sources and start ingestion
3. **Search Tab**: Query your paper database semantically
4. **Analyze Tab**: Get LLM-powered research insights
5. **Settings Tab**: Configure system parameters

### Via REST API

```bash
# Start paper ingestion
curl -X POST http://localhost:8000/api/ingest/start/ \
  -H "Content-Type: application/json" \
  -d '{
    "days": 7,
    "max_results": 100
  }'

# Get ingestion status
curl http://localhost:8000/api/ingest/status/

# Execute research query
curl -X POST http://localhost:8000/api/research/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer attention mechanisms",
    "analysis_type": "comprehensive",
    "use_mcp": false
  }'

# Health check
curl http://localhost:8000/api/health/

# Search papers
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "limit": 20
  }'
```

### Via WebSocket (Real-time Streaming)

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/ingest/');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'start_ingestion',
    days: 7,
    max_results: 100
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Status: ${message.status}`);
  console.log(`Progress: ${message.progress_percent}%`);
  console.log(`Documents: ${message.docs_ingested}/${message.docs_found}`);
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Via Django CLI

```bash
cd src/web

# Start ingestion from command line
python manage.py run_ingestion --days 7 --max_results 100

# Monitor real-time progress in terminal
# Output: [searching] 25% | [parsing] 50% | [storing] 75% | [complete] 100%

# Create sample data
python manage.py create_sample_data

# Export papers to CSV
python manage.py export_papers --format csv --output papers.csv
```

---

## API Documentation

### Core Endpoints

#### Ingestion API

**`POST /api/ingest/start/`** - Start paper ingestion workflow

Request:
```json
{
  "days": 7,
  "max_results": 100
}
```

Response (Streaming NDJSON):
```jsonl
{"type": "progress", "status": "searching", "progress_percent": 25}
{"type": "progress", "status": "parsing", "progress_percent": 50, "docs_ingested": 12}
{"type": "complete", "docs_ingested": 44, "docs_failed": 1, "duration_seconds": 120}
```

**`GET /api/ingest/status/`** - Get current ingestion status

Response:
```json
{
  "status": "in_progress",
  "progress_percent": 75,
  "docs_found": 45,
  "docs_ingested": 33,
  "docs_failed": 1,
  "current_stage": "storing"
}
```

#### Search API

**`POST /api/search/`** - Search papers by query

Request:
```json
{
  "query": "transformer neural networks",
  "limit": 20,
  "rerank_strategy": "ensemble"
}
```

Response:
```json
{
  "query": "transformer neural networks",
  "results": [
    {
      "id": "arxiv-2312.12345",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani, A.", "Shazeer, N."],
      "year": 2017,
      "relevance_score": 0.92,
      "summary": "...",
      "pdf_url": "https://arxiv.org/pdf/..."
    }
  ],
  "total": 1250
}
```

#### Analysis API

**`POST /api/research/query/`** - Execute comprehensive research analysis

Request:
```json
{
  "query": "transformer attention mechanisms",
  "analysis_type": "comprehensive",
  "limit": 30,
  "use_mcp": false
}
```

Response:
```json
{
  "query": "transformer attention mechanisms",
  "final_response": {
    "answer": "Transformers use multi-head attention...",
    "gaps": [
      "Limited work on attention efficiency in long sequences",
      "Few studies on attention bias in downstream tasks"
    ],
    "design_suggestions": [
      "Implement sparse attention patterns",
      "Explore dynamic head pruning"
    ],
    "patterns": [
      "Attention mechanisms improve with model scale",
      "Multi-head attention captures diverse relationships"
    ],
    "future_directions": [
      "Energy-efficient attention mechanisms",
      "Interpretable attention weights"
    ]
  },
  "sources": [
    {"title": "...", "relevance": 0.89}
  ]
}
```

#### System API

**`GET /api/health/`** - System health check

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-03T10:30:00Z",
  "components": {
    "qdrant": "ok",
    "postgres": "ok",
    "redis": "ok",
    "llm": "ok"
  }
}
```

**`GET /api/stats/`** - System statistics

Response:
```json
{
  "total_papers": 1543,
  "total_chunks": 23456,
  "vector_db_size": "234.5 MB",
  "cache_hit_rate": 0.78,
  "avg_query_time": 1.2
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

### Database Connection Issues

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# 1. Verify PostgreSQL is running
psql -U postgres -c "SELECT 1"

# 2. Check credentials in .env
grep POSTGRES .env

# 3. Ensure database exists
createdb research_agent

# 4. Check connection string format
# POSTGRES_URL=postgresql://user:password@localhost:5432/research_agent
```

### Qdrant Connection Issues

**Problem:** `ConnectionError: Cannot connect to Qdrant at localhost:6333`

**Solution:**
```bash
# 1. Verify Qdrant is running
docker ps | grep qdrant

# 2. Check if port is accessible
curl http://localhost:6333/health

# 3. View Qdrant logs
docker logs qdrant

# 4. Restart Qdrant
docker restart qdrant
```

### LLM API Errors

**Problem:** `AuthenticationError: Invalid API key` or `RateLimitError`

**Solution:**
```bash
# 1. Verify API key in .env
echo $OPENAI_API_KEY

# 2. Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. Check rate limits at provider dashboard
# 4. Use different provider temporarily
```

### Model Download Issues

**Problem:** `RuntimeError: Failed to download embedding model`

**Solution:**
```bash
# 1. Check internet connectivity
ping huggingface.co

# 2. Pre-download model
python -c "from sentence_transformers import SentenceTransformer; \
  SentenceTransformer('all-MiniLM-L6-v2')"

# 3. Use local model path
# EMBEDDING_MODEL=/path/to/local/model

# 4. Set Hugging Face cache directory
export HF_HOME=/path/to/cache
```

### Performance Issues

**Problem:** Slow search or ingestion

**Solutions:**
```bash
# 1. Check CPU/Memory usage
docker stats

# 2. Verify Redis caching is enabled
grep ENABLE_CACHING .env

# 3. Optimize Qdrant performance
curl -X PUT http://localhost:6333/collections/papers/optimize

# 4. Check database indexes
psql research_agent -c "\di"

# 5. Increase batch size in config
# INGEST_BATCH_SIZE=50
```

### Port Already in Use

**Problem:** `Address already in use` error

**Solution:**
```bash
# Find process using port
lsof -i :8000  # On Unix
netstat -ano | findstr :8000  # On Windows

# Kill process
kill -9 <PID>  # Unix
taskkill /PID <PID> /F  # Windows

# Use different port
python manage.py runserver 8001
```

---

## Quick Reference Commands

```bash
# Start development
docker-compose up -d && cd src/web && python manage.py runserver

# Run tests
pytest --cov=src/backend

# Format code
black src/ && isort src/

# Create database backup
pg_dump research_agent > backup_$(date +%Y%m%d).sql

# View logs
tail -f logs/research_agent.log

# Database shell
psql research_agent

# Django shell
python src/web/manage.py shell

# Stop all services
docker-compose down
```

---

## Support & Contributing

For issues, questions, or contributions:
- 🐛 **Bug Reports**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions
- 📧 **Email**: support@example.com

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

**Built with ❤️ using LangGraph, Django, and modern AI technologies**
