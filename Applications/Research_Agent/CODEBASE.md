# Research Agent - Complete Codebase Documentation

## Project Overview

**Research Agent** is an intelligent AI-powered research assistant that orchestrates complex research workflows. It combines semantic search, advanced ranking, and LLM-powered analysis to help researchers discover insights from large academic paper collections.

**Tech Stack**: LangGraph + Django 5.0 + PostgreSQL + Qdrant + Redis + OLLAMA/OpenAI

---

## Directory Structure

```
Research_Agent/
├── src/
│   ├── backend/                          # Core backend logic
│   │   ├── __init__.py
│   │   ├── cli.py                       # Command-line interface
│   │   ├── config.py                    # Configuration management
│   │   ├── langgraph/                   # LangGraph workflow orchestration
│   │   │   ├── __init__.py
│   │   │   ├── graphs.py                # Main graph definitions
│   │   │   └── nodes/                   # Workflow nodes
│   │   │       ├── __init__.py
│   │   │       ├── analysis_nodes.py    # Analysis nodes (gap, design, pattern, future)
│   │   │       ├── ingestion_nodes.py   # Paper ingestion workflow
│   │   │       ├── mcp_nodes.py         # Model Context Protocol integration
│   │   │       └── retrieval_nodes.py   # Search & reranking nodes
│   │   ├── models/                      # Data models & state definitions
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py               # Pydantic schemas
│   │   │   └── states.py                # LangGraph state definitions
│   │   ├── routers/                     # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py               # Analysis endpoints
│   │   │   ├── generate.py              # Generation endpoints
│   │   │   ├── ingest.py                # Ingestion endpoints
│   │   │   └── search.py                # Search endpoints
│   │   ├── services/                    # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── answer_quality.py        # Quality metrics assessment (NEW)
│   │   │   ├── audit_trail.py           # Audit logging
│   │   │   ├── chunker.py               # Document chunking
│   │   │   ├── design_suggester.py      # Design suggestion analysis
│   │   │   ├── embeddings.py            # Embedding generation
│   │   │   ├── gap_analysis.py          # Gap analysis service
│   │   │   ├── llm_client.py            # LLM interface (OLLAMA/Cloud)
│   │   │   ├── logging.py               # Logging setup
│   │   │   ├── pdf_parse.py             # PDF parsing
│   │   │   ├── qdrant_store.py          # Vector database interface
│   │   │   ├── rerank.py                # Reranking strategies
│   │   │   ├── retriever.py             # Semantic search
│   │   │   └── sources/                 # Paper source integrations
│   │   │       └── arxiv_client.py      # ArXiv API integration
│   │   └── stores/                      # Data access layers
│   │       ├── __init__.py
│   │       ├── postgres_repo.py         # PostgreSQL operations
│   │       └── redis_cache.py           # Redis caching
│   ├── tests/                           # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Pytest configuration
│   │   ├── test_smoke.py                # Smoke tests
│   │   ├── eval/                        # Evaluation scripts
│   │   │   └── eval.py
│   │   ├── integration/                 # Integration tests
│   │   │   ├── integration_test.py
│   │   │   └── test_workflows.py
│   │   └── unit/                        # Unit tests
│   │       ├── test_api.py
│   │       ├── test_services.py
│   │       └── unite_test.py
│   └── web/                             # Django web application
│       ├── manage.py                    # Django management script
│       ├── webapp/                      # Django app
│       │   ├── api_views.py             # REST API endpoints
│       │   ├── api.py                   # API configuration
│       │   ├── asgi.py                  # ASGI server config
│       │   ├── settings.py              # Django settings
│       │   ├── urls.py                  # URL routing
│       │   ├── views.py                 # Web UI views
│       │   ├── ws_consumers.py          # WebSocket handlers
│       │   ├── wsgi.py                  # WSGI server config
│       │   ├── management/              # Django management commands
│       │   │   ├── __init__.py
│       │   │   └── commands/
│       │   │       ├── __init__.py
│       │   │       └── run_ingestion.py # Custom ingestion command
│       │   ├── static/                  # Static assets
│       │   │   ├── css/
│       │   │   │   └── style.css
│       │   │   └── js/
│       │   │       ├── api.js           # API client
│       │   │       ├── app.js           # Main application logic
│       │   │       └── websocket.js     # WebSocket client
│       │   └── templates/               # HTML templates
│       │       └── index.html           # Main web interface
│       └── tests/                       # Django app tests
│
├── docker-compose.yml                   # Docker services definition
├── Dockerfile                           # Docker image definition
├── Makefile                             # Build automation
├── pyproject.toml                       # Project dependencies
├── pytest.ini                           # Pytest configuration
├── .env.example                         # Environment template
├── README.md                            # Project documentation
├── QUALITY_METRICS_README.md            # Quality metrics guide
├── QUALITY_METRICS_IMPLEMENTATION.md    # Technical implementation
├── IMPLEMENTATION_REPORT.md             # Deployment guide
├── QUALITY_METRICS_QUICK_REFERENCE.md   # Developer quick reference
├── COMPLETION_SUMMARY.md                # Feature completion summary
├── IMPLEMENTATION_CHECKLIST.md          # Status checklist
├── DOCUMENTATION_INDEX.md               # Documentation navigation
├── verify_quality_metrics.py            # Verification script
├── data/                                # Data storage
│   └── qdrant/                          # Qdrant persistent data
├── logs/                                # Application logs
└── bin/                                 # Binary/executable scripts
```

