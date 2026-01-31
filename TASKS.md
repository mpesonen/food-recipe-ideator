# Tasks

## Phase 1: Project Setup

- [x] Create project structure (backend/, frontend/ directories)
- [x] Initialize backend with uv (`uv init`, pyproject.toml)
- [x] Add pytest + pytest-asyncio as dev dependencies
- [x] Create docker-compose.yml for Neo4j + PostgreSQL (pgvector) + API
- [x] Create backend/src/config.py for API keys and connections
- [x] Initialize frontend with Vite + React + TypeScript

## Phase 2: Data Ingestion

- [x] Create backend/src/data_ingestion/csv_parser.py - parse and clean CSV
- [x] Create backend/src/data_ingestion/kg_loader.py - load into Neo4j
- [x] Create backend/src/data_ingestion/pg_loader.py - load into PostgreSQL + embeddings
- [x] Run ingestion and verify data in both databases

## Phase 3: Query Engine

- [x] Create backend/src/query_engine/intent_parser.py - LLM query understanding
- [x] Create backend/src/query_engine/kg_query.py - Cypher query builder
- [x] Create backend/src/query_engine/pg_query.py - SQL + vector queries
- [x] Create backend/src/query_engine/fusion.py - combine and rank results
- [x] Test query engine with sample queries

## Phase 4: Backend API

- [x] Create backend/src/api/main.py - FastAPI app
- [x] Create backend/src/api/routes.py - /search, /search-stream, /recipes/{id}, /health, /recipes/preview
- [x] Add CORS configuration for frontend
- [x] Create backend/Dockerfile

## Phase 5: Backend Tests

- [x] Create backend/tests/conftest.py - pytest fixtures (mock DBs, test data)
- [x] Create backend/tests/test_csv_parser.py - CSV parsing and cleaning
- [x] Create backend/tests/test_intent_parser.py - LLM intent extraction (mock OpenAI)
- [x] Create backend/tests/test_kg_query.py - Cypher query generation
- [x] Create backend/tests/test_pg_query.py - SQL + vector query generation
- [x] Create backend/tests/test_api.py - FastAPI endpoint tests (including SSE streaming)
- [x] Run tests: `uv run pytest` (49 tests passing)

## Phase 6: Frontend

- [x] Set up API service layer (src/services/api.ts) with SSE streaming support
- [x] Create RecipeAssistant conversational interface component
- [x] Create RecipeCard recipe results component
- [x] Create QueryBreakdown component showing parsed intent
- [x] Display query source breakdown (KG/SQL/Vector) for demo
- [x] Add example query suggestions
- [x] Create frontend/Dockerfile

### Additional Features Implemented

- [x] ThinkingPanel component - real-time LLM reasoning visibility
- [x] SSE streaming - character-by-character reasoning display with phase indicators
- [x] Auto-retry with broadened search on zero results
- [x] Recipe image preview fetching from source URLs
- [x] Loading skeleton UI during search
- [x] Case-insensitive ingredient matching (Neo4j + PostgreSQL)

## Phase 7: Local Integration Testing

- [x] Run full stack with `docker-compose up`
- [x] Verify Neo4j browser accessible at localhost:7474
- [x] Verify PostgreSQL connection and pgvector extension
- [x] Run data ingestion scripts
- [x] Verify data in both databases (counts, sample queries)
- [x] Test API endpoints manually (curl/Postman)
- [x] Test frontend search functionality end-to-end
- [x] Verify query source breakdown displays correctly (KG/SQL/Vector)
- [x] Test all demo queries

## Phase 8: AWS Deployment (EC2 + Docker Compose)

- [x] Create docker-compose.prod.yml (production config, nginx for frontend)
- [x] Create .env.example and ops/deploy.sh helper script
- [ ] Launch EC2 instance (t3.medium+)
- [ ] Install Docker + Docker Compose on EC2
- [ ] Clone repo and configure environment variables
- [ ] Run `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Run data ingestion on EC2 (`./ops/deploy.sh --ingest`)
- [ ] Configure security groups (ports 80, 443)
- [ ] End-to-end testing with EC2 public IP

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────────┐ │
│  │RecipeAssistant│  │ThinkingPanel│  │RecipeCard + QueryBreak │ │
│  │(Conversational│  │(Real-time   │  │down (Results Display)  │ │
│  │ Search UI)   │  │ LLM Reasoning│  │                        │ │
│  └──────────────┘  └─────────────┘  └────────────────────────┘ │
│                          │ SSE Stream                           │
└──────────────────────────┼──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│  /search-stream (SSE) │ /search │ /recipes/{id} │ /health      │
└───────────────────────┼─────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Query Engine                               │
│  ┌───────────────┐  ┌───────────┐  ┌───────────┐               │
│  │ Intent Parser │→ │ KG Query  │  │ PG Query  │               │
│  │ (OpenAI LLM)  │  │ (Cypher)  │  │(SQL+Vector)│               │
│  └───────────────┘  └─────┬─────┘  └─────┬─────┘               │
│                           └──────┬───────┘                      │
│                                  ▼                              │
│                         ┌─────────────┐                         │
│                         │   Fusion    │                         │
│                         │ (Rank+Merge)│                         │
│                         └─────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌─────────────────┐
│     Neo4j       │           │   PostgreSQL    │
│ Knowledge Graph │           │   + pgvector    │
│  (Ingredients)  │           │  (Recipes+Emb)  │
└─────────────────┘           └─────────────────┘
```

## Demo Queries to Test

- "Indian vegetarian quick" → SQL filters + vector ranking
- "healthy breakfast under 20 minutes" → SQL time filter + semantic search
- "comfort food for dinner" → Vector-heavy (semantic concept)
- "recipes with chicken and rice" → KG ingredient relationships
- "easy dessert" → Vector search + course filter