---

## Core Components & Functionalities

### 1. Backend Services (`src/backend/services/`)

#### **answer_quality.py** ✨ [NEW]
- **Purpose**: Assess quality metrics for LLM-generated answers
- **Key Classes**:
  - `SourceReference`: Metadata for each source (chunk ID, paper ID, text snippet, page info)
  - `AnswerQuality`: Container for answer + all quality metrics
  - `AnswerQualityAssessor`: Main service with scoring methods
- **Key Methods**:
  - `assess_answer()`: Orchestrates quality assessment
  - `_extract_and_score_sources()`: Identifies top 5 relevant sources
  - `_calculate_confidence_score()`: 70% source quality + 30% answer length
  - `_evaluate_faithfulness()`: Uses OLLAMA to evaluate answer vs. sources
  - `_calculate_source_coverage()`: Measures topic coverage in sources
- **Features**:
  - Confidence scoring (0.0-1.0): How well-supported is the answer?
  - Faithfulness scoring (0.0-1.0): How accurately does it reflect sources?
  - Source tracking: Complete metadata for attribution
  - Graceful fallbacks: Returns neutral scores if assessment fails
  - No external APIs: Uses local OLLAMA for evaluation
- **Performance**: ~3-8 seconds per assessment (depends on answer length)

#### **llm_client.py**
- **Purpose**: Unified interface to LLM providers
- **Supported Providers**:
  - OLLAMA (local): qwen3:4b (chat), deepseek-r1:1.5b (reasoning)
  - OpenAI: GPT-4, GPT-3.5-turbo
  - Anthropic: Claude variants
  - Google: Generative AI models
- **Key Methods**:
  - `generate()`: Main text generation
  - `create_embeddings()`: Generate semantic vectors
  - `stream_generate()`: Streaming responses
- **Features**:
  - Fallback mechanism (try OLLAMA, then cloud provider)
  - Prompt templating and formatting
  - Rate limiting and error handling
  - Token counting and optimization

#### **embeddings.py**
- **Purpose**: Generate semantic embeddings for papers
- **Technology**: Sentence Transformers (all-MiniLM-L6-v2)
- **Key Methods**:
  - `embed_text()`: Generate embedding for text
  - `batch_embed()`: Efficient batch processing
  - `embed_paper()`: Embed entire paper chunks
- **Features**:
  - Cached embeddings (Redis)
  - Batch processing for efficiency
  - Multiple embedding models support
  - Dimension: 384 (all-MiniLM)

#### **qdrant_store.py**
- **Purpose**: Vector database interface for semantic search
- **Key Methods**:
  - `store_embeddings()`: Save vectors to Qdrant
  - `search()`: Semantic similarity search
  - `search_with_filter()`: Filtered search
  - `delete_collection()`: Cleanup operations
- **Features**:
  - Manages paper embeddings
  - Efficient vector search
  - Metadata filtering
  - Batch operations

#### **rerank.py**
- **Purpose**: Advanced reranking strategies
- **Supported Strategies**:
  - **cross_encoder**: Neural ranking (highest accuracy)
  - **semantic_diversity**: MMR algorithm (diverse results)
  - **ensemble**: Weighted combination (balanced)
- **Key Methods**:
  - `rerank()`: Apply reranking strategy
  - Separate methods for each strategy
- **Features**:
  - Configurable top-K selection
  - Multi-strategy support
  - Relevance score calibration

#### **retriever.py**
- **Purpose**: Semantic search using vector database
- **Key Methods**:
  - `retrieve()`: Search semantically similar papers
  - `retrieve_with_filter()`: Search with metadata filters
- **Features**:
  - Qdrant integration
  - Score normalization
  - Configurable result limits

#### **pdf_parse.py**
- **Purpose**: Extract text from PDF papers
- **Key Methods**:
  - `parse_pdf()`: Extract text from PDF file
  - `extract_pages()`: Get page-by-page content
  - `get_metadata()`: Extract paper metadata
- **Features**:
  - Handles malformed PDFs gracefully
  - Page limit configuration
  - Metadata extraction
  - OCR support (optional)

#### **chunker.py**
- **Purpose**: Intelligent document chunking
- **Chunking Strategies**:
  - Fixed-size with overlap
  - Semantic chunking (respect structure)
  - Section-based chunking
- **Key Methods**:
  - `chunk_text()`: Split text into chunks
  - `create_chunks_from_paper()`: Create chunks with metadata
- **Features**:
  - Configurable chunk size and overlap
  - Metadata preservation
  - Efficient batch processing

#### **gap_analysis.py**
- **Purpose**: Heuristic gap analysis (fallback)
- **Key Methods**:
  - `analyze_gaps()`: Detect research gaps
- **Features**:
  - Pattern-based gap detection
  - Used as fallback when LLM unavailable

#### **design_suggester.py**
- **Purpose**: Heuristic design suggestions (fallback)
- **Key Methods**:
  - `suggest_designs()`: Generate design suggestions
- **Features**:
  - Architecture pattern matching
  - Used as fallback when LLM unavailable

#### **audit_trail.py**
- **Purpose**: Track all system operations
- **Key Methods**:
  - `log_operation()`: Log operation
  - `get_audit_log()`: Retrieve audit history
- **Features**:
  - Complete operation tracking
  - Compliance/auditing support
  - Performance metrics

#### **logging.py**
- **Purpose**: Configure logging throughout application
- **Features**:
  - Console and file logging
  - Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Structured logging format

---

### 2. LangGraph Orchestration (`src/backend/langgraph/`)

#### **graphs.py**
- **Purpose**: Define main workflow graphs
- **Graphs**:
  - `ingestion_graph`: Paper ingestion workflow
  - `research_graph`: Research analysis workflow
  - `mcp_graph`: Model Context Protocol integration
- **Features**:
  - State management
  - Node orchestration
  - Branching logic
  - Error handling

#### **nodes/analysis_nodes.py** [UPDATED with quality metrics]
- **Purpose**: LLM-powered analysis nodes
- **Nodes**:
  - `gap_analysis_node`: Identify research gaps
  - `design_suggestion_node`: Suggest improvements
  - `pattern_detection_node`: Find trends
  - `future_directions_node`: Predict future directions
- **Each Node**:
  - Generates LLM response
  - Calls quality assessor
  - Populates quality metrics (confidence, faithfulness, sources)
  - Falls back to heuristic with neutral scores if needed
- **New Features**:
  - Quality assessment integration
  - Source tracking
  - Faithfulness evaluation
  - Automatic serialization

#### **nodes/ingestion_nodes.py**
- **Purpose**: Paper ingestion workflow
- **Nodes**:
  - `search_papers_node`: Query paper sources
  - `filter_duplicates_node`: Dedup new papers
  - `parse_pdfs_node`: Extract text from PDFs
  - `chunk_documents_node`: Create searchable chunks
  - `generate_embeddings_node`: Create semantic vectors
  - `store_in_qdrant_node`: Save to vector DB
  - `store_metadata_node`: Save to PostgreSQL
- **Features**:
  - Progress tracking
  - Error handling & retries
  - Batch processing
  - Resource cleanup

#### **nodes/retrieval_nodes.py**
- **Purpose**: Search and ranking workflow
- **Nodes**:
  - `retrieve_from_qdrant_node`: Vector similarity search
  - `rerank_results_node`: Advanced reranking
  - `check_coverage_node`: Verify result coverage
- **Features**:
  - Multiple reranking strategies
  - Result deduplication
  - Coverage checking

#### **nodes/mcp_nodes.py**
- **Purpose**: Model Context Protocol tool integration
- **Nodes**:
  - `invoke_mcp_node`: Call external tools
  - `merge_mcp_results_node`: Combine results
- **Features**:
  - Tool invocation
  - Result aggregation
  - Error handling

---

### 3. Data Models (`src/backend/models/`)

#### **states.py**
- **Purpose**: Define LangGraph state classes
- **Key States**:
  - `ResearchState`: Main research workflow state
  - `IngestionState`: Paper ingestion state
  - Analysis results with quality metrics:
    - `GapAnalysis` [UPDATED]
    - `DesignSuggestion` [UPDATED]
    - `PatternDetection` [UPDATED]
    - `FutureDirections` [UPDATED]
- **New Fields** (each analysis class):
  - `faithfulness_score: float` (0.0-1.0)
  - `sources: List[Dict[str, Any]]` (with metadata)
- **Features**:
  - Pydantic validation
  - Type safety
  - Serialization support

#### **schemas.py**
- **Purpose**: Data validation schemas
- **Key Schemas**:
  - Request/response validation
  - API schema definitions

---

### 4. Web Application (`src/web/webapp/`)

#### **api_views.py**
- **Purpose**: REST API endpoints
- **Endpoints**:
  - `POST /api/ingest/start/` - Start ingestion
  - `GET /api/ingest/status/` - Get status
  - `POST /api/search/` - Search papers
  - `POST /api/research/query/` - Analyze query
  - `GET /api/health/` - Health check
  - `GET /api/stats/` - System statistics
- **Features**:
  - Streaming responses (NDJSON)
  - Error handling
  - Rate limiting (optional)
  - Response serialization with quality metrics

#### **ws_consumers.py**
- **Purpose**: WebSocket handlers
- **Features**:
  - Real-time progress updates
  - Streaming ingestion status
  - Live analysis results

#### **views.py**
- **Purpose**: Web UI views
- **Templates**:
  - Main research interface
  - Ingestion, search, analysis, settings tabs

#### **settings.py**
- **Purpose**: Django configuration
- **Configured**:
  - Database connections
  - Installed apps
  - Middleware
  - Static files
  - Logging

#### **urls.py**
- **Purpose**: URL routing
- **Routes**:
  - API endpoints
  - Web UI views
  - WebSocket connections

#### **asgi.py & wsgi.py**
- **Purpose**: Server entry points
- **Features**:
  - ASGI for async (WebSockets)
  - WSGI for sync (REST API)

#### **management/commands/run_ingestion.py**
- **Purpose**: CLI ingestion command
- **Usage**: `python manage.py run_ingestion --days 7 --max_results 100`

---

### 5. Data Access Layer (`src/backend/stores/`)

#### **postgres_repo.py**
- **Purpose**: PostgreSQL operations
- **Key Methods**:
  - `save_paper()`: Store paper metadata
  - `save_chunks()`: Store document chunks
  - `save_analysis()`: Store analysis results
  - `query_papers()`: Retrieve papers
  - `get_audit_log()`: Audit trail queries
- **Features**:
  - ORM abstraction
  - Transaction management
  - Batch operations

#### **redis_cache.py**
- **Purpose**: Redis caching layer
- **Key Methods**:
  - `cache_embedding()`: Cache computed embeddings
  - `cache_ranking()`: Cache ranking scores
  - `get_cached()`: Retrieve cached value
  - `clear_cache()`: Invalidate cache
- **Features**:
  - Fast retrieval
  - Configurable TTL
  - Pattern-based invalidation

---

### 6. Paper Sources (`src/backend/services/sources/`)

#### **arxiv_client.py**
- **Purpose**: ArXiv paper source integration
- **Key Methods**:
  - `search_arxiv()`: Query ArXiv API
  - `get_recent_papers()`: Get recent publications
  - `fetch_pdf()`: Download paper PDF
- **Features**:
  - Configurable search parameters
  - Rate limiting
  - Error handling

---

## Feature Implementations

### Feature 1: Paper Ingestion
- **Files**: `ingestion_nodes.py`, `pdf_parse.py`, `chunker.py`, `embeddings.py`
- **Workflow**: Search → Parse → Chunk → Embed → Store
- **Status**: ✅ Complete with progress tracking

### Feature 2: Semantic Search
- **Files**: `retriever.py`, `qdrant_store.py`, `embeddings.py`
- **Workflow**: Query → Embed → Vector search → Retrieve
- **Status**: ✅ Complete with result pagination

### Feature 3: Advanced Reranking
- **Files**: `rerank.py`, `retrieval_nodes.py`
- **Strategies**: Cross-encoder, Semantic Diversity (MMR), Ensemble
- **Status**: ✅ Complete with configurable strategies

### Feature 4: LLM-Powered Analysis
- **Files**: `analysis_nodes.py`, `llm_client.py`, design supporting services
- **Analysis Types**:
  - Gap Analysis: Identify research gaps
  - Design Suggestions: Methodological improvements
  - Pattern Detection: Emerging trends
  - Future Directions: Research trajectories
- **Status**: ✅ Complete with OLLAMA local support

### Feature 5: Quality Metrics ✨ [NEW]
- **Files**: `answer_quality.py`, `analysis_nodes.py`, `states.py`
- **Metrics**:
  - Confidence Scoring: How well-supported is the answer?
  - Faithfulness Scoring: How accurately does it reflect sources?
  - Source Tracking: Complete metadata for attribution
- **Status**: ✅ Complete with automatic assessment

### Feature 6: Web Interface
- **Files**: `views.py`, `templates/index.html`, `static/js/app.js`
- **Sections**: Ingest, Search, Analyze, Settings
- **Status**: ✅ Complete with real-time updates

### Feature 7: REST API
- **Files**: `api_views.py`, `api.py`
- **Endpoints**: Ingestion, Search, Analysis, Health, Stats
- **Features**: Streaming, error handling, quality metrics in responses
- **Status**: ✅ Complete with full documentation

### Feature 8: WebSocket Streaming
- **Files**: `ws_consumers.py`, `static/js/websocket.js`
- **Features**: Real-time progress, live result updates
- **Status**: ✅ Complete with fallback to polling

### Feature 9: Data Persistence
- **Files**: `postgres_repo.py`, `redis_cache.py`, `qdrant_store.py`
- **Storage**: PostgreSQL (metadata), Qdrant (vectors), Redis (cache)
- **Status**: ✅ Complete with backup support

### Feature 10: Audit Trail
- **Files**: `audit_trail.py`, `postgres_repo.py`
- **Tracking**: All operations logged with timestamps
- **Status**: ✅ Complete for compliance

### Feature 11: OLLAMA Integration ✨ [NEW]
- **Files**: `llm_client.py`, `config.py`, `.env`, `docker-compose.yml`
- **Models**: qwen3:4b (chat), deepseek-r1:1.5b (reasoning)
- **Benefits**: No API keys, local execution, cost-free
- **Status**: ✅ Complete with fallback to cloud providers

---

## Configuration Files

### `.env` - Environment Variables
- LLM provider selection (OLLAMA/OpenAI/Anthropic/Google)
- Database credentials (PostgreSQL, Redis, Qdrant)
- Model selections (embedding, reranking)
- Feature flags (caching, MCP tools)
- Logging configuration

### `pyproject.toml` - Dependencies
- Core: langchain, langgraph, django, pydantic
- Data: sqlalchemy, psycopg2, redis, qdrant-client
- ML: torch, sentence-transformers, scikit-learn
- API: fastapi, httpx, requests
- Utils: python-dotenv, pyyaml, click

### `docker-compose.yml` - Docker Services
- PostgreSQL: Database
- Qdrant: Vector database
- Redis: Cache layer
- OLLAMA: Local LLM (NEW)
- Research Agent: Main application

### `Dockerfile` - Docker Image
- Python 3.12 base image
- Dependency installation
- Entrypoint configuration

---

## Testing Structure (`src/tests/`)

### Unit Tests (`unit/`)
- `test_services.py`: Service layer tests
- `test_api.py`: API endpoint tests
- Service-specific tests for embeddings, reranking, etc.

### Integration Tests (`integration/`)
- `test_workflows.py`: Full workflow tests
- `integration_test.py`: End-to-end tests

### Evaluation (`eval/`)
- `eval.py`: Model evaluation scripts
- Performance and quality benchmarking

---

## Documentation Files

### Main Documentation
- **README.md**: Project overview, installation, usage (UPDATED)
- **CODEBASE.md**: This file - complete codebase documentation

### Quality Metrics Documentation ✨ [NEW]
- **QUALITY_METRICS_README.md**: Feature overview
- **QUALITY_METRICS_IMPLEMENTATION.md**: Technical deep dive
- **QUALITY_METRICS_QUICK_REFERENCE.md**: Developer guide
- **IMPLEMENTATION_REPORT.md**: Deployment guide
- **COMPLETION_SUMMARY.md**: What was implemented
- **IMPLEMENTATION_CHECKLIST.md**: Status tracking
- **DOCUMENTATION_INDEX.md**: Navigation guide

### Verification
- **verify_quality_metrics.py**: Installation verification script

---

## Workflow Diagrams

### Paper Ingestion Workflow
```
Start Ingestion
    ↓
Search Papers (ArXiv)
    ↓
Filter Duplicates
    ↓
Download & Parse PDFs
    ↓
Chunk Documents
    ↓
Generate Embeddings
    ↓
Store in Qdrant (vectors)
    ↓
Store in PostgreSQL (metadata)
    ↓
Complete
```

### Research Analysis Workflow
```
User Query
    ↓
Retrieve Similar Papers (Qdrant)
    ↓
Rerank Results
    ↓
Gap Analysis Node → LLM/Heuristic → Quality Assessment
    ↓
Design Suggestion Node → LLM/Heuristic → Quality Assessment
    ↓
Pattern Detection Node → LLM/Heuristic → Quality Assessment
    ↓
Future Directions Node → LLM/Heuristic → Quality Assessment
    ↓
Aggregate Results
    ↓
API Response (with quality metrics)
```

### Quality Metrics Assessment
```
LLM-Generated Answer
    ↓
Extract & Score Sources
    ↓
Calculate Confidence
    ↓
Evaluate Faithfulness (using OLLAMA)
    ↓
Calculate Coverage
    ↓
Return AnswerQuality Object
    ├── confidence_score (0.0-1.0)
    ├── faithfulness_score (0.0-1.0)
    └── sources (List of SourceReferences)
```

---

## Key Design Patterns

### 1. Service Layer Pattern
- Business logic isolated in services
- Clean separation from models/views
- Reusable across API/CLI/scheduled tasks

### 2. Repository Pattern
- Data access abstraction
- `postgres_repo.py`, `redis_cache.py`, `qdrant_store.py`
- Easy to swap implementations

### 3. Singleton Pattern
- `get_llm_client()`, `get_answer_quality_assessor()`
- Efficient resource usage
- Consistent state across application

### 4. State Machine Pattern
- LangGraph-based orchestration
- Deterministic workflows
- Clear state transitions

### 5. Fallback/Graceful Degradation
- OLLAMA → Cloud providers
- LLM analysis → Heuristic fallback
- Quality assessment → Neutral scores
- Never breaks pipeline

---

## Performance Characteristics

### Ingestion
- **Per Paper**: 1-5 seconds (includes PDF download)
- **100 Papers**: ~2-5 minutes (with parallelization)
- **Bottleneck**: PDF parsing, embedding generation

### Search
- **Latency**: 50-500ms (depends on result size)
- **Bottleneck**: Reranking (use fast strategy for speed)
- **Optimization**: Redis caching reduces to <50ms

### Analysis
- **Latency**: 3-30 seconds (depends on LLM model)
- **Gap Analysis**: 5-15 seconds
- **Pattern Detection**: 3-8 seconds
- **Quality Assessment**: +3-8 seconds (OLLAMA evaluation)
- **Bottleneck**: LLM generation and faithfulness evaluation

### Storage
- **Vector DB**: ~100MB per 1000 papers (embedding size 384)
- **Metadata DB**: ~10MB per 1000 papers
- **Cache**: Configurable, typically 100-500MB

---

## Security Considerations

### Data Security
- ✅ Password hashing for Django users
- ✅ API authentication (optional)
- ✅ HTTPS support (production)
- ✅ Database encryption (optional)

### API Security
- ✅ CORS configuration
- ✅ CSRF protection (Django)
- ✅ Rate limiting (optional)
- ✅ Input validation (Pydantic)

### LLM Security
- ✅ OLLAMA: Local, no API exposure
- ✅ Cloud APIs: Secure key management (.env)
- ✅ No sensitive data in prompts

### Database Security
- ✅ PostgreSQL: User authentication required
- ✅ Redis: Optional password protection
- ✅ Qdrant: Optional API key

---

## Scalability Considerations

### Horizontal Scaling
- Services can be containerized and load-balanced
- PostgreSQL can be replicated
- Redis can be clustered
- Qdrant can be scaled

### Vertical Scaling
- Increase OLLAMA GPU allocation
- Increase database memory
- Optimize batch sizes

### Optimization Tips
- Enable Redis caching: `ENABLE_CACHING=True`
- Use ensemble reranking (balanced speed/accuracy)
- Batch ingestion operations
- Use faster LLM for non-critical analysis
- Implement result pagination

---

## Development Workflow

### Adding New Analysis Node
1. Create node function in `analysis_nodes.py`
2. Add to `graphs.py` workflow
3. Integrate quality assessment
4. Update state model in `states.py`
5. Add API endpoint in `api_views.py`
6. Write tests in `tests/unit/`

### Adding New Paper Source
1. Create client in `services/sources/`
2. Implement search and fetch methods
3. Handle errors gracefully
4. Add to ingestion workflow
5. Update documentation

### Customizing Reranking
1. Add strategy to `rerank.py`
2. Update strategy selection in `retrieval_nodes.py`
3. Configure in `.env`
4. Test performance

---

## Troubleshooting Guide

### Common Issues

**OLLAMA not connecting**
- Check: `OLLAMA_HOST` in .env
- Verify: `ollama serve` is running
- Test: `curl http://localhost:11434/api/tags`

**PostgreSQL connection failed**
- Check: `POSTGRES_*` credentials in .env
- Verify: Database exists
- Test: `psql -U postgres -c "SELECT 1"`

**Qdrant connection failed**
- Check: `QDRANT_*` settings in .env
- Verify: Qdrant container running
- Test: `curl http://localhost:6333/health`

**Slow ingestion**
- Increase batch size in config
- Enable Redis caching
- Use faster PDF parser settings
- Check system resources

**Low quality metrics**
- Verify OLLAMA models downloaded
- Check ranked_results population
- Adjust `RELEVANCE_THRESHOLD`
- Review answer length

---

## Future Enhancements

1. **RAGAS Integration**: Full RAGAS metrics instead of custom scoring
2. **Fine-tuned Models**: Domain-specific models for better analysis
3. **User Feedback Loop**: Improve metrics based on user ratings
4. **Advanced Caching**: Smarter cache invalidation
5. **Distributed Processing**: Task queue for large-scale processing
6. **Advanced UI**: Charts, visualizations of quality metrics
7. **Multi-language Support**: Support for non-English papers
8. **Custom Prompt Management**: UI for managing analysis prompts

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2 | Jan 2026 | Added quality metrics, OLLAMA integration |
| 1.1 | Dec 2025 | Added MCP support, WebSocket streaming |
| 1.0 | Oct 2025 | Initial release with core features |

---

## Contact & Support

For questions about the codebase:
- 📄 See [README.md](./README.md) for usage
- 📚 See [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) for navigation
- 💻 Check code comments and docstrings
- 🧪 Run tests to verify functionality

---

**Last Updated**: January 4, 2026  
**Status**: Production Ready  
**Maintained By**: Research Agent Team

